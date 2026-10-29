import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    base_share = get_package_share_directory('mycar_base')
    cartographer_share = get_package_share_directory('mycar_cartographer')
    lidar_share = get_package_share_directory('lslidar_driver')

    use_sim_time = LaunchConfiguration('use_sim_time')
    serial_port = LaunchConfiguration('serial_port')
    baud_rate = LaunchConfiguration('baud_rate')
    max_rpm = LaunchConfiguration('max_rpm')
    max_pwm = LaunchConfiguration('max_pwm')
    imu_port = LaunchConfiguration('imu_port')
    imu_baud = LaunchConfiguration('imu_baud')
    imu_rate = LaunchConfiguration('imu_rate')
    start_rviz = LaunchConfiguration('start_rviz')

    base = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_share, 'launch', 'base.launch.py')),
        launch_arguments={
            'serial_port': serial_port,
            'baud_rate': baud_rate,
            'max_rpm': max_rpm,
            'max_pwm': max_pwm,
            'imu_port': imu_port,
            'imu_baud': imu_baud,
            'imu_rate': imu_rate,
            'use_sim_time': use_sim_time,
        }.items(),
    )

    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(lidar_share, 'launch', 'lsn10_launch.py')),
        launch_arguments={'output': 'screen', 'log_level': 'warn'}.items(),
    )

    cartographer = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=[
            '-configuration_directory',
            os.path.join(cartographer_share, 'config'),
            '-configuration_basename', 'mycar_2d.lua',
        ],
        remappings=[('scan', '/scan'), ('odom', '/odom'), ('imu', '/imu/data')],
    )

    occupancy_grid = Node(
        package='cartographer_ros',
        executable='cartographer_occupancy_grid_node',
        name='cartographer_occupancy_grid_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=['-resolution', '0.05', '-publish_period_sec', '1.0'],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        condition=IfCondition(start_rviz),
        arguments=['-d', os.path.join(cartographer_share, 'rviz', 'mycar_cartographer.rviz')],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB0'),
        DeclareLaunchArgument('baud_rate', default_value='115200'),
        DeclareLaunchArgument('max_rpm', default_value='100.0'),
        DeclareLaunchArgument('max_pwm', default_value='3599'),
        DeclareLaunchArgument('imu_port', default_value='/dev/ttyUSB1'),
        DeclareLaunchArgument('imu_baud', default_value='115200'),
        DeclareLaunchArgument('imu_rate', default_value='100'),
        DeclareLaunchArgument('start_rviz', default_value='true'),
        base,
        lidar,
        cartographer,
        occupancy_grid,
        rviz,
    ])
