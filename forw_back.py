#!/usr/bin/env python

from dronekit import connect, VehicleMode, LocationGlobal, LocationGlobalRelative
from pymavlink import mavutil # Needed for command message definitions
import time
import math
from time import sleep

# Set up option parsing to get connection string
import argparse
parser = argparse.ArgumentParser(description='Control Copter and send commands in GUIDED mode ')
parser.add_argument('--connect',
                   help="Vehicle connection target string. If not specified, SITL automatically started and used.")
args = parser.parse_args()

connection_string = args.connect
sitl = None

# Start SITL if no connection string specified
#if not connection_string:
#    import dronekit_sitl
#    sitl = dronekit_sitl.start_default()
#    connection_string = sitl.connection_string()


# Connect to the Vehicle
print('Connecting to vehicle on: %s' % connection_string)
#vehicle = connect(connection_string, wait_ready=True)
vehicle = connect('127.0.0.1:14550', wait_ready=False)


def arm_and_takeoff_nogps(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude without GPS data.
    """

    ##### CONSTANTS #####
    DEFAULT_TAKEOFF_THRUST = 0.7
    SMOOTH_TAKEOFF_THRUST = 0.6

    print("Basic pre-arm checks")
    # Don't let the user try to arm until autopilot is ready
    # If you need to disable the arming check,
    # just comment it with your own responsibility.
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)


    print("Arming motors")
    # Copter should arm in GUIDED_NOGPS mode
    vehicle.mode = VehicleMode("GUIDED")
  
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        vehicle.armed = True
        time.sleep(1)

    print("Taking off!")

    thrust = DEFAULT_TAKEOFF_THRUST
    while True:
        current_altitude = vehicle.location.global_relative_frame.alt
        print(" Altitude: %f  Desired: %f" %
              (current_altitude, aTargetAltitude))
        if current_altitude >= aTargetAltitude*0.95: # Trigger just below target alt.
            print("Reached target altitude")
            break
        elif current_altitude >= aTargetAltitude*0.6:
            thrust = SMOOTH_TAKEOFF_THRUST
        set_attitude(thrust = thrust)
        time.sleep(0.2)

def send_attitude_target(roll_angle = 0.0, pitch_angle = 0.0,
                         yaw_angle = None, yaw_rate = 0.0, use_yaw_rate = False,
                         thrust = 0.5):
    """
    Control the vehicle's attitude and velocity.
    """
    # Set the desired velocity for forward movement
    #send_ned_velocity(15, 0, 0, duration)

    """
    use_yaw_rate: the yaw can be controlled using yaw_angle OR yaw_rate.
                  When one is used, the other is ignored by Ardupilot.
    thrust: 0 <= thrust <= 1, as a fraction of maximum vertical thrust.
            Note that as of Copter 3.5, thrust = 0.5 triggers a special case in
            the code for maintaining current altitude.
    """
    if yaw_angle is None:
        # this value may be unused by the vehicle, depending on use_yaw_rate
        yaw_angle = vehicle.attitude.yaw
    # Thrust >  0.5: Ascend
    # Thrust == 0.5: Hold the altitude
    # Thrust <  0.5: Descend
    msg = vehicle.message_factory.set_attitude_target_encode(
        0, # time_boot_ms
        1, # Target system
        1, # Target component
        0b00000000 if use_yaw_rate else 0b00000100,
        #0b10111000,
        to_quaternion(roll_angle, pitch_angle, yaw_angle), # Quaternion
        0, # Body roll rate in radian
        0, # Body pitch rate in radian
        math.radians(yaw_rate), # Body yaw rate in radian/second
        thrust  # Thrust
    )
    vehicle.send_mavlink(msg)

def set_attitude(roll_angle = 0.0, pitch_angle = 0.0,
                 yaw_angle = 0.0, yaw_rate = 0.0, use_yaw_rate = False,
                 thrust = 0.5, duration = 0):
    """
    Note that from AC3.3 the message should be re-sent more often than every
    second, as an ATTITUDE_TARGET order has a timeout of 1s.
    In AC3.2.1 and earlier the specified attitude persists until it is canceled.
    The code below should work on either version.
    Sending the message multiple times is the recommended way.
    """
    send_attitude_target(roll_angle, pitch_angle,
                         yaw_angle, yaw_rate, False,
                         thrust)
    start = time.time()
    while time.time() - start < duration:
        send_attitude_target(roll_angle, pitch_angle,
                             yaw_angle, yaw_rate, True,
                             thrust)
        time.sleep(0.1)
    # Reset attitude, or it will persist for 1s more due to the timeout
    send_attitude_target(0, 0,
                         0, 0, True,
                         thrust)

#def to_quaternion(roll = 0.0, pitch = 0.0, yaw = 0.0):
def to_quaternion(roll, pitch, yaw):
    """
    Convert degrees to quaternions
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
def calculate_bearing(coord_start, coord_end):
    # Конвертируем градусы в радианы
    lat1, lon1 = math.radians(coord_start[0]), math.radians(coord_start[1])
    lat2, lon2 = math.radians(coord_end[0]), math.radians(coord_end[1])
    # Вычисляем разницу в долготе
    delta_lon = lon2 - lon1
    # Вычисляем азимут в радианах
    azimuth_rad = math.atan2(math.sin(delta_lon) * math.cos(lat2),
                             math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon))
    # Преобразуем азимут из радиан в градусы
    azimuth_deg = math.degrees(azimuth_rad)
    # Преобразуем азимут в положительное значение, если он отрицательный
    azimuth_deg = (azimuth_deg + 360) % 360

    return azimuth_deg

