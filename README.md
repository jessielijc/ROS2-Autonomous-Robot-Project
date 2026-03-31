




#  ROS 2 Omni-Bot: Fully Autonomous Mobile Arm with Gesture Control, Voice Interaction & SLAM

This repository provides a highly integrated, end-to-end autonomous mobile manipulation system built on **ROS 2 Humble**. It features a custom 3-DOF robotic arm on a differential-drive base. The robot can be operated via offline voice recognition or real-time hand gestures, seamlessly transitioning into autonomous visual target searching, precision grasping, and SLAM-based navigation.

---

## Workspace Initialization
Before running any mission, we must compile the workspace. This ensures all custom C++ nodes, Python scripts, URDF/XACRO models, and parameter files are correctly linked.

Open a terminal and run:
```bash
cd ~/project_ws
colcon build --symlink-install
source install/setup.bash
```
*(Tip: Using `--symlink-install` allows you to modify Python scripts and XACRO files without needing to rebuild every time.)*

---

## Pipeline A: Gesture-Controlled Autonomous Mission

In this pipeline, we use a webcam and **Google MediaPipe** to translate skeletal hand tracking into complex robot commands. This features a UI with a progress bar for command confirmation.

### Step 1: Launch the Simulation Environment
Open **Terminal 1**:
```bash
ros2 launch car_model_moveit_config demo_gazebo.launch.py
```
**What happens here:**
* Gazebo (Classic) physics engine starts.
* The custom 3D house environment (`.world`) is loaded.
* The Omni-Bot is spawned into the world. The `ros2_control` hardware interface and `MoveIt 2` nodes are initialized in the background.

