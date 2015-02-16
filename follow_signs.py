#! /usr/bin/python

#-----------------------------------------------------------------------------------------------------------------------------------------------------------
# This script searches a blue rectangular object,
#             moves towards the object while adjusting focus on the centre of the object
#             and adjusting motor speeds based upon the postion of the neck
#
# Inspirational site for this script: http://roboticssamy.blogspot.nl/ (balancing robot, reading signs and following lines by vision) Great Stuff !!
#
# Very good instructions on openCV can be found at the site of Adrian Rosebrock: http://www.pyimagesearch.com 
#
# Light quality is essential for object detection by color. (Hobbying at night enforces tight calibration for testing scripts)
# This might be mitigated by adjusting (or stop) the Auto White Balancing and/or enabling Dynamic Range
# Up till now I don't know how to set these parameters through the raspberry_pi_camera_streamer class of Dawn Robotics
#
# The script is well commented; I hope in this way it will be of use for beginners like me 
#-----------------------------------------------------------------------------------------------------------------------------------------------------------

import time
import argparse
import cv2
import numpy as np
import math
import py_websockets_bot
import py_websockets_bot.mini_driver
import py_websockets_bot.robot_config
import random
import csv
#import RPi.GPIO as GPIO

# -------------------------------------------------------------------------------------
# Neck routine
#
# Uses:    Last pan_angle + Switch for left/right
# Returns: New pan_angle  + Switch for left/right
# -------------------------------------------------------------------------------------
def look_around (pan_angle_returned, pan_switch):
    pan_angle = pan_angle_returned
    if pan_switch == 'RIGHT':
        if pan_angle > min_pan_angle:
            pan_angle -= 5.0
            bot.set_neck_angles( pan_angle_degrees=pan_angle,
                                 tilt_angle_degrees=tilt_angle)
            pan_angle_return = pan_angle
        else:
            pan_switch = 'LEFT'
            pan_angle += 5.0
            bot.set_neck_angles( pan_angle_degrees=pan_angle,
                                 tilt_angle_degrees=tilt_angle)
            pan_angle_return = pan_angle
    else:
        if pan_angle < max_pan_angle:
            pan_angle += 5.0
            bot.set_neck_angles( pan_angle_degrees=pan_angle,
                                 tilt_angle_degrees=tilt_angle)
            pan_angle_return = pan_angle
        else:
            pan_switch = 'RIGHT'
            pan_angle_return = pan_angle
            if ride_switch == 0:
                robot_status = move_degr(45)
    return pan_angle_return, pan_switch
# -------------------------------------------------------------------------------------
# Motor routine
# Working with dc motors creates a need for calibrating exact movements 
# Values beneath are the result of testing, testing, testing ,........
# and seem to be continously changing ;-(
#
# Uses: Motor angle_to_turn
# -------------------------------------------------------------------------------------
def move_degr (motor_angle):
    flag_ready = 1
    if motor_angle == 0:
        bot.set_motor_speeds( 12.0, 12.0 )
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
def stop_moving ():
    flag_ready = 0
    bot.set_motor_speeds( 0.0, 0.0 )
    return flag_ready
# -------------------------------------------------------------------------------------
# Ultrasonic range routine
#
# Returns: Range measured
# -------------------------------------------------------------------------------------
def get_range ():
    bot.update()
    status_dict, read_time = bot.get_robot_status_dict()
    sensor_dict = status_dict[ "sensors" ]
    data = sensor_dict[ "ultrasonic" ][ "data" ]
    range_return = data
    return range_return
