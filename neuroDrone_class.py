import os
import re
import sys
import time
import math
import pandas as pd
from time import sleep
from datetime import datetime
from dronekit import VehicleMode


# прямое управление ardupilot в режиме MAVLink CMD
class Drone:
    def __init__(self, vehicle):
        self.vehicle = vehicle

    def arm_and_takeoff(self, aTargetAltitude):
        """
        Arms vehicle and fly to aTargetAltitude.
        """
        print("Basic pre-arm checks")
        # Don't try to arm until autopilot is ready
        while not self.vehicle.is_armable:
            print(" Waiting for vehicle to initialise...")
            time.sleep(1)

        print("Arming motors")
        # Copter should arm in GUIDED mode
        self.vehicle.mode = VehicleMode("GUIDED")
        self.vehicle.armed = True

        # Confirm vehicle armed before attempting to take off
        while not self.vehicle.armed:
            print(" Waiting for arming...")
            time.sleep(1)

        print("Taking off!")
        self.vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
        #  after Vehicle.simple_takeoff will execute immediately).
        while True:
            print(" Altitude: ", self.vehicle.location.global_relative_frame.alt)
            # Break and return from function just below target altitude.
            if self.vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95:
                print("Reached target altitude")
                break
            time.sleep(1)


# классы подключения нейронок
#
#
# Uncomment the lines below for testing roll angle and yaw rate.
# Make sure that there is enough space for testing this.

#print("Test yaw")
# neuro_drone.set_attitude(roll_angle = 1, thrust = 0.5, duration = 30)
# neuro_drone.set_attitude(yaw_rate = 30, thrust = 0.5, duration = 30)

# Move the drone forward and backward.
# Note that it will be in front of original position due to inertia.

#print("Move forward")
# neuro_drone.set_attitude(pitch_angle = -pitch_angle_calc, roll_angle = roll_angle_calc, thrust = 0.5, duration = duration_calc)


#print("Move backward 7")
# neuro_drone.set_attitude(pitch_angle = pitch_angle_calc + 5, roll_angle = roll_angle_calc, thrust = 0.5, duration = duration_calc)
#print("Move backward 12")
# neuro_drone.set_attitude(pitch_angle = pitch_angle_calc + 10, roll_angle = roll_angle_calc, thrust = 0.5, duration = duration_calc)

