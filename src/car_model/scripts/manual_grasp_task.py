#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
import time

class ArmCommander(Node):
    def __init__(self):
        super().__init__('manual_grasp_commander')
        
        print(">>> 正在连接控制器...")
        self.arm_client = ActionClient(self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')
        self.gripper_client = ActionClient(self, FollowJointTrajectory, '/gripper_controller/follow_joint_trajectory')
        
        # 等待服务连接
        if not self.arm_client.wait_for_server(timeout_sec=10.0):
            print("❌ 连接手臂控制器失败！")
            return
        if not self.gripper_client.wait_for_server(timeout_sec=10.0):
            print("❌ 连接夹爪控制器失败！")
            return
        print("✅ 控制器连接成功！")

    def send_goal(self, client, joint_names, positions, duration=2.0):
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = joint_names
        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start.sec = int(duration)
        point.time_from_start.nanosec = int((duration - int(duration)) * 1e9)
        goal.trajectory.points = [point]
        
        future = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        time.sleep(duration + 0.2) # 等待动作物理完成

def main(args=None):
    rclpy.init(args=args)
    bot = ArmCommander()
    
    # === 关键关节定义 ===
    arm_joints = ['joint1', 'joint2', 'joint3']
    gripper_joints = ['paw1_joint']

    # === 关键姿态数据 (弧度) ===
    # ⚠️ 请根据你在 RViz 里试出来的数值微调这里！
    POSES = {
        "home":  [0.0, 0.0, 0.0],       # 直立
        "ready": [0.0, 1.2, 1.2],       # 前伸准备
        "grasp": [0.0, 1.5, 0.8],       # 下探抓取 (如果不准，去RViz里看Joints面板的值)
        "lift":  [0.0, 1.2, 0.5],       # 抓到后举起
    }
    GRIPPER = {
        "open":  [0.02], # 张开
        "close": [0.0],  # 闭合
    }

    try:
        # --- 阶段 1: 等待发车 ---
        print("\n" + "="*40)
        print("🚗 阶段 1: 人工驾驶模式")
        print("请在另一个终端用键盘控制小车移动到目标位置。")
        input("👉 到达位置停稳后，请按 [回车键] 开始抓取...")
        print("="*40)

        # --- 阶段 2: 自动抓取 ---
        print("\n🤖 开始执行抓取序列...")
        
        print("1. 伸出手臂 (Ready)...")
        bot.send_goal(bot.arm_client, arm_joints, POSES["ready"], 3.0)

        print("2. 张开爪子...")
        bot.send_goal(bot.gripper_client, gripper_joints, GRIPPER["open"], 1.0)

        print("3. 下探抓取 (Grasp)...")
        bot.send_goal(bot.arm_client, arm_joints, POSES["grasp"], 2.0)

        print("4. 闭合爪子 (Close)...")
        bot.send_goal(bot.gripper_client, gripper_joints, GRIPPER["close"], 1.0)

        print("5. 举起物体 (Lift)...")
        bot.send_goal(bot.arm_client, arm_joints, POSES["lift"], 2.0)

        print("6. 收回手臂 (Home)...")
        bot.send_goal(bot.arm_client, arm_joints, POSES["home"], 3.0)

        print("\n✅ 抓取完成！")
        print("="*40)
        
        # --- 阶段 3: 等待返航 ---
        print("🚗 阶段 3: 返航模式")
        print("现在你可以用键盘把车开回去了。")
        input("👉 任务结束后，按 [回车键] 退出程序...")

    except KeyboardInterrupt:
        pass
    finally:
        bot.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
