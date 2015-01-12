#! /usr/bin/python

# Example for testing movements of the motor without use of encoders and movement of the neck.
# Because of a variance between the output of both motors, a difference in speed has to be determined
# I couldn't get the right results with the slider on the config-page of the web-interface, so I adjusted motor speeds in the movement functions
# The objective of my tests was to get straight line moving foreward and backwards and making turns in a 90degr angle
# (Later-on, when coding the line follower robot, I need to be able to make turns in a certain predefined angle)
# For testing purposes there's some feedback added:
# - on the terminal console by the print statements and(/or) by the variable robot_status which returns a flag_status that differs per routine
# - visual by adding LED-light signals per routine
# Note: Connect the LED's by a 270 - 330 Ohm resitor to GND to reduce the current off the 3.3V GPIO's
# Note: GPIO setup requires executing the script as with Root rights:
#       chmod +x test_1_motors_basic.py
#       sudo ./test_1_motors_basic.py
# Note: As in all scripts, I used straight forward linear coding to increase readability for beginning users (like me)
# The scripts can easely be translated into modules and classes

import time
import argparse
import py_websockets_bot
import py_websockets_bot.mini_driver
import py_websockets_bot.robot_config
import random
import csv
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)     # Use the GPIO numbers i.s.o. the pin numbers
TRIG = 23                  # Used for triggering of the HC-SR04 ultrasonic distance sensor (in the next script)
ECHO = 24                  # Used for echo reading of the HC-SR04 ultrasonic sensor (in the next script)
YELLOW = 26
GREEN = 19
RED = 13
BLUE = 6
GPIO.setwarnings (False)   # To suppress "RuntimeWarning: This channel is already in use, continuing anyway"
GPIO.setup(TRIG,GPIO.OUT)  # Initialize trigger
GPIO.output(TRIG,False)
GPIO.setup(ECHO,GPIO.IN)   # Initialize echo signal
GPIO.setup(BLUE,GPIO.OUT)  # Initialize LED - Blue
GPIO.output(BLUE,False)
GPIO.setup(YELLOW,GPIO.OUT)# Initialize LED - Yellow
GPIO.output(YELLOW,False)
GPIO.setup(RED,GPIO.OUT)   # Initialize LED - Red
GPIO.output(RED,False)
GPIO.setup(GREEN,GPIO.OUT) # Initialize LED - Green
GPIO.output(GREEN,False)
time.sleep (2.0)           # GPIO needs time before any routine can start

# IDLE = "Idle"            # Still no idea why I need this

# Motor movements
def move_stop ():
    flag_ready = 0
    bot.set_motor_speeds( 0.0, 0.0 )
    time.sleep (0.25)
    return flag_ready
def move_forward ():
    flag_ready = 1
    bot.set_motor_speeds(20.0, 20.0 )
    time.sleep(2.5)
    return flag_ready
def move_backward ():
    flag_ready = 2
    bot.set_motor_speeds( -20.0, -20.0 )    
    time.sleep(2.5)
    return flag_ready
def move_right ():
    flag_ready = 3
    bot.set_motor_speeds (10.0,-10.0)    
    time.sleep(0.05)
    return flag_ready
def move_left ():
    flag_ready = 4
    bot.set_motor_speeds( -10.0, 10.0 )
    time.sleep(0.05)
    return flag_ready

# LED lights 
def blink_blue (switch):
    if switch == "ON":
        GPIO.output(BLUE,True)
    else:
        GPIO.output(BLUE,False)
def blink_red (switch):
    if switch == "ON":
        GPIO.output(RED,True)
    else:
        GPIO.output(RED,False)
def blink_yellow (switch):
    if switch == "ON":
        GPIO.output(YELLOW,True)
    else:
        GPIO.output(YELLOW,False)
def blink_green (switch):
    if switch == "ON":
        GPIO.output(GREEN,True)
    else:
        GPIO.output(GREEN,False)

# Neck movements
def look_down (pan_angle, tilt_angle):
    flag_ready = 5
    while tilt_angle < max_tilt_angle :
        tilt_angle += 0.5
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        #time.sleep( 0.001 )
    return flag_ready
