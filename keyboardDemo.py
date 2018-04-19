#!/usr/bin/env python
 
from threading import Thread
import serial
import time
import collections
import struct
import pyautogui
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class serialPlot:
    def __init__(self, serialPort='COM3', serialBaud=38400, dataNumBytes=2, windowLength=100, threshold=150, numPlots=1):
        self.port = serialPort
        self.baud = serialBaud
        self.dataNumBytes = dataNumBytes
        self.numPlots = numPlots
        self.rawData = bytearray(dataNumBytes)
        self.dataType = None
        self.threshold = threshold
        if dataNumBytes == 2:
            self.dataType = 'h'     # 2 byte integer
        elif dataNumBytes == 4:
            self.dataType = 'f'     # 4 byte float
        self.data = []
        for i in range(numPlots):
            self.data.append(collections.deque([0] * windowLength, maxlen=windowLength))
        self.isRun = True   
        self.isReceiving = False
        self.thread = None
        self.thread1 = None
        self.thread2 = None # plotting thread
        self.high = False
 
        print('Trying to connect to: ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
        try:
            self.serialConnection = serial.Serial(serialPort, serialBaud, timeout=4)
            print('Connected to ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
        except:
            print("Failed to connect with " + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
 
    def readSerialStart(self):
        if self.thread == None:
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            # Block till we start receiving values
            while self.isReceiving != True:
                time.sleep(0.1)
        if self.thread1 == None:
            self.thread1 = Thread(target=self.processSerialData)
            self.thread1.start()
        if self.thread2 == None:
            self.thread2 = Thread(target=self.plotThread)
            self.thread2.start()

    def shouldClick(self):
        return self.high

    def tick(self):
        self.high = False

    def processSerialData(self):
        time.sleep(1.0)
        pltNumber = 0
        try:
            while self.isRun:
                time.sleep(0.1)
                while self.isReceiving and self.isRun:
                    data_point = self.rawData[(pltNumber*self.dataNumBytes):(self.dataNumBytes * (pltNumber + 1))]
                    print(len(data_point))
                    value, = struct.unpack(self.dataType, data_point)
                    
                    #allow for plotting
                    self.data[pltNumber].append(value)
                    pltNumber = pltNumber + 1 if pltNumber < 2 else 0

                    if value > self.threshold:
                        self.high = True

                    #positionStr = str(value)
                    #print(positionStr, end='')
                    #print('\b' * len(positionStr), end='', flush=True)
        except KeyboardInterrupt:
            self.close()
            print('Done.\n')
            quit()

    def backgroundThread(self):    # retrieve data
        try:
            time.sleep(1.0)  # give some buffer time for retrieving data
            self.serialConnection.reset_input_buffer()
            while self.isRun:
                self.serialConnection.readinto(self.rawData)
                self.isReceiving = True
        except KeyboardInterrupt:
            self.close()
            print('Done.\n')
            quit()

    def makeFigure(self, xLimit, yLimit, title):
        xmin, xmax = xLimit
        ymin, ymax = yLimit
        fig = plt.figure()
        ax = plt.axes(xlim=(xmin, xmax), ylim=(int(ymin - (ymax - ymin) / 10), int(ymax + (ymax - ymin) / 10)))
        ax.set_title(title)
        ax.set_xlabel("Time")
        ax.set_ylabel("EMG Output")
        return fig, ax

    def plotThread(self):
        try:
            maxPlotLength = 100
            pltInterval = 50    # Period at which the plot animation updates [ms]
            lineLabelText = ['Signal 1', 'Signal 2']
            title = ['Right Hand Signal', 'Left Hand Signal']
            xLimit = [(0, maxPlotLength), (0, maxPlotLength)]
            yLimit = [(0, 500), (0, 500)]
            style = ['r-', 'b-']    # linestyles for the different plots
            anim = []
            
            for i in range(self.numPlots):
                fig, ax = self.makeFigure(xLimit[i], yLimit[i], title[i])
                #lines = ax.plot([], [], style[i], label=lineLabelText[i])[0]
                #timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
                #lineValueText = ax.text(0.50, 0.90, '', transform=ax.transAxes)
                anim.append(animation.FuncAnimation(fig, self.doNothing, frames=self.data[i], interval=pltInterval))
                #plt.legend(loc="upper left")
            plt.show()


        except KeyboardInterrupt:
            self.close()
            print('Done.\n')
            quit()

        self.close()
        print('Done.\n')
        quit()

    def doNothing(self):
        return

    def close(self):
        self.isRun = False
        self.thread.join()
        self.thread1.join()
        self.serialConnection.close()
        print('Disconnected...')

 
def cycle(x, y, s, back_x, back_y, x_increment = 105, count=10):
    pyautogui.moveTo(x, y, duration=0.5)
    s.tick()
    time.sleep(0.5)
    if s.shouldClick():
        pyautogui.click()
    for i in range(10):
        s.tick()
        pyautogui.moveRel(x_increment, 0, duration=0.25)
        time.sleep(0.5) # replace this with a while loop to keep checking
        if s.shouldClick():  # ToDo: Check if it's still over the right color
            pyautogui.click()
            time.sleep(1.0)

            x_temp, y_temp = pyautogui.position()
            s.tick()
            pyautogui.moveTo(back_x, back_y, duration=0.25)
            time.sleep(0.5)
            if s.shouldClick():
                pyautogui.click()
                time.sleep(1.0)
            pyautogui.moveTo(x_temp, y_temp)

 
def main(threshold = -215):
    portName = 'COM3'
    # portName = '/dev/ttyUSB0'
    baudRate = 9600
    windowLength = 20
    dataNumBytes = 2        # number of bytes of 1 data point
    s = serialPlot(portName, baudRate, dataNumBytes, windowLength, threshold, numPlots=2)   # initializes all required variables
    s.readSerialStart()     # starts background thread

    x_increment = 105
    y_increment = 95
    
    #pyautogui.click(1700, 1050)
    x_key, y_key, h_key, w_key = pyautogui.locateOnScreen('keyboard.png')
    if x_key == None:
        print('Could not locate keyboard button. Exiting...')
        s.close()
        quit()
    pyautogui.click(x_key + h_key/2, y_key + w_key/2)

    time.sleep(3.0)

    x0, y0, h, w = pyautogui.locateOnScreen('q.png')
    if x0 == None:
        x0, y0, h, w = pyautogui.locateOnScreen('Q_cap.png')
    if x0 == None:
        print('Could not locate keyboard. Exiting...')
        s.close()
        quit()


    try:
        while True:
            # first row
            x = x0 + h/2
            y = y0 + w/2
            cycle(x, y, s, x0 + 1115, y0)

            # second row
            x = x0 + h/2 + 45
            y = y0 + w/2 + y_increment
            cycle(x, y, s, x0 + 1115, y0)

            # third row
            x = x0 + h/2
            y = y0 + w/2 + 2 * y_increment
            cycle(x, y, s, x0 + 1115, y0)

            # fourth row
            x = x0 + h/2 + 5 * x_increment
            y = y0 + w/2 + 3 * y_increment
            s.tick()
            pyautogui.moveTo(x, y, duration=0.35)
            time.sleep(0.5)
            if s.shouldClick():
                pyautogui.click()
                time.sleep(0.1)

                s.tick()
                pyautogui.moveTo(x0 + 1115, y0, duration=0.25)
                time.sleep(0.5)
                if s.shouldClick():
                    pyautogui.click()
                    time.sleep(1.0)
    except KeyboardInterrupt:
        """Pass error through"""
    
    s.close()
    print('Done.\n')
        

if __name__ == '__main__':
    main()