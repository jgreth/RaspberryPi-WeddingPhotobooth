#!/usr/bin/env python

#TODO:
#   4- Upload picture to google album
#   Have the script create the output folder

import datetime
from linkedList import *
from time import sleep
import subprocess
import shlex
from threading import Thread
import threading #TODO Remove
import RPIO as GPIO
import os
import sys
import signal
import Image
import shutil
import wx
import gc
from wx.lib.pubsub import Publisher
import urllib2 
import shutil

pictureDelay = 3 #Seconds between each picture
totalPictures = 4 # The total number of pictures that will be taken.
#pictureWidth = 640
#pictureHeight = 480
pictureWidth = 2592
pictureHeight = 1944

reducedHeight = 430
reducedWidth = 322
collageReducedPictureSize = reducedHeight, reducedWidth

pictureName= "photoBoothPic.jpg"
imageList = LinkedList()
photo = 0
img = Image.open("./res/photoboothlayout.jpg")

outputPath = "/media/KINGSTON/"

currentTime = datetime.datetime.now()

raspistillPID = "0"


#GPIO Setup
GPIO_RESET_PIN = 18
GPIO_INPUT_PIN = 24
GPIO_FLASH_PIN = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_RESET_PIN,GPIO.IN)
GPIO.setup(GPIO_INPUT_PIN,GPIO.IN)
GPIO.setup(GPIO_FLASH_PIN,GPIO.OUT)

GPIO.output(GPIO_FLASH_PIN, True)

#Configure sound TODO may want to move this to be set at login in the user profile type file
os.system("sudo amixer cset numid=3 2")

class GPIOThread(Thread):
    #This thread is in charge of handling the button presses to trigger
    #the capturing of the pictures, reset button and eventually control the flash also.

    def __init__(self, captureThread):
        Thread.__init__(self)
        self.captureThread = captureThread

    def run(self): 
        print "GPIO is run from: " + threading.current_thread().name
        
        resetShutdownCounter = 0

        while True:
            inputValue = GPIO.input(GPIO_INPUT_PIN)
            if inputValue== True:
                print "Button Pressed"
                #Play sound
                os.system("aplay ./res/smw_1-up.wav")
                self.captureThread.setButtonPressed(inputValue)
            
            resetShutdownValue = GPIO.input(GPIO_RESET_PIN)
            if resetShutdownValue == True:
                resetShutdownCounter += 1
            elif resetShutdownValue == False and resetShutdownCounter != 0:          
                if resetShutdownCounter >= 10:
                    print "Shutdown Button Pressed! Shutting down system now....."
                    os.system("sudo shutdown -h now")   
                elif resetShutdownCounter > 1:
                    print "Reset Button Pressed! Rebooting system now....."
                    os.system("sudo reboot")  
                
                resetShutdownCounter = 0 
                
            sleep(0.25)

class RaspiThread(Thread):
    #This thread launches the camera feed
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        print "Running raspitstill from " + threading.current_thread().name
        raspiInitCommand = ['raspistill', '-o', pictureName, '-t', '0', '-s', '-w' , str(pictureWidth), "-h", str(pictureHeight), "-p", "85,118,800,600", '-v', "-q", "100", "-fp"] 
        #raspiInitCommand = ['raspistill', '-o', pictureName, '-t', '0', '-s', '-w' , str(pictureWidth), "-h", str(pictureHeight), "--fullpreview", '-v'] 
        subprocess.call(raspiInitCommand)

class CaptureThread(Thread):
    #This thread is in charge of sending the signal to the camera to capture the 4 images 
    def __init__(self):
        Thread.__init__(self)
        self.buttonPressed = False
        
    def run(self):
        global raspistillPID
        global currentTime

        print "Capture thread name is: " + threading.current_thread().name
        
        count = 0
        while True:
            if self.buttonPressed:
                Publisher().sendMessage("hideBeginningText", "Nothing")
                Publisher().sendMessage("reset", "Nothing")
                print "Remember to Smile"
                currentTime = datetime.datetime.now()
                newDirName = outputPath + str(currentTime).replace(' ', '_').split('.')[0].replace(':', '-')
                os.mkdir(newDirName)
                subprocess.call(['chmod', '777', newDirName])
                sleep(3)
                while count != totalPictures:
                    print "Taking picture " + str(count)
                    Publisher().sendMessage("startCountdown", str(count))
                    sleep(.2)
                    for i in range(0, pictureDelay):                        
                        #Do the Beep and update the GUI
                        os.system("aplay ./res/beep-07.wav")
                        sleep(1.2)

                    #Turn on flash
                    GPIO.output(GPIO_FLASH_PIN, False)
                    
                    #Play photo sound
                    os.system("aplay ./res/camera-shutter-click-01.wav")
                    
                    #Take picture
                    subprocess.call(['kill', '-USR1' , raspistillPID])
                    #sleep(0.25)

                    outputPictureName = newDirName + "/pic-" + str(count) + ".jpg"
                    subprocess.call(['cp',pictureName, outputPictureName])
                    #shutil.copy(pictureName, outputPictureName)

                    count = count + 1

                    sleep(1)

                    #Turn off flash
                    GPIO.output(GPIO_FLASH_PIN, True)

                    #Send message to GUI thread
                    print "Publishing message to update picture from " + threading.current_thread().name
                    Publisher().sendMessage("update", outputPictureName)

                    sleep(4)

                    #gc.collect()
                    
                print "Picture capture complete"
                Publisher().sendMessage("showProcessingText", "Nothing")
                monitorFolder(newDirName)
                makeCollage()
                Publisher().sendMessage("hideProcessingText", "Nothing")
                Publisher().sendMessage("showBeginningText", "Nothing")

                #Reset for next picture
                self.buttonPressed = False
                count = 0

                
    def setButtonPressed(self, buttonInput):
        self.buttonPressed = buttonInput