def look_up (pan_angle, tilt_angle):
    flag_ready = 6
    while tilt_angle > min_tilt_angle :
        tilt_angle -= 0.5
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        #time.sleep( 0.001 )
    return flag_ready
def look_right (pan_angle, tilt_angle):
    flag_ready = 7
    while pan_angle > min_pan_angle :
        pan_angle -= 0.5
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        #time.sleep( 0.001 )
    return flag_ready
def look_left (pan_angle, tilt_angle):
    flag_ready = 8
    while pan_angle < max_pan_angle :
        pan_angle += 0.5
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        #time.sleep( 0.001 )
    return flag_ready
def look_around (pan_angle, tilt_angle): # Just for fun: has no use, but nice to make the bot look intelligent ;-0)
    flag_ready = 9
    bot.centre_neck ()
    look_up (pan_angle, tilt_angle)
    tilt_angle = 0.0
    look_left (pan_angle, tilt_angle)
    pan_angle = 180.0
    look_down (pan_angle, tilt_angle)
    tilt_angle = 180.0
    look_right (pan_angle, tilt_angle)
    pan_angle = 0.0
    look_up (pan_angle, tilt_angle)
    time.sleep (0.5)
    bot.centre_neck()
    return flag_ready

flag_ready = 0             # Redundant switch, just to enforce waiting for movements to finish
list_flag_ready = []       # Feedback for test purposes
robot_status = 0
switch = "OUT"
on = "ON"
out = "OUT"

# ----------------------------------------------------------------------------------------------

if __name__ == "__main__":

# Start
    # Set up a parser for command line arguments
    parser = argparse.ArgumentParser( "Gets sensor readings from the robot and displays them" )
    parser.add_argument( "hostname", default="localhost", nargs='?', help="The ip address of the robot" )
    args = parser.parse_args()
 
    # Connect to the robot
    #bot = py_websockets_bot.WebsocketsBot( args.hostname ) # When running a local script on the Pi
    bot = py_websockets_bot.WebsocketsBot( "192.168.42.1" ) # When running a script at a remote computer using webSockets
        
    # Update any background communications with the robot
    bot.update()
    # Sleep to avoid overload of the web server on the robot
    time.sleep( 0.1 )

    # Prepare to move
    bot.set_motor_speeds(0.0, 0.0)
    bot.centre_neck()
        
# Procedure
    while True:
        print "Riding along ......."
        blink_yellow(on)
        robot_status = move_forward ()
        list_flag_ready.append (robot_status)
        print list_flag_ready
        print "waiting 2 seconds ........"
        time.sleep (2.0)
        blink_yellow(off)
        print "Looking to the left"
        blink_blue(on)
        robot_status = look_left(pan_angle, tilt_angle)
        list_flag_ready.append (robot_status)
        print list_flag_ready
        time.sleep(2.0)
        print "Turn left"
        robot_status = move_left()
        list_flag_ready.append (robot_status)
        print list_flag_ready
        time.sleep (2.0)
        bot.centre_neck()
        print "waiting 2 seconds ........"
        time.sleep(2.0)
        blink_blue(out)
        print "Riding backwards ......."
        blink_green(on)
        robot_status = move_backward ()
        list_flag_ready.append (robot_status)
        print list_flag_ready
        print "waiting 2 seconds ........"
        time.sleep(2.0)
        blink_green(out)
        print "Looking to the right"
        blink_red(on)
        robot_status = look_right(pan_angle, tilt_angle)
        list_flag_ready.append (robot_status)
        print list_flag_ready
        time.sleep (2.0)
        print "Turn right" 
        robot_status = move_right()
        list_flag_ready.append (robot_status)
        print list_flag_ready
        time.sleep (2.0)
        bot.centre_neck ()
        print "waiting 2 seconds ........"
        time.sleep(2.0)
        blink_red(out)
        print "Riding along ......."
        blink_yellow(on)
        robot_status = move_forward()
        list_flag_ready.append (robot_status)
        print list_flag_ready
        look_around(pan_angle, tilt_angle)
        blink_yellow(out)
# Finalize
    # Reset GPIO pins
    GPIO.cleanup()
    bot.set_motor_speeds( 0.0, 0.0 )
    bot.centre_neck()
    bot.disconnect()
