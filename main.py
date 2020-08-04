from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np
import sys
import time
import serial

import detectYesNo
import read_file

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=0.1)
ser.flush()
def receive_from_mega(ser):
    if ser.in_waiting > 0:
        cmd = ser.readline().decode('utf-8').rstrip()
        print(cmd)
        return cmd


class Thread(QThread):
    img = pyqtSignal(np.ndarray)
    data = pyqtSignal(np.ndarray)
    statistic = pyqtSignal(str)
    
    def run(self):
        # Camera Pi config
        self.camera = PiCamera()
        self.camera.rotation = 180
        self.camera.resolution = (2592, 1944)   # resolution
        self.camera.iso = 800				    # set ISO to the desired value
        self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
        
        global ser

        # time to get camera warm up
        time.sleep(0.5)
        while True:           
            cmd = receive_from_mega(ser)
            # cmd = "9"
            if cmd == "9":
                cam = np.zeros(84)
                for _ in range(3):
                    self.camera.capture(self.rawCapture, format="bgr")
                    image = self.rawCapture.array
                    resize_img = cv2.resize(image, (972,729))

                    cam += detectYesNo.runDetectImage(resize_img)
                    time.sleep(0.25)
                    self.rawCapture.truncate(0)
                    if _ == 2:
                        # send image
                        self.img.emit(resize_img)
                    
                cam = np.rint(cam/3)
                cam = np.array(cam, dtype=int)
                # data_cam = str(cam)[1:-1].replace(", ", '').replace(' ', '').replace('\n','')
                # print(data_cam)
                
                # send data of Camera
                # ser.write(data_cam.encode('utf-8'))
                self.data.emit(cam)

                
            elif cmd == "1":
                self.statistic.emit("1")
                print('1')
            elif cmd == "0":
                self.statistic.emit("0") 
                print('0')
            
            time.sleep(5)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = "MCNEX"
        self.left = 0; self.top = 0
        self.width = 1920; self.height = 1080 # full HD screen
        
        self.number_total = 0
        self.number_success = 0
        self.number_error = 0
        
        self.date, self.time = read_file.get_date_time()
        read_file.save_current_time(self.date, self.time)

        self.count = 0

        global ser

        self.initUI()
    
    def initUI(self):
        # Config main window
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setStyleSheet("background-color: rgb(171, 171, 171);")
        
        # Logo
        self.mcnex_logo = QLabel(self)
        self.mcnex_pixmap = QPixmap('logo/mcnex.png').scaled(273,130,Qt.KeepAspectRatio)
        self.mcnex_logo.setPixmap(self.mcnex_pixmap)
        self.mcnex_logo.setGeometry(120, 20, 273, 130)
        self.uet_logo = QLabel(self)
        self.uet_pixmap = QPixmap('logo/uet.png').scaled(128,130,Qt.KeepAspectRatio)
        self.uet_logo.setPixmap(self.uet_pixmap)
        self.uet_logo.setGeometry(440, 20, 128, 130)

        # Show current time
        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setGeometry(1090, 30, 430, 120)
        font_timer = QFont('', 60, QFont.Bold)
        self.time_label.setFont(font_timer)
        timer = QTimer(self)
        timer.timeout.connect(self.updateTimer)
        timer.start(1000)
        self.time_label.setStyleSheet("color: rgb(255, 255, 255);")

        # Camera area
        self.cam_name = QLabel("CAMERA", self)
        self.cam_name.setGeometry(46, 199, 648, 55)
        self.cam_name.setAlignment(Qt.AlignCenter)
        self.cam_name.setStyleSheet("background-color: rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")
        self.cam = QLabel(self)
        self.cam.setGeometry(46, 254, 648, 486)
        self.th = Thread(self)
        self.th.img.connect(self.update_image)
        self.th.data.connect(self.update_data)
        self.th.statistic.connect(self.update_statistic)
        # self.th.start()
        self.cam.setStyleSheet("border-color: rgb(50, 130, 184);"
                                "border-width: 5px;"
                                "border-style: inset;")

        # Start button
        self.start_button = QPushButton("START",self)
        self.start_button.setGeometry(1223, 780, 180, 100)
        self.start_button.clicked.connect(self.clickStartButton)
        self.start_button.setStyleSheet("background-color: rgb(67, 138, 94);"
                                        "font: bold 20px;"
                                        "color:rgb(255, 255, 255);"
                                        "border-width: 5px;"
                                        "border-color: rgb(67, 138, 94);"
                                        "border-radius: 5px;")

        # Stop button
        self.stop_button = QPushButton("STOP",self)
        self.stop_button.setGeometry(1483, 780, 180, 100)
        self.stop_button.clicked.connect(self.clickStopButton)
        self.stop_button.setStyleSheet("background-color: rgb(232, 80, 91);"
                                        "font: bold 20px;"
                                        "color:rgb(255, 255, 255);"
                                        "border-width: 5px;"
                                        "border-color: rgb(232, 80, 91);"
                                        "border-radius: 5px;")

        # Home button
        self.home_button = QPushButton("HOME",self)
        self.home_button.setGeometry(1483, 920, 180, 100)
        self.home_button.clicked.connect(self.clickHomeButton)
        self.home_button.setStyleSheet("background-color: rgb(50, 130, 184);"
                                        "font: bold 20px;"
                                        "color:rgb(255, 255, 255);"
                                        "border-width: 5px;"
                                        "border-color: rgb(50, 130, 184);"
                                        "border-radius: 5px;")

        # Calibrate button
        self.calibrate_button = QPushButton("CALIBRATE",self)
        self.calibrate_button.setGeometry(1223, 920, 180, 100)
        self.calibrate_button.clicked.connect(self.clickAlignButton)
        self.calibrate_button.setStyleSheet("background-color: rgb(249, 210, 118);"
                                            "font: bold 20px;"
                                            "color:rgb(255, 255, 255);"
                                            "border-width: 5px;"
                                            "border-color: rgb(249, 210, 118);"
                                            "border-radius: 5px;")

        # Set font
        self.font = QFont()
        self.font.setPointSize(14)
        self.font.setBold(True)

        # Table area
        self.table_area = QLabel(self)
        self.table_area.setGeometry(740, 199, 1130, 541)
        self.table_area.setStyleSheet("background-color: rgb(196, 196, 196);"
                                    "border-color: rgb(50, 130, 184);"
                                    "border-width: 5px;"
                                    "border-style: inset;")
        self.table_name = QLabel("INFORMATION", self)
        self.table_name.setGeometry(740, 199, 1130, 55)
        self.table_name.setAlignment(Qt.AlignCenter)
        self.table_name.setStyleSheet("background-color:rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")

        # Trays information
        self.tray = []
        for i in range(4):
            tray_name = QLabel("TRAY{}".format(i+1), self)
            tray_name.setGeometry(773+275*i, 303, 242, 55)
            tray_name.setAlignment(Qt.AlignCenter)
            tray_name.setStyleSheet("background-color:rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")
            table = QTableWidget(7,3,self)
            table.setGeometry(773+275*i,358,242,352)
            table.horizontalHeader().hide()
            table.verticalHeader().hide()
            for j in range(3):
                table.setColumnWidth(j,80)
            for j in range(7):
                table.setRowHeight(j,50)
            table.setFont(self.font)
            table.setStyleSheet("color: rgb(255, 255, 255);")
            self.tray.append(table)

        # Statistics table
        self.statistic_table = QTableWidget(2,3,self)
        self.statistic_table.setGeometry(46, 780, 648, 170)
        self.statistic_table.horizontalHeader().hide()
        self.statistic_table.verticalHeader().hide()
        self.statistic_table.setFont(self.font)
        self.statistic_table.setStyleSheet("color: rgb(255, 255, 255);"
                                            "text-align: center;"
                                            "border-width: 5px;"
                                            "border-style: inset;"
                                            "border-color: rgb(50, 130, 184);")
        for j in range(3):
            self.statistic_table.setColumnWidth(j,212)
        for j in range(2):
            self.statistic_table.setRowHeight(j,80)
        total_item = QTableWidgetItem("TOTAL")
        total_item.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,0,total_item)
        success_item = QTableWidgetItem("SUCCESS")
        success_item.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,1,success_item)
        error_item = QTableWidgetItem("ERROR")
        error_item.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,2,error_item)

        self.show()

    @pyqtSlot(np.ndarray)
    def update_image(self, img):
        rgbImage = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        p = convertToQtFormat.scaled(648, 486, Qt.KeepAspectRatio)
        self.cam.setPixmap(QPixmap.fromImage(p))
    
    def update_statistic(self, data):
        self.number_total += 1
        while(self.data_cam != "1"):
            self.count += 1
            
        tray_idx = self.count % 21
        row = 6 - self.count % 21 % 7
        col = self.count % 21 // 7
        if(data == "1"):
            self.number_success += 1
            self.statistic_table.setItem(1,1,QTableWidgetItem(self.number_error))
            self.tray[tray_idx].setItem(row, col, QTableWidgetItem("OK"))
        else:
            self.number_error += 1
            self.statistic_table.setItem(1,2,QTableWidgetItem(self.number_error))
            self.tray[tray_idx].setItem(row, col, QTableWidgetItem("NG"))
        if self.count == 84:
            self.date, self.time = read_file.get_date_time()
            read_file.save_current_time(self.date, self.time)
            self.number_total = 0; self.number_success = 0; self.number_error = 0
            self.count = 0

    def update_data(self, data):
        # Update data to table
        c = 0
        for k in range(4):
            for j in range(3):
                for i in range(6,-1,-1):
                    self.tray[k].setItem(i,j,QTableWidgetItem())
                    if(int(data[c])):
                        self.tray[k].item(i,j).setBackground(QColor(0,208,0))
                    else:
                        self.tray[k].item(i,j).setBackground(QColor(250,30,50))
                    c += 1
        # Update current data
        data[:self.count] = 0
        data_cam = str(data)[1:-1].replace(", ", '').replace(' ', '').replace('\n','')
        self.cam_data = data
        ser.write(data_cam.encode('utf-8'))

    def updateTimer(self):
        cr_time = QTime.currentTime()
        time = cr_time.toString('hh:mm AP')
        self.time_label.setText(time)

    def clickStartButton(self):
        print("START")
        self.th.start()
        ser.write("a".encode('utf-8'))
        self.number_total, self.number_success, self.number_error = read_file.get_data_from_file(self.date, self.time)
        ser.write(self.count.encode('utf-8'))

    def clickStopButton(self):
        print("STOP")
        self.th.quit()
        ser.write("o".encode('utf-8'))
        read_file.write_data_to_file(self.date, self.time, (self.number_total, self.number_success, self.number_error))

    def clickHomeButton(self):
        print("HOME")
        ser.write("h".encode('utf-8'))

    # def reset(self):
    #     print("RESET")
    #     self.date, self.time = read_file.get_date_time()
    #     read_file.save_current_time(self.date, self.time)
    #     self.number_total = 0; self.number_success = 0; self.number_error = 0
    #     self.count = 0
    
    def clickAlignButton(self):
        print("CALIBRATE")
        self.alignWindow = AlignWindow()
        # self.alignWindow.__init__()
        self.alignWindow.show()

