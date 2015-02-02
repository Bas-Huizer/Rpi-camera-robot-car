#! /usr/bin/python

import time
import argparse
import cv2
import numpy as np
import py_websockets_bot
import py_websockets_bot.mini_driver
import py_websockets_bot.robot_config
import random
import csv
#import RPi.GPIO as GPIO
# -------------------------------------------------------------------------------------------------------- Neck routines
def look_around (pan_angle_return, pan_switch, ride_switch):
    pan_angle = pan_angle_return
    if pan_switch == 'RIGHT':
        if pan_angle_return > min_pan_angle:
            pan_angle -= 5.0
            bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
            pan_angle_send = pan_angle
        else:
            pan_switch = 'LEFT'
            pan_angle += 5.0
            bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
            pan_angle_send = pan_angle
    else:
        if pan_angle_return < max_pan_angle:
            pan_angle += 5.0
            bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
            pan_angle_send = pan_angle
        else:
            pan_switch = 'RIGHT'
            pan_angle_send = pan_angle_return
            if ride_switch == 0:
                robot_status = move_degr(30)
    return pan_angle_send, pan_switch
# -------------------------------------------------------------------------------------------------------- Motor routines
def stop_moving ():
    flag_ready = 0
    bot.set_motor_speeds( 0.0, 0.0 )
    return flag_ready
def move_degr (motor_angle):                                                                             # Not elegant; using experimental values
    flag_ready = 1
    if motor_angle == 180:
        bot.set_motor_speeds( -12.0, -12.0 )
    if motor_angle == 90:
        bot.set_motor_speeds( -12.0, 12.0 )
        time.sleep(1.3)
        stop_moving()
    if motor_angle == 75:
        bot.set_motor_speeds( -12.0, 12.0 )
        time.sleep(1.1)
        stop_moving()
    if motor_angle == 60:
        bot.set_motor_speeds( -11.0, 11.0 )
        time.sleep(1.0)
        stop_moving()
    if motor_angle == 45:
        bot.set_motor_speeds( -10.0, 10.0 )
        time.sleep(1.0)
        stop_moving()
    if motor_angle == 30:
        bot.set_motor_speeds( -10.0, 10.0 )
        time.sleep(0.6)
        stop_moving()
    if motor_angle == 15:
        bot.set_motor_speeds( -10.0, 10.0 )
        time.sleep(0.3)
        stop_moving()
    if motor_angle == -90:
        bot.set_motor_speeds( 12.0, -12.0 )
        time.sleep(1.2)
        stop_moving()
    if motor_angle == -75:
        bot.set_motor_speeds( 12.0, -12.0 )
        time.sleep(1.0)
        stop_moving()
    if motor_angle == -60:
        bot.set_motor_speeds( 11.0, -11.0 )
        time.sleep(0.8)
        stop_moving()
    if motor_angle == -45:
        bot.set_motor_speeds( 11.0, -11.0 )
        time.sleep(1.0)
        stop_moving()
    if motor_angle == -30:
        bot.set_motor_speeds( 10.0, -10.0 )
        time.sleep(0.8)
        stop_moving()
    if motor_angle == -15:
        bot.set_motor_speeds( 10.0, -10.0 )
        time.sleep(0.3)
        stop_moving()
    return flag_ready
# -------------------------------------------------------------------------------------------------------- Ultrasonic range 
def get_range ():
    bot.update()
    status_dict, read_time = bot.get_robot_status_dict()
    sensor_dict = status_dict[ "sensors" ]
    data = sensor_dict[ "ultrasonic" ][ "data" ]
    distance = data
    return distance
