# import the necessary packages
import numpy as np
import cv2
 
def order_points(pts):
	# initialzie a list of coordinates that will be ordered
	# such that the first entry in the list is the top-left,
	# the second entry is the top-right, the third is the
	# bottom-right, and the fourth is the bottom-left
	rect = np.zeros((4, 2), dtype = "float32")
 
	# the top-left point will have the smallest sum, whereas
	# the bottom-right point will have the largest sum
	s = pts.sum(axis = 1)
	rect[0] = pts[np.argmin(s)]
	rect[2] = pts[np.argmax(s)]
 
	# now, compute the difference between the points, the
	# top-right point will have the smallest difference,
	# whereas the bottom-left will have the largest difference
	diff = np.diff(pts, axis = 1)
	rect[1] = pts[np.argmin(diff)]
	rect[3] = pts[np.argmax(diff)]
 
	# return the ordered coordinates
	return rect

def four_point_transform(image, pts):
	# obtain a consistent order of the points and unpack them
	# individually
	rect = order_points(pts)
	(tl, tr, br, bl) = rect
 
	# compute the width of the new image, which will be the
	# maximum distance between bottom-right and bottom-left
	# x-coordiates or the top-right and top-left x-coordinates
	widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[0] - bl[0]) ** 2))
	widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[0] - tl[0]) ** 2))
	maxWidth = max(int(widthA), int(widthB))
 
	# compute the height of the new image, which will be the
	# maximum distance between the top-right and bottom-right
	# y-coordinates or the top-left and bottom-left y-coordinates
	heightA = np.sqrt(((tr[1] - br[1]) ** 2) + ((tr[1] - br[1]) ** 2))
	heightB = np.sqrt(((tl[1] - bl[1]) ** 2) + ((tl[1] - bl[1]) ** 2))
	maxHeight = max(int(heightA), int(heightB))
 
	# now that we have the dimensions of the new image, construct
	# the set of destination points to obtain a "birds eye view",
	# (i.e. top-down view) of the image, again specifying points
	# in the top-left, top-right, bottom-right, and bottom-left
	# order
	dst = np.array([
		[0, 0],
		[maxWidth - 1, 0],
		[maxWidth - 1, maxHeight - 1],
		[0, maxHeight - 1]], dtype = "float32")
 
	# compute the perspective transform matrix and then apply it
	M = cv2.getPerspectiveTransform(rect, dst)
	warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
 
	# return the warped image
	return warped

def translate(image, x, y): 
 	# define the translation matrix and perform the translation 
 	M = np.float32([[1, 0, x], [0, 1, y]]) 
 	shifted = cv2.warpAffine(image, M, (image.shape[1], image.shape[0])) 
 
 
 	# return the translated image 
 	return shifted 

def rotate(image, angle, center=None, scale=1.0): 
 	# grab the dimensions of the image 
 	(h, w) = image.shape[:2] 
 	# if the center is None, initialize it as the center of 
 	# the image 
 	if center is None: 
 		center = (w / 2, h / 2) 
 	# perform the rotation 
 	M = cv2.getRotationMatrix2D(center, angle, scale) 
 	rotated = cv2.warpAffine(image, M, (w, h)) 
 	# return the rotated image 
 	return rotated 
 
def resize(image, width=None, height=None, inter=cv2.INTER_AREA): 
	# initialize the dimensions of the image to be resized and 
 	# grab the image size 
 	dim = None 
 	(h, w) = image.shape[:2] 
 	# if both the width and height are None, then return the 
 	# original image 
 	if width is None and height is None: 
 		return image 
 	# check to see if the width is None 
 	if width is None: 
 		# calculate the ratio of the height and construct the 
 		# dimensions 
 		r = height / float(h) 
 		dim = (int(w * r), height) 
  	# otherwise, the height is None 
 	else: 
 		# calculate the ratio of the width and construct the 
 		# dimensions 
 		r = width / float(w) 
 		dim = (width, int(h * r)) 
 	# resize the image 
 	resized = cv2.resize(image, dim, interpolation=inter) 
 	# return the resized image 
 	return resized 

def skeletonize(image, size, structuring=cv2.MORPH_RECT): 
 	# determine the area (i.e. total number of pixels in the image), 
 	# initialize the output skeletonized image, and construct the 
 	# morphological structuring element 
 	area = image.shape[0] * image.shape[1] 
 	skeleton = np.zeros(image.shape, dtype="uint8") 
 	elem = cv2.getStructuringElement(structuring, size) 
	# keep looping until the erosions remove all pixels from the 
 	# image 
 	while True: 
 		# erode and dilate the image using the structuring element 
 		eroded = cv2.erode(image, elem) 
 		temp = cv2.dilate(eroded, elem) 
 		# subtract the temporary image from the original, eroded 
 		# image, then take the bitwise 'or' between the skeleton 
 		# and the temporary image 
 		temp = cv2.subtract(image, temp) 
 		skeleton = cv2.bitwise_or(skeleton, temp) 
 		image = eroded.copy() 
 		# if there are no more 'white' pixels in the image, then 
 		# break from the loop 
 		if area == area - cv2.countNonZero(image): 
 			break 
 	# return the skeletonized image 
 	return skeleton 

def opencv2matplotlib(image): 
 	# OpenCV represents images in BGR order; however, Matplotlib 
 	# expects the image in RGB order, so simply convert from BGR 
 	# to RGB and return 
 	return cv2.cvtColor(image, cv2.COLOR_BGR2RGB) 
