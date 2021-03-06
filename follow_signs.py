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
# Uses:    Last pan_angle
# Returns: New pan_angle
# -------------------------------------------------------------------------------------
def look_around (pan_angle_returned):
    pan_angle = pan_angle_returned
    if pan_angle < max_pan_angle:
        pan_angle += 5.0
        pan_angle_return = pan_angle
    else:
        pan_angle = min_pan_angle
        pan_angle_return = pan_angle
        bot.set_motor_speeds( -motor_speed, motor_speed )                                           # Corrolates to PWM 50 Hz
        time.sleep(0.4)                                                               # Turn left for approx 45 degr
    bot.set_neck_angles( pan_angle_degrees=pan_angle,
                             tilt_angle_degrees=tilt_angle)
    time.sleep (0.001)
    return pan_angle_return
# -------------------------------------------------------------------------------------
# Ultrasonic range routine
#
# Returns: Range measured
# -------------------------------------------------------------------------------------
def get_range ():                                                                     # TO DO: reference range through camera
    bot.update()
    status_dict, read_time = bot.get_robot_status_dict()
    sensor_dict = status_dict[ "sensors" ]
    data = sensor_dict[ "ultrasonic" ][ "data" ]
    if data > 100:
        data = 100
    range_return = data
    return range_return
# -------------------------------------------------------------------------------------
# Image search routine, searches for a large blue object
#
# Returns: switch found + centroid coordinates + contour found
# -------------------------------------------------------------------------------------
def search_sign():
    bot.update()
    sign_found = 0
    centroid_x_save = 0
    centroid_y_save = 0
    area_save = 0.0
    image, _ = bot.get_latest_camera_image()
    #cv2.imshow('img', image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)                                      # 0 - Set color range to search for blue shapes
    lower_blue = np.array([106,30,101]) 
    upper_blue = np.array([130,102,246])
    mask_image = cv2.inRange(hsv, lower_blue, upper_blue)                             # 1 - Mask only blue
    #cv2.imshow('mask', mask_image)
    result_image = cv2.bitwise_and(image,image, mask= mask_image)                     # 2 - Convert masked color to white. Rest to black 
    result_image = cv2.bilateralFilter(result_image,9,75,75)                          # 3 - Optional: Blurring the result to de-noise
    result_image = cv2.cvtColor(result_image, cv2.COLOR_BGR2GRAY )                    # 4 - Convert to Gray (needed for binarizing)
    result_image = cv2.Canny(result_image,threshold1=90, threshold2=190)              # 5 - Find edges of all shapes
    cv2.imshow('Edged', result_image)                                                
    cv2.waitKey(1)                                                                    # Needed for display 
    contours, _ = cv2.findContours(result_image,cv2.RETR_LIST,
                                   cv2.CHAIN_APPROX_SIMPLE)                           # 6 - Find contours of all shapes
    contours = sorted(contours, key=cv2.contourArea, reverse=True) [:4]               # 7 - Select biggest 4; drop the rest
    contour_save = None
    objects_found = len(contours)
    if objects_found >= 1:               
        loop_count = 0
        loop_count = int(loop_count)
        rectangle_count = 0
        while loop_count < objects_found:
            cnt = contours[loop_count]
            M = cv2.moments(cnt)
            area = cv2.contourArea(cnt)
            epsilon = 0.1*cv2.arcLength(cnt,True)                                     
            approx = cv2.approxPolyDP(cnt,epsilon,True)
            if len (approx) == 4:
                if area > 5000:
                    if loop_count == 0:                                               # 8 - Keep the smallest aledged rectangle
                        rectangle_count += 1
                        contour_save = approx
                        area_save = area
                        centroid_x_save = int(M['m10']/M['m00'])                      # 9 - Calculate centroid coordinates
                        centroid_y_save = int(M['m01']/M['m00'])
                    elif area < area_save:
                        rectangle_count += 1
                        contour_save = approx
                        centroid_x_save = int(M['m10']/M['m00'])
                        centroid_y_save = int(M['m01']/M['m00'])
            loop_count += 1
        if rectangle_count > 0:
            sign_found = 1
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
    motor_speed = 50.0
    #left_motor_scaling = -(0.5*1.66667)
    #motor_speed_left += left_motor_scaling
    # --------------------------------------------------------------------------------- Detect obstacles and react
    bot.update()
    status_dict, read_time = bot.get_robot_status_dict()                              # Currently just emergency break
    sensor_dict = status_dict[ "sensors" ]                                            # Evasion routine will be filled in later
    sensor_data = sensor_dict[ "digital" ][ "data" ]
    if sensor_data != 24:                                                             # Test for any IR sensor signal
       bot.set_motor_speeds( -0.0, 0.0 )
       print 'Obstacle detected!'
       wait = raw_input ()
    # --------------------------------------------------------------------------------- Focus view on centroid coordinates
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
    # --------------------------------------------------------------------------------- Adjust motor speeds to direction
    angle_to_turn = pan_angle - 90.0                                                  
    angle_radians = abs(angle_to_turn)* 0.017453
    differential_distance = round ((14.8 * angle_radians),1)                          # Length of arc to turn (angle times bot-width
    outer_wheel_distance = range_returned + differential_distance                     # Total distance to run for the outer wheel
    perc_outer_wheel_distance =  round ((outer_wheel_distance / range_returned),1)    
    half_diff_speed = ((perc_outer_wheel_distance * motor_speed)-motor_speed)/2
    if angle_to_turn < 0:                                                             # Curve to right
        bot.set_motor_speeds (motor_speed + half_diff_speed), (motor_speed -
                                                               half_diff_speed)
    else:                                                                             # Curve to left
        bot.set_motor_speeds (motor_speed - half_diff_speed), (motor_speed +
                                                               half_diff_speed)
    time.sleep (2.0)                                                                  # interval before next adjustment
    # --------------------------------------------------------------------------------- Get new range measurement                            
    range_returned = get_range()
    # --------------------------------------------------------------------------------- Get new centroid coordinates
    sign_found = 0
    while sign_found == 0:
        sign_found,centroid_x_returned,centroid_y_returned, contour_save=search_sign()
        if sign_found == 0:                                                           # When focus is lost
            bot.update()
            bot.set_motor_speeds (0.0, 0.0)
            pan_angle_returned = look_around(pan_angle_returned)
        time.sleep (0.001)
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
    bot.update()
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
                v_4 = mse(resized,signStop)
                if v_4 > 5000:
                    next_action = 'NO MATCH'
                else:
                    next_action = 'STOP'
            else:
                next_action = 'TURN'
        else:
            next_action = 'LEFT'
    else:
        next_action = 'RIGHT'
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
min_pan_angle = 65.0
max_pan_angle = 115.0
range_limit = 40                                                                      # When move in to close, the sign will be to big
next_action = 'START'
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
        pan_angle = min_pan_angle
        pan_angle_returned = pan_angle
        tilt_angle = 90.0
        tilt_angle_returned = tilt_angle
        sign_found = 0
        #print 'INITIAL SEARCH'
        while sign_found == 0:
            sign_found, \
                        centroid_x_returned, centroid_y_returned, \
                        contour_save = search_sign()
            if sign_found == 0:
                pan_angle_returned = look_around(pan_angle_returned)
            time.sleep (0.001)
        print 'c-x/c-y/pan/tilt'
        print centroid_x_returned, centroid_y_returned, pan_angle_returned, tilt_angle_returned
        # --------------------------------------------------------------------------------
        # MOVE_TO_SIGN (until <= 25 cm)
        # --------------------------------------------------------------------------------
        sign_found = 0
        range_returned = get_range()
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
            print 'c-x/c-y/pan/tilt/range'
            print centroid_x_returned, centroid_y_returned, pan_angle_returned, tilt_angle_returned, range_returned
        # --------------------------------------------------------------------------------
        # READ_SIGN (until match) and ACT_ON_SIGN (next action or stop)
        # --------------------------------------------------------------------------------
        next_action = compare_images(centroid_x_returned, centroid_y_returned, contour_save)
        if next_action == 'STOP':
            print 'STOP'
            pass
        if next_action == 'RIGHT':
            print 'RIGHT'
            bot.set_motor_speeds( motor_speed, -motor_speed )
            time.sleep(0.8)
        if next_action == 'LEFT':
            print 'LEFT'
            bot.set_motor_speeds( -motor_speed, motor_speed )
            time.sleep(0.8)
        if next_action == 'TURN':
            print 'TURN'
            bot.set_motor_speeds( motor_speed, -motor_speed )
            time.sleep(0.8)
            bot.set_motor_speeds( motor_speed, -motor_speed )
            time.sleep(0.8)            
        if next_action == 'NO MATCH':
            print 'NO MATCH'
        time.sleep(3.0)
        cv2.destroyAllWindows()
        bot.update()
    # ---------------------------------------------------------------------------------- Finalize    
    cv2.destroyAllWindows()
    bot.set_motor_speeds( 0.0, 0.0 )
    bot.centre_neck()
    print 'FINISHED'
    bot.disconnect()
