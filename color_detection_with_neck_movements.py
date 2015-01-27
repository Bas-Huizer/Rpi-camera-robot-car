E#! /usr/bin/python

#----------------------------------------------------------------------------------------------------------------------------------------- 
# This script detects objects in a video stream (blue rectangles A4 size)
# 
# Inspirational site: http://roboticssamy.blogspot.nl/ (balancing robot, reading signs and following lines by vision)
#
# Note: Content of ........ is copied into this script
#       The speed of the neck movements is adjusted to the latency of websockets It probably could be increased when processed local
#----------------------------------------------------------------------------------------------------------------------------------------- 
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

latest_camera_image = None
def camera_image_callback( image, image_time ):
    global latest_camera_image
    # Put image processing here...
    latest_camera_image = image
# -------------------------------------------------------------------------------------------------------- Neck movements
def search_right (pan_angle):
    pan_angle -= 9.0
    bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
    time.sleep( 0.1 )
    return pan_angle
def search_left (pan_angle):
    pan_angle += 9.0
    bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
    time.sleep( 0.1 )
    return pan_angle
def look_left (pan_angle):
    while pan_angle < 90.0:
        pan_angle += 1.0
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        time.sleep( 0.1 )
    return pan_angle
def look_right (pan_angle):
    while pan_angle > 90.0:
        pan_angle -= 1.0
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        time.sleep( 0.1)
    return pan_angle
#--------------------------------------------------------------------------------------------------------- Set up a parser for command line arguments
parser = argparse.ArgumentParser( "Gets images from the robot using callbacks" )
parser.add_argument( "hostname", default="localhost", nargs='?', help="The ip address of the robot" )
args = parser.parse_args()
# -------------------------------------------------------------------------------------------------------- Connect to the robot
#bot = py_websockets_bot.WebsocketsBot( args.hostname )                               # When running a local script on the Pi
bot = py_websockets_bot.WebsocketsBot( "192.168.42.1" )                               # When running a script at a remote computer using webSockets
# -------------------------------------------------------------------------------------------------------- Initializing variables
flag_ready = 0                                                                        # Redundant switch, just to enforce waiting for movements to finish
robot_status = 0
min_pan_angle = 0.0
max_pan_angle = 180.0
#---------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    
    bot.start_streaming_camera_images( camera_image_callback )
    ################################################################################################## Start of SEARCH_SIGN routine
    bot.centre_neck()
    pan_angle = 90.0
    pan_angle_save = 90.0
    tilt_angle = 90.0
    pan_switch = 'RIGHT'
    sign_found = 0
    while sign_found == 0:
        start_timer = time.time()
        bot.update()
        if latest_camera_image != None:
            hsv = cv2.cvtColor(latest_camera_image, cv2.COLOR_BGR2HSV)                               # 0 - Set color range to search for blue shapes
            lower_blue = np.array([110,50,80])
            upper_blue = np.array([131,119,255])
            mask_image = cv2.inRange(hsv, lower_blue, upper_blue)                                    # 1 - Mask only blue
            result_image = cv2.bitwise_and(latest_camera_image,latest_camera_image, mask= mask_image)# 2 - Convert masked color to white. Rest to black 
            blurred_image = cv2.bilateralFilter(result_image,9,75,75)                                # 3 - Blurring the result to de-noise
            gray_image = cv2.cvtColor(blurred_image, cv2.COLOR_BGR2GRAY )                            # 4 - Convert to Gray (needed for binarizing)
            ret3,threshold_image = cv2.threshold(gray_image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU) # 5 - Binarizing (Otsus threshold)
            edged_image = cv2.Canny(threshold_image,threshold1=90, threshold2=190)                   # 6 - Find edges of all shapes 
            #cv2.imshow('step-6 - Canny', edged_image)                                                
            contours, hierarchy = cv2.findContours(edged_image,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)# 7 - Find contours of all shapes
            time_lapse = round((time.time() - start_timer),2)                                        # Just for testing purposes
            objects_found = len(contours)                                                            # 8 - Filter on size and shape
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
                        if area > 4000:
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
                    print 'Shape',loop_count_save, ', largest rectangle of', rectangle_count,', size', area_save, ', coordinates', centroid_x_save, centroid_y_save
                print 'Duration of analyzing image =', time_lapse, 'sec'
            if sign_found == 0:
                if pan_switch == 'RIGHT':
                    if pan_angle_save > min_pan_angle:
                        pan_angle_save = search_right(pan_angle)
                        pan_angle = pan_angle_save
                        print 'pan angle =', pan_angle, 'pan angle save =', pan_angle_save
                    else:
                        pan_switch = 'LEFT'
                        pan_angle_save = look_left(pan_angle)
                        pan_angle = pan_angle_save
                else:
                    if pan_angle_save < max_pan_angle:
                        pan_angle_save = search_left(pan_angle)
                        pan_angle = pan_angle_save
                        print 'pan angle =', pan_angle, 'pan angle save =', pan_angle_save
                    else:
                        pan_switch = 'RIGHT'
                        pan_angle_save = look_right(pan_angle)
                        pan_angle = pan_angle_save
        cv2.waitKey( 1 ) #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Not sure why, but should be within arching IF !!!!!
    print 'Sign found, size',area_save,', coordinates', centroid_x_save, centroid_y_save,'neck position', pan_angle_save
    ################################################################################################## End of SEARCH_SIGN routine
    bot.centre_neck()
    cv2.destroyAllWindows()
    bot.disconnect()
