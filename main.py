from pyvirtualcam import PixelFormat
from PyQt5.QtWidgets import QMessageBox, QApplication, QLabel, QWidget, QPushButton, QVBoxLayout, QApplication, QGridLayout, QHBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QThread, QTimer
from imutils.perspective import four_point_transform
from cv2 import cv2
import numpy as np
import argparse, imutils, time, helpers
import pyvirtualcam


# helpers.initializeTrackbars()

webCamFeed = True
cap = cv2.VideoCapture(0)
heightImg = 1080
widthImg  = 1920

heightImgSmall = 360
widthImgSmall = 640
# helpers.set_res(cap, widthImg, heightImg)

min_diff = 3
borders_width = 5

count = 1
prev_exist = False
prev_screenCnt = [[[]]]

class UI_Window(QWidget):
    def __init__(self, camera = None):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)

        layout = QGridLayout()
        layout.setSpacing(10)

        button_layout = QHBoxLayout()

        btnCamera = QPushButton("Open camera")
        # btnCamera.clicked.connect(self.start)
        button_layout.addWidget(btnCamera)
        layout.addLayout(button_layout, 0, 0)

        self.videoOrig = QLabel()
        self.videoOrig.setFixedSize(widthImgSmall, heightImgSmall)
        self.videoLines = QLabel()
        self.videoLines.setFixedSize(widthImgSmall, heightImgSmall)
        self.videoWraped = QLabel()
        self.videoWraped.setFixedSize(widthImgSmall, heightImgSmall)
        
        layout.addWidget(self.videoOrig, 0, 1)
        layout.addWidget(self.videoLines, 1, 1)
        layout.addWidget(self.videoWraped, 2, 1)

        self.setLayout(layout)
        self.setWindowTitle("First GUI with QT")
        self.setFixedSize(widthImg, heightImg)

        self.timer.start(1000. / 24)

    # def start(self):
        
     
    def nextFrameSlot(self):
        global prev_exist
        global prev_screenCnt

        if webCamFeed:success, image = cap.read()
        image = cv2.resize(image, (widthImg, heightImg))
        image_original = image

        img_orig_rsz = cv2.resize(image_original, (widthImgSmall, heightImgSmall))
        imgLines = QImage(img_orig_rsz, img_orig_rsz.shape[1], img_orig_rsz.shape[0], QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(imgLines)
        self.videoOrig.setPixmap(pixmap)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 1)

        # val = helpers.valTrackbars()
        val = [60, 0]
        edged = cv2.Canny(gray, val[0], val[1])

        edged_rsz = cv2.resize(edged, (widthImgSmall, heightImgSmall))
        imgLines = QImage(edged_rsz, edged_rsz.shape[1], edged_rsz.shape[0], QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(imgLines)
        self.videoLines.setPixmap(pixmap)

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
            # cv2.imshow("Outline", image)

            warped = four_point_transform(image_original, prev_screenCnt.reshape(4, 2))
            warped = warped[borders_width:warped.shape[0] - borders_width, borders_width:warped.shape[1] - borders_width]
            
            warped = cv2.resize(warped, (widthImgSmall, heightImgSmall))

            # colors magic
            # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
            # T = threshold_local(warped, 11, offset = 10, method = "gaussian")
            # warped = (warped > T).astype("uint8") * 255

            # cv2.imshow("OO", image_original)
            # cv2.imshow("Warped", warped)

            # cam.send(warped)
            # cam.sleep_until_next_frame()

        # rval, frame = camera.vc.read()
        # frame = cv2.csvtColor(frame, cv2.COLOR_BGR2RGB)

            img = QImage(warped, warped.shape[1], warped.shape[0], QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(img)
            self.videoWraped.setPixmap(pixmap)

            

app = QApplication([])
start_window = UI_Window()
start_window.show()
app.exit(app.exec_())