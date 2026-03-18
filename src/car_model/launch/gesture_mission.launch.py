import os
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # 1. 加载 MoveIt 模型配置参数 (必须提供给 arm_driver 和 arm_release)
    # 确保 package_name 与你的 MoveIt 配置包名一致
    moveit_config = MoveItConfigsBuilder("car_model", package_name="car_model_moveit_config").to_moveit_configs()

    # 2. 机械臂[抓取]驱动节点 (C++)
    arm_driver_node = Node(
        package='car_model',
        executable='arm_driver',
        output='screen',
        parameters=[
            moveit_config.to_dict(),
            {'use_sim_time': True}
        ]
    )

    # 3. 机械臂[放下]驱动节点 (C++)
    arm_release_node = Node(
        package='car_model',
        executable='arm_release',
        output='screen',
        parameters=[
            moveit_config.to_dict(),
            {'use_sim_time': True}
        ]
    )

    # 4. 视觉自动对准节点 (Python)
    vision_node = Node(
        package='car_model',
        executable='vision_detector_auto.py',
        name='vision_detector',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    # 5. 手势主控节点 (Python - 处理 1, 2, 3 手势逻辑)
    gesture_node = Node(
        package='car_model',
        executable='gesture_control.py',
        name='gesture_control',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        arm_driver_node,
        arm_release_node,
        vision_node,
        gesture_node
    ])
