#! /usr/bin/python

# Routine with 2 methods of comparing images 
# Both seem to be equaly fast enough for use in robot control scripts
#
# Output: MSE: 0.0 8799.6  10124.9  19609.9  19609.9  19568.8  16205.0  0.0   0.016 sec
#         BWC:   0 53966   24103,   53911    24103    28310    26171    0     0.016 sec

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

def bwc(imageA, imageB):
    cv2.bitwise_xor(imageA,imageB,output,mask=None)
    diff=cv2.countNonZero(output)
    #cv2.imshow('output',output)                                         # uncomment to watch output images one by one
    #cv2.waitKey(0)
    return diff

def mse(imageA, imageB):                                                 # Mean Squared Error = differance in pixelintensity 
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2) # NOTE: the two images must have the same dimension
    err /= float(imageA.shape[0] * imageA.shape[1])
    return err

if __name__ == "__main__":

    signright = cv2.imread('signright.jpg',0)
    if signright != None:
        cv2.imshow( "SR", signright )
        cv2.waitKey(1)
    signleft = cv2.imread('signleft.jpg',0)
    if signleft != None:
        cv2.imshow( "SL", signleft )
        cv2.waitKey(1)
    signturn = cv2.imread('signturn.jpg',0)
    if signturn != None:
        cv2.imshow( "ST", signturn )
        cv2.waitKey(1)
    signstop = cv2.imread('signstop.jpg',0)
    if signstop != None:
        cv2.imshow( "SS", signstop )
        cv2.waitKey(1)
    #--------------------------------------------------------------------- comparing by MSE
    time_start = time.time()
    v_1 = mse(signright, signright)
    v_2 = mse(signright, signleft)
    v_3 = mse(signright, signturn)
    v_4 = mse(signright, signstop)
    v_5 = mse(signstop, signright)
    v_6 = mse(signstop, signleft)
    v_7 = mse(signstop, signturn)
    v_8 = mse(signstop, signstop)
    time_stop = time.time()
    print round((v_1),1)
    print round((v_2),1)
    print round((v_3),1)
    print round((v_4),1)
    print round((v_5),1)
    print round((v_6),1)
    print round((v_7),1)
    print round((v_8),1)
    print round((time_stop - time_start),3), 'sec'
    #-------------------------------------------------------------------- comparing by bitwise
    output=signright
    time_start = time.time()
    v_1 = bwc(signright, signright)
    v_2 = bwc(signright, signleft)
    v_3 = bwc(signright, signturn)
    v_4 = bwc(signright, signstop)
    v_5 = bwc(signstop, signright)
    v_6 = bwc(signstop, signleft)
    v_7 = bwc(signstop, signturn)
    v_8 = bwc(signstop, signstop)
    time_stop = time.time()
    print v_1
    print v_2
    print v_3
    print v_4
    print v_5
    print v_6
    print v_7
    print v_8
    print round((time_stop - time_start),5), 'sec'
