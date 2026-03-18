from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. 机械臂驱动
        Node(
            package='car_model',
            executable='arm_driver',
            output='screen'
        ),
        # 2. 视觉对准
        Node(
            package='car_model',
            executable='vision_detector_auto.py',
            output='screen'
        ),
        # 3. 手势主控 (带 UI 显示)
        Node(
            package='car_model',
            executable='gesture_control.py',
            output='screen'
        )
    ])