def haversine(coord1, coord2):
    # Константа для радиуса Земли в метрах
    R = 6371000.0    
    # Извлекаем широты и долготы из координат
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])    
    # Разницы в координатах
    dlat = lat2 - lat1
    dlon = lon2 - lon1    
    # Формула гаверсинусов для расчета расстояния
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance


coord_start = (50.424556, 30.173575)
coord_end = (50.437774, 30.158996)



azimuth = calculate_bearing(coord_start, coord_end)
print(f'Азимут между точками: {azimuth} градусов')

distance = haversine(coord_start, coord_end)
print(f'Расстояние между точками A и B: {distance} метров')

pitch_angle_calc = 2
#roll_angle_calc = azimuth - 20
#roll_angle_calc = -17
roll_angle_calc = 0
#duration_calc = distance / 10
duration_calc = 120

print(f'Параметры моторов: {pitch_angle_calc} pitch_angle {roll_angle_calc} roll_angle {duration_calc} duration')


# Hold the position for 3 seconds.
#print("Hold position for 3 seconds")

#print("AltHold mode")
# Copter should arm in GUIDED_NOGPS mode
#vehicle.mode = VehicleMode("ALT_HOLD")

#set_attitude(duration = duration_calc)

# Uncomment the lines below for testing roll angle and yaw rate.
# Make sure that there is enough space for testing this.

#print("Test yaw")
#set_attitude(roll_angle = 1, thrust = 0.5, duration = 30)
#set_attitude(yaw_rate = 30, thrust = 0.5, duration = 30)

# Move the drone forward and backward.
# Note that it will be in front of original position due to inertia.

#print("Move forward")
#set_attitude(pitch_angle = -pitch_angle_calc, roll_angle = roll_angle_calc, thrust = 0.5, duration = duration_calc)


#print("Move backward 2")
#set_attitude(pitch_angle = pitch_angle_calc, roll_angle = roll_angle_calc, thrust = 0.5, duration = duration_calc)
#print("Move backward 7")
#set_attitude(pitch_angle = pitch_angle_calc + 5, roll_angle = roll_angle_calc, thrust = 0.5, duration = duration_calc)
#print("Move backward 12")
#set_attitude(pitch_angle = pitch_angle_calc + 10, roll_angle = roll_angle_calc, thrust = 0.5, duration = duration_calc)

#print("Move left")
#set_attitude(roll_angle = -55, pitch_angle = 0.0, thrust = 0.5, duration = 36.21)
def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """

    print("Basic pre-arm checks")
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    # Copter should arm in GUIDED mode
    vehicle.mode    = VehicleMode("GUIDED")
    vehicle.armed   = True

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        #Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95:
            print("Reached target altitude")
            break
        time.sleep(1)

# Take off 2.5m in GUIDED_NOGPS mode.
#arm_and_takeoff_nogps(10)
#set_attitude(duration = duration_calc)
#Create a message listener for all messages.
# Функция для сохранения log message в файл
def log_msg(message):
    with open('log.txt', 'a') as log_file:
        log_file.write(str(message) + '\n')
    
#@vehicle.on_message('WIND')
@vehicle.on_message('ATTITUDE')
def listener(self, name, message):
    log_msg(message)
    #print("message: %s" % message)
@vehicle.on_message('BATTERY_STATUS')
def listener(self, name, message):
    log_msg(message)
@vehicle.on_message('WIND')
def listener(self, name, message):
    log_msg(message)


arm_and_takeoff(10)
print("Set default/target airspeed to 0")
vehicle.airspeed = 0
time.sleep(duration_calc)

print("Setting LAND mode...")
vehicle.mode = VehicleMode("LAND")
time.sleep(1)

# Close vehicle object before exiting script
print("Close vehicle object")
vehicle.close()

# Shut down simulator if it was started.
if sitl is not None:
    sitl.stop()

print("Completed")
