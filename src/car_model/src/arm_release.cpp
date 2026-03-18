#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <std_msgs/msg/bool.hpp>
#include <std_srvs/srv/set_bool.hpp>
#include <thread>
#include <atomic>

std::atomic<bool> g_release_triggered(false);

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  auto node = rclcpp::Node::make_shared("arm_release");

  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  std::thread([&executor]() { executor.spin(); }).detach();

  // 1. 订阅放下信号
  auto sub = node->create_subscription<std_msgs::msg::Bool>(
    "/start_release_trigger", 10,
    [&](const std_msgs::msg::Bool::SharedPtr msg) {
      if (msg->data) g_release_triggered = true;
    });

  // 2. 发布任务完成信号
  auto pub_finished = node->create_publisher<std_msgs::msg::Bool>("/release_finished", 10);

  // 吸盘控制客户端
  auto toggle_vacuum = [node](bool enable) {
    auto client = node->create_client<std_srvs::srv::SetBool>("/gripper/switch");
    if (client->wait_for_service(std::chrono::seconds(2))) {
      auto req = std::make_shared<std_srvs::srv::SetBool::Request>();
      req->data = enable; 
      client->async_send_request(req);
    }
  };

  moveit::planning_interface::MoveGroupInterface move_group_arm(node, "arm");
  moveit::planning_interface::MoveGroupInterface move_group_gripper(node, "gripper");
  move_group_arm.setMaxVelocityScalingFactor(1.0);
  move_group_gripper.setMaxVelocityScalingFactor(1.0);

  RCLCPP_INFO(node->get_logger(), ">>> 机械臂[放下]系统就绪...");

  while (rclcpp::ok()) {
    if (g_release_triggered) {
      RCLCPP_INFO(node->get_logger(), "🚀 执行放下序列...");

      // Step 1: 移动到 approach 姿态（物体上方）
      move_group_arm.setStartStateToCurrentState();
      move_group_arm.setNamedTarget("approach");
      move_group_arm.move();

      // Step 2: 移动到 ready 姿态（接触地面/托盘）
      move_group_arm.setStartStateToCurrentState();
      move_group_arm.setNamedTarget("ready");
      move_group_arm.move();

      // Step 3: 释放吸盘 + 张开夹爪
      toggle_vacuum(false); // 释放物体
      std::this_thread::sleep_for(std::chrono::milliseconds(500));
      move_group_gripper.setNamedTarget("open");
      move_group_gripper.move();

      // Step 4: 返回 approach（避开物体）
      move_group_arm.setStartStateToCurrentState();
      move_group_arm.setNamedTarget("approach");
      move_group_arm.move();

      // Step 5: 返回 Home
      move_group_arm.setNamedTarget("home");
      move_group_arm.move();

      RCLCPP_INFO(node->get_logger(), "✅ 物体已放下，发送完成信号。");
      std_msgs::msg::Bool finish_msg; finish_msg.data = true;
      pub_finished->publish(finish_msg);

      g_release_triggered = false;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
  }
  rclcpp::shutdown(); return 0;
}