class NeuroDrone:
    def __init__(self, config_data, file_path):
        self.resultData_dict = {field: [] for fields in config_data.values() for field in fields}
        self.config_data = config_data
        self.file_path = file_path

    def log_msg(self, message, drone_name, current_date):
        log_cols = []
        for msg_name, fields in self.config_data.items():
            log_cols.extend(fields)
        
        with open('log.txt', 'a') as log_file:
            log_file.write(str(message) + '\n')
        
        msg_name, msg_values = str(message).split(' {', 1)
        msg_values = '{' + msg_values

        values = re.findall(r'(\w+)\s:\s([-+]?\d+(?:\.\d+)?)', msg_values) 
        data = {key: float(value) for key, value in values}    

        if msg_name in self.config_data:
            fields = self.config_data[msg_name]      
            for field_name in fields:
                if field_name in data:
                    self.update_result_data(field_name, data[field_name])
                else:
                    #print(f"Поле {field_name} отсутствует в данных сообщения {msg_name}")
                    pass
        else:
            #print(f"Сообщение {msg_name} отсутствует в конфигурационных данных")
            pass
        
        all_filled = all(self.resultData_dict[key] for key in self.resultData_dict)
        
        if all_filled:
            resultData_DF = pd.DataFrame(self.resultData_dict)

            if os.path.exists(self.file_path):
                df = pd.read_pickle(self.file_path)
            else:
                df = pd.DataFrame(columns=log_cols)

            df = pd.concat([df, resultData_DF], ignore_index=True)
            df.to_pickle(self.file_path)
            # Создание пустого словаря для хранения данных
            self.resultData_dict = {field: [] for fields in self.config_data.values() for field in fields}

    def update_result_data(self, key, value):
        self.resultData_dict[key].append(value)

    def arm_and_takeoff_nogps(self, aTargetAltitude):
        DEFAULT_TAKEOFF_THRUST = 0.75
        SMOOTH_TAKEOFF_THRUST = 0.6

        print("Basic pre-arm checks")
        while not self.vehicle.is_armable:
            print(" Waiting for vehicle to initialise...")
            time.sleep(1)

        print("Arming motors")
        self.vehicle.mode = VehicleMode("GUIDED_NOGPS")
        self.vehicle.armed = True

        while not self.vehicle.armed:
            print(" Waiting for arming...")
            self.vehicle.armed = True
            time.sleep(1)

        print("Taking off!")

        thrust = DEFAULT_TAKEOFF_THRUST
        while True:
            current_altitude = self.vehicle.location.global_relative_frame.alt
            print(" Altitude: %f  Desired: %f" %
                  (current_altitude, aTargetAltitude))
            if current_altitude >= aTargetAltitude * 0.95:
                print("Reached target altitude")
                break
            elif current_altitude >= aTargetAltitude * 0.6:
                thrust = SMOOTH_TAKEOFF_THRUST
            self.set_attitude(thrust=thrust)
            time.sleep(0.2)

    def send_attitude_target(self, roll_angle=0.0, pitch_angle=0.0, yaw_angle=None, yaw_rate=0.0, use_yaw_rate=False, thrust=0.5):
        if yaw_angle is None:
            # this value may be unused by the vehicle, depending on use_yaw_rate
            yaw_angle = self.vehicle.attitude.yaw

        msg = self.vehicle.message_factory.set_attitude_target_encode(
            0,  # time_boot_ms
            1,  # Target system
            1,  # Target component
            0b00000000 if use_yaw_rate else 0b00000100,
            self.to_quaternion(roll_angle, pitch_angle, yaw_angle),  # Quaternion
            0,  # Body roll rate in radian
            0,  # Body pitch rate in radian
            math.radians(yaw_rate),  # Body yaw rate in radian/second
            thrust  # Thrust
        )
        self.vehicle.send_mavlink(msg)

    @staticmethod
    def to_quaternion(roll=0.0, pitch=0.0, yaw=0.0):
        """
        Convert degrees to quaternions.
        """
        t0 = math.cos(math.radians(yaw * 0.5))
        t1 = math.sin(math.radians(yaw * 0.5))
        t2 = math.cos(math.radians(roll * 0.5))
        t3 = math.sin(math.radians(roll * 0.5))
        t4 = math.cos(math.radians(pitch * 0.5))
        t5 = math.sin(math.radians(pitch * 0.5))

        w = t0 * t2 * t4 + t1 * t3 * t5
        x = t0 * t3 * t4 - t1 * t2 * t5
        y = t0 * t2 * t5 + t1 * t3 * t4
        z = t1 * t2 * t4 - t0 * t3 * t5

        return [w, x, y, z]

    def set_attitude(self, roll_angle=0.0, pitch_angle=0.0, yaw_angle=0.0, yaw_rate=0.0, use_yaw_rate=False, thrust=0.5, duration=0):
        self.send_attitude_target(roll_angle, pitch_angle, yaw_angle, yaw_rate, False, thrust)
        start = time.time()
        while time.time() - start < duration:
            self.send_attitude_target(roll_angle, pitch_angle, yaw_angle, yaw_rate, True, thrust)
            time.sleep(0.1)
        # Reset attitude, or it will persist for 1s more due to the timeout
        self.send_attitude_target(0, 0, 0, 0, True, thrust)

    def calculate_bearing(self, coord_start, coord_end):
        lat1, lon1 = math.radians(coord_start[0]), math.radians(coord_start[1])
        lat2, lon2 = math.radians(coord_end[0]), math.radians(coord_end[1])
        delta_lon = lon2 - lon1
        azimuth_rad = math.atan2(math.sin(delta_lon) * math.cos(lat2),
                                 math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon))
        azimuth_deg = math.degrees(azimuth_rad)
        azimuth_deg = (azimuth_deg + 360) % 360
        return azimuth_deg

    def haversine(self, coord1, coord2):
        R = 6371000.0    
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance
