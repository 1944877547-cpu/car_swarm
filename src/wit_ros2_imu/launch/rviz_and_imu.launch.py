from pathlib import Path
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # 沿用原入口名称，统一到可配置端口的IMU启动文件。
    return LaunchDescription([IncludeLaunchDescription(PythonLaunchDescriptionSource(
        str(Path(__file__).with_name('demo.launch.py'))))])
