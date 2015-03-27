#! /usr/bin/python

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

# -------------------------------------------------------------------------------------
# Global variables
# -------------------------------------------------------------------------------------
b_low = 108                                                                           # BGR values (calibrate first)
g_low = 56                                                                            # Defaults:   
r_low = 36                                                                            # Low:  110,  50,  50
b_high = 129                                                                          # High: 130, 255, 255
g_high = 134                                                                          # At home:
r_high = 76                                                                           # Low:  110,  50,  85
lower_blue = np.array([b_low,g_low,r_low])                                            # High: 131, 119, 255
upper_blue = np.array([b_high,g_high,r_high])                                         #
min_pan_angle = 75.0                                                                  # Limit swirling of neck
max_pan_angle = 105.0                                                                 #
range_limit = 40                                                                      # Safety limit 
motor_speed = 50.0                                                                    # = 50%; corr. to PMW 50Hz
next_action = 'START'                                                                 # 
max_area = 108384                                                                     # 
tuner_pan = 1                                                                         # Tuning factor multiplies area ratio (motors)
tuner_tilt = 2.5                                                                      # Idem (Tilt)
# -------------------------------------------------------------------------------------
# Timer routine
# To mitigate Python signal dependancy of time.sleep
#
# Input: milliseconds
# -------------------------------------------------------------------------------------
def time_out (milsec):
    for i in  xrange (milsec):
        time.sleep(0.001)
# -------------------------------------------------------------------------------------
# Ultrasonic range routine
#
# Returns: Range measured
# -------------------------------------------------------------------------------------
def get_range ():
    bot.update()
    status_dict, read_time = bot.get_robot_status_dict()
    sensor_dict = status_dict[ "sensors" ]
    range_return = sensor_dict[ "ultrasonic" ][ "data" ]
    print 'Sensor range     =', range_return, 'cm'
    return range_return
# -------------------------------------------------------------------------------------
# Camera range routine          
#                                                                                     | focal_length = (pixels_width * distance)/real_width
# Input: area in pixels                                                               | pixel_width  = SQR ((real_width/real_hight) * area)       
# Returns: Range measured    
# -------------------------------------------------------------------------------------
def get_camera_range (area):
    range_return = round(((real_width * focal_length)/ math.sqrt(ratio_w_h * area)),0)
    print 'Camera range     =', range_return, 'cm'
    return range_return
# -------------------------------------------------------------------------------------
# Fast image search routine, searches for a large blue object
#
# Returns: centroid coordinates, area and switch 
# -------------------------------------------------------------------------------------
def find_marker():
    bot.update()
    marker_found = 0
    centroid_x = 0
    centroid_y = 0
    area = 0
    image, _ = bot.get_latest_camera_image()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)                                      # 0 - Set color space
    mask_image = cv2.inRange(hsv, lower_blue, upper_blue)                             # 1 - Mask only blue
    result_image = cv2.bitwise_and(image,image, mask= mask_image)                     # 2 - Convert masked color to white. Rest to black 
    result_image = cv2.cvtColor(result_image, cv2.COLOR_BGR2GRAY )                    # 3 - Convert to Gray (needed for binarizing)
    contours, _ = cv2.findContours(result_image,
                                   cv2.RETR_LIST,
                                   cv2.CHAIN_APPROX_SIMPLE)                           # 4 - Find contours of all shapes
    contours = sorted(contours, key=cv2.contourArea, reverse=True) [:1]               # 5 - Select biggest; drop the rest
    if len (contours) > 0:
        cnt = contours[0]
        x,y,w,h = cv2.boundingRect(cnt)
        cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.drawContours(image, [cnt], -1, (0, 0, 255), 1)                            # Not needed; Just to display the differance
        cv2.imshow("Cnt Found", image)
        cv2.waitKey( 1 )                                                              # Needed for display of the window
        centroid_x = x + (w/2)
        centroid_y = y + (y/2)
        area = w * h
        if area > 5000:
            marker_found = 1
        print'centroids at      =', centroid_x, ' / ', centroid_y
        print'area              =', area
    return centroid_x, centroid_y, area, marker_found
#-------------------------------------------------------------------------------------- Set up a parser for command line arguments
parser = argparse.ArgumentParser( "Gets images from the robot" )
parser.add_argument( "hostname", default="localhost", nargs='?',
                     help="The ip address of the robot" )
args = parser.parse_args()
# ------------------------------------------------------------------------------------- Connect to the robot
#bot = py_websockets_bot.WebsocketsBot( args.hostname )
bot = py_websockets_bot.WebsocketsBot( "192.168.42.1" )
#--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------
if __name__ == "__main__":
    bot.start_streaming_camera_images()
    time.sleep(2.0)
    print 'camera started'
    image, _ = bot.get_latest_camera_image()
    image_height, image_width = image.shape [:2]
    centroid_image_x = int(image_width/2)
    centroid_image_y = int(image_height/2)
    image_size = image.size
    image_size_calc = image_height * image_width
    while next_action != 'STOP':
        # --------------------------------------------------------------------------------
        # SEARCH_MARKER (until blue object found)
        # --------------------------------------------------------------------------------
        marker_found = 0
        tilt_angle = 90
        pan_angle = 90
        centroid_x, centroid_y, area, marker_found = find_marker()
        while marker_found == 0:
            if pan_angle < max_pan_angle:
               pan_angle += 2.5
            else:
                pan_angle = 90
                print 'SHUFFLE 25 degr', motor_speed
            #    bot.set_motor_speeds( -motor_speed, motor_speed )
                time_out (200)                                                                 # Turn left for approx 25 degr
                bot.set_motor_speeds (0.0 , 0.0)
            bot.set_neck_angles( pan_angle,tilt_angle)
            time_out (200)
            centroid_x, centroid_y, area, marker_found = find_marker()
            print pan_angle
        print'centroid at      =', centroid_x, centroid_y
        print'area             =', area
        lapse_tot += lapse_time 
        # --------------------------------------------------------------------------------
        # MOVE_TO_SIGN (until <= 40 cm)
        # --------------------------------------------------------------------------------
        marker_found = 0
        # Calculate motor speeds for curve (pan & centroid offset) -----------------------
        area_dist_corr = (image_size_calc / area) * tuner_pan
        pan_offset_corr = (90-pan_angle) * 1.00000
        pan_offset_corr = pan_offset_corr / 180
        pan_offset_corr = pan_offset_corr / area_dist_corr
        pxs_offset_corr = (centroid_x - centroid_image_x) * 1.00000
        pxs_offset_corr = pxs_offset_corr / (image_width / 2)
        pxs_offset_corr = pxs_offset_corr / area_dist_corr
        tot_offset_corr = pan_offset_corr + pxs_offset_corr
        motor_speed_l = round((motor_speed + (tot_offset_corr * motor_speed)),1)
        motor_speed_r = round((motor_speed - (tot_offset_corr * motor_speed)),1)
        # Calculate tilt correction ------------------------------------------------------
        pxs_offset_corr_t = (centroid_y - centroid_image_y) * 1.00000
        pxs_offset_corr_t = pxs_offset_corr_t / (image_height / 2)
        pxs_offset_corr_t = pxs_offset_corr_t / (area_dist_corr /tuner_tilt)
        tilt_offset_corr = 180 * pxs_offset_corr_t
        print'Motor left       =', motor_speed_l
        print'Motor right      =', motor_speed_r
        tilt_angle = round((tilt_angle + tilt_offset_corr),1)
        bot.set_neck_angles( pan_angle,tilt_angle)
        #print'__________________'
        wait = raw_input ()
        if wait == 'q':
            bot.centre_neck ()
            break
