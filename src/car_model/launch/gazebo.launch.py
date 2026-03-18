import os
import xacro
import numpy as np  # 新增这行
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_name = 'car_model'
    pkg_share = get_package_share_directory(pkg_name)
    gazebo_ros_pkg = get_package_share_directory('gazebo_ros')
   
    #world_file_name = 'my_world.world'
    world_file_name = 'jessie_world.world'
    world_path = os.path.join(pkg_share, 'worlds', world_file_name)
    
    xacro_file = os.path.join(pkg_share, 'urdf', 'car_model.xacro')
    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc)
    robot_desc = doc.toxml()

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_pkg, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_path,
            'pause': 'false'
        }.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': robot_desc},
            {'use_sim_time': True}
        ]
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'car_model',
            '-topic', '/robot_description',
            '-x', '0.1',
            '-y', '0.05',
            '-z', '0.05',
            '-Y', '0.0',      
        ],
        output='screen'
    )

    return LaunchDescription([
        gazebo_server,
        robot_state_publisher,
        spawn_entity
    ])
