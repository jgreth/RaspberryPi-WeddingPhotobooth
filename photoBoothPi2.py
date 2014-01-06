#!/usr/bin/env python

import datetime
from linkedList import *
from time import sleep
import subprocess
import shlex
from threading import Thread
import RPIO as GPIO
import os
import sys
import signal
import Image
 
fps = 1 # The number of frames to capture per second.
totalPictures = 4 # The total capture time.
pictureWidth = 640
pictureHeight = 480

pictureName= "photoBoothPic.jpg"
imageList = LinkedList()
photo = 0
img = Image.new("RGB",(int(1280),int(960)))


raspistillPID = "0"

GPIO_INPUT_PIN = 24
GPIO_FLASH_PIN = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_INPUT_PIN,GPIO.IN)
GPIO.setup(GPIO_FLASH_PIN,GPIO.OUT)

GPIO.output(GPIO_FLASH_PIN, False)


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
        global raspistillPID
        
        count = 0
        while True:
            if self.buttonPressed:
                print "Remember to Smile"
                newDirName = str(datetime.datetime.now()).replace(' ', '_').split('.')[0].replace(':', '-')
                os.mkdir(newDirName)
                subprocess.call(['chmod', '777', newDirName])
                sleep(3)
                while count != totalPictures:
                    print "Taking pictue " + str(count)
                    GPIO.output(GPIO_FLASH_PIN, True)

                    print "1"
                    subprocess.call(['kill', '-USR1' , raspistillPID])
                    sleep(0.25)
                    GPIO.output(GPIO_FLASH_PIN, False)

                    subprocess.call(['mv',pictureName, newDirName + "/pic-" + str(count) + ".jpg"])
                    sleep(fps)
                    count = count + 1
                print "Picture capture complete"

                monitorFolder(newDirName)
                makeCollage()

                #Reset
                self.buttonPressed = False
                count = 0

                
    def setButtonPressed(self, buttonInput):
        self.buttonPressed = buttonInput

def addPicture(fileName, location):
    global imageList
    imageList.add(fileName,location)
    print "Added " + fileName + " to " + location

def monitorFolder(source):
    fileExtList = [".jpg"];
    tempList = os.listdir(source)
    
    if len(tempList) % 4 == 0:
        for picture in tempList:
            if os.path.splitext(picture)[1] in fileExtList:
                fileName = os.path.join(source,picture)
                pindex = tempList.index(picture) + 1
                if pindex % 4 == 1:
                    location = "0,0"
                elif pindex % 4 == 2:
                    location = "640,0"
                elif pindex % 4 == 3:
                    location = "0,480"
                elif pindex % 4 == 0:
                    location = "640,480"
                addPicture(fileName,location)

def makeCollage():
    print "Creating collage"
    global imageList
    global photo
    global img
    
    destination = "/home/pi/MyProjects/raw"
    fileName = "/home/pi/MyProjects/img"
    current = imageList.selfHead()
    while not imageList.isEmpty() and current != None:
        pic = current.getData()
        img.paste(pic,(int(current.getLocation()[0]),int(current.getLocation()[1])))          
        if current.getPosition() % 4 == 0 :
            photo += 1
            img.save(fileName+ "/Photobooth "+ str(photo) + ".jpg")
        shutil.move(current.getFileName(), destination)
        current = current.getNext()
    imageList = LinkedList()
    print "Collage created"

def main():
    global raspistillPID
    raspiThread = RaspiThread()
    raspiThread.start()

    sleep(2)

    #Get raspistill process id
    proc1 = subprocess.Popen(shlex.split('ps t'),stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(shlex.split('grep raspistill'),stdin=proc1.stdout,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc1.stdout.close() # Allow proc1 to receive a SIGPIPE if proc2 exits.
    out,err=proc2.communicate()
    print out
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
    sys.exit()
