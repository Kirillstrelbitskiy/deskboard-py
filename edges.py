# import the necessary packages
from pyimagesearch import four_point_transform
# from skimage.filters import threshold_local
import numpy as np
import argparse
from cv2 import cv2
import imutils
import time
import helpers

helpers.initializeTrackbars()

webCamFeed = True
pathImage = "img.jpg"
cap = cv2.VideoCapture(42)
heightImg = 720
widthImg  = 1280
# helpers.set_res(cap, widthImg, heightImg)

count = 1

count=0
use_prev = False

while True:
    if webCamFeed:success, image = cap.read()
    else: image = cv2.imread(pathImage)
    image = cv2.resize(image, (widthImg, heightImg))

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 1)

    # val = helpers.valTrackbars()
    val = [60, 0]
    edged = cv2.Canny(gray, val[0], val[1])

    cv2.imshow("Image", image)
    cv2.imshow("Edged", edged)

    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)

    area, square = helpers.biggestContour(cnts)
    
    if(square > 0):
        cv2.drawContours(image, [area], -1, (0, 255, 0), 2)
        cv2.imshow("Outline", image)
    
    if cv2.waitKey(1) and 0xFF == ord('s'):
        count += 1