class AlignWindow(QWidget):
    def __init__(self):
        super(AlignWindow, self).__init__(None, Qt.WindowStaysOnTopHint)
        self.title = "CALIBRATION"
        self.left = 1000; self.top = 400
        self.width = 500; self.height = 500

        self.initUI()
    
    def initUI(self):
        # Config alignment window
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setStyleSheet("background-color: rgb(171, 171, 171);")

        # OK button
        self.up_button = QPushButton("⇧",self)
        self.up_button.setGeometry(190, 70, 120, 120)
        self.up_button.clicked.connect(self.clickUpButton)
        self.up_button.setStyleSheet("background-color: rgb(50, 130, 184);"
                                    "font: bold 50px;"
                                    "color:rgb(255, 255, 255);"
                                    "border-width: 5px;"
                                    "border-color: rgb(50, 130, 184);"
                                    "border-radius: 5px;")
        
        self.down_button = QPushButton("⇩",self)
        self.down_button.setGeometry(190, 310, 120, 120)
        self.down_button.clicked.connect(self.clickDownButton)
        self.down_button.setStyleSheet("background-color: rgb(50, 130, 184);"
                                    "font: bold 50px;"
                                    "color:rgb(255, 255, 255);"
                                    "border-width: 5px;"
                                    "border-color: rgb(50, 130, 184);"
                                    "border-radius: 5px;")
        
        self.left_button = QPushButton("⇦",self)
        self.left_button.setGeometry(70, 190, 120, 120)
        self.left_button.clicked.connect(self.clickLeftButton)
        self.left_button.setStyleSheet("background-color: rgb(50, 130, 184);"
                                    "font: bold 50px;"
                                    "color:rgb(255, 255, 255);"
                                    "border-width: 5px;"
                                    "border-color: rgb(50, 130, 184);"
                                    "border-radius: 5px;")
        
        self.right_button = QPushButton("⇨",self)
        self.right_button.setGeometry(310, 190, 120, 120)
        self.right_button.clicked.connect(self.clickRightButton)
        self.right_button.setStyleSheet("background-color: rgb(50, 130, 184);"
                                    "font: bold 50px;"
                                    "color:rgb(255, 255, 255);"
                                    "border-width: 5px;"
                                    "border-color: rgb(50, 130, 184);"
                                    "border-radius: 5px;")

        self.show()
    
    @pyqtSlot()

    def clickUpButton(self):
        print("UP")
    def clickDownButton(self):
        print("DOWN")
    def clickLeftButton(self):
        print("LEFT")
    def clickRightButton(self):
        print("RIGHT")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())