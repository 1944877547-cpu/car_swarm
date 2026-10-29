#!/usr/bin/env bash
# 在 NX 的 car_swarm 目录运行：bash nx_build.sh base（底盘+IMU），或 all（全部包）。
set -eo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
log_file="$PWD/nx_build_$(date +%Y%m%d_%H%M%S)_$$.log"
exec > >(tee "$log_file") 2>&1
trap 'echo "编译在第 $LINENO 行停止，日志：$log_file"' ERR

# 只针对当前 NX 的 Ubuntu 22.04 / ARM64 / ROS 2 Humble。
if [ "$(uname -m)" != aarch64 ]; then
  echo "请在 NX 终端运行此脚本，当前机器不是 ARM64。"
  exit 1
fi
source /etc/os-release
if [ "$ID" != ubuntu ] || [ "$VERSION_ID" != 22.04 ]; then
  echo "此脚本适用于 Ubuntu 22.04，当前系统：$PRETTY_NAME"
  exit 1
fi
if [ ! -f /opt/ros/humble/setup.bash ]; then
  echo "未找到 ROS 2 Humble，请先确认 NX 的 ROS 安装。"
  exit 1
fi

case "${1:-base}" in
  base)
    paths=(src/mycar_base src/wit_ros2_imu)
    packages=(--packages-up-to mycar_base)
    ;;
  all)
    paths=(src)
    packages=()
    ;;
  *) echo "用法：bash nx_build.sh base 或 bash nx_build.sh all"; exit 1 ;;
esac
for path in "${paths[@]}"; do
  test -d "$path"
done

# 清除其他 ROS 工作空间的路径，避免编译时引用旧的同名包。
unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH ROS_PACKAGE_PATH
unset PYTHONPATH LD_LIBRARY_PATH ROS_DISTRO ROS_VERSION ROS_PYTHON_VERSION
source /opt/ros/humble/setup.bash

# 只安装编译工具和本项目依赖，不进行整机升级。
tools=(build-essential cmake python3-colcon-common-extensions python3-serial)
if ! command -v rosdep >/dev/null 2>&1; then
  tools+=(python3-rosdep)
fi
sudo apt-get update
sudo apt-get install -y "${tools[@]}"
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  sudo rosdep init
fi
rosdep update --rosdistro humble
rosdep install --from-paths "${paths[@]}" --ignore-src --rosdistro humble -y

# 逐个编译包，每个包最多使用两个编译任务，减少 NX 内存占用。
CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS=-j2 \
  colcon build --symlink-install --executor sequential "${packages[@]}" \
  --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/local_setup.bash
ros2 pkg prefix mycar_base
ros2 pkg prefix wit_ros2_imu
echo "编译完成，日志：$log_file"
echo "新终端先 source /opt/ros/humble/setup.bash，再 source $PWD/install/local_setup.bash。"
echo "串口确认后，再按 readme.md 启动底盘和 IMU。"
