#!/usr/bin/env python

import wx
import os
import sys
from wx.lib.pubsub import Publisher
import threading
from time import sleep
import datetime
from linkedList import *
import subprocess
import shlex
from threading import Thread
import RPIO as GPIO
import signal
import Image
import shutil
import wx
import gc
from wx.lib.pubsub import Publisher
import urllib2 

import pdb

pictureDelay = 3 #Seconds between each picture
totalPictures = 4 # The total number of pictures that will be taken.
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

    def __init__(self):
        Thread.__init__(self)
        self.busy = False
        
        Publisher().subscribe(self.finished, "finished")

    def run(self): 
        print "GPIO is run from: " + threading.current_thread().name
        
        resetShutdownCounter = 0

        while True:
            inputValue = GPIO.input(GPIO_INPUT_PIN)
            if inputValue == True and (not self.busy):
                print "Button Pressed"
                self.beginPictureCapture()
            
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

    def finished(self, param):
       self.busy = False      
       
    def beginPictureCapture(self):
        #Play sound
        os.system("aplay ./res/smw_1-up.wav")
        Publisher().sendMessage("hideBeginningText", "Nothing")
        Publisher().sendMessage("reset", "Nothing")
        print "Remember to Smile"
        currentTime = datetime.datetime.now()
        self.newDirName = outputPath + str(currentTime).replace(' ', '_').split('.')[0].replace(':', '-')
        os.mkdir(self.newDirName)
        subprocess.call(['chmod', '777', self.newDirName])   
        Publisher().sendMessage("startCountdown", self.newDirName)

class RaspiThread(Thread):
    #This thread launches the camera feed
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        print "Running raspitstill from " + threading.current_thread().name
        raspiInitCommand = ['raspistill', '-o', pictureName, '-t', '0', '-s', '-w' , str(pictureWidth), "-h", str(pictureHeight), "-p", "85,118,800,600", '-v', "-q", "100", "-fp"] 
        #raspiInitCommand = ['raspistill', '-o', pictureName, '-t', '0', '-s', '-w' , str(pictureWidth), "-h", str(pictureHeight), "--fullpreview", '-v'] 
        subprocess.call(raspiInitCommand)

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
    global gpioThread
    gpioThread.beginPictureCapture()
    
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

def main(lock):
    global raspistillPID
    global gpioThread #Need for test script, to mimic button press
    
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

    gpioThread = GPIOThread()
    gpioThread.setDaemon(True)
    gpioThread.start()


class PhotoBoothApp(wx.App):
    def __init__(self):
        wx.App.__init__(self,0)

        self.mainFrame = MainWindow(None," ")
        self.mainFrame.Show(True)

    def MainLoop(self):

        eventLoop = wx.EventLoop()
        old = wx.EventLoop.GetActive()
        wx.EventLoop.SetActive(eventLoop)
        while True:
 
            while eventLoop.Pending():
                eventLoop.Dispatch()
                       
            if self.mainFrame.showCollage == True:
                print "Showing Collage"
                self.mainFrame.showCollageInner()
                self.mainFrame.showCollage = False
                print "Finished Showing Collage"
            elif self.mainFrame.panel.updatePicture == True:
                print "Updating picture"
                self.mainFrame.updatePicturesInPanel()
                self.mainFrame.panel.updatePicture = False
            elif self.mainFrame.panel.reset == True:
                self.mainFrame.panel.resetPanelInner()
            elif self.mainFrame.panel.updateCountdownImage == True:
                self.mainFrame.panel.updateCountdownInner()                
            else:    
                self.ProcessIdle()

