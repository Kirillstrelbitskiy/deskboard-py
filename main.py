from pyvirtualcam import PixelFormat
from PyQt5.QtWidgets import QMessageBox, QApplication, QLabel, QWidget, QPushButton, QVBoxLayout, QApplication, QGridLayout, QHBoxLayout, QMessageBox, QSlider, QComboBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QThread, QTimer, Qt
from imutils.perspective import four_point_transform
from cv2 import cv2
import numpy as np
import argparse, imutils, time, helpers
import pyvirtualcam


# helpers.initializeTrackbars()

# cap = cv2.VideoCapture(0)
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
            
            self.streamActivated = False
            self.webCamFeed = False

            # cameras activation
            self.findCameras()
            if len(self.cameras) > 0:
                self.cap = cv2.VideoCapture(self.cameras[0])
                self.webCamFeed = True

            layout = QGridLayout()
            layout.setSpacing(10)
            
            listCamerasLayout = QHBoxLayout()
            listCameras = QComboBox()
            listCameras.addItems(map(str, self.cameras))
            listCameras.activated[int].connect(self.changeCamera)

            labelCameras = QLabel()
            labelCameras.setText("Select camera from the list:")

            listCamerasLayout.addWidget(labelCameras)
            listCamerasLayout.addWidget(listCameras)
            layout.addLayout(listCamerasLayout, 0, 0)

            # video previewes
            self.videoOrig = QLabel()
            self.videoOrig.setFixedSize(widthImgSmall, heightImgSmall)
            self.videoLines = QLabel()
            self.videoLines.setFixedSize(widthImgSmall, heightImgSmall)
            self.videoWraped = QLabel()
            self.videoWraped.setFixedSize(widthImgSmall, heightImgSmall)
            
            layout.addWidget(self.videoOrig, 0, 1)
            layout.addWidget(self.videoLines, 1, 1)
            layout.addWidget(self.videoWraped, 2, 1)

            # sliders seetings
            sliders_layout = QVBoxLayout()
            self.val1_sl = QSlider(Qt.Horizontal)
            self.val1_sl.setMinimum(0)
            self.val1_sl.setMaximum(300)
            self.val1_sl.setValue(60)
            self.val1_sl.setTickPosition(QSlider.TicksBelow)
            self.val1_sl.setTickInterval(2)

            sliders_layout.addWidget(self.val1_sl)

            self.val2_sl = QSlider(Qt.Horizontal)
            self.val2_sl.setMinimum(0)
            self.val2_sl.setMaximum(300)
            self.val2_sl.setValue(0)
            self.val2_sl.setTickPosition(QSlider.TicksBelow)
            self.val2_sl.setTickInterval(2)

            sliders_layout.addWidget(self.val2_sl)

            layout.addLayout(sliders_layout, 1, 0)

            # stream activation
            btnActivate = QPushButton("Start stream")
            btnActivate.clicked.connect(self.activateStream)
            layout.addWidget(btnActivate, 2, 0)

            self.setLayout(layout)
            self.setWindowTitle("First GUI with QT")
            # self.setFixedSize(widthImg, heightImg)

            self.timer.start(1000. / 24)  
    
    def changeCamera(self, camera):
        if self.cap.isOpened():
            self.cap.release()
        self.cap = cv2.VideoCapture(camera)

    def findCameras(self):
        num = 100
        self.cameras = []
        for index in range(num):
            device = cv2.VideoCapture(index)
            if device.isOpened():
                self.cameras.append(index)
            device.release()

        print(self.cameras)

    def activateStream(self):
        self.streamActivated = True
        self.cam = pyvirtualcam.Camera(widthImg, heightImg, 20, fmt=PixelFormat.BGR)

    def nextFrameSlot(self):
        global prev_exist
        global prev_screenCnt

        if self.webCamFeed:
            success, image = self.cap.read()
            image = cv2.resize(image, (widthImg, heightImg))
            image_original = image

            img_orig_rsz = cv2.resize(image_original, (widthImgSmall, heightImgSmall))
            imgLines = QImage(img_orig_rsz, img_orig_rsz.shape[1], img_orig_rsz.shape[0], QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(imgLines)
            self.videoOrig.setPixmap(pixmap)

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 1)

            # val = helpers.valTrackbars()
            val = [self.val1_sl.value(), self.val2_sl.value()]
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
                # cv2.drawContours(image, [prev_screenCnt], -1, (0, 255, 0), 1)
                # cv2.imshow("Outline", image)

                warped = four_point_transform(image_original, prev_screenCnt.reshape(4, 2))
                warped = warped[borders_width:warped.shape[0] - borders_width, borders_width:warped.shape[1] - borders_width]
                

                # colors magic
                # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)W
                # T = threshold_local(warped, 11, offset = 10, method = "gaussian")
                # warped = (warped > T).astype("uint8") * 255

                # cv2.imshow("OO", image_original)
                # cv2.imshow("Warped", warped)
                
                warped = cv2.resize(warped, (widthImg, heightImg))
                
                if self.streamActivated:
                    self.cam.send(warped)
                    self.cam.sleep_until_next_frame()

                warped = cv2.resize(warped, (widthImgSmall, heightImgSmall))

                img = QImage(warped, warped.shape[1], warped.shape[0], QImage.Format_RGB888).rgbSwapped()
                pixmap = QPixmap.fromImage(img)
                self.videoWraped.setPixmap(pixmap)

            

app = QApplication([])
start_window = UI_Window()
start_window.show()
app.exit(app.exec_())