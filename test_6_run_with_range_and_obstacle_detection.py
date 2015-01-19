#! /usr/bin/python

# Example for testing with ultrasonic range measuring by the Seeed ultrasonic sensor (connected to D13)
# and obstacle detection with two Sharp GP2Y0D810Z0F Digital Distance Sensors with Pololu Carrier (adafruit)
# The Sharp sensors are connected to A2 and A1 (configured as DIGITAL-READ)
# Not used in this script: Grove Line Sensors (connected to A5 - A3)
# Visual feedback by adding LED-light signals per routine (all routines are commented for running the script remote)
# Note: Connect the LED's by a 270 - 330 Ohm resitor to GND to reduce the current off the 3.3V GPIO's
# Note: GPIO setup requires executing the script as with Root rights:
#       chmod +x test_1_motors_basic.py
#       sudo ./test_1_motors_basic.py
# Note: This script will never execute "finalize". If needed a Try - Except clause can be added (now CTRL-C will give a KeyboardInterrupt)
# Note: As in all scripts, I used straight forward linear coding to increase readability for beginning users (like me)
# The scripts can easely be translated into modules and classes

import time
import argparse
import py_websockets_bot
import py_websockets_bot.mini_driver
import py_websockets_bot.robot_config
import random
import csv
#import RPi.GPIO as GPIO

#GPIO.setmode(GPIO.BCM)     # Use the GPIO numbers i.s.o. the pin numbers
#YELLOW = 26
#GREEN = 19
#RED = 13
#BLUE = 6
#GPIO.setwarnings (False)   # To suppress "RuntimeWarning: This channel is already in use, continuing anyway"
#GPIO.setup(BLUE,GPIO.OUT)  # Initialize LED - Blue
#GPIO.output(BLUE,False)
#GPIO.setup(YELLOW,GPIO.OUT)# Initialize LED - Yellow
#GPIO.output(YELLOW,False)
#GPIO.setup(RED,GPIO.OUT)   # Initialize LED - Red
#GPIO.output(RED,False)
#GPIO.setup(GREEN,GPIO.OUT) # Initialize LED - Green
#GPIO.output(GREEN,False)
#time.sleep (2.0)           # GPIO needs time before any routine can start

# Motor movements
def move_stop ():
    flag_ready = 0
    bot.set_motor_speeds( 0.0, 0.0 )
    return flag_ready
def move_forward ():
    flag_ready = 1
    bot.set_motor_speeds(12.0, 12.0 )
    return flag_ready
def move_backward ():
    flag_ready = 2
    bot.set_motor_speeds( -12.0, -12.0 )    
    return flag_ready
def move_right ():
    flag_ready = 3
    bot.set_motor_speeds (12.0,-12.0)
    time.sleep(1.0)
    return flag_ready
def move_left ():
    flag_ready = 4
    bot.set_motor_speeds( -12.0, 12.0 )
    time.sleep(1.0)
    return flag_ready

# LED lights 
#def blink_blue (switch):
#    if switch == "ON":
#        GPIO.output(BLUE,True)
#    else:
#        GPIO.output(BLUE,False)
#def blink_red (switch):
#    if switch == "ON":
#        GPIO.output(RED,True)
#    else:
#        GPIO.output(RED,False)
#def blink_yellow (switch):
#    if switch == "ON":
#        GPIO.output(YELLOW,True)
#    else:
#        GPIO.output(YELLOW,False)
#def blink_green (switch):
#    if switch == "ON":
#        GPIO.output(GREEN,True)
#    else:
#        GPIO.output(GREEN,False)

# Neck movements
def look_down (pan_angle, tilt_angle):
    flag_ready = 5
    while tilt_angle < max_tilt_angle :
        tilt_angle += 1.0
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        #time.sleep( 0.001 )
    return flag_ready

def look_up (pan_angle, tilt_angle):
    flag_ready = 6
    while tilt_angle > min_tilt_angle :
        tilt_angle -= 1.0
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        #time.sleep( 0.001 )
    return flag_ready

def look_right (pan_angle, tilt_angle):
    flag_ready = 7
    while pan_angle > min_pan_angle :
        pan_angle -= 1.0
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        #time.sleep( 0.001 )
    return flag_ready

def look_left (pan_angle, tilt_angle):
    flag_ready = 8
    while pan_angle < max_pan_angle :
        pan_angle += 1.0
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        #time.sleep( 0.001 )
    return flag_ready

# Ultrasonic range 
def get_range ():
    bot.update()
    status_dict, read_time = bot.get_robot_status_dict()
    sensor_dict = status_dict[ "sensors" ]
    data = sensor_dict[ "ultrasonic" ][ "data" ]
    distance = data
    return distance

# Set up a parser for command line arguments
parser = argparse.ArgumentParser( "Gets sensor readings from the robot and displays them" )
parser.add_argument( "hostname", default="localhost", nargs='?', help="The ip address of the robot" )
args = parser.parse_args()
 
