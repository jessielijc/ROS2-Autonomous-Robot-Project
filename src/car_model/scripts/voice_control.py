#!/usr/bin/env python3
import os
import sys
import json
import pyaudio
import threading
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from std_msgs.msg import Bool
from vosk import Model, KaldiRecognizer
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

class VoiceMasterNode(Node):
    def __init__(self):
        super().__init__('class_world_voice')
        
        # 1. 状态机: MANUAL (手动语音), AUTO_GRASP (抓取中), NAVIGATING (导航中)
        self.state = "MANUAL"
        
        # 2. 发布者与订阅者
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_vision_enable = self.create_publisher(Bool, '/enable_vision', 10)
        self.sub_finish = self.create_subscription(Bool, '/grasp_finished', self.grasp_finish_callback, 10)
        
        # 🟢 3. 初始化 Nav2 导航接口
        self.navigator = BasicNavigator()
        
        # Vosk 模型加载 (请确保路径正确)
        model_path = "/home/jessie/vosk-model-small-cn-0.22"
        if not os.path.exists(model_path):
            self.get_logger().error(f"找不到模型文件: {model_path}")
            sys.exit(1)
            
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        
        self.speed = 0.3
        self.turn = 0.8
        self.current_twist = Twist()

        # 启动语音识别线程
        self.thread = threading.Thread(target=self.run_voice_recognition)
        self.thread.daemon = True
        self.thread.start()

        self.get_logger().info(">>> 🎙️ 系统就绪！指令：前进、后退、左转、右转、停止、抓取、导航")

    def grasp_finish_callback(self, msg):
        """机械臂抓取完后由 arm_driver.cpp 发回信号"""
        if msg.data:
            self.get_logger().info("🏁 抓取任务圆满完成，切回语音控制。")
            self.state = "MANUAL"

    def send_navigation_goal(self):
        """执行导航逻辑"""
        self.state = "NAVIGATING"
        self.get_logger().info("📍 正在启动导航前往预设终点...")
        
        # 导航前先让小车静止
        self.pub_cmd_vel.publish(Twist())

        # 设置终点位姿
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        
        # ==========================================
        # 🟢 关键：在这里填入你刚才在 RViz 里查到的坐标
        goal_pose.pose.position.x = 5.412400722503662  # 替换这里的 X
        goal_pose.pose.position.y = 5.350781440734863 # 替换这里的 Y
        goal_pose.pose.orientation.w = 0.0025634765625 # 朝向
        # ==========================================

        # 发送目标给 Nav2
        self.navigator.goToPose(goal_pose)
        
        # 轮询直到导航结束
        while not self.navigator.isTaskComplete():
            time.sleep(1.0)

        result = self.navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info("🎉 已成功到达目的地！切回语音模式。")
        else:
            self.get_logger().warn("❌ 导航未能到达目标。")
        
        self.state = "MANUAL"

    def run_voice_recognition(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        stream.start_stream()

        while rclpy.ok():
            data = stream.read(4000, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result['text'].replace(" ", "")
                if text:
                    self.get_logger().info(f"🎤 听到: {text}")
                    self.handle_command(text)
            
            # 手动模式下发布速度指令
            if self.state == "MANUAL":
                self.pub_cmd_vel.publish(self.current_twist)

    def handle_command(self, text):
        if self.state != "MANUAL":
            return

        # 前后左右停...
        if "前进" in text:
            self.current_twist.linear.x = self.speed
            self.current_twist.angular.z = 0.0
        elif "后退" in text:
            self.current_twist.linear.x = -self.speed
            self.current_twist.angular.z = 0.0
        elif "左" in text:
            self.current_twist.angular.z = self.turn
        elif "右" in text:
            self.current_twist.angular.z = -self.turn
        elif "停" in text:
            self.current_twist = Twist()
            self.pub_cmd_vel.publish(self.current_twist)

        # --- 任务触发 ---
        elif "抓" in text or "拿" in text or "开始" in text:
            self.get_logger().info("🚀 语音触发：开始视觉对准抓取")
            self.state = "AUTO_GRASP"
            self.current_twist = Twist() # 停止当前移动
            self.pub_cmd_vel.publish(self.current_twist)
            # 激活视觉脚本
            msg = Bool(data=True)
            self.pub_vision_enable.publish(msg)

        elif "导航" in text or "去终点" in text:
            self.get_logger().info("🧭 语音触发：自动导航中...")
            # 开新线程防止导航过程卡死语音识别
            threading.Thread(target=self.send_navigation_goal).start()

def main():
    rclpy.init()
    node = VoiceMasterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
