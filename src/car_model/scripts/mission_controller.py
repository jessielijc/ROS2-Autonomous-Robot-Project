#!/usr/bin/env python3
import rclpy
import time
from rclpy.node import Node
from moveit.planning import MoveItPy

def main():
    rclpy.init()
    
    print(">>> 正在初始化 MoveItPy (可能需要几秒钟)...")
    # 注意：这里的 node_name 并不重要，重要的是 Launch 文件传进来的参数
    car_robot = MoveItPy(node_name="mission_controller")
    
    # 获取规划组
    arm = car_robot.planning_component("arm")
    gripper = car_robot.planning_component("gripper")
    
    print(">>> MoveItPy 初始化成功！")
    time.sleep(2.0) # 等待一下，让它同步 Gazebo 的状态

    # ----------------------------
    # 动作 1: 去 Ready
    # ----------------------------
    print("\n>>> [1/3] 规划前往 Ready...")
    arm.set_start_state_to_current_state()
    arm.set_goal_state(configuration_name="ready") # 确保 SRDF 里有这个名字
    
    plan_result = arm.plan()
    
    if plan_result:
        print("    规划成功，执行中...")
        arm.execute()
        print("    到达 Ready！")
    else:
        print("    Ready 规划失败！(可能是目标不可达)")

    time.sleep(2.0)

    # ----------------------------
    # 动作 2: 张开爪子 (Open)
    # ----------------------------
    print("\n>>> [2/3] 张开夹爪...")
    # 如果 SRDF 里没定义 open，可以用关节值
    # gripper.set_goal_state(configuration_name="open") 
    
    # 也可以直接设置关节目标 (0.015 是全开)
    robot_state = car_robot.get_current_state()
    robot_state.set_joint_group_positions("gripper", [0.015])
    gripper.set_goal_state(robot_state=robot_state)

    plan_result = gripper.plan()
    if plan_result:
        gripper.execute()
    
    time.sleep(1.0)

    # ----------------------------
    # 动作 3: 回家 (Home)
    # ----------------------------
    print("\n>>> [3/3] 回家...")
    arm.set_start_state_to_current_state()
    arm.set_goal_state(configuration_name="home")
    
    plan_result = arm.plan()
    if plan_result:
        arm.execute()
        print(">>> 任务全部完成！")
    
    rclpy.shutdown()

if __name__ == "__main__":
    main()
