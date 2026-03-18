import os
import yaml
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import xacro

def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    try:
        with open(absolute_file_path, "r") as file:
            return yaml.safe_load(file)
    except EnvironmentError:
        return None

def generate_launch_description():
    moveit_config_pkg = 'car_model_moveit_config'
    robot_pkg = 'car_model'
    
    # 加载URDF（你的xacro文件）
    xacro_file = os.path.join(get_package_share_directory(robot_pkg), 'urdf', 'car_model.xacro')
    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc)
    robot_description = {'robot_description': doc.toxml()}
    
    # 加载SRDF（语义描述）
    srdf_file = os.path.join(get_package_share_directory(moveit_config_pkg), 'config', 'car_model.srdf')
    with open(srdf_file, 'r') as f:
        robot_description_semantic = {'robot_description_semantic': f.read()}
    
    # 加载kinematics等YAML配置
    kinematics_yaml = load_yaml(moveit_config_pkg, 'config/kinematics.yaml')
    ompl_yaml = load_yaml(moveit_config_pkg, 'config/ompl_planning.yaml')
    planning_pipelines = {'planning_pipelines': ['ompl'], 'ompl': ompl_yaml}
    moveit_controllers = load_yaml(moveit_config_pkg, 'config/moveit_controllers.yaml')
    
    # 组合MoveIt参数
    moveit_params = {}
    moveit_params.update(robot_description)
    moveit_params.update(robot_description_semantic)
    moveit_params.update({'robot_description_kinematics': kinematics_yaml})
    moveit_params.update(planning_pipelines)
    moveit_params.update(moveit_controllers)
    moveit_params.update({'use_sim_time': True})
    moveit_params.update({'trajectory_execution.allowed_start_tolerance': 10.0})  # 宽松容忍度，避免启动时规划失败
    
    # 包括Gazebo launch（你的第一个文件）
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory(robot_pkg), 'launch', 'gazebo.launch.py')
        )
    )
    
    # MoveIt move_group节点
    run_move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_params],
    )
    
    # RViz节点（使用你的MoveIt RViz配置）
    run_rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", os.path.join(get_package_share_directory(moveit_config_pkg), "config", "moveit.rviz")],
        parameters=[
            robot_description,
            robot_description_semantic,
            {'robot_description_kinematics': kinematics_yaml},
            {'use_sim_time': True}
        ],
    )
    
    # Spawn控制器（joint_state_broadcaster必须先spawn，因为它发布/joint_states）
    spawn_jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
        output="screen"
    )
    
    spawn_arm = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller", "-c", "/controller_manager"],
        output="screen"
    )
    
    spawn_grip = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "-c", "/controller_manager"],
        output="screen"
    )
    
    # 注意：这里我们不启动joint_state_publisher！如果你的MoveIt config有默认的demo.launch包括它，别用demo.launch。
    
    return LaunchDescription([
        gazebo_launch,  # 先启动Gazebo
        TimerAction(period=5.0, actions=[run_move_group_node]),  # 延时5s启动MoveIt（等Gazebo准备好）
        TimerAction(period=8.0, actions=[run_rviz_node]),  # 延时8s启动RViz（等MoveIt准备好）
        TimerAction(period=10.0, actions=[spawn_jsb]),  # 延时10s spawn joint_state_broadcaster
        TimerAction(period=12.0, actions=[spawn_arm, spawn_grip]),  # 再spawn臂和夹爪控制器
    ])
