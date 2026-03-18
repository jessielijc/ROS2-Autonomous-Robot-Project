import os
import xacro  # 1. 必须导入 xacro 库
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_name = 'car_model'
    share_dir = get_package_share_directory(pkg_name)
    
    # 获取 xacro 文件路径
    xacro_file = os.path.join(share_dir, 'urdf', 'car_model.xacro')
    
    # RViz 配置文件路径
    rviz_config_file = os.path.join(share_dir, 'urdf.rviz')

    # =======================================================================
    # 2. 核心修改：解析 Xacro 文件 (编译成 XML)
    # =======================================================================
    # 不要用 open().read()，那是读纯文本的
    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc)
    robot_desc = doc.toxml() # 这一步把 xacro 变成了机器人能看懂的 xml
    # =======================================================================

    return LaunchDescription([
        # 1. 启动 robot_state_publisher (发布 TF)
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_desc}]
        ),

        # 2. 启动 joint_state_publisher_gui (通过 GUI 控制关节)
        # 注意：如果你同时运行了 Gazebo，这个节点最好关掉，否则会和 Gazebo 的物理引擎打架
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen'
        ),

        # 3. 启动 RViz2
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen'
        ),
    ])
