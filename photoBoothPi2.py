#!/usr/bin/env python
'''
Usage:
python timed_capture.py
'''
import datetime
from time import sleep
import subprocess
import shlex
from threading import Thread
import RPIO as GPIO
import os
import sys
import signal
 
fps = 1 # The number of frames to capture per second.
totalPictures = 4 # The total capture time.
pictureWidth = 640
pictureHeight = 480

pictureName= "photoBoothPic.jpg"

raspistillPID = "0"

GPIO_INPUT_PIN = 24
GPIO_FLASH_PIN = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_INPUT_PIN,GPIO.IN)
GPIO.setup(GPIO_FLASH_PIN,GPIO.OUT)

GPIO.output(GPIO_FLASH_PIN, False)

def sigint_handler(signum, frame):
    print "Control C detected, exiting"
    sys.exit()
 
signal.signal(signal.SIGINT, sigint_handler)

class RaspiThread(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        raspiInitCommand = ['raspistill', '-o', pictureName, '-t', '0', '-s', '-w' , str(pictureWidth), "-h", str(pictureHeight), "-p", "0,0,640,480", '-v']
        subprocess.call(raspiInitCommand)

class CaptureThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.buttonPressed = False
        
    def run(self):
        
        count = 0
        while True:
            if self.buttonPressed:
                print "Remember to Smile"
                newDirName = str(datetime.datetime.now()).replace(' ', '_')
                os.mkdir(newDirName)
                sleep(3)
                while count != totalPictures:
                    print "Taking pictue " + str(count)
                    GPIO.output(GPIO_FLASH_PIN, True)
                    subprocess.call(['kill', '-USR1' , raspistillPID])
                    sleep(0.25)
                    GPIO.output(GPIO_FLASH_PIN, False)

                    subprocess.call(['mv',pictureName, newDirName + "/pic-" + str(count) + ".jpg"])
                    sleep(fps)
                    count = count + 1
                print "Picture capture complete"

                #Reset
                self.buttonPressed = False
                count = 0

                
    def setButtonPressed(self, buttonInput):
        print "Setting buttonPressed to " + str(buttonInput)
        self.buttonPressed = buttonInput

def main():
    raspiThread = RaspiThread()
    raspiThread.start()

    sleep(2)

    #Get raspistill process id
    proc1 = subprocess.Popen(shlex.split('ps t'),stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(shlex.split('grep raspistill'),stdin=proc1.stdout,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc1.stdout.close() # Allow proc1 to receive a SIGPIPE if proc2 exits.
    out,err=proc2.communicate()
    raspistillPID = out.split(" ")[1]
    proc2.stdout.close()

    print "raspistill pid = " + raspistillPID

    captureThread = CaptureThread()
    captureThread.start()


    print "Ready to capture images"

    while True:
        inputValue = GPIO.input(GPIO_INPUT_PIN)
        if inputValue== True:
            print "Button Pressed"
            captureThread.setButtonPressed(inputValue)

        sleep(0.25)
try:
    main()
except KeyboardInterrupt:
    print "Exception caught"
    
