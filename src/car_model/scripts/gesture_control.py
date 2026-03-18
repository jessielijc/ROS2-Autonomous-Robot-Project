#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import Twist, PoseStamped
from std_msgs.msg import Bool
import cv2
import mediapipe as mp
import numpy as np
import threading
import time
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

class GestureMissionMaster(Node):
    def __init__(self):
        super().__init__('gesture_mission_master')
        self.state = "MANUAL"
        
        # 计时器与确认逻辑
        self.last_detected_gesture = -1  
        self.gesture_start_time = 0.0    
        self.confirm_duration = 1.0  
        
        # UI 样式
        self.bar_color = (255, 150, 255) # 浅紫色
        self.font_style = cv2.FONT_HERSHEY_COMPLEX 
        self.box_size = 100 

        # 发布者
        self.pub_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_vision_enable = self.create_publisher(Bool, '/enable_vision', 10)
        self.pub_release = self.create_publisher(Bool, '/start_release_trigger', 10)
        
        # 订阅反馈
        self.create_subscription(Bool, '/grasp_finished', self.grasp_done_cb, 10)
        self.create_subscription(Bool, '/release_finished', self.release_done_cb, 10)

        # 导航器初始化
        self.get_logger().info(">>> 正在连接 Nav2 服务器...")
        self.nav = BasicNavigator()
        
        # 视觉初始化
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8)
        self.mp_draw = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            self.get_logger().error("❌ 无法打开摄像头！检查设备连接。")

    def create_pose(self, x, y, w=1.0):
        """助手函数：创建一个 PoseStamped 消息"""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.w = w
        return pose

    def stop_all_actions(self):
        """取消当前所有后台任务，强制停下小车"""
        self.nav.cancelTask()
        self.pub_vision_enable.publish(Bool(data=False))
        self.pub_vel.publish(Twist())

    def grasp_done_cb(self, msg):
        if msg.data and self.state == "AUTO_GRASPING":
            self.get_logger().info("📦 抓取完成！开始多途径点导航前往 B 点...")
            self.state = "NAV_TO_B"
            # 开启新线程执行导航，不阻塞主画面刷新
            threading.Thread(target=self.navigate_to_b, daemon=True).start()

    def release_done_cb(self, msg):
        if msg.data:
            self.get_logger().info("🏁 卸货完成，恢复手动手势模式。")
            self.state = "MANUAL"

    def navigate_to_a(self):
        """导航至位置 A"""
        goal = self.create_pose(-0.7242, 5.1663)
        self.nav.goToPose(goal)
        while not self.nav.isTaskComplete():
            time.sleep(0.1)
        if self.nav.getResult() == TaskResult.SUCCEEDED:
            self.get_logger().info("🎯 已到达位置 A")
            self.state = "MANUAL"

    def navigate_to_b(self):
        """核心修改：按照指定顺序穿过途径点前往 B 点"""
        # 1. 定义三个途径点 (使用你提供的新坐标)
        wp1 = self.create_pose(0.7979291677474976, 3.7896153926849365)
        wp2 = self.create_pose(-0.025931628420948982, 1.766912817955017)
        wp3 = self.create_pose(-6.12554407119751, 2.684091567993164)
        
        # 2. 最终目标点 B
        final_b = self.create_pose(-7.037160873413086, 0.31587284803390503)

        # 3. 合并路径列表
        path = [wp1, wp2, wp3, final_b]

        # 4. 执行多点导航指令
        self.nav.goThroughPoses(path)

        # 5. 轮询导航状态
        while not self.nav.isTaskComplete():
            time.sleep(0.1)

        # 6. 到达终点后的逻辑
        if self.nav.getResult() == TaskResult.SUCCEEDED:
            self.get_logger().info("📍 已顺利穿过所有途径点并到达 B 点，正在放下物体...")
            self.state = "RELEASING"
            self.pub_release.publish(Bool(data=True)) # 触发 arm_release.cpp

    def navigate_home(self):
        """导航回原点"""
        goal = self.create_pose(0.0, 0.0)
        self.nav.goToPose(goal)
        while not self.nav.isTaskComplete():
            time.sleep(0.1)
        if self.nav.getResult() == TaskResult.SUCCEEDED:
            self.state = "MANUAL"

    def process_image(self):
        """处理图像、识别手势并计算控制指令"""
        ret, frame = self.cap.read()
        if not ret: return None
        
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        
        # 绘制中心死区方框 (黄色)
        cv2.rectangle(frame, (cx-self.box_size, cy-self.box_size), (cx+self.box_size, cy+self.box_size), (255, 255, 0), 1)
        
        results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        current_gesture = -1 
        twist = Twist()

        if results.multi_hand_landmarks:
            hand_lms = results.multi_hand_landmarks[0]
            self.mp_draw.draw_landmarks(frame, hand_lms, self.mp_hands.HAND_CONNECTIONS)
            
            f = [0,0,0,0] # 食, 中, 无, 小
            if hand_lms.landmark[8].y < hand_lms.landmark[6].y: f[0]=1
            if hand_lms.landmark[12].y < hand_lms.landmark[10].y: f[1]=1
            if hand_lms.landmark[16].y < hand_lms.landmark[14].y: f[2]=1
            if hand_lms.landmark[20].y < hand_lms.landmark[18].y: f[3]=1
            up = sum(f)

            # 手势逻辑：1-食指, 2-食中, 3-三指, 0-握拳
            if up == 1 and f[0] == 1: current_gesture = 1
            elif up == 2: current_gesture = 2
            elif up == 3: current_gesture = 3
            elif up == 0: current_gesture = 0 

            # 切换/触发逻辑
            if current_gesture != -1 and self.is_new_command(current_gesture):
                if current_gesture == self.last_detected_gesture:
                    elapsed = time.time() - self.gesture_start_time
                    progress = min(elapsed / self.confirm_duration, 1.0)
                    
                    # 绘制进度条 (浅紫色)
                    bar_w = 400
                    bx, by = (w - bar_w) // 2, h - 80
                    cv2.rectangle(frame, (bx, by), (bx + bar_w, by + 25), (255, 255, 255), 1)
                    cv2.rectangle(frame, (bx, by), (bx + int(bar_w * progress), by + 25), self.bar_color, -1)
                    cv2.putText(frame, f"SWITCHING TO {current_gesture}...", (bx, by - 15), self.font_style, 0.6, self.bar_color, 1)

                    if elapsed >= self.confirm_duration:
                        self.stop_all_actions()
                        self.execute_task(current_gesture)
                        self.last_detected_gesture = -1
                else:
                    self.last_detected_gesture = current_gesture
                    self.gesture_start_time = time.time()
            else:
                # 握拳控制逻辑
                if self.state == "MANUAL" and current_gesture == 0:
                    self.apply_teleop(hand_lms, w, h, cx, cy, frame)
                self.last_detected_gesture = -1
        else:
            self.last_detected_gesture = -1

        # UI 状态文字
        s_color = (0, 255, 0) if self.state == "MANUAL" else (0, 255, 255)
        cv2.putText(frame, f"STATUS: {self.state}", (20, 50), self.font_style, 0.8, s_color, 2)
        return frame

    def is_new_command(self, g):
        """判断当前手势是否为切换状态的新手势"""
        if self.state == "MANUAL" and g != 0: return True
        if self.state != "MANUAL" and g != -1: return True
        return False

    def execute_task(self, g):
        """触发不同手势对应的任务"""
        if g == 1:
            self.state = "NAV_TO_A"
            threading.Thread(target=self.navigate_to_a, daemon=True).start()
        elif g == 2:
            self.state = "AUTO_GRASPING"
            self.pub_vision_enable.publish(Bool(data=True)) # 激活 vision_detector_auto.py
        elif g == 3:
            self.state = "NAV_TO_HOME"
            threading.Thread(target=self.navigate_home, daemon=True).start()
        elif g == 0:
            self.state = "MANUAL"
            self.get_logger().info("✔ 已切回手动控制模式")

    def apply_teleop(self, hand_lms, w, h, cx, cy, frame):
        """握拳手动开车逻辑"""
        twist = Twist()
        px, py = int(hand_lms.landmark[9].x * w), int(hand_lms.landmark[9].y * h)
        cv2.circle(frame, (px, py), 10, (0, 255, 0), -1)
        if py < cy - self.box_size: twist.linear.x = 0.5    
        elif py > cy + self.box_size: twist.linear.x = -0.5 
        if px < cx - self.box_size: twist.angular.z = 0.8   
        elif px > cx + self.box_size: twist.angular.z = -0.8
        self.pub_vel.publish(twist)

def main():
    rclpy.init()
    node = GestureMissionMaster()
    
    # 使用多线程执行器处理 ROS 通讯，防止导航阻塞 GUI
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    try:
        while rclpy.ok():
            display_frame = node.process_image()
            if display_frame is not None:
                cv2.imshow("Omni Gesture Mission Hub", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        node.cap.release()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__': main()
