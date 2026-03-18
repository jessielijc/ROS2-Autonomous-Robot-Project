from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_move_group_launch

def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("car_model", package_name="car_model_moveit_config").to_moveit_configs()

    return LaunchDescription([
        # 启动 MoveGroup（提供 robot_description 和 SRDF）
        *generate_move_group_launch(moveit_config).entities,

        # 启动你的 C++ 抓取控制器
        Node(
            package='car_model',
            executable='grasp_controller',
            name='grasp_controller',
            output='screen',
        ),
    ])
