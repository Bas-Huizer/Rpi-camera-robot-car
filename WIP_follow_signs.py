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
#            if ride_switch == 0:
#                robot_status = move_degr(30)
    return pan_angle_send, pan_switch
# -------------------------------------------------------------------------------------------------------- Motor routines
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
    time_start = time.time()
    pan_angle_return = pan_angle_send
    bot.update()
    sign_found = 0
    centroid_x_save = 0
    centroid_y_save = 0
    area_save = 0.0
    leftmost = (0,0)
    bottommost = (0,0)
    topmost = (0,0)
    rightmost = (0,0)
    image, image_time = bot.get_latest_camera_image()
    image_height, image_width = image.shape[:2]
    #cv2.imshow('Original', image)
    #cv2.waitKey(1)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)                                               # 0 - Set color range to search for blue shapes
    lower_blue = np.array([110,50,80])
    upper_blue = np.array([131,119,255])
    mask_image = cv2.inRange(hsv, lower_blue, upper_blue)                                      # 1 - Mask only blue
    result_image = cv2.bitwise_and(image,image, mask= mask_image)                              # 2 - Convert masked color to white. Rest to black 
    #cv2.destroyWindow(mask_image)
    result_image = cv2.bilateralFilter(result_image,9,75,75)                                   # 3 - Optional: Blurring the result to de-noise
    result_image = cv2.cvtColor(result_image, cv2.COLOR_BGR2GRAY )                             # 4 - Convert to Gray (needed for binarizing)
    #ret3,threshold_image = cv2.threshold(gray_image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)  # 5 - Optional: Binarizing (Otsus threshold)
    result_image = cv2.Canny(result_image,threshold1=90, threshold2=190)                       # 6 - Find edges of all shapes
    cv2.imshow('Edged', result_image)                                                
    cv2.waitKey(1)
    contours, hierarchy = cv2.findContours(result_image,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE) # 7 - Find contours of all shapes
    objects_found = len(contours)                                                              # 8 - Filter on size and shape
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
            epsilon = 0.1*cv2.arcLength(cnt,True)                                              # 9 - Calculate centroid coordinates
            approx = cv2.approxPolyDP(cnt,epsilon,True)
            corners_shape = len (approx)
            if corners_shape == 4:
                if area > 5000:
                    centroid_x = int(M['m10']/M['m00'])
                    centroid_y = int(M['m01']/M['m00'])
                    if loop_count == 0:                                                        # 10 - Keep the largest rectangle
                        loop_count_save = loop_count
                        rectangle_count += 1
                        area_save = area
                        centroid_x_save = centroid_x
                        centroid_y_save = centroid_y
                    elif area < area_save:
                        loop_count_save = loop_count
                        rectangle_count += 1
                        centroid_x_save = centroid_x
                        centroid_y_save = centroid_y
                        area_save = area
            loop_count += 1
        if rectangle_count > 0:
            print 'rectangle', rectangle_count, 'of', objects_found, 'objects'
            sign_found = 1
            cnt = contours[loop_count_save]
            leftmost = tuple(cnt[cnt[:,:,0].argmin()][0])
            rightmost = tuple(cnt[cnt[:,:,0].argmax()][0])
            bottommost = tuple(cnt[cnt[:,:,1].argmax()][0])
            topmost = tuple(cnt[cnt[:,:,1].argmin()][0])
            time_stop = time.time()
            print leftmost, rightmost, topmost, bottommost
            print 'Duration ', round((time_stop - time_start),1), 'sec'
    return sign_found, pan_angle_return, centroid_x_save, centroid_y_save, area_save,image_height, image_width, leftmost, rightmost, bottommost, topmost
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
range_limit = 15                                                                      # If closer, the sign will be to big
leftmost = (0,0)
bottommost = (0,0)
rightmost = (0,0)
topmost = (0,0)
#---------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    
    bot.start_streaming_camera_images()
    time.sleep(2.0)
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
        sign_found, pan_angle_returned, centroid_x_returned, centroid_y_returned, area_returned,image_height, image_width,leftmost, rightmost, bottommost, topmost = search_sign(pan_angle_send)
        if sign_found == 0:
            pan_angle_send, pan_switch = look_around(pan_angle_returned, pan_switch, ride_switch)
            time.sleep(0.01)
        time.sleep(0.5)                                                               # To avoid overload (Search routine takes 0.4 sec)
    print 'Found coord.', centroid_x_returned, centroid_y_returned,'neck angle', pan_angle_returned, 'current angle', pan_angle_send
    print 'Image size  ', image_width, image_height
    #time.sleep(2.0)
    ################################################################################################## End of SEARCH_SIGN Start of MOVE_TO_SIGN
    # ------------------------------------------------------------------------------------------------ init move
    centroid_image_x = int(image_width/2)
    centroid_image_y = int(image_height/2)
    #min_pan_angle = 75.0
    #max_pan_angle = 105.0
    sign_found = 0
    ride_switch = 1
    tilt_angle_save = tilt_angle
    range_returned = get_range()
    test_range_returned = range_returned
    print 'First range =', range_returned
    while test_range_returned > range_limit:
        motor_speed_right = 12.0
        motor_speed_left = 12.0
        bot.update()
    # ------------------------------------------------------------------------------------------------ Focus view
        if centroid_x_returned != centroid_image_x and centroid_x_returned != 0:
            differance_x = round(((centroid_image_x - centroid_x_returned) * 0.0264583),1)
            tangent_x = differance_x / range_returned 
            pan_angle = pan_angle_returned + round(math.degrees(math.atan(tangent_x)),0)
            pan_angle_send = pan_angle
        if centroid_y_returned != centroid_image_y and centroid_y_returned != 0:
            differance_y = round(((centroid_image_y - centroid_y_returned) * 0.0264583),1)
            tangent_y = differance_y / range_returned 
            tilt_angle = tilt_angle_save - round(math.degrees(math.atan(tangent_y)),0)
            tilt_angle_save = tilt_angle
        bot.set_neck_angles( pan_angle_degrees=pan_angle, tilt_angle_degrees=tilt_angle)
        #time.sleep(0.01)
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
        #time.sleep(2.0)
    # ------------------------------------------------------------------------------------------------ Get new range measurement                            
        range_returned = get_range()
        print 'New range =', range_returned, test_range_returned
        time.sleep(0.01)
    # ------------------------------------------------------------------------------------------------ Get new image coordinates
        while sign_found == 0:
            sign_found, pan_angle_returned, centroid_x_returned, centroid_y_returned, area_returned,image_height, image_width, leftmost, rightmost, bottommost, topmost = search_sign(pan_angle_send)
            time.sleep(0.1)
        print 'New coordinates =', centroid_x_returned, centroid_y_returned
        sign_found = 0
        test_range_returned -= 5
    ################################################################################################## End of MOVE_TO_SIGN Start of READ_SIGN
    print 'leftmost', leftmost, 'rightmost',rightmost,'bottommost', bottommost, 'topmost',topmost,
    print 'center', centroid_x_returned, centroid_y_returned
    print 'area', area_returned
    x = leftmost [0]
    x1 = rightmost [0]
    y = bottommost [1]
    y1 = topmost[1]
    w = x1 - x
    h = y - y1
    image, image_time = bot.get_latest_camera_image()
    print image.shape
    print x, x1, y, y1,
    #roi= cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),2)
    roi= cv2.rectangle(image,(x,y1),(x1,y),(0,255,0),2)                                              # top_left => bottom_right
    image[x:y1, x1:y] = roi                                                                          # Location in image 
    cv2.imshow ('?',image)                                                                           # uncomment these 3 lines for visual feedback 
    cv2.waitKey(1)                                                                                   # while testing the routine
    
    # ------------------------------------------------------------------------------------------------ Finalize    
    #cv2.destroyAllWindows()
    bot.disconnect()

