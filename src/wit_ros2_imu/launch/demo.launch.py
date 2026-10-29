from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('port', default_value='/dev/ttyUSB1'),
        DeclareLaunchArgument('baud', default_value='115200'),
        DeclareLaunchArgument('rate_hz', default_value='100'),
        Node(package='wit_ros2_imu', executable='wit_ros2_imu', output='screen',
             parameters=[{'port': LaunchConfiguration('port'),
                          'baud': ParameterValue(LaunchConfiguration('baud'), value_type=int),
                          'rate_hz': ParameterValue(LaunchConfiguration('rate_hz'), value_type=int)}],
             remappings=[('imu/data_raw', '/imu/data')]),
    ])
