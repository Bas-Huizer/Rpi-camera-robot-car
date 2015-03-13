#! /usr/bin/python

#-----------------------------------------------------------------------------------------------------------------------------------------------------------
# This script enables interactive manipulating of the BGR values while detecting colored shapes in a video stream   
# Light quality is essential for object detection by color. Hobbying at night enforces tight calibration for testing scripts. ;-)
# The script uses callback video streaming through websockets. It enables remote execution of the Rpi scripts
# The BGR  values can be adjusted trough the use of the trackbars.
# I used 2 trackbar windows to present the collors as well. If not needed, the trackbars can be put in one window leaving 1pxs black for creating the window
# Notes: GPIO configuration can't be used (yet) when running remote scripts 
#        Inspirational site: http://roboticssamy.blogspot.nl/ (balancing robot, reading signs and following lines by vision) Great Stuff !!
#        The trackbars are preset for detecting shapes within the blue range at my own best average values
#        In documentation 110,50,50 - low and 130,255,255 - high, is commonly used 
#        Start with increasing the lower values. Red is essential, secondly adjust the blue value, last the green
#        Then lower the high values by the same priority
#        BGR values that worked fine for me:
#               -----low-----   -----high----
#                B    G    R     B    G    R
#        Blue   110   50   85   131  119  255
#        Red    162   83  104   180  148  204
#        Green    0    0   86   112   29  156
#        Yellow   0   91   90    42  137  138
#-----------------------------------------------------------------------------------------------------------------------------------------------------------
import time
import argparse
import cv2
import numpy as np
import py_websockets_bot

latest_camera_image = None

def camera_image_callback( image, image_time ):
    global latest_camera_image
    # Put image processing here...
    latest_camera_image = image

def nothing(*arg):
     pass

if __name__ == "__main__":

    #----------------------------------------------------------------------------------------------------- Set up a parser for command line arguments
    parser = argparse.ArgumentParser( "Gets images from the robot using callbacks and displays them" )
    parser.add_argument( "hostname", default="localhost", nargs='?', help="The ip address of the robot" )
    args = parser.parse_args()
    #----------------------------------------------------------------------------------------------------- Connect to the robot
    bot = py_websockets_bot.WebsocketsBot( "192.168.42.1" )
    #----------------------------------------------------------------------------------------------------- Start streaming images from the camera
    bot.start_streaming_camera_images( camera_image_callback )
    #----------------------------------------------------------------------------------------------------- Create trackbars to manipulate the low RGB values
    img_low = np.zeros((15,512,3), np.uint8)
    cv2.namedWindow('BGR_low')
    cv2.createTrackbar('R','BGR_low',85,255,nothing)
    cv2.createTrackbar('G','BGR_low',50,255,nothing)
    cv2.createTrackbar('B','BGR_low',110,255,nothing)
    cv2.imshow('BGR_low',img_low)
#----------------------------------------------------------------------------------------------------- Create trackbars to manipulate the low RGB values
#                                                                                                      Default is blue range, low: 50,50,110 high: 255,255,130 
    img_high = np.zeros((15,512,3), np.uint8)
    cv2.namedWindow('BGR_high')
    cv2.createTrackbar('R','BGR_high',255,255,nothing)
    cv2.createTrackbar('G','BGR_high',119,255,nothing)
    cv2.createTrackbar('B','BGR_high',131,255,nothing)
    cv2.imshow('BGR_high',img_high)
#-----------------------------------------------------------------------------------------------------
    while True:
        bot.update()
        if latest_camera_image != None:
#----------------------------------------------------------------------------------------------------- get current positions of four trackbars
            r_low = cv2.getTrackbarPos('R','BGR_low')
            g_low = cv2.getTrackbarPos('G','BGR_low')
            b_low = cv2.getTrackbarPos('B','BGR_low')
            r_high = cv2.getTrackbarPos('R','BGR_high')
            g_high = cv2.getTrackbarPos('G','BGR_high')
            b_high = cv2.getTrackbarPos('B','BGR_high')
            img_low[:] = [b_low,g_low,r_low]
            img_high[:] = [b_high,g_high,r_high]
            #cv2.imshow("Low/High", np.hstack([img_low, img_high]))
            cv2.imshow('BGR_low',img_low)
            cv2.imshow('BGR_high',img_high)
#----------------------------------------------------------------------------------------------------- 0 - Set color range to search for
            hsv = cv2.cvtColor(latest_camera_image, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([b_low,g_low,r_low])
            upper_blue = np.array([b_high,g_high,r_high])
#----------------------------------------------------------------------------------------------------- 1 - Mask only with trackbar values
            mask_image = cv2.inRange(hsv, lower_blue, upper_blue)
            cv2.imshow('BGR High', mask_image)
#----------------------------------------------------------------------------------------------------- 2 - Convert masked color to white. rest to black 
            result_image = cv2.bitwise_and(latest_camera_image,latest_camera_image, mask= mask_image)
            cv2.imshow('BGR Low', result_image)
            #cv2.imshow("Low/High", np.hstack([result_image, mask_image]))
            if cv2.waitKey( 1 ) & 0xFF == ord ('c'):
                break
    #----------------------------------------------------------------------------------------------------- Clean-up windows if needed  
    cv2.destroyAllWindows()
    bot.stop_streaming_camera_images ()
    #----------------------------------------------------------------------------------------------------- Disconnect from the robot
