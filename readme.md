# car_swarm

ROS 2 Humble 双轮差速小车上位机，配合 `~/STM32Cube/car_swarm` 的 STM32 + TB6612 固件。

- `mycar_base`：差速控制、HEX PWM 串口、IMU 和 EKF。
- `mycar_cartographer`：N10 雷达 + IMU 建图。
- `mycar_navigation2`：Nav2 导航。
- `wit_ros2_imu`：从 `imu_test` 当前使用的维特驱动复制而来。

**不需要编码器。IMU 提供姿态和角速度，线速度由运动指令估计；这不能提供编码器那样的实测轮速和距离。** EKF 不使用 IMU 加速度二次积分位置。

## 编译

在新终端执行，避免混入 `my_roscar` 等同名包的旧环境：

```bash
source /opt/ros/humble/setup.bash
cd ~/car_swarm
colcon build --symlink-install --parallel-workers 2
source install/setup.bash
```

依赖 ROS 2 Humble、ros2_control、robot_localization、Cartographer、Nav2 和 Python 的 pyserial。新设备需要先安装相应依赖。

## Jetson Orin NX 首次编译

适用于 Ubuntu 22.04 ARM64，并要求已安装 ROS 2 Humble。在 NX 的工作空间目录执行：

```bash
# 先安装底盘和 IMU 的依赖并编译这两个包。
bash nx_build.sh base

# 底盘和 IMU 验证后，再安装建图、导航依赖并编译全部包。
bash nx_build.sh all
```

脚本用 rosdep 安装依赖并在 NX 上编译，不自动启动电机；日志保存在工作空间根目录。
串口用户需要在 `dialout` 组：`sudo usermod -aG dialout "$USER"`，新增组权限后需注销并重新登录。

## 启动

每个新终端先执行：

```bash
source /opt/ros/humble/setup.bash
source ~/car_swarm/install/setup.bash
```

默认 STM32 为 `/dev/ttyUSB0`，IMU 为 `/dev/ttyUSB1`，两者均为 115200、8N1；N10 雷达默认 `/dev/ttyACM0`。

下面三种启动方式选择一种，建图和导航都已包含底盘、IMU、EKF，勿重复启动：

```bash
# 仅底盘和IMU，按实际串口修改参数。
ros2 launch mycar_base base.launch.py serial_port:=/dev/ttyUSB0 imu_port:=/dev/ttyUSB1

# 建图；串口参数与上面相同。
ros2 launch mycar_cartographer mapping.launch.py

# 导航；使用 mycar_navigation2/maps/map.yaml。
ros2 launch mycar_navigation2 navigation.launch.py
```

建图后保存地图：

```bash
ros2 run nav2_map_server map_saver_cli -f ~/car_swarm/src/mycar_navigation2/maps/map
```

## 检查和控制

```bash
ros2 topic echo /imu/data --once
ros2 topic echo /odom --once
ros2 control list_controllers

# 低速前进；Ctrl+C停止发送后，控制器约0.5秒后清零指令。
ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.05}, angular: {z: 0.0}}"
```

`/imu/data` 是标准 IMU 数据，`/imu/angle` 是角度制欧拉角；`/odom_raw` 是指令估计里程计，`/odom` 是 EKF 融合结果。只有 EKF 发布 `odom → base_link`，建图或 AMCL 发布 `map → odom`。

## 首次需要调整

- 轮半径初值 **0.0325 m**、轮距初值 **0.125 m**：同时修改 `src/mycar_base/config/controllers.yaml` 和 `src/mycar_base/urdf/mycar.urdf.xacro`。
- `max_rpm` 默认 **100**，表示满 PWM 时轮速的初始标定值，需实测校准；启动时可加 `max_rpm:=实际值`。左右差异可在 Xacro 中调整 `left_pwm_scale`、`right_pwm_scale`。
- IMU 安装位置和姿态：修改 Xacro 的 `imu_joint`；默认 x 向前、y 向左、z 向上，小车逆时针转动时 yaw 和 z 轴角速度应增加。
- IMU 默认输出 100 Hz，可用 `imu_rate:=200` 调整；波特率可用 `imu_baud:=115200` 调整。
- 没有编码器时，位置仍是估计值，电压、负载和打滑都会影响距离；建图、导航效果需要实车验证。

## STM32 通信

发送和回包都是8字节二进制，左右PWM为有符号16位大端数，范围 **−3599～+3599**：

```text
AA 55 左高 左低 右高 右低 0D 0A
AA 55 03 E8 FC 18 0D 0A    左+1000，右-1000
AA 55 00 00 00 00 0D 0A    停车
```

上位机以50 Hz发送。STM32超过500 ms未收到有效包会停车，回包只确认PWM指令，不是实测轮速。左右顺序与当前STM32固件一致，方向修正在STM32的 `L_REV`、`R_REV` 中完成。
