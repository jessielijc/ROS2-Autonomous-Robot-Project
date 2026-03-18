cmake_minimum_required(VERSION 3.8)
project(car_model)

# 1. 设置 C++ 标准
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
endif()

# 编译警告
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ==================== 2. 查找依赖 ====================
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED) 
find_package(std_srvs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_visual_tools REQUIRED)
find_package(moveit_core REQUIRED)      
find_package(moveit_ros_planning REQUIRED)
find_package(moveit_msgs REQUIRED)

# ==================== 3. 定义 C++ 可执行文件 ====================
add_executable(arm_driver src/arm_driver.cpp)
add_executable(arm_release src/arm_release.cpp)

# ==================== 4. 自动链接依赖 ====================
# 定义一个变量存放公共依赖，省得写两遍
set(MOVEIT_DEPS
  rclcpp
  geometry_msgs
  std_msgs
  std_srvs
  moveit_ros_planning_interface
  moveit_visual_tools
  moveit_core
  moveit_ros_planning
  moveit_msgs
)

ament_target_dependencies(arm_driver ${MOVEIT_DEPS})
ament_target_dependencies(arm_release ${MOVEIT_DEPS})

# ==================== 5. 安装 C++ 可执行文件 ====================
install(TARGETS 
  arm_driver 
  arm_release 
  DESTINATION lib/${PROJECT_NAME}
)

# ==================== 6. 安装 Python 脚本 ====================
install(PROGRAMS
  scripts/vision_detector_auto.py
  scripts/gesture_control.py
  # 如果还有其他脚本，请继续添加
  DESTINATION lib/${PROJECT_NAME}
)

# ==================== 7. 安装资源目录 ====================
install(DIRECTORY
  config
  launch
  meshes
  urdf
  worlds
  maps
  DESTINATION share/${PROJECT_NAME}
)

# ==================== 8. 导出包 ====================
ament_package()