# -------------------------------------------------------------------------------------------------------- Image search
def search_sign(pan_angle_send):
    pan_angle_return = pan_angle_send
    bot.update()
    sign_found = 0
    centroid_x_save = 0
    centroid_y_save = 0
    area_save = 0.0
    image, image_time = bot.get_latest_camera_image()
    image_height, image_width = image.shape[:2]
    #image = cv2.resize(image-l,None,fx=0.25, fy=0.25, interpolation = cv2.INTER_CUBIC)
    #cv2.imshow('Original', image)
    #cv2.waitKey(1)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)                                              # 0 - Set color range to search for blue shapes
    lower_blue = np.array([110,50,80])
    upper_blue = np.array([131,119,255])
    mask_image = cv2.inRange(hsv, lower_blue, upper_blue)                                     # 1 - Mask only blue
    result_image = cv2.bitwise_and(image,image, mask= mask_image)                             # 2 - Convert masked color to white. Rest to black 
    blurred_image = cv2.bilateralFilter(result_image,9,75,75)                                 # 3 - Optional: Blurring the result to de-noise
    gray_image = cv2.cvtColor(blurred_image, cv2.COLOR_BGR2GRAY )                             # 4 - Convert to Gray (needed for binarizing)
    #ret3,threshold_image = cv2.threshold(gray_image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU) # 5 - Optional: Binarizing (Otsus threshold)
    edged_image = cv2.Canny(gray_image,threshold1=90, threshold2=190)                         # 6 - Find edges of all shapes
    cv2.imshow('step-6 - Canny', edged_image)                                                
    cv2.waitKey(1)
    contours, hierarchy = cv2.findContours(edged_image,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE) # 7 - Find contours of all shapes
    objects_found = len(contours)                                                             # 8 - Filter on size and shape
    if objects_found >= 1 and objects_found < 50:               
        loop_count = 0
        loop_count = int(loop_count)
        area_save = 0
        loop_count_save = 0
        rectangle_count = 0
        while loop_count < objects_found:
            cnt = contours[loop_count]
            M = cv2.moments(cnt)
            area = cv2.contourArea(cnt)
            epsilon = 0.1*cv2.arcLength(cnt,True)
            approx = cv2.approxPolyDP(cnt,epsilon,True)
            corners_shape = len (approx)
            if corners_shape == 4:
                if area > 5000:
                    centroid_x = int(M['m10']/M['m00'])
                    centroid_y = int(M['m01']/M['m00'])
                    if loop_count == 0:
                        loop_count_save = loop_count
                        rectangle_count += 1
                        area_save = area
                        centroid_x_save = centroid_x
                        centroid_y_save = centroid_y
                    elif area > area_save:
                        loop_count_save = loop_count
                        rectangle_count += 1
                        centroid_x_save = centroid_x
                        centroid_y_save = centroid_y
                        area_save = area
            loop_count += 1
        if rectangle_count > 0:
            sign_found = 1
            #print 'Shape',loop_count_save, ', largest rectangle of', rectangle_count,', size', area_save, ', coordinates', centroid_x_save, centroid_y_save
    return sign_found, pan_angle_return, centroid_x_save, centroid_y_save, area_save,image_height, image_width
#--------------------------------------------------------------------------------------------------------- Set up a parser for command line arguments
parser = argparse.ArgumentParser( "Gets images from the robot without callback" )
parser.add_argument( "hostname", default="localhost", nargs='?', help="The ip address of the robot" )
args = parser.parse_args()
# -------------------------------------------------------------------------------------------------------- Connect to the robot
#bot = py_websockets_bot.WebsocketsBot( args.hostname )                               # When running a local script on the Pi
bot = py_websockets_bot.WebsocketsBot( "192.168.42.1" )                               # When running a script at a remote computer using webSockets
# --------------------------------------------------------------------------------------------------------- Configure the sensors on the robot
sensorConfiguration = py_websockets_bot.mini_driver.SensorConfiguration(
    configD12=py_websockets_bot.mini_driver.PIN_FUNC_ULTRASONIC_READ,                 # SeeeD 3-pin Ultrasonic sensor
    configD13=py_websockets_bot.mini_driver.PIN_FUNC_INACTIVE, 
    configA0=py_websockets_bot.mini_driver.PIN_FUNC_ANALOG_READ, 
    configA1=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ,                     # Sharp IR switch RIGHT
    configA2=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ,                     # Sharp IR switch LEFT
    configA3=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ,                     # Grove Line sensor RIGHT
    configA4=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ,                     # Grove Line sensor MIDDLE
    configA5=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ,                     # Grove Line sensor LEFT
    leftEncoderType=py_websockets_bot.mini_driver.ENCODER_TYPE_QUADRATURE, 
    rightEncoderType=py_websockets_bot.mini_driver.ENCODER_TYPE_QUADRATURE )
      
