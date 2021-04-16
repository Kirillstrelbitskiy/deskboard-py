import cv2
from PyQt5.QtWidgets import QMessageBox, QApplication, QLabel, QWidget, QPushButton, QVBoxLayout, QApplication, QHBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QThread, QTimer

class Camera:
    def __init__(self, camera):
        self.camera = camera
        self.cap = None

    def openCamera(self):
        self.vc = cv2.VideoCapture(0)
        # vc.set(5, 30)  #set FPS
        self.vc.set(3, 640)  # set width
        self.vc.set(4, 480)  # set height

        if not self.vc.isOpened():
            print('failure')
            msgBox = QMessageBox()
            msgBox.setText("Failed to open camera.")
            msgBox.exec_()
            return

    def initialize(self):
        self.cap = cv2.VideoCapture(self.camera)


class UI_Window(QWidget):
    def __init__(self, camera = None):
        super().__init__()
        self.camera = camera

        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)

        layout = QVBoxLayout()

        button_layout = QHBoxLayout()

        btnCamera = QPushButton("Open camera")
        btnCamera.clicked.connect(self.start)
        button_layout.addWidget(btnCamera)
        layout.addLayout(button_layout)

        self.label = QLabel()
        self.label.setFixedSize(640, 640)

        layout.addWidget(self.label)

        self.setLayout(layout)
        self.setWindowTitle("First GUI with QT")
        self.setFixedSize(800, 800)

       

    def start(self):
        camera.openCamera()
        self.timer.start(1000. / 24)
     
    def nextFrameSlot(self):

        rval, frame = camera.vc.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)

class MovieThread(QThread):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera

    def run(self):
        self.camera.acquire_movie(200)



camera = Camera(0)
app = QApplication([])
start_window = UI_Window(camera)
start_window.show()
app.exit(app.exec_())