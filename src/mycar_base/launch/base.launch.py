from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('mycar_base')
    defaults = {
        'serial_port': '/dev/ttyUSB0',
        'baud_rate': '115200',
        'imu_port': '/dev/ttyUSB1',
        'imu_baud': '115200',
        'imu_rate': '100',
        'max_rpm': '100.0',
        'max_pwm': '3599',
        'use_sim_time': 'false',
    }
    args = {name: LaunchConfiguration(name) for name in defaults}
    sim = ParameterValue(args['use_sim_time'], value_type=bool)
    description = ParameterValue(Command([
        'xacro ', share + '/urdf/mycar.urdf.xacro',
        ' serial_port:=', args['serial_port'],
        ' baud_rate:=', args['baud_rate'],
        ' max_rpm:=', args['max_rpm'],
        ' max_pwm:=', args['max_pwm'],
    ]), value_type=str)

    control = Node(
        package='controller_manager', executable='ros2_control_node', output='screen',
        parameters=[{'robot_description': description, 'use_sim_time': sim},
                    share + '/config/controllers.yaml'],
        remappings=[('/diff_drive_controller/cmd_vel_unstamped', '/cmd_vel'),
                    ('/diff_drive_controller/odom', '/odom_raw')],
    )
    state = Node(
        package='robot_state_publisher', executable='robot_state_publisher', output='screen',
        parameters=[{'robot_description': description, 'use_sim_time': sim}],
    )
    imu = Node(
        package='wit_ros2_imu', executable='wit_ros2_imu', name='imu_driver_node', output='screen',
        parameters=[{'port': args['imu_port'],
                     'baud': ParameterValue(args['imu_baud'], value_type=int),
                     'rate_hz': ParameterValue(args['imu_rate'], value_type=int),
                     'use_sim_time': sim}],
        remappings=[('imu/data_raw', '/imu/data')],
    )
    ekf = Node(
        package='robot_localization', executable='ekf_node', name='ekf_filter_node', output='screen',
        parameters=[share + '/config/ekf.yaml', {'use_sim_time': sim}],
        remappings=[('odometry/filtered', '/odom')],
    )
    spawners = [Node(
        package='controller_manager', executable='spawner', output='screen',
        arguments=[name, '--controller-manager', '/controller_manager'],
    ) for name in ['joint_state_broadcaster', 'diff_drive_controller']]
    # 核心节点退出时一起退出，避免留下仍占用串口的孤立进程。
    handlers = [RegisterEventHandler(OnProcessExit(
        target_action=node,
        on_exit=[EmitEvent(event=Shutdown(reason='A base node exited'))],
    )) for node in [control, imu, ekf]]
    return LaunchDescription(
        [DeclareLaunchArgument(name, default_value=value) for name, value in defaults.items()]
        + handlers + [state, control, imu, ekf] + spawners)
