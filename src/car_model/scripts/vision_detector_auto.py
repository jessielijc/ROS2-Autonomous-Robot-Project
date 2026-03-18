#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from cv_bridge import CvBridge
import cv2
import numpy as np
import math
import time

class AutoApproachNode(Node):
    def __init__(self):
        super().__init__('auto_approach_node')
        self.active = False 
        self.grasp_triggered = False
        self.start_search_time = 0.0

        self.sub_enable = self.create_subscription(Bool, '/enable_vision', self.enable_cb, 10)
        self.sub_image = self.create_subscription(Image, '/camera_sensor/image_raw', self.image_callback, 10)
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_trigger = self.create_publisher(Bool, '/start_grasp_trigger', 10)
        self.pub_finish = self.create_publisher(Bool, '/grasp_finished', 10) 
        
        self.bridge = CvBridge()
        self.search_speed = 0.6
        self.timeout = 22.0

    def enable_cb(self, msg):
        self.active = msg.data
        if self.active:
            self.grasp_triggered = False
            self.start_search_time = time.time()
            self.get_logger().info("🎯 视觉节点：激活")

    def image_callback(self, msg):
        if not self.active or self.grasp_triggered: return

        try:
            img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except: return

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([0,100,100]), np.array([10,255,255])) + \
               cv2.inRange(hsv, np.array([160,100,100]), np.array([180,255,255]))
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        largest_cnt = max(contours, key=cv2.contourArea) if contours and cv2.contourArea(max(contours, key=cv2.contourArea)) > 500 else None

        twist = Twist()
        if largest_cnt is not None:
            area = cv2.contourArea(largest_cnt)
            x, y, w_box, h_box = cv2.boundingRect(largest_cnt)
            err_x = (img.shape[1]/2.0) - (x + w_box/2.0)
            err_area = 32000.0 - area

            twist.angular.z = 0.005 * err_x
            if abs(err_x) < 40 and abs(err_area) < 1000:
                self.pub_cmd_vel.publish(Twist())
                self.pub_trigger.publish(Bool(data=True)) # 🟢 触发抓取
                self.grasp_triggered = True; self.active = False
            else:
                twist.linear.x = np.clip(0.00005 * err_area, -0.15, 0.25)
            self.pub_cmd_vel.publish(twist)
        else:
            # 转圈寻物
            if time.time() - self.start_search_time > self.timeout:
                self.active = False; self.pub_finish.publish(Bool(data=True))
            else:
                twist.angular.z = self.search_speed; self.pub_cmd_vel.publish(twist)

        cv2.imshow("Vision Tracking", img); cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args); rclpy.spin(AutoApproachNode()); rclpy.shutdown()

if __name__ == '__main__': main()
