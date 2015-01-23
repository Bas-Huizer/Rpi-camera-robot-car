#! /usr/bin/python

# This script detects objects in a video stream (blue rectangles A4 size)
# It's meant as kernel for a sign-following robot script Part of the logical flow: find a blue rectangle in a video stream
# Inspirational site: http://roboticssamy.blogspot.nl/ (balancing robot, reading signs and following lines by vision)
#
# Note: insert cv2.imgshow statements to follow the image handling step by step (comment all steps and start with nr 1)  

import time
import argparse
import cv2
import numpy as np
import py_websockets_bot

latest_camera_image = None
latest_small_camera_image = None

# the camera_small_image_callback produced to much fall-out during manipulation of the images

def camera_image_callback( image, image_time ):
    global latest_camera_image
    # Put image processing here...
    latest_camera_image = image
      
if __name__ == "__main__":

    # Set up a parser for command line arguments
    parser = argparse.ArgumentParser( "Gets images from the robot using callbacks and displays them" )
    parser.add_argument( "hostname", default="localhost", nargs='?', help="The ip address of the robot" )
    args = parser.parse_args()
    # Connect to the robot
    bot = py_websockets_bot.WebsocketsBot( "192.168.42.1" )
    # Start streaming images from the camera
    bot.start_streaming_camera_images( camera_image_callback )
    # Run in a loop until the user presses Ctrl+C to quit
    try:
        while True:
            bot.update()
            switch_object_found = False
            if latest_camera_image != None:
                #1 - Set color range to search for blue shapes
                hsv = cv2.cvtColor(latest_camera_image, cv2.COLOR_BGR2HSV)
                lower_blue = np.array([110,50,50])
                upper_blue = np.array([130,255,255])
                #2 - Convert color found to white. Convert rest of image to back 
                mask_image = cv2.inRange(hsv, lower_blue, upper_blue)
                result_image = cv2.bitwise_and(latest_camera_image,latest_camera_image, mask= mask_image)
                #3 - Convert to Gray (needed for smoothing)
                gray_image = cv2.cvtColor(result_image, cv2.COLOR_BGR2GRAY )
                #4 - Remove Noise by smoothing and binarizing (several other options here, but this gave the best results at the end)
                blurred_image = cv2.GaussianBlur(gray_image,(15,15),0)
                ret3,threshold_image = cv2.threshold(blurred_image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
                #5 - Find edges of all shapes 
                edged_image = cv2.Canny(threshold_image,threshold1=90, threshold2=190)
                #6 - Find contours of all shapes
                contours, hierarchy = cv2.findContours(edged_image,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
                #7 - Determine size and select the biggest shape with 3 - 5 corners
                objects_found = len(contours)
                if objects_found >= 1:               
                    loop_count = 0
                    loop_count = int(loop_count)
                    area_save = 0
                    loop_count_save = 0
                    while loop_count < objects_found:
                        cnt = contours[loop_count]
                        M = cv2.moments(cnt)
                        area = cv2.contourArea(cnt)
                        epsilon = 0.1*cv2.arcLength(cnt,True)
                        approx = cv2.approxPolyDP(cnt,epsilon,True)
                        corners_shape = len (approx)
                        # Filtering shapes (approximately rectangle and > 30 x 30 pxs) 
                        if corners_shape > 3 and corners_shape < 6:
                            if area > 900:
                                if loop_count == 0:
                                    loop_count_save = loop_count
                                    area_save = area
                                elif area > area_save:
                                    loop_count_save = loop_count
                                    area_save = area
                        loop_count += 1
                    if area_save > 900:
                        switch_object_found = True
                        print 'Found largest rectangle = nr',loop_count_save, 'area size =', area_save
            cv2.waitKey( 1 )
    except KeyboardInterrupt:
        pass    # Catch Ctrl+C
        
    cv2.destroyAllWindows()
    # Disconnect from the robot
    bot.disconnect()
