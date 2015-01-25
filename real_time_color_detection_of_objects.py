#! /usr/bin/python

#-----------------------------------------------------------------------------------------------------------------------------------------
# This script detects objects (blue rectangles 20x27 cm) in a video stream.
# It's created as routine for a sign-reading robot script. 
# 
# Tip: use cv2.imgshow to follow the image handling step by step (comment all steps and start with nr 1)
#
# Note: Light conditions are essential for color tracing Used ranges work with lamp light but make the script very slow!
#       The centroid coordinates of the largest rectangle found will be used while moving towards the sign (switch found_for_the_first_time)
#       The camera_small_image_callback produced to much fall-out while morphing the images
#       Inspirational site: http://roboticssamy.blogspot.nl/ (balancing robot, reading signs and following lines by vision) Great Stuff !!
#-----------------------------------------------------------------------------------------------------------------------------------------
import time
import argparse
import cv2
import numpy as np
import py_websockets_bot
#----------------------------------------------------------------------------------------------------------------------------------------- 
latest_camera_image = None
def camera_image_callback( image, image_time ):
    global latest_camera_image
    # If needed put image processing here...
    latest_camera_image = image
#--------------------------------------------------------------------------------------------------------- Set up a parser for command line arguments
parser = argparse.ArgumentParser( "Gets images from the robot using callbacks" )
parser.add_argument( "hostname", default="localhost", nargs='?', help="The ip address of the robot" )
args = parser.parse_args()
#--------------------------------------------------------------------------------------------------------- Connect to the robot
bot = py_websockets_bot.WebsocketsBot( "192.168.42.1" )
#--------------------------------------------------------------------------------------------------------- Initialize global variables
found_for_the_first_time = 1
#---------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    #----------------------------------------------------------------------------------------------------- Start streaming images from the camera
    bot.start_streaming_camera_images( camera_image_callback )
    try:
        while True:
            bot.update()
            switch_object_found = False
            if latest_camera_image != None:
                cv2.imshow('Original', latest_camera_image)
                #----------------------------------------------------------------------------------------- 0 - Set color range to search for blue shapes
                hsv = cv2.cvtColor(latest_camera_image, cv2.COLOR_BGR2HSV)
                lower_blue = np.array([110,50,80])
                upper_blue = np.array([131,119,255])
                #----------------------------------------------------------------------------------------- 1 - Mask only blue  
                mask_image = cv2.inRange(hsv, lower_blue, upper_blue)
                cv2.imshow('step-1 - mask', mask_image)
                #----------------------------------------------------------------------------------------- 2 - Convert masked color to white. Rest to black 
                result_image = cv2.bitwise_and(latest_camera_image,latest_camera_image, mask= mask_image)
                cv2.imshow('step-2 - convert', result_image)
                #----------------------------------------------------------------------------------------- 3 - Blurring the result to de-noise
                blurred_image = cv2.bilateralFilter(result_image,9,75,75)
                cv2.imshow('step 3 - blurred', blurred_image)
                #----------------------------------------------------------------------------------------- 4 - Convert to Gray (needed for binarizing)
                gray_image = cv2.cvtColor(blurred_image, cv2.COLOR_BGR2GRAY )
                cv2.imshow('step-4 - gray', gray_image)
                #----------------------------------------------------------------------------------------- 5 - Binarizing (Otsus threshold)
                ret3,threshold_image = cv2.threshold(gray_image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
                cv2.imshow('step-5 - Otsus Threshold', threshold_image)
                #----------------------------------------------------------------------------------------- 6 - Find edges of all shapes 
                edged_image = cv2.Canny(threshold_image,threshold1=90, threshold2=190)
                cv2.imshow('step-6 - Canny', edged_image)                                                    # Will disappear as result of contours
                #----------------------------------------------------------------------------------------- 7 - Find contours of all shapes
                contours, hierarchy = cv2.findContours(edged_image,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
                cv2.imshow('step-7 - Contouren', edged_image)
                #----------------------------------------------------------------------------------------- 8 - Filter on size and shape
                objects_found = len(contours)
                if objects_found >= 1:               
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
                            if area > 900:
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
                    if area_save > 900:
                        switch_object_found = True
                        print 'Shape',loop_count_save, ', largest rectangle of', rectangle_count,', size', area_save, ', coordinates', centroid_x_save, centroid_y_save
                        if found_for_the_first_time:
                            centroid_x_first_found = centroid_x_save
                            centroid_y_first_found = centroid_y_save
                            found_for_the_first_time = 0
                        print 'First coordinates found =',centroid_x_first_found, centroid_x_first_found
            cv2.waitKey( 1 )
    except KeyboardInterrupt:
        pass    # Catch Ctrl+C
        
    #cv2.destroyAllWindows()
    # Disconnect from the robot
    bot.disconnect()