# -------------------------------------------------------------------------------------
# Image search routine, searches for a large blue object
#
# Returns: switch found + centroid coordinates + contour found
# -------------------------------------------------------------------------------------
def search_sign():
    time_start = time.time()
    bot.update()
    sign_found = 0
    centroid_x_save = 0
    centroid_y_save = 0
    area_save = 0.0
    image, _ = bot.get_latest_camera_image()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)                                      # 0 - Set color range to search for blue shapes
    lower_blue = np.array([110,50,80])
    upper_blue = np.array([131,119,255])
    mask_image = cv2.inRange(hsv, lower_blue, upper_blue)                             # 1 - Mask only blue
    result_image = cv2.bitwise_and(image,image, mask= mask_image)                     # 2 - Convert masked color to white. Rest to black 
    result_image = cv2.bilateralFilter(result_image,9,75,75)                          # 3 - Optional: Blurring the result to de-noise
    result_image = cv2.cvtColor(result_image, cv2.COLOR_BGR2GRAY )                    # 4 - Convert to Gray (needed for binarizing)
    result_image = cv2.Canny(result_image,threshold1=90, threshold2=190)              # 5 - Find edges of all shapes
    cv2.imshow('Edged', result_image)                                                
    cv2.waitKey(1)                                                                    # Needed for display 
    contours, _ = cv2.findContours(result_image,cv2.RETR_TREE,
                                   cv2.CHAIN_APPROX_SIMPLE)                           # 6 - Find contours of all shapes
    contours = sorted(contours, key=cv2.contourArea, reverse=True) [:6]               # 7 - Select 6 biggest; drop the rest
    contour_save = None
    objects_found = len(contours)                                                     # 8 - Filter on size and shape
    if objects_found >= 1:               
        loop_count = 0
        loop_count = int(loop_count)
        loop_count_save = 0
        rectangle_count = 0
        while loop_count < objects_found:
            cnt = contours[loop_count]
            M = cv2.moments(cnt)
            area = cv2.contourArea(cnt)
            epsilon = 0.1*cv2.arcLength(cnt,True)                                     # 8 - Calculate centroid coordinates
            approx = cv2.approxPolyDP(cnt,epsilon,True)
            if len (approx) == 4:
                if area > 5000:
                    centroid_x = int(M['m10']/M['m00'])
                    centroid_y = int(M['m01']/M['m00'])
                    if loop_count == 0:                                               # 9 - Keep the smallest aledged rectangle
                        loop_count_save = loop_count
                        rectangle_count += 1
                        contour_save = approx
                        centroid_x_save = centroid_x
                        centroid_y_save = centroid_y
                    elif area < area_save:
                        loop_count_save = loop_count
                        rectangle_count += 1
                        contour_save = approx
                        centroid_x_save = centroid_x
                        centroid_y_save = centroid_y
            loop_count += 1
        if rectangle_count > 0:
            sign_found = 1
            cnt = contours[loop_count_save]
            time_stop = time.time()
    return sign_found, centroid_x_save, centroid_y_save, contour_save
# -------------------------------------------------------------------------------------
# Moving towards blue sign: adjust focus view of camera, adjust motor speeds if needed,
# detects obstacles (not yet inserted), moves with adjusted motor speeds, obtains
# adjusted range, obtains adjusted centroid coordiantes of sign
#
# Uses: centroids found by search, current pan angle and tilt angle, range returned
# Returns: new range, new coordinates, (new) contour, new pan angle and tilt angle
# -------------------------------------------------------------------------------------
def move_to_sign(centroid_x_returned, centroid_y_returned,
                 pan_angle_returned, tilt_angle_returned,
                 range_returned):
    motor_speed_right = 12.0
    motor_speed_left = 12.0
    bot.update()
    # --------------------------------------------------------------------------------- Focus view
    if centroid_x_returned != centroid_image_x \
       and centroid_x_returned != 0:
        differance_x = round(((centroid_image_x - centroid_x_returned) * 0.0264583),3)
        tangent_x = differance_x / range_returned 
        pan_angle = pan_angle_returned + round(math.degrees(math.atan(tangent_x)),1)
    else:
        pan_angle = pan_angle_returned
    pan_angle_return = pan_angle
    if centroid_y_returned != centroid_image_y \
       and centroid_y_returned != 0:
        differance_y = round(((centroid_image_y - centroid_y_returned) * 0.0264583),3)
        tangent_y = differance_y / range_returned 
        tilt_angle = tilt_angle_returned - round(math.degrees(math.atan(tangent_y)),1)
    else:
        tilt_angle = tilt_angle_returned
    tilt_angle_return = tilt_angle
    bot.set_neck_angles( pan_angle_degrees=pan_angle,
                         tilt_angle_degrees=tilt_angle)
    #time.sleep(0.01)
    # --------------------------------------------------------------------------------- Determine direction adjustment
    if pan_angle > 100:
        motor_speed_left = 10.0
    if pan_angle < 80:
        motor_speed_right = 10.0
    # --------------------------------------------------------------------------------- Detect obstacles and react
    # Will be inserted later on
    # --------------------------------------------------------------------------------- Moving car
    bot.set_motor_speeds( motor_speed_left, motor_speed_right )
    time.sleep(2.0)
    # --------------------------------------------------------------------------------- Get new range measurement                            
    range_returned = get_range()
    time.sleep(0.01)
    # --------------------------------------------------------------------------------- Get new centroid coordinates
    sign_found = 0
    while sign_found == 0:
        sign_found,centroid_x_returned,centroid_y_returned, contour_save=search_sign()
        time.sleep(0.1)
    return range_returned, centroid_x_returned, centroid_y_returned, contour_save, \
           pan_angle_return, tilt_angle_return
