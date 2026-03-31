# Integrated ROS 2 Mobile Manipulator: A Multimodal Control Tutorial

This repository provides a complete framework for an autonomous **Mobile Manipulator** (3-DOF arm + differential drive base) using **ROS 2 Humble**. 

The system integrates **SLAM**, **Nav2**, **MoveIt 2**, **OpenCV**, and **Human-Robot Interaction (HRI)** via voice and gesture.

---

## 🛠 Hardware Architecture
The robot features a custom-designed chassis:
*   **Locomotion**: Differential drive (2 rear driving wheels + 1 front caster).
*   **Manipulation**: 3-Degree-of-Freedom (DOF) robotic arm.
*   **Sensors**: 2D LiDAR, Depth Camera, and Microphone.

---

## 📦 Prerequisites & Installation
Ensure you have ROS 2 Humble and Gazebo 11 installed.

```bash
# Install core dependencies
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup \
                 ros-humble-moveit ros-humble-slam-toolbox \
                 ros-humble-cv-bridge python3-pip
# Install HRI libraries
pip install mediapipe vosk pyaudio
```

---

## 🗺 Tutorial 1: Autonomous Navigation (SLAM & Nav2)
Learn how to make the robot perceive its environment and move autonomously.

### 1.1 SLAM Mapping
Launch the SLAM Toolbox to create a 2D occupancy grid map.
1. Run `ros2 launch car_model start_slam.launch.py`
2. Use the keyboard to drive the robot around.
3. Save the map: `ros2 run nav2_map_server map_saver_cli -f my_map`

> **[GIF Placeholder: Robot scanning the room in RViz]**
> <!-- <img src="docs/gifs/slam_demo.gif" width="600"/> -->

### 1.2 Navigation & Initialization
Once the map is ready, use Nav2 for path planning.
1. Run `ros2 launch car_model navigation.launch.py`
2. **Crucial**: Use the "2D Pose Estimate" tool in RViz to align the LiDAR scan with the map.
3. Set a "Nav2 Goal" to watch the robot navigate avoiding obstacles.

---

## 🦾 Tutorial 2: Vision-Guided Grasping (MoveIt 2 & OpenCV)
Learn how to combine computer vision with motion planning to pick up objects.

### 2.1 Object Detection
The robot uses `OpenCV` to detect specific color blocks (red by default) and publishes target coordinates.
1. The `vision_detector_auto.py` node handles color segmentation and proximity calculation.

### 2.2 Grasping Execution
`MoveIt 2` handles the Inverse Kinematics (IK) and collision avoidance.
1. The `arm_driver.cpp` script executes a synchronized sequence: `Approach -> Open -> Ready -> Vacuum Enable -> Close -> Home`.

> **[GIF Placeholder: Robot arm detecting and picking up a red block]**
> <!-- <img src="docs/gifs/grasping_demo.gif" width="600"/> -->

---

## 🖐 Tutorial 3: Multimodal HRI (Gesture & Voice)
Control your robot using intuitive human commands.

### 3.1 Hand Gesture Control (MediaPipe)
The system tracks 21 hand landmarks to trigger different tasks:
*   **Fist (0)**: Manual Teleop mode (Move hand outside the center box to drive).
*   **Digit 1**: Trigger Navigation to Point A.
*   **Digit 2**: Trigger Autonomous Search & Grasp mission.
*   **Digit 3**: Trigger Navigation back to Home.

> **[GIF Placeholder: Switching modes using hand gestures with the progress bar]**
> <!-- <img src="docs/gifs/gesture_ui_demo.gif" width="600"/> -->

### 3.2 Voice Command (Vosk)
Supports offline Chinese/English voice commands like "Forward", "Grasp", or "Navigate" to trigger the state machine.

---

## 🌍 Tutorial 4: Creating Custom 3D Worlds in Gazebo
To build your own testing environment:
1. Open Gazebo: `gazebo`
2. Go to **Edit -> Building Editor** (Ctrl+B).
3. Draw walls, add windows/doors, and save it as a `model`.
4. Insert your building into a new world and save as `.world` in the `worlds/` folder.
5. Update the `world_file` path in your launch scripts.

---

## 🚀 Engineering Challenges Solved (Debug Log)
This project serves as a showcase of problem-solving in robotics:
*   **Fixed Joint Lumping**: Prevented Gazebo from merging the `grasp_link` into the arm, ensuring the vacuum plugin could find the link.
*   **TF Mirroring**: Corrected a 180-degree navigation error by re-aligning the `base_link` X-axis and LiDAR data start-angle.
*   **Multi-Threaded UI**: Implemented `MultiThreadedExecutor` in Python to prevent OpenCV window freezes during heavy Nav2/MoveIt tasks.
*   **Physics Tuning**: Optimized `kp/kd` contact parameters and added a `vacuum_gripper` plugin to overcome friction simulation instability.

---

## 🛠 Tech Stack
*   **MiddleWare**: ROS 2 Humble
*   **Simulation**: Gazebo 11 (Classic)
*   **Planning**: MoveIt 2, Nav2 (Simple Commander API)
*   **Vision**: OpenCV, MediaPipe
*   **Voice**: Vosk (Offline)
*   **Modeling**: SolidWorks to URDF

