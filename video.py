from imutils.perspective import four_point_transform
from cv2 import cv2
import numpy as np
import argparse, imutils, time, helpers
import pyvirtualcam
from pyvirtualcam import PixelFormat

helpers.initializeTrackbars()

webCamFeed = True
cap = cv2.VideoCapture(0)
heightImg = 1080
widthImg  = 1920
# helpers.set_res(cap, widthImg, heightImg)

min_diff = 3
borders_width = 5

count = 1
prev_exist = False
prev_screenCnt = [[[]]]


with pyvirtualcam.Camera(widthImg, heightImg, 20, fmt=PixelFormat.BGR) as cam:
    print(f'Virtual cam started: {cam.device} ({cam.width}x{cam.height} @ {cam.fps}fps)')
    while True:
        if webCamFeed:success, image = cap.read()
        image = cv2.resize(image, (widthImg, heightImg))
        image_original = image

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 1)

        val = helpers.valTrackbars()
        # val = [60, 0]
        edged = cv2.Canny(gray, val[0], val[1])

        cv2.imshow("Image", image)
        cv2.imshow("Edged", edged)

        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key = cv2.contourArea, reverse = True)

        screenCnt, square = helpers.biggestContour(cnts)

        if square > 0:
            update = True

            if prev_exist:
                for i in range(len(screenCnt)):
                    for j in range(len(screenCnt[i][0])):
                        if(abs(screenCnt[i][0][j] - prev_screenCnt[i][0][j]) < min_diff):
                            update = False


            if update:
                prev_screenCnt = screenCnt
                prev_exist = True
            else:
                screenCnt = prev_screenCnt

        if prev_exist:
            cv2.drawContours(image, [prev_screenCnt], -1, (0, 255, 0), 1)
            cv2.imshow("Outline", image)

            warped = four_point_transform(image_original, prev_screenCnt.reshape(4, 2))
            warped = warped[borders_width:warped.shape[0] - borders_width, borders_width:warped.shape[1] - borders_width]
            
            warped = cv2.resize(warped, (widthImg, heightImg))

            # colors magic
            # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
            # T = threshold_local(warped, 11, offset = 10, method = "gaussian")
            # warped = (warped > T).astype("uint8") * 255

            cv2.imshow("OO", image_original)
            cv2.imshow("Warped", warped)

            cam.send(warped)
            cam.sleep_until_next_frame()

        if cv2.waitKey(1) and 0xFF == ord('s'):
            count += 1
