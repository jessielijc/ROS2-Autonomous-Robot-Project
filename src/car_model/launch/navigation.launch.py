import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_share = get_package_share_directory('car_model')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # 1. 路径定义
    map_yaml_path = os.path.join(pkg_share, 'maps', 'jessie_world.yaml')
    nav2_params_path = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    rviz_config_dir = os.path.join(nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('map', default_value=map_yaml_path),
        DeclareLaunchArgument('params_file', default_value=nav2_params_path),

        # 2. 启动 Nav2 Bringup
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
            ),
            launch_arguments={
                'map': map_yaml_path,
                'use_sim_time': 'true',
                'params_file': nav2_params_path,
                'autostart': 'true',
                'use_composition': 'False' # 🟢 关闭组合模式，增强参数传递稳定性
            }.items()
        ),

        # 3. 启动 RViz
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_dir, 'launch', 'rviz_launch.py')
            ),
            launch_arguments={
                'use_sim_time': 'true',
                'rviz_config': rviz_config_dir
            }.items()
        )
    ])
