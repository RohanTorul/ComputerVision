#!/usr/bin/env python
import rospy
import math
import numpy as np
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Vector3, Quaternion
from tf.transformations import quaternion_from_euler, euler_from_quaternion

class ROS_interface:
    def __init__(self):
        """
        ROS interface for UAV navigation and gimbal control
        Handles elevation, distance, and bearing data with gimbal orientation
        """
        rospy.init_node('uav_gimbal_controller')
        
        # Navigation metrics
        self.elevation = 0.0      # Angle in degrees
        self.distance = 0.0       # Distance in meters
        self.bearing = 0.0        # Bearing in degrees (-180 to 180)
        self.bank_angle = 0.0     # Bank angle in degrees
        self.pitch_angle = 0.0    # Pitch angle in degrees
        
        # Gimbal angles (Euler angles in radians)
        self.current_theta0 = 0.0  # Rotation around z-axis (yaw)
        self.current_theta1 = 0.0  # Rotation around y-axis (pitch)
        self.current_theta2 = 0.0  # Rotation around x-axis (roll)
        
        # ROS Publishers/Subscribers
        self.gimbal_pub = rospy.Publisher('/gimbal_control', JointState, queue_size=10)
        rospy.Subscriber('/joint_states', JointState, self.joint_states_callback)
        
        # PID parameters
        self.Kp = 0.8  # Proportional gain
        self.Ki = 0.01 # Integral gain
        self.Kd = 0.1  # Derivative gain
        self.integral_error = [0.0, 0.0, 0.0]
        self.last_error = [0.0, 0.0, 0.0]
        
    def update_metrics(self, elevation, distance, bearing, bank_angle, pitch_angle):
        """
        Update the navigation metrics
        :param elevation: Angle in degrees (positive = above horizon)
        :param distance: Distance in meters
        :param bearing: Bearing in degrees (-180 to 180, 0 = straight ahead)
        :param bank_angle: Bank angle in degrees
        :param pitch_angle: Pitch angle in degrees
        """
        self.elevation = elevation
        self.distance = distance
        self.bearing = bearing
        self.bank_angle = bank_angle
        self.pitch_angle = pitch_angle
        
    def joint_states_callback(self, msg):
        """
        Callback for current joint states (gimbal angles)
        """
        try:
            # Assuming joint names are 'gimbal_yaw', 'gimbal_pitch', 'gimbal_roll'
            self.current_theta0 = msg.position[msg.name.index('gimbal_yaw')]
            self.current_theta1 = msg.position[msg.name.index('gimbal_pitch')]
            self.current_theta2 = msg.position[msg.name.index('gimbal_roll')]
        except ValueError:
            rospy.logwarn("Gimbal joint names not found in joint_states")
            
    def get_current_gimble_theta(self):
        """
        Get the current gimbal angles (theta0, theta1, theta2)
        :return: Tuple of angles in radians (theta0, theta1, theta2)
        """
        return (self.current_theta0, self.current_theta1, self.current_theta2)
    
    def set_gimble_theta(self, target_theta0, target_theta1, target_theta2):
        """
        Set the gimbal angles (theta0, theta1, theta2)
        :param theta0: Angle in radians for gimbal 0 (z-axis)
        :param theta1: Angle in radians for gimbal 1 (y-axis)
        :param theta2: Angle in radians for gimbal 2 (x-axis)
        """
        gimbal_cmd = JointState()
        gimbal_cmd.name = ['gimbal_yaw', 'gimbal_pitch', 'gimbal_roll']
        gimbal_cmd.position = [target_theta0, target_theta1, target_theta2]
        self.gimbal_pub.publish(gimbal_cmd)
        
    def calculate_current_orientation(self):
        """
        Calculate the current end effector orientation in ground frame
        :return: Rotation matrix (Rx, Ry, Rz) in ground frame
        """
        # Convert gimbal angles to rotation matrix
        # Note: Order of rotations matters (typically Z-Y-X)
        Rz = np.array([
            [math.cos(self.current_theta0), -math.sin(self.current_theta0), 0],
            [math.sin(self.current_theta0), math.cos(self.current_theta0), 0],
            [0, 0, 1]
        ])
        
        Ry = np.array([
            [math.cos(self.current_theta1), 0, math.sin(self.current_theta1)],
            [0, 1, 0],
            [-math.sin(self.current_theta1), 0, math.cos(self.current_theta1)]
        ])
        
        Rx = np.array([
            [1, 0, 0],
            [0, math.cos(self.current_theta2), -math.sin(self.current_theta2)],
            [0, math.sin(self.current_theta2), math.cos(self.current_theta2)]
        ])
        
        # Combined rotation (Z-Y-X order)
        R = Rz @ Ry @ Rx
        
        # Account for UAV orientation (bank and pitch)
        bank_rad = math.radians(self.bank_angle)
        pitch_rad = math.radians(self.pitch_angle)
        
        R_bank = np.array([
            [1, 0, 0],
            [0, math.cos(bank_rad), -math.sin(bank_rad)],
            [0, math.sin(bank_rad), math.cos(bank_rad)]
        ])
        
        R_pitch = np.array([
            [math.cos(pitch_rad), 0, math.sin(pitch_rad)],
            [0, 1, 0],
            [-math.sin(pitch_rad), 0, math.cos(pitch_rad)]
        ])
        
        # Final orientation in ground frame
        R_ground = R_pitch @ R_bank @ R
        
        return R_ground
        
    def calculate_target_orientation(self):
        """
        Calculate target gimbal angles to point at target
        :return: Tuple of target angles in radians (theta0, theta1, theta2)
        """
        # Convert to radians
        bearing_rad = math.radians(self.bearing)
        elevation_rad = math.radians(self.elevation)
        
        # Theta0 (yaw) should point toward the bearing
        target_theta0 = bearing_rad
        
        # Theta1 (pitch) should account for elevation
        target_theta1 = elevation_rad
        
        # Theta2 (roll) compensates for UAV bank angle to keep camera level
        target_theta2 = -math.radians(self.bank_angle)
        
        return (target_theta0, target_theta1, target_theta2)
        
    # def calculate_target_thetas(self):
    #     """
    #     Alias for calculate_target_orientation
    #     """
    #     return self.calculate_target_orientation()
        
    def calculate_pid(self, target_angle, current_angle, axis):
        """
        Calculate PID control signal
        :param target_angle: Target angle in radians
        :param current_angle: Current angle in radians
        :param axis: Axis index (0=z, 1=y, 2=x)
        :return: PID control output in radians
        """
        error = target_angle - current_angle
        
        # Proportional term
        p = self.Kp * error
        
        # Integral term (with anti-windup)
        self.integral_error[axis] += error
        i = self.Ki * self.integral_error[axis]
        
        # Derivative term
        d = self.Kd * (error - self.last_error[axis])
        self.last_error[axis] = error
        
        return p + i + d
        
    def set_gimble_thetas_pid(self, theta0, theta1, theta2):
        """
        Set gimbal angles using PID control
        :param theta0: Target angle in radians for gimbal 0 (z-axis)
        :param theta1: Target angle in radians for gimbal 1 (y-axis)
        :param theta2: Target angle in radians for gimbal 2 (x-axis)
        """
        current_theta0, current_theta1, current_theta2 = self.get_current_gimble_theta()
        
        pid_theta0 = current_theta0 + self.calculate_pid(theta0, current_theta0, 0)
        pid_theta1 = current_theta1 + self.calculate_pid(theta1, current_theta1, 1)
        pid_theta2 = current_theta2 + self.calculate_pid(theta2, current_theta2, 2)
        
        self.set_gimble_theta(pid_theta0, pid_theta1, pid_theta2)
        
    def auto_point_gimbal(self):
        """
        Automatically point gimbal at target using PID control
        """
        target_thetas = self.calculate_target_orientation()
        self.set_gimble_thetas_pid(*target_thetas)

if __name__ == "__main__":
    try:
        controller = ROS_interface()
        
        # Example usage
        rate = rospy.Rate(10)  # 10Hz
        while not rospy.is_shutdown():
            # Simulate detecting target at 30° bearing, 15° elevation, 50m distance
            # With UAV at 10° bank and 5° pitch
            controller.update_metrics(
                elevation=15.0,
                distance=50.0,
                bearing=30.0,
                bank_angle=10.0,
                pitch_angle=5.0
            )
            
            # Auto-point gimbal
            controller.auto_point_gimbal()
            
            rate.sleep()
            
    except rospy.ROSInterruptException:
        pass