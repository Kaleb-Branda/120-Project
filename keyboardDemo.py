#!/usr/bin/env python
 
from threading import Thread
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
import copy
import pyautogui
 
class serialPlot:
    def __init__(self, serialPort='COM6', serialBaud=38400, plotLength=100, dataNumBytes=2, numPlots=1, threshold=300):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.numPlots = numPlots
        self.rawData = bytearray(numPlots * dataNumBytes)
        self.dataType = None
        if dataNumBytes == 2:
            self.dataType = 'h'     # 2 byte integer
        elif dataNumBytes == 4:
            self.dataType = 'f'     # 4 byte float
        self.high = []
        self.data = []
        self.privateData = None     # for storing a copy of the data so all plots are synchronized
        for i in range(numPlots):   # give an array for each type of data and store them in a list
            self.data.append(collections.deque([0] * plotLength, maxlen=plotLength))
            self.high.append(False)
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.thread1 = None
        self.plotTimer = 0
        self.previousTimer = 0
        self.threshold = threshold


        # Filter variables
        self.EMA_S = [0,0]
        self.EMA_a = 0.3
 
        print('Trying to connect to: ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
        try:
            self.serialConnection = serial.Serial(serialPort, serialBaud, timeout=4)
            print('Connected to ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
        except:
            print("Failed to connect with " + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
 
    def readSerialStart(self):
        if self.thread1 == None:
            self.thread1 = Thread(target=self.keyboardThread)
            self.thread1.start()
        if self.thread == None:
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            # Block till we start receiving values
            while self.isReceiving != True:
                time.sleep(0.1)
 
    def getSerialData(self, frame, lines, lineValueText, lineLabel, timeText, pltNumber):
        if pltNumber == 0:  # in order to make all the clocks show the same reading
            currentTimer = time.clock()
            self.plotTimer = int((currentTimer - self.previousTimer) * 1000)     # the first reading will be erroneous
            self.previousTimer = currentTimer
            self.privateData = copy.deepcopy(self.rawData)    # so that the 3 values in our plots will be synchronized to the same sample time
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
        data = self.privateData[(pltNumber*self.dataNumBytes):(self.dataNumBytes + pltNumber*self.dataNumBytes)]
        value,  = struct.unpack(self.dataType, data)

        ### Filters go here
        self.EMA_S[pltNumber] = (self.EMA_a * value) + ((1-self.EMA_a) * self.EMA_S[pltNumber])
        value_filtered = value - self.EMA_S[pltNumber]

        #value_filtered = value

        if value_filtered > self.threshold:
            self.high[pltNumber] = True
        self.data[pltNumber].append(value_filtered)    # we get the latest data point and append it to our array
        lines.set_data(range(self.plotMaxLength), self.data[pltNumber])
        lineValueText.set_text('[' + lineLabel + '] = ' + str(value_filtered))
 
    def shouldClick(self):
        for i in range(self.numPlots):
            if not self.high[i]:
                return False
        return True

    def shouldRight(self):
        return self.high[1] and not self.high[0] 

    def shouldDown(self):
        return self.high[0] and not self.high[1]

    def tick(self):
        for i in range(self.numPlots):
            self.high[i] = False

    def backgroundThread(self):    # retrieve data
        time.sleep(1.0)  # give some buffer time for retrieving data
        self.serialConnection.reset_input_buffer()
        while (self.isRun):
            self.serialConnection.readinto(self.rawData)
            self.isReceiving = True

    def keyboardThread(self):
        try:
            x_key, y_key, h_key, w_key = pyautogui.locateOnScreen('keyboard.png')
        except:
            print('Could not locate keyboard button. Exiting...')
            self.close()
            quit()
        pyautogui.click(x_key + h_key/2, y_key + w_key/2)
        
        try:
            x0, y0, h, w = pyautogui.locateOnScreen('q.png')
        except:
            try:
                x0, y0, h, w = pyautogui.locateOnScreen('Q_cap.png')
            except:
                print('Could not locate keyboard. Exiting...')
                self.close()
                quit()
        x0 = x0 + w//2;
        y0 = y0 + h//2;

        # Establish Keyboard mappings in pixel offsets from Q
        locations = [[(i * 105, 95 * 0) for i in range(11)], 
            [(i * 105 + 35, 95 * 1) for i in range(11)], 
            [(i * 105, 95 * 2) for i in range(12)], 
            [(105, 290), (575, 290), (960, 290), (1085, 290)]]

        x = 0 # current column in above array
        y = 0 # current row in above array

        pyautogui.moveTo(x0, y0, duration=0.5)

        try:
            while self.isRun:
                time.sleep(0.5)
                while self.isReceiving and self.isRun:
                    self.tick()
                    time.sleep(0.2)
                    if self.shouldClick():
                        pyautogui.click()
                        time.sleep(0.2)
                        continue
                    if self.shouldRight():
                        if x < (len(locations[y]) - 1):
                            x = x + 1
                        else:
                            x = 0
                        try:
                            new_location = locations[y][x]
                        except:
                            print('1: y=' + str(y) + '; x=' + str(x))
                        pyautogui.moveTo(x0 + new_location[0], y0 + new_location[1], duration=0.3)
                        time.sleep(0.2)
                        continue
                    if self.shouldDown():
                        if y < (len(locations) - 1):
                            y = y + 1
                        else:
                            y = 0
                            x = 0
                        if x >= len(locations[y]):
                            x = len(locations[y]) - 1
                        try:
                            new_location = locations[y][x]
                        except:
                            print('2: y=' + str(y) + '; x=' + str(x))
                        pyautogui.moveTo(x0 + new_location[0], y0 + new_location[1], duration=0.3)
                        time.sleep(0.2)

                    
        except KeyboardInterrupt:
            self.close()
            print('Done.\n')
 
    def close(self):
        self.isRun = False
        self.thread.join()
        self.serialConnection.close()
        print('Disconnected...')
 
 
def makeFigure(xLimit, yLimit, title):
    xmin, xmax = xLimit
    ymin, ymax = yLimit
    fig = plt.figure()
    ax = plt.axes(xlim=(xmin, xmax), ylim=(int(ymin - (ymax - ymin) / 10), int(ymax + (ymax - ymin) / 10)))
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("EMG Output")
    return fig, ax
 
 
def main():
    portName = 'COM3'
    # portName = '/dev/ttyUSB0'
    baudRate = 9600
    maxPlotLength = 100     # number of points in x-axis of real time plot
    dataNumBytes = 2        # number of bytes of 1 data point
    numPlots = 2           # number of plots in 1 graph
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes, numPlots, threshold=200)   # initializes all required variables
    s.readSerialStart()                                               # starts background thread
 
    # plotting starts below
    pltInterval = 50    # Period at which the plot animation updates [ms]
    lineLabelText = ['Signal 1', 'Signal 2']
    title = ['Left Hand Signal', 'Right Hand Signal']
    xLimit = [(0, maxPlotLength), (0, maxPlotLength)]
    yLimit = [(0, 1050), (0, 1050)]
    style = ['r-', 'b-']    # linestyles for the different plots
    anim = []
    for i in range(numPlots):
        fig, ax = makeFigure(xLimit[i], yLimit[i], title[i])
        lines = ax.plot([], [], style[i], label=lineLabelText[i])[0]
        timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
        lineValueText = ax.text(0.50, 0.90, '', transform=ax.transAxes)
        anim.append(animation.FuncAnimation(fig, s.getSerialData, fargs=(lines, lineValueText, lineLabelText[i], timeText, i), interval=pltInterval))  # fargs has to be a tuple
        plt.legend(loc="upper left")
    plt.show()
 
    s.close()
 
 
if __name__ == '__main__':
    main()