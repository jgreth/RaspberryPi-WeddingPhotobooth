#!/usr/bin/env python

#TODO:
#   1- Resize the window displaying the collage
#   2- Create a window that show some dialow of what is happening
#   3- Add sound to the countdown
#   4- Upload picture to google album


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
import shutil
import wx
 
fps = 1 # The number of frames to capture per second.
totalPictures = 4 # The total capture time.
pictureWidth = 640
pictureHeight = 480

reducedHeight = 430
reducedWidth = 322
collageReducedPictureSize = reducedHeight, reducedWidth

pictureName= "photoBoothPic.jpg"
imageList = LinkedList()
photo = 0
#img = Image.new("RGB",(int(1280),int(960)))
#img = Image.new("RGB",(int(1400),int(1200)))
#img = Image.new("RGB",(int(640),int(480)))
img = Image.open("img/photoboothlayout.jpg")

currenTime = datetime.datetime.now()


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
        raspiInitCommand = ['raspistill', '-o', pictureName, '-t', '0', '-s', '-w' , str(pictureWidth), "-h", str(pictureHeight), "-p", "0,100,640,480", '-v']
        subprocess.call(raspiInitCommand)

class CaptureThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.buttonPressed = False
        
    def run(self):
        global raspistillPID
        global currentTime
        
        count = 0
        while True:
            if self.buttonPressed:
                print "Remember to Smile"
                currentTime = datetime.datetime.now()
                newDirName = str(currentTime).replace(' ', '_').split('.')[0].replace(':', '-')
                os.mkdir(newDirName)
                subprocess.call(['chmod', '777', newDirName])
                sleep(3)
                while count != totalPictures:
                    print "Taking pictue " + str(count)

                    #Turn on flash
                    GPIO.output(GPIO_FLASH_PIN, True)

                    subprocess.call(['kill', '-USR1' , raspistillPID])
                    sleep(0.25)

                    #Turn off flash
                    GPIO.output(GPIO_FLASH_PIN, False)

                    sleep(1)

                    outputPictureName = newDirName + "/pic-" + str(count) + ".jpg"
                    subprocess.call(['mv',pictureName, outputPictureName])
                    
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
    
    fileExtList = [".jpg"];
    tempList = os.listdir(source)

    print tempList
    print len(tempList) % 4

    topBorderOffset = "139"
    leftBorderOffset = "73"
    
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
                    location = str(reducedWidth + 200) + "," + topBorderOffset
                elif pindex % 4 == 3:
                    print "Pic % 3 " + picture
                    location = str(reducedWidth + 200) + "," + str(reducedHeight + 37)
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
    
    destination = "/home/pi/MyProjects/raw"
    fileName = "/home/pi/MyProjects/img"
    current = imageList.selfHead()
    collageName = ""
    while not imageList.isEmpty() and current != None:
        pic = current.getData()
        img.paste(pic,(int(current.getLocation()[0]),int(current.getLocation()[1])))          
        if current.getPosition() % 4 == 0 :
            photo += 1
            collageName = fileName+ "/Photobooth_"+ currentTime.strftime("%H_%M_%S") + ".jpg"
            img.save(collageName)
        shutil.move(current.getFileName(), destination)
        current = current.getNext()
    imageList = LinkedList()
    showCollage(collageName)
    print "Collage created"

def showCollage(filepath):
    a = wx.PySimpleApp()
    print filepath 
    wximg = wx.Image(filepath,wx.BITMAP_TYPE_JPEG)
    wxbmp = wximg.ConvertToBitmap()
    f = wx.Frame(None, -1, "Your Picture")
    f.SetPosition(wx.Point(640,0))
    #f.SetSize( wxbmp.GetSize() )
    #f.SetSize( wx.Size(726,768) )
    f.SetSize( wx.Size(1224,984) )
    wx.StaticBitmap(f,-1,wxbmp,(0,0))
    f.Show(True)

    #Show picture for 5 seconds and close down
    wx.FutureCall(5000, f.Destroy)
    a.MainLoop()

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

if __name__ == "__main__":      
    try:
        main()
    except KeyboardInterrupt:
        print "Exception caught"
        sys.exit()
