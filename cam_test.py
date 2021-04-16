from cv2 import cv2
import numpy as np
 
webCamFeed = True
pathImage = "1.jpg"
cap = cv2.VideoCapture(0)
cap.set(10,160)
heightImg = 720
widthImg  = 1280
 
count=0
use_prev = False

while True:
    if webCamFeed:success, img = cap.read()
    else:img = cv2.imread(pathImage)
    
    img = cv2.resize(img, (widthImg, heightImg))
    
    cv2.imshow("Image", img)
    cv2.waitKey(1)