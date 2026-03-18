import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # 1. 获取 MoveIt 配置 (必须提供给 arm_driver)
    moveit_config = MoveItConfigsBuilder("car_model", package_name="car_model_moveit_config").to_moveit_configs()

    return LaunchDescription([
        # 机械臂 C++ 驱动
        Node(
            package='car_model',
            executable='arm_driver',
            output='screen',
            parameters=[moveit_config.to_dict(), {'use_sim_time': True}]
        ),
        
        # 视觉自动对准 Python
        Node(
            package='car_model',
            executable='vision_detector_auto.py',
            output='screen',
            parameters=[{'use_sim_time': True}]
        ),
        
        # 语音总控 Python
        Node(
            package='car_model',
            executable='voice_control.py',
            output='screen',
            parameters=[{'use_sim_time': True}]
        )
    ])
