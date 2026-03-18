#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from cv_bridge import CvBridge
import cv2
import numpy as np

class RedObjectDetector(Node):
    def __init__(self):
        super().__init__('vision_detector')

        # 1. 设置 QoS (防止连不上)
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # 2. 订阅话题
        self.subscription = self.create_subscription(
            Image,
            '/camera_sensor/image_raw',
            self.image_callback,
            qos_profile)
        
        self.publisher_ = self.create_publisher(Bool, '/start_grasp_trigger', 10)
        self.bridge = CvBridge()
        self.grasp_triggered = False

        print(">>> 视觉节点启动！等待画面...")

    def image_callback(self, msg):
        if self.grasp_triggered:
            return

        try:
            # 尝试转换图片
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            # 如果报错，打印出来但不闪退
            print(f"图像转换错误: {e}")
            return

        # --- 调试：检查图片是不是全黑 ---
        if np.max(cv_image) == 0:
            print("⚠️ 警告：画面全黑！请检查 Gazebo 里是否有光，或者摄像头是否被遮挡！", end="\r")
        # ----------------------------

        h, w, _ = cv_image.shape
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        
        # 红色范围
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        mask = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        target_found = False
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500: 
                x, y, w_box, h_box = cv2.boundingRect(cnt)
                center_x = x + w_box / 2
                
                # 画框
                cv2.rectangle(cv_image, (x, y), (x+w_box, y+h_box), (0, 255, 0), 2)
                
                # 判断中心
                if abs(center_x - w/2) < 50: 
                    target_found = True
                    cv2.putText(cv_image, "LOCKED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 显示窗口 (加了 try-except 防止 OpenCV 报错崩溃)
        try:
            cv2.imshow("Robot Vision", cv_image)
            cv2.waitKey(1)
        except Exception as e:
            print(f"显示错误: {e}")

        if target_found:
            print("\n>>> ✅ 锁定红色目标！发送抓取指令！")
            msg = Bool()
            msg.data = True
            self.publisher_.publish(msg)
            self.grasp_triggered = True 
            # 发送后不关闭节点，保持显示，方便演示

def main(args=None):
    rclpy.init(args=args)
    node = RedObjectDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
