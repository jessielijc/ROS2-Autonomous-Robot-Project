# ROS 2 Autonomous Multimodal Mobile Manipulator

This project features a fully integrated autonomous robot system developed using **ROS 2 Humble**. It coordinates a custom differential-drive mobile base with a 3-DOF robotic arm to perform vision-guided grasping tasks, driven by multimodal Human-Robot Interaction (HRI).

##  Key Technical Highlights
- **Autonomous Navigation Stack**: Utilized `SLAM Toolbox` for high-fidelity mapping and `Nav2` (AMCL) for robust localization and path planning.
- **Vision-Guided Manipulation**: Integrated `OpenCV` color segmentation for object detection and `MoveIt 2` (with KDL Kinematics Solver) for collision-free trajectory planning.
- **Multimodal HRI Interface**:
  - **Gesture Control**: Leveraged `Google MediaPipe` to translate hand skeletal data into chassis movement and task triggers (supporting logic for specific gestures 1, 2, and 3).
  - **Voice Control**: Integrated `Vosk` offline speech recognition for Chinese voice command processing.
- **Simulation Optimization**: Developed a high-fidelity Gazebo environment with customized physics parameters and custom world layouts.

##  Engineering Challenges & Solutions (Debug Log)
This project demonstrated significant problem-solving in robotics software engineering:
- **Kinematic Stability**: Resolved a chassis suspension issue caused by incorrect caster wheel dimensions in URDF.
- **TF Frame Alignment**: Fixed a 180-degree navigation mirroring error by recalibrating the `base_link` and Lidar coordinate frames.
- **Controller Synchronization**: Resolved real-time node conflicts between `MoveIt` virtual states and `ros2_control` hardware interfaces by configuring a unified state broadcaster.
- **Physics Simulation Fidelity**: Overcame ODE friction limitations in Gazebo by implementing a `libgazebo_ros_vacuum_gripper` plugin to ensure stable grasping.

##  System Architecture
- **Middleware**: ROS 2 Humble
- **Simulation**: Gazebo 11 (Classic)
- **Planning**: MoveIt 2, Nav2
- **Interaction**: MediaPipe, Vosk, OpenCV
- **Modeling**: SolidWorks to URDF

##  Demo
**to be released**

##  Quick Start
1. **Launch Environment**:
   `ros2 launch car_model_moveit_config demo_gazebo.launch.py`
2. **Start Navigation**:
   `ros2 launch car_model navigation.launch.py`
3. **Run Integrated Mission**:
   `ros2 launch car_model gesture_mission.launch.py`
