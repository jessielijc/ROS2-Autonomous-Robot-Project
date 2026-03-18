#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <std_msgs/msg/bool.hpp>
#include <std_srvs/srv/set_bool.hpp>
#include <thread>
#include <atomic>

std::atomic<bool> g_grasp_triggered(false);

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  auto node = rclcpp::Node::make_shared("arm_driver");

  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  std::thread([&executor]() { executor.spin(); }).detach();

  // 1. 订阅触发信号 (由视觉脚本发送)
  auto sub = node->create_subscription<std_msgs::msg::Bool>(
    "/start_grasp_trigger", 10,
    [&](const std_msgs::msg::Bool::SharedPtr msg) {
      if (msg->data) g_grasp_triggered = true;
    });

  // 2. 发布任务完成信号 (发给手势主控)
  auto pub_finished = node->create_publisher<std_msgs::msg::Bool>("/grasp_finished", 10);

  auto toggle_vacuum = [node](bool enable) {
    auto client = node->create_client<std_srvs::srv::SetBool>("/gripper/switch");
    if (client->wait_for_service(std::chrono::seconds(2))) {
      auto req = std::make_shared<std_srvs::srv::SetBool::Request>();
      req->data = enable; client->async_send_request(req);
    }
  };

  moveit::planning_interface::MoveGroupInterface move_group_arm(node, "arm");
  moveit::planning_interface::MoveGroupInterface move_group_gripper(node, "gripper");
  
  // 提速配置
  move_group_arm.setMaxVelocityScalingFactor(1.0);
  move_group_gripper.setMaxVelocityScalingFactor(1.0);

  RCLCPP_INFO(node->get_logger(), ">>> 机械臂系统已就绪...");

  while (rclcpp::ok()) {
    if (g_grasp_triggered) {
      RCLCPP_INFO(node->get_logger(), "🚀 执行全自动动作中...");
      
      // 执行序列
      move_group_gripper.setNamedTarget("open"); move_group_gripper.move();
      move_group_arm.setNamedTarget("approach"); move_group_arm.move();
      move_group_arm.setNamedTarget("ready"); move_group_arm.move();
      
      toggle_vacuum(true);
      std::this_thread::sleep_for(std::chrono::seconds(1));
      
      move_group_gripper.setNamedTarget("close"); move_group_gripper.asyncMove();
      std::this_thread::sleep_for(std::chrono::seconds(2));
      
      move_group_arm.setNamedTarget("home"); move_group_arm.move();

      RCLCPP_INFO(node->get_logger(), "✅ 完成，通知主控恢复手动。");
      std_msgs::msg::Bool finish_msg; finish_msg.data = true;
      pub_finished->publish(finish_msg);

      g_grasp_triggered = false;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
  }
  rclcpp::shutdown(); return 0;
}