robot_config = bot.get_robot_config()
robot_config.miniDriverSensorConfiguration = sensorConfiguration
bot.set_robot_config( robot_config )
bot.update()                                                                          # Update any background communications with the robot
time.sleep( 0.1 )                                                                     # Sleep to avoid overload of the web server on the robot
# -------------------------------------------------------------------------------------------------------- Initializing variables
flag_ready = 0                                                                        # Redundant, just to enforce waiting for movements to finish
robot_status = 0
min_pan_angle = 65.0
max_pan_angle = 115.0
range_limit = 25
#---------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    
    bot.start_streaming_camera_images()
    time.sleep(1.0)
    ###################################################################################################### Start of SEARCH_SIGN routine
    bot.centre_neck()
    pan_angle = 90.0
    pan_angle_send = 90.0
    pan_switch = 'RIGHT'
    ride_switch = 0
    #pan_angle_return = 90
    tilt_angle = 90.0
    sign_found = 0
    while sign_found == 0:
        sign_found, pan_angle_returned, centroid_x_returned, centroid_y_returned, area_returned,image_height, image_width = search_sign(pan_angle_send)
        #time.sleep(0.5)
        if sign_found == 0:
            pan_angle_send, pan_switch = look_around(pan_angle_returned, pan_switch, ride_switch)
            time.sleep(1.0)
        time.sleep(0.5)       
    print 'Found coord.', centroid_x_returned, centroid_y_returned,'neck angle', pan_angle_returned, 'current angle', pan_angle_send
    #time.sleep(2.0)
    ################################################################################################## End of SEARCH_SIGN Start of MOVE_TO_SIGN
    # ------------------------------------------------------------------------------------------------ init move
    centroid_image_x = int(image_width/2)
    centroid_image_y = int(image_height/2)
    print 'Image:', image_width, 'x', image_height, 'center =', centroid_image_x, centroid_image_y
    sign_found = 0
    ride_switch = 1
    tilt_angle_save = tilt_angle
    range_returned = get_range()
    print 'First range =', range_returned
    while range_returned > range_limit:
        motor_speed_right = 12.0
        motor_speed_left = 12.0
    # ------------------------------------------------------------------------------------------------ Focus view
        if centroid_x_returned != centroid_image_x:
            differance_x = round(((centroid_image_x - centroid_x_returned) * 0.0264583),1)
            tangent_x = differance_x / range_returned 
            pan_angle = pan_angle_returned + round(math.degrees(math.atan(tangent_x)),0)
            #time.sleep(0.5)
        if centroid_y_returned != centroid_image_y:
            differance_y = round(((centroid_image_y - centroid_y_returned) * 0.0264583),1)
            tangent_y = differance_y / range_returned 
            tilt_angle = tilt_angle_save + round(math.degrees(math.atan(tangent_y)),0)
            tilt_angle_save = tilt_angle
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        #time.sleep(0.5)
        print 'Adjusted angles =', pan_angle, tilt_angle
    # ------------------------------------------------------------------------------------------------ Determine direction adjustment
        if pan_angle > 100:
            motor_speed_left = 10.0
        if pan_angle < 80:
            motor_speed_right = 10.0
        print 'Adjusted speeds L/R =', motor_speed_left, motor_speed_right
    # ------------------------------------------------------------------------------------------------ Detect obstacles and react
        # Will be inserted later on
    # ------------------------------------------------------------------------------------------------ Moving car
        #bot.set_motor_speeds( motor_speed_left, motor_speed_right )
        time.sleep(2.0)
    # ------------------------------------------------------------------------------------------------ Get new image coordinates
        pan_angle_send = pan_angle
        while sign_found == 0:
            sign_found, pan_angle_returned, centroid_x_returned, centroid_y_returned, area_returned,image_height, image_width = search_sign(pan_angle_send)
            if sign_found == 0:
                pan_angle_send, pan_switch = look_around(pan_angle_returned, pan_switch, ride_switch)
                time.sleep(1.0)
            time.sleep(0.5)
        print 'New coordinates =', centroid_x_returned, centroid_y_returned
    # ------------------------------------------------------------------------------------------------ Get new range measurement                            
        range_returned = get_range()
        print 'New range =', range_returned
    ################################################################################################## End of MOVE_TO_SIGN Start of READ_SIGN
    
    # ------------------------------------------------------------------------------------------------ Finalize    
    #cv2.destroyAllWindows()
    bot.disconnect()
