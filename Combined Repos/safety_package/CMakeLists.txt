cmake_minimum_required(VERSION 3.5)
project(safety_package)

# std::optional in safety_node.cpp needs C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(ackermann_msgs REQUIRED)

# C++ node: ros2 run safety_package safety_node_cpp
add_executable(safety_node_cpp src/safety_node.cpp)
ament_target_dependencies(safety_node_cpp
  rclcpp
  sensor_msgs
  nav_msgs
  ackermann_msgs
)
install(TARGETS safety_node_cpp
  DESTINATION lib/${PROJECT_NAME}
)

# Python node: ros2 run safety_package safety_node
ament_python_install_package(${PROJECT_NAME})
install(PROGRAMS safety_package/safety_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME safety_node
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_copyright test/test_copyright.py)
  ament_add_pytest_test(test_flake8 test/test_flake8.py)
  ament_add_pytest_test(test_pep257 test/test_pep257.py)
endif()

ament_package()