# Connect to the robot
#bot = py_websockets_bot.WebsocketsBot( args.hostname ) # When running a local script on the Pi
bot = py_websockets_bot.WebsocketsBot( "192.168.42.1" ) # When running a script at a remote computer using webSockets

# Configure the sensors on the robot
sensorConfiguration = py_websockets_bot.mini_driver.SensorConfiguration(
    configD12=py_websockets_bot.mini_driver.PIN_FUNC_ULTRASONIC_READ, 
    configD13=py_websockets_bot.mini_driver.PIN_FUNC_INACTIVE, 
    configA0=py_websockets_bot.mini_driver.PIN_FUNC_ANALOG_READ, 
    configA1=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ,
    configA2=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ, 
    configA3=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ,
    configA4=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ, 
    configA5=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ,
    leftEncoderType=py_websockets_bot.mini_driver.ENCODER_TYPE_QUADRATURE, 
    rightEncoderType=py_websockets_bot.mini_driver.ENCODER_TYPE_QUADRATURE )
      
robot_config = bot.get_robot_config()
robot_config.miniDriverSensorConfiguration = sensorConfiguration
bot.set_robot_config( robot_config )    

# Update any background communications with the robot
bot.update()

# Sleep to avoid overload of the web server on the robot
time.sleep( 0.1 )

# Prepare to move
move_stop()
#bot.set_motor_speeds(0.0, 0.0)
bot.centre_neck()

flag_ready = 0            # Redundant switch, just to enforce waiting for movements to finish
robot_status = 0
on = "ON"
out = "OUT"
pan_angle = 90.0
tilt_angle = 90.0
min_pan_angle = 0.0
max_pan_angle = 180.0
min_tilt_angle = 0.0
max_tilt_angle = 180.0
range_limit = 30         # The target distance to the wall

#blink_blue(out)
#blink_red(out)
#blink_yellow(out)
#blink_green(out)

# ----------------------------------------------------------------------------------------------

if __name__ == "__main__":
    robot_status = move_stop()
    bot.centre_neck()
    range_measured = get_range()
    bot.update()
    status_dict, read_time = bot.get_robot_status_dict()
    sensor_dict = status_dict[ "sensors" ]
    sensor_data = sensor_dict[ "digital" ][ "data" ]
    while True:
        range_measured = get_range()
        print "Loop meting:", range_measured,"range_limit", range_limit, "robot_status", robot_status
        bot.update()
        status_dict, read_time = bot.get_robot_status_dict()
        sensor_dict = status_dict[ "sensors" ]
        sensor_data = sensor_dict[ "digital" ][ "data" ]
        if sensor_data == 0:
            #blink_yellow(out)
            #blink_green(on)
            print "Sensor data:", sensor_data, "Object in front of the robot,", "backing out"
            robot_status = move_backward()
            time.sleep(1.0)
            #blink_green(out)
            #blink_red(on)
            robot_status = move_right()
            robot_status = move_right()
            #blink_red(out)
        if sensor_data == 8:
            #blink_yellow(out)
            #blink_green(on)
            print "Sensor data:", sensor_data,"Object at front right of the robot,", "backout left"
            robot_status = move_backward()
            time.sleep(1.0)
            #blink_green(out)
            #blink_blue(on)
            robot_status = move_left()
            #blink_blue(out)
        if sensor_data == 16:
            #blink_yellow(out)
            #blink_green(on)
            print "Sensor data:", sensor_data,"Object at front left of the robot,", "backout right"
            robot_status = move_backward()
            time.sleep(1.0)
            #blink_green(out)
            #blink_red(on)
            robot_status = move_right()
            #blink_red(out)
        if range_measured < range_limit:
            #Stop and look
            #blink_yellow(out)
            robot_status = move_stop()
            robot_status = look_left (pan_angle, tilt_angle)
            pan_angle = 180.0
            range_measured = get_range()
            range_left = range_measured
            time.sleep(0.5)
            print "Range left", range_left, "range_limit", range_limit, "robot_status", robot_status,
            robot_status = look_right (pan_angle, tilt_angle)
            pan_angle = 0.0
            range_measured = get_range()
            range_right = range_measured
            time.sleep(0.5)
            print "Range right", range_right, "range_limit", range_limit, "robot_status", robot_status,
            bot.centre_neck()
            pan_angle = 90.0
            if range_left >= range_right:
                #blink_blue(on)
                print "To the left"
                robot_status = move_left()
                #blink_blue(out)
            else:
                #blink_red(on)
                print "To the right"
                robot_tatus = move_right()
                #blink_red(out)
        else:
            #blink_yellow(on)
            robot_status = move_forward()
            print "foreward"
   
    # Finalize
    # Reset GPIO pins
    #GPIO.cleanup()
    bot.set_motor_speeds( 0.0, 0.0 )
    bot.centre_neck()
    bot.disconnect()