![1](https://github.com/user-attachments/assets/73bf9947-ec95-4642-93f3-033f837b31bf)
> <!-- <img src="docs/gifs/gazebo_spawn.gif" width="700"/> -->

### Step 2: Launch Navigation & RViz Localization (CRITICAL)
Open **Terminal 2**:
```bash
ros2 launch car_model navigation.launch.py
```
**How to manually localize the robot in RViz:**
When RViz opens, the robot might look "lost" (the map is gray, and the red LiDAR points do not align with the black walls). You must initialize the AMCL localization:
1. Look at your Gazebo window to see the robot's actual spawn location and heading (the direction the gripper is pointing).
2. Go to the RViz top toolbar and click the **"2D Pose Estimate"** button.
3. Move your mouse to the corresponding location on the RViz map.
4. **Click and HOLD the left mouse button**, then **drag the cursor** in the direction the robot is facing. A green arrow will appear.
5. **Release the mouse**. 
6. Look at the **red dots (LaserScan)**. They should now perfectly overlap the **black lines (walls)** on the map. If they don't, repeat steps 2-5 until they match perfectly.

![2](https://github.com/user-attachments/assets/e1b800d1-e73f-4541-8011-f8e699462899)
> <!-- <img src="docs/gifs/rviz_localization.gif" width="700"/> -->

### Step 3: Launch Gesture Mission & Execute
Open **Terminal 3**:
```bash
ros2 launch car_model gesture_mission.launch.py
```
**Detailed Operation Flow:**
A camera window will open showing your hand with a central yellow bounding box (Deadzone).

1. **Manual Teleop (Make a Fist ✊)**: 
   * Keep all fingers closed. Move your fist outside the yellow box. 
   * Up = Forward, Down = Backward, Left = Turn Left, Right = Turn Right.
![ezgif com-optimize](https://github.com/user-attachments/assets/5477dbe0-95bc-4b8a-bb79-ef781a2c6e75)
> <!-- <img src="docs/gifs/rviz_localization.gif" width="700"/> -->

2. **Navigate to Point A (Index Finger Up ☝️)**:
   * Hold up *only* your index finger.
   * A purple progress bar will appear at the bottom of the screen. **Hold the gesture still for 1 second** to confirm.
   * The robot will autonomously navigate to Point A.
![ezgif2 com-optimize](https://github.com/user-attachments/assets/7277bca9-2262-4c65-9b98-2fe7a9ba6442)
> <!-- <img src="docs/gifs/rviz_localization.gif" width="700"/> -->


3. **Vision Grasp & Multi-Waypoint Delivery (Peace Sign ✌️)**:
   * Hold up your index and middle fingers for 1 second.
   * The robot begins visual searching -> aligns with the red block -> grasps it.
   * Once grasped, the robot autonomously navigates through multiple waypoints (avoiding walls) to Point B, lowers the arm, releases the vacuum, and returns to the Home pose.
![ezgif3 com-optimize](https://github.com/user-attachments/assets/a424cf2f-396a-4c98-9369-5544a95949d2)
![ezgif4 com-optimize](https://github.com/user-attachments/assets/f320b372-5d2a-461a-8303-b5c3260d47f1)


**Preemption Feature**: You can interrupt any ongoing autonomous task! For example, while the robot is navigating to Point A, you can make a fist for 1 second to instantly cancel the navigation and regain manual chassis control.

> **[GIF Placeholder 3: Webcam view showing the hand tracking UI, progress bar filling up, and the robot executing the gesture commands in Gazebo]**
> <!-- <img src="docs/gifs/gesture_mission_full.gif" width="700"/> -->

---

## Pipeline B: Voice-Controlled Autonomous Mission

In this pipeline, the robot is commanded entirely via offline voice recognition (**Vosk**). It will drive around, autonomously search for a target, pick it up, and navigate to a final destination.

*Make sure to close all previous mission terminals before starting this pipeline.*

### Step 1 & Step 2: Environment & Navigation
Just like Pipeline A, start the environment and perform the RViz localization.
```bash
# Terminal 1
ros2 launch car_model_moveit_config demo_gazebo.launch.py

# Terminal 2
ros2 launch car_model navigation.launch.py
# (Perform 2D Pose Estimate in RViz as explained above)
```

### Step 3: Launch Voice Mission & Execute
Open **Terminal 3**:
```bash
ros2 launch car_model voice_mission.launch.py
```
**Detailed Operation Flow:**
1. **Manual Teleop**: Speak Chinese commands into your microphone: `"前进"` (Forward), `"后退"` (Backward), `"左"` (Left), `"右"` (Right), `"停"` (Stop). The robot will move accordingly via `/cmd_vel`.
2. **Autonomous Grasping**: Say `"抓取"` (Grasp). 
   * The robot overrides manual control and starts **spinning in place**.
   * The camera feed is processed using **OpenCV HSV Color Segmentation** to isolate the red block. Contour detection calculates the target's centroid and pixel area.
   * A PID controller aligns the robot's center with the block and drives it forward until a specific area threshold is reached.
   * **MoveIt 2** then executes the picking sequence: `Open -> Approach -> Ready -> Vacuum ON -> Close -> Home`.
3. **Autonomous Navigation**: After grasping, say `"导航"` (Navigate).
   * The Nav2 Simple Commander API sends a predefined goal coordinate to the behavior tree.
   * The robot plans a global path and autonomously drives to the destination while avoiding obstacles.

> **[GIF Placeholder 4: Voice commanding the robot -> Spinning to find the red block -> Robot arm picking it up -> Driving away via Nav2]**
> <!-- <img src="docs/gifs/voice_mission_full.gif" width="700"/> -->

---

## Core Technical Highlights
* **Robust Grasping Simulation**: Overcame default ODE friction limitations in Gazebo by implementing a `libgazebo_ros_vacuum_gripper` plugin, ensuring the block never drops during navigation.
* **Multi-Threaded Python Executors**: Implemented `MultiThreadedExecutor` in the Gesture Node to ensure OpenCV's GUI `cv2.imshow` runs smoothly at 30fps without being blocked by long-running Nav2 action client requests.
* **State Machine & Decoupling**: Designed a loosely coupled architecture. The vision detector (`vision_detector_auto.py`) acts as an independent service listening to `/enable_vision`, allowing it to be triggered by either Voice or Gesture controllers without code duplication.