class CollageFrame(wx.Frame):
    def __init__(self, collagePath):  
        print "Initializing CollageFrame"
        wx.Frame.__init__(self, None, -1, "Your Picture")

        cbmp = wx.Image(collagePath,wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.SetPosition(wx.Point(1000,0))
        self.SetSize( cbmp.GetSize() )
        wx.StaticBitmap(self,-1,cbmp,(0,0))
        print "CollageFrame initialized!"


class MainPanel(wx.Panel):

    takenPictureSizeWindowWidth = 300
    takenPictureSizeWindowHeight = 220
    takenPictureLeftOffset = 1560

    pictureTakenCounter = 0

    countdownImages = []
    countdownCounter = 0

    updatePicture = False
    updateCountdownImage = False
    picturePath = ""
    reset = False
    
    def __init__(self, parent):
        wx.Panel.__init__(self,parent=parent)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.frame = parent
        
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
        self.resetPanelInner()

        self.initCountdownTimerImage()

        wxBmp =  wx.Image("res/processing.jpg",wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.processingText = wx.StaticBitmap(self,-1, wxBmp,(85,850))
        self.processingText.Hide()
        
        wxBmp =  wx.Image("res/begin.jpg",wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.beginningText = wx.StaticBitmap(self,-1, wxBmp,(85,850))
        self.beginningText.Show()

        self.lock = threading.Lock()
        main(self.lock)
        
        Publisher().subscribe(self.playSound, "playSound")


    def resetPanelInner(self):
        
        wximg = wx.Image("res/blankPicture1.jpg",wx.BITMAP_TYPE_JPEG)
        wxbmp = wx.BitmapFromImage(wximg)
        self.picture1 = wx.StaticBitmap(self,-1,wxbmp,(self.takenPictureLeftOffset,60))

        wximg = wx.Image("res/blankPicture2.jpg",wx.BITMAP_TYPE_JPEG)
        wxbmp = wx.BitmapFromImage(wximg)
        self.picture2 = wx.StaticBitmap(self,-1,wxbmp,(self.takenPictureLeftOffset,305))

        wximg = wx.Image("res/blankPicture3.jpg",wx.BITMAP_TYPE_JPEG)
        wxbmp = wx.BitmapFromImage(wximg)
        self.picture3 = wx.StaticBitmap(self,-1,wxbmp,(self.takenPictureLeftOffset,550))

        wximg = wx.Image("res/blankPicture4.jpg",wx.BITMAP_TYPE_JPEG)
        wxbmp = wx.BitmapFromImage(wximg)
        self.picture4 = wx.StaticBitmap(self,-1,wxbmp,(self.takenPictureLeftOffset,795))

        self.reset = False

    def resetPanel(self, msg):
        self.reset = True

    def onEraseBackground(self, evt):
        loc = wx.Bitmap("res/photoboothappbackground.jpg")
        dc = wx.ClientDC(self)
        dc.DrawBitmap(loc, 0, 0)

    def updatePictureInner(self):
        print "Updating picture " + str(self.pictureTakenCounter) + " from " + threading.current_thread().name

        twximg = wx.Image(str(self.picturePath.data),wx.BITMAP_TYPE_JPEG)
        bmp = twximg.Rescale(self.takenPictureSizeWindowWidth, self.takenPictureSizeWindowHeight).ConvertToBitmap()

        if self.pictureTakenCounter == 1:
            self.picture1 = wx.StaticBitmap(self, -1, bmp, (self.takenPictureLeftOffset,60))
        elif self.pictureTakenCounter == 2:
            self.picture2 = wx.StaticBitmap(self,-1, bmp, (self.takenPictureLeftOffset,305))
        elif self.pictureTakenCounter == 3:
            self.picture3 = wx.StaticBitmap(self,-1, bmp,(self.takenPictureLeftOffset,550))
        elif self.pictureTakenCounter == 4:
            self.picture4 = wx.StaticBitmap(self,-1, bmp,(self.takenPictureLeftOffset,795))
            self.pictureTakenCounter = 0

        print "Completed updating picture"

    def updatePicture(self,picturePath):
        self.pictureTakenCounter += 1
        self.picturePath = picturePath
        self.updatePicture = True

    def initCountdownTimerImage(self):
        
        wximg = wx.Image("res/countdown3.jpg",wx.BITMAP_TYPE_JPEG)
        wxbmp = wx.BitmapFromImage(wximg)
        self.countdownImages.append(wxbmp)

        wximg = wx.Image("res/countdown2.jpg",wx.BITMAP_TYPE_JPEG)
        wxbmp = wx.BitmapFromImage(wximg)
        self.countdownImages.append(wxbmp)

        wximg = wx.Image("res/countdown1.jpg",wx.BITMAP_TYPE_JPEG)
        wxbmp = wx.BitmapFromImage(wximg)
        self.countdownImages.append(wxbmp)  
        
    def playSound(self, sound):
        sleep(.75)
        os.system("aplay " + sound)        

    def startCountdown(self, param):
        self.updateCountdownImage = True
        self.newDirName = param.data
        
    def updateCountdownInner(self):

        if self.countdownCounter < 3:
            if self.countdownCounter != 0:
                self.countdownImage.Hide()
            print "Updating countdown: " + str(self.countdownCounter)
            
            self.countdownImage = wx.StaticBitmap(self,-1, self.countdownImages[self.countdownCounter],(1025,100))
            self.countdownCounter += 1
            sleep(1)
            threading.Thread(target=self.playSound,args=["./res/beep-07.wav"]).start()
            
        else:
            self.countdownCounter = 0
            self.countdownImage.Hide()
            #Stop the countdown process
            self.updateCountdownImage = False 
            threading.Thread(target=self.takePicture).start()
            
    def takePicture(self):
        
        sleep(1.5)
        #Turn on flash
        GPIO.output(GPIO_FLASH_PIN, False)
                    
        #Play photo sound
        os.system("aplay ./res/camera-shutter-click-01.wav")
                    
        #Take picture
        subprocess.call(['kill', '-USR1' , raspistillPID])
        #sleep(0.25)

        outputPictureName = self.newDirName + "/pic-" + str(self.pictureTakenCounter) + ".jpg"
        shutil.copy(pictureName, outputPictureName)

        sleep(.5)

        #Turn off flash
        GPIO.output(GPIO_FLASH_PIN, True)

        #Send message to GUI thread
        print "Publishing message to update picture from " + threading.current_thread().name
        Publisher().sendMessage("update", outputPictureName)
            
        if self.pictureTakenCounter == 4:
            #Stop the countdown process
            self.updateCountdownImage = False 
                
            print "Picture capture complete"
            Publisher().sendMessage("showProcessingText", "Nothing")
            monitorFolder(self.newDirName)
            makeCollage()
            Publisher().sendMessage("hideProcessingText", "Nothing")  
            Publisher().sendMessage("showBeginningText", "Nothing")  
        else:
            #Start the countdown process
            self.updateCountdownImage = True     

    def showProcessingText(self, param):
        print "Showing processing message..."
        self.processingText.Show()


    def hideProcessingText(self, param):
        print "Showing processing message..."
        self.processingText.Hide()
        
    def showBeginningText(self, param):
        print "Showing beginning message..."
        self.beginningText.Show()


    def hideBeginningText(self, param):
        print "Showing beginning message..."
        self.beginningText.Hide()        
        
class MainWindow(wx.Frame):

    showCollage = True
    
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, size=(wx.DisplaySize()), pos=(0,0), title="Photo Booth")
        self.panel = MainPanel(self)
        
        print wx.DisplaySize()

        self.countdownFont = wx.Font(500, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.countdown = wx.StaticText(self.panel, label="3", pos=(1025,0), size=(500,500))
        self.countdown.SetFont(self.countdownFont)

        self.ShowFullScreen(True)

        Publisher().subscribe(self.showCollage, "showCollage")
        Publisher().subscribe(self.panel.updatePicture, "update")
        Publisher().subscribe(self.panel.resetPanel, "reset")
        Publisher().subscribe(self.panel.startCountdown, "startCountdown")
        Publisher().subscribe(self.panel.showProcessingText, "showProcessingText")
        Publisher().subscribe(self.panel.hideProcessingText, "hideProcessingText")
        Publisher().subscribe(self.panel.showBeginningText, "showBeginningText")
        Publisher().subscribe(self.panel.hideBeginningText, "hideBeginningText")

        print "MainWindow thread: " + threading.current_thread().name

    def showCollageInner(self):
        print "Showing collage from GUI"
        collageWindow = CollageFrame(self.collagePath)
        collageWindow.Show()

        #Show picture for 15 seconds and close down
        wx.FutureCall(15000, collageWindow.Destroy)
        print "Collage Displayed!"

    def showCollage(self, collagePath):
        self.collagePath = collagePath.data
        self.showCollage = True
        print self.collagePath

    def updatePicturesInPanel(self):
        self.panel.updatePictureInner();

    def resetPanel(self):
        self.panel.resetPanel()

    def getReset(self):
        return self.panel.reset

def startGUI():
    global mainFrame
    app = PhotoBoothApp()

    app.MainLoop()

if __name__ == "__main__":
    try:
        startGUI()
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print message
        sys.exit()