def playSound(filePath):
    os.system("aplay " + filePath)

def addPicture(fileName, location):
    global imageList
    resizePicture(fileName)
    imageList.add(fileName + "_collage",location)
    print "Added " + fileName + " to " + location

def resizePicture(imagePath):
    global collageReducedPictureSize
    
    image = Image.open(imagePath)
    image.thumbnail(collageReducedPictureSize, Image.ANTIALIAS)
    image.save(imagePath + "_collage", "JPEG")

def monitorFolder(source):
    global reducedHeight
    global reducedWidth

    print "MonitorFolder is run from: " + threading.current_thread().name
    
    fileExtList = [".jpg"];
    tempList = os.listdir(source)

    print tempList
    print len(tempList) % 4

    topBorderOffset = "139"
    leftBorderOffset = "60" #"73"
    
    if len(tempList) % 4 == 0:
        for picture in tempList:
            if os.path.splitext(picture)[1] in fileExtList:
                fileName = os.path.join(source,picture)
                pindex = tempList.index(picture) + 1
                if pindex % 4 == 1:
                    print "Pic % 1 " + picture
                    location = leftBorderOffset + "," + topBorderOffset
                elif pindex % 4 == 2:
                    print "Pic % 2 " + picture
                    location = str(reducedWidth + 213) + "," + topBorderOffset
                elif pindex % 4 == 3:
                    print "Pic % 3 " + picture
                    location = str(reducedWidth + 213) + "," + str(reducedHeight + 37)
                elif pindex % 4 == 0:
                    print "Pic % 0 " + picture
                    location = leftBorderOffset + "," + str(reducedHeight + 37)
                addPicture(fileName,location)

def makeCollage():
    print "Creating collage"
    global imageList
    global photo
    global img
    global currentTime
    
    destination = "./raw"
    fileName = outputPath + "/photoBoothOutput"
    current = imageList.selfHead()
    collageName = ""
    tempName = ""
    while not imageList.isEmpty() and current != None:
        pic = current.getData()
        img.paste(pic,(int(current.getLocation()[0]),int(current.getLocation()[1])))          
        if current.getPosition() % 4 == 0 :
            photo += 1
            tempName = "Photobooth_"+ currentTime.strftime("%H_%M_%S") + ".jpg"
            collageName = fileName+ "/" + tempName
            img.save(collageName)
        shutil.move(current.getFileName(), destination)
        current = current.getNext()
    imageList = LinkedList()

    #Send message to GUI thread
    print "Calling showCollage from: " + threading.current_thread().name
    Publisher().sendMessage("showCollage", collageName)
    print "Collage created"
    
    if checkInternetConnection():
        print "Uploading to DropBox: " + collageName + " to: " + tempName
        dropboxThread = threading.Thread(target=sendToDropbox, args=[collageName, tempName])
        dropboxThread.start()

def mimicButtonPress():
    global captureThread
    captureThread.buttonPressed = True;
    
def checkInternetConnection():
    try:
        response=urllib2.urlopen('http://74.125.228.100',timeout=1)
        print "Connected to internet."
        return True
    except urllib2.URLError as err: pass
    print "Not connected to internet."
    return False  

def sendToDropbox(fullFilePath, fileName):
    command = "/home/pi/Photobooth/Dropbox-Uploader/dropbox_uploader.sh upload " + fullFilePath + " " + fileName
    print "Uploading to Dropbox: " + command 
    subprocess.call([command], shell=True)

def main():
    global raspistillPID
    global captureThread
    
    raspiThread = RaspiThread()
    raspiThread.setDaemon(True)
    raspiThread.start()


    sleep(2)

    #Get raspistill process id, needed to tell camera to capture picture
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
    captureThread.setDaemon(True)
    captureThread.start()

    gpioThread = GPIOThread(captureThread)
    gpioThread.setDaemon(True)
    gpioThread.start()