# -------------------------------------------------------------------------------------
# Compare 2 images Both routines can be used (current use: MSE)
#
# Uses: image from disk, image found on sign
# Returns: number of non-zero pixels
# -------------------------------------------------------------------------------------
def bwc(imageA, imageB):
    cv2.bitwise_xor(imageA,imageB,output,mask=None)
    diff=cv2.countNonZero(output)
    #cv2.imshow('output',output)                                                      # (un)comment to hide/watch output images one by one
    #cv2.waitKey(0)
    return diff
def mse(imageA, imageB):                                                              # Mean Squared Error = differance in pixelintensity 
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])
    return err
# -------------------------------------------------------------------------------------
# Read the reference files from disk Blurring and thresholding to assure the pictures
# corrolate in values with the printed sign  
#
# Returns: images read 
# -------------------------------------------------------------------------------------    
def get_reference_images():
    signRight = cv2.imread('signright.jpg',0)
    if signRight != None:
        signRight = cv2.GaussianBlur(signRight,(5,5),0)
        _,signRight = cv2.threshold(signRight,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        signLeft = cv2.imread('signleft.jpg',0)
        if signLeft != None:
            signLeft = cv2.GaussianBlur(signLeft,(5,5),0)
            _,signLeft = cv2.threshold(signLeft,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
            signTurn = cv2.imread('signturn.jpg',0)
            if signTurn != None:
                signTurn = cv2.GaussianBlur(signTurn,(5,5),0)
                _,signTurn = cv2.threshold(signTurn,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
                signStop = cv2.imread('signstop.jpg',0)
                if signStop != None:
                    signStop = cv2.GaussianBlur(signStop,(5,5),0)
                    _,signStop = cv2.threshold(signStop,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    else:
        print 'Error(s) reading files !!!'
        wait = raw_input()
    flag_ready = 20
    return signRight, signLeft, signTurn, signStop
# -------------------------------------------------------------------------------------
# Match images: crop, warp and intensivy rectangle found and compare images
#
# Returns: next action
# -------------------------------------------------------------------------------------
def compare_images(centroid_x_returned, centroid_y_returned, contour_save):
    signRight, signLeft, signTurn, signStop = get_reference_images()                   # read reference files
    image, _ = bot.get_latest_camera_image()
    contour_points = contour_save.reshape(4, 2)                                                      
    points_sorted = np.zeros((4, 2), dtype = "float32")                                # initializing output window in same order
    sum_of_points = contour_points.sum(axis = 1)                                       # determine top-left, top-right, bottom-right, bottom-left
    points_sorted[0] = contour_points[np.argmin(sum_of_points)]
    points_sorted[2] = contour_points[np.argmax(sum_of_points)]
    differance = np.diff(contour_points, axis = 1)
    points_sorted[1] = contour_points[np.argmin(differance)]
    points_sorted[3] = contour_points[np.argmax(differance)]
    (tl, tr, br, bl) = points_sorted
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[0] - bl[0]) ** 2))                  # need this; for example: it could as well be a parallelogram 
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[0] - tl[0]) ** 2))
    heightA = np.sqrt(((tr[1] - br[1]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[1] - bl[1]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    maxHeight = max(int(heightA), int(heightB))
    destination = np.array([[0, 0],[maxWidth - 2, 0],
                            [maxWidth - 2, maxHeight - 2],
                            [0, maxHeight - 2]],dtype = "float32")
    M = cv2.getPerspectiveTransform(points_sorted, destination)
    warped_image = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    cv2.drawContours(image, [contour_save], -1, (0, 255, 0), 2)
    cv2.imshow("Cnt Found", image)
    cv2.waitKey(1)                                                                                       
    warped_image = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)                      # convert to gray, blur and threshold
    warped_image = cv2.GaussianBlur(warped_image,(5,5),0)
    thrh,warped_image = cv2.threshold(warped_image,0,255,
                                      cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    (h, w) = signRight.shape[:2]                                                       # equalize shapes
    resized = cv2.resize(warped_image, (w,h),
                         interpolation=cv2.INTER_AREA)
    cv2.imshow ('resized', resized)
    cv2.waitKey(1)
    output=signRight                                                                   # create window for bitwise output
    v_1 = mse(resized,signRight)
    if v_1 > 5000:
        v_2 = mse(resized,signLeft)
        if v_2 > 5000:
            v_3 = mse(resized,signTurn)
            if v_3 > 5000:
                next_action = 'STOP'
            else:
                next_action = 'TURN'
        else:
            next_action = 'LEFT'
    else:
        next_action = 'RIGHT'
    v_4 = mse(resized,signStop)
    return next_action
#--------------------------------------------------------------------------------------
# INITIALIZE_RB1
#--------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------- Set up a parser for command line arguments
parser = argparse.ArgumentParser( "Gets images from the robot" )
parser.add_argument( "hostname", default="localhost", nargs='?',
                     help="The ip address of the robot" )
args = parser.parse_args()
# ------------------------------------------------------------------------------------- Connect to the robot
#bot = py_websockets_bot.WebsocketsBot( args.hostname )
bot = py_websockets_bot.WebsocketsBot( "192.168.42.1" )
# ------------------------------------------------------------------------------------- Configure the sensors on the robot
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
# ------------------------------------------------------------------------------------- Initializing global variables
flag_ready = 0                                                                        # Redundant, just to enforce waiting for movements to finish
robot_status = 0
min_pan_angle = 65.0
max_pan_angle = 115.0
range_limit = 20                                                                      # When move in to close, the sign will be to big
next_action = 'START'
ride_switch = 0
#--------------------------------------------------------------------------------------
if __name__ == "__main__":

    bot.start_streaming_camera_images()
    time.sleep(2.0)
    image, _ = bot.get_latest_camera_image()
    image_height, image_width = image.shape [:2]
    centroid_image_x = int(image_width/2)
    centroid_image_y = int(image_height/2)
    while next_action != 'STOP':
        # --------------------------------------------------------------------------------
        # SEARCH_SIGN (until blue object found)
        # --------------------------------------------------------------------------------
        bot.centre_neck()
        pan_angle = 90.0
        pan_angle_returned = pan_angle
        pan_switch = 'RIGHT'
        tilt_angle = 90.0
        tilt_angle_returned = tilt_angle
        sign_found = 0
        while sign_found == 0:
            sign_found, \
                        centroid_x_returned, centroid_y_returned, \
                        contour_save = search_sign()
            if sign_found == 0:
                pan_angle_returned, pan_switch = look_around(pan_angle_returned,
                                                             pan_switch)
                time.sleep(0.01)
            time.sleep(0.5)                                                               # To avoid overload of web sockets
        # --------------------------------------------------------------------------------
        # MOVE_TO_SIGN (until <= 15 cm)
        # --------------------------------------------------------------------------------
        sign_found = 0
        ride_switch = 1
        range_returned = get_range()
        test_loop = 0
        #while test_loop <= 10:                                                             # For testing without motors
        while range_returned > range_limit:    
            range_returned, \
                            centroid_x_returned, \
                            centroid_y_returned, \
                            contour_save, \
                            pan_angle_returned, \
                            tilt_angle_returned = \
            move_to_sign(centroid_x_returned,
                         centroid_y_returned,
                         pan_angle_returned,
                         tilt_angle_returned,
                         range_returned)
        #    test_loop += 1
        # --------------------------------------------------------------------------------
        # READ_SIGN (until match) and ACT_ON_SIGN (next action or stop)
        # --------------------------------------------------------------------------------
        next_action = compare_images(centroid_x_returned, centroid_y_returned, contour_save)
        if next_action == 'STOP':
            pass
        if next_action == 'RIGHT':
            move_degr (-90)
        if next_action == 'LEFT':
            move_degr (90)
        if next_action == 'TURN':
            move_degr (90)
            move_degr (90)
        wait=raw_input()                                                               # Testing purposes
    # ---------------------------------------------------------------------------------- Finalize    
    cv2.destroyAllWindows()
    bot.set_motor_speeds( 0.0, 0.0 )
    bot.centre_neck()
    bot.disconnect()
