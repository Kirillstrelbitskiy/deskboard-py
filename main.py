from pyvirtualcam import PixelFormat
from PyQt5.QtWidgets import QMessageBox, QApplication, QLabel, QWidget, QPushButton, QVBoxLayout, QApplication, QGridLayout, QHBoxLayout, QMessageBox, QSlider, QComboBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QThread, QTimer, Qt, QSize
from PyQt5.QtGui import QIcon
from imutils.perspective import four_point_transform
from cv2 import cv2
import numpy as np
import argparse, imutils, time, helpers
import pyvirtualcam

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
            
            self.angle = 0
            self.streamActivated = False
            self.webCamFeed = False
            self.cam = pyvirtualcam.Camera(widthImg, heightImg, 20, fmt=PixelFormat.BGR)

            # cameras activation
            self.findCameras()
            self.camerasNames = {}
            camerasList = []
            index = 1
            for c in self.cameras:
                self.camerasNames["Camera " + str(index)] = c
                camerasList.append("Camera " + str(index))
                index += 1

            if len(self.cameras) > 0:
                self.cap = cv2.VideoCapture(self.cameras[0])
                self.webCamFeed = True

            layout = QHBoxLayout()
            layout.setSpacing(10)
            
            layoutLeft = QVBoxLayout()
            layoutRight= QVBoxLayout()
            listCamerasLayout = QHBoxLayout()
            listCameras = QComboBox()
            listCameras.addItems(map(str, camerasList))
            listCameras.activated[str].connect(self.changeCamera)

            labelCameras = QLabel()
            labelCameras.setText("Select camera from the list:")

            listCamerasLayout.addWidget(labelCameras)
            listCamerasLayout.addWidget(listCameras)
            layoutLeft.addLayout(listCamerasLayout)

            # video previewes
            self.videoOrig = QLabel()
            self.videoOrig.setFixedSize(widthImgSmall, heightImgSmall)
            self.videoLines = QLabel()
            self.videoLines.setFixedSize(widthImgSmall, heightImgSmall)
            self.videoWraped = QLabel()
            self.videoWraped.setFixedSize(widthImgSmall, heightImgSmall)
            
            layoutRight.addWidget(self.videoOrig)
            layoutRight.addWidget(self.videoLines)
            layoutRight.addWidget(self.videoWraped)

            # sliders seetings
            labelSlider = QLabel("Find your optimal params")
            sliders_layout = QVBoxLayout()
            sliders_layout.addWidget(labelSlider)

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

            sliders_layout.setAlignment(Qt.AlignCenter)
            sliders_layout.addWidget(self.val2_sl)

            layoutLeft.addLayout(sliders_layout)

            # image corrections
            corrLayout = QVBoxLayout()
            labelCorr = QLabel("Flip the image")
            corrLayout.addWidget(labelCorr)

            coorLine = QHBoxLayout()
            rotateCounterClockwise = QPushButton()
            rotateCounterClockwise.setIcon(QIcon('icons/counter-clockwise.png'))
            rotateCounterClockwise.setIconSize(QSize(50, 50))  
            rotateCounterClockwise.resize(50, 50)
            rotateCounterClockwise.clicked.connect(self.changeAngle)

            coorLine.addWidget(rotateCounterClockwise)

            corrLayout.addLayout(coorLine)
            corrLayout.setAlignment(Qt.AlignVCenter)

            layoutLeft.addLayout(corrLayout)

            # stream activation
            layoutStream = QHBoxLayout()
            self.btnChangeState = QPushButton("Start stream")
            self.btnChangeState.clicked.connect(self.changeStream)
            self.labelStream = QLabel("You're offline")

            layoutStream.addWidget(self.labelStream)
            layoutStream.addWidget(self.btnChangeState)
            layoutLeft.addLayout(layoutStream)

            layout.addLayout(layoutLeft)
            layout.addLayout(layoutRight)
            self.setLayout(layout)
            self.setWindowTitle("DeskBoard")
            # self.setFixedSize(widthImg, heightImg)

            self.timer.start(1000. / 24)  
    
    def changeCamera(self, camera):
        cameraIndex = self.camerasNames[camera]
        if self.cap.isOpened():
            self.cap.release()
        self.cap = cv2.VideoCapture(cameraIndex)

    def findCameras(self):
        num = 100
        self.cameras = []
        for index in range(num):
            device = cv2.VideoCapture(index)
            if device.isOpened():
                self.cameras.append(index)
            device.release()

        print(self.cameras)
    
    def changeAngle(self):
        self.angle += 180

    def changeStream(self):
        if not self.streamActivated:
            self.streamActivated = True
            self.btnChangeState.setText("Stop stream")
            self.labelStream.setText("You're online")
        else:
            self.streamActivated = False
            self.btnChangeState.setText("Start stream")
            self.labelStream.setText("You're offline")
 
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
                # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
                # T = threshold_local(warped, 11, offset = 10, method = "gaussian")
                # warped = (warped > T).astype("uint8") * 255

                # cv2.imshow("OO", image_original)
                # cv2.imshow("Warped", warped)
                

                warped = cv2.resize(warped, (widthImg, heightImg))
                warped = helpers.rotateImage(warped, self.angle)

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