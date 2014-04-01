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
import resource


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
GPIO.cleanup() 
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
        resetShutdownCounter = 0

        while True:
            inputValue = GPIO.input(GPIO_INPUT_PIN)
            if inputValue == True and (not self.busy):
                print("Button Pressed")
                self.beginPictureCapture()
            
            resetShutdownValue = GPIO.input(GPIO_RESET_PIN)
            if resetShutdownValue == True:
                resetShutdownCounter += 1
            elif resetShutdownValue == False and resetShutdownCounter != 0:          
                if resetShutdownCounter >= 10:
                    print("Shutdown Button Pressed! Shutting down system now.....")
                    os.system("sudo shutdown -h now")   
                elif resetShutdownCounter > 1:
                    print("Reset Button Pressed! Rebooting system now.....")
                    os.system("sudo reboot")  
                
                resetShutdownCounter = 0 
                
            sleep(0.25)

    def finished(self, param):
       self.busy = False      
       
    def beginPictureCapture(self):
        
        print("beginPictureCapture - Start - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        
        #Play sound
        p = subprocess.Popen(["aplay", "./res/smw_1-up.wav"])
        p.kill()
        
        Publisher().sendMessage("hideBeginningText", "Nothing")
        Publisher().sendMessage("reset", "Nothing")
        print("Remember to Smile")
        currentTime = datetime.datetime.now()
        self.newDirName = outputPath + str(currentTime).replace(' ', '_').split('.')[0].replace(':', '-')
        os.mkdir(self.newDirName)
        subprocess.call(['chmod', '777', self.newDirName])   
        Publisher().sendMessage("startCountdown", self.newDirName)
        
        print("beginPictureCapture - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        

class RaspiThread(Thread):
    #This thread launches the camera feed
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        print("Running raspitstill from " + threading.current_thread().name)
        raspiInitCommand = ['raspistill', '-o', pictureName, '-t', '0', '-s', '-w' , str(pictureWidth), "-h", str(pictureHeight), "-p", "85,118,800,600", '-v', "-q", "100", "-fp"] 
        #raspiInitCommand = ['raspistill', '-o', pictureName, '-t', '0', '-s', '-w' , str(pictureWidth), "-h", str(pictureHeight), "--fullpreview", '-v'] 
        subprocess.call(raspiInitCommand)
        
def addPicture(fileName, location):
    global imageList
    resizePicture(fileName)
    imageList.add(fileName + "_collage",location)
    print("Added " + fileName + " to " + location)

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

    print(tempList)
    print(len(tempList) % 4)

    topBorderOffset = "139"
    leftBorderOffset = "60" #"73"
    
    if len(tempList) % 4 == 0:
        for picture in tempList:
            if os.path.splitext(picture)[1] in fileExtList:
                fileName = os.path.join(source,picture)
                pindex = tempList.index(picture) + 1
                if pindex % 4 == 1:
                    print("Pic % 1 " + picture)
                    location = leftBorderOffset + "," + topBorderOffset
                elif pindex % 4 == 2:
                    print("Pic % 2 " + picture)
                    location = str(reducedWidth + 213) + "," + topBorderOffset
                elif pindex % 4 == 3:
                    print("Pic % 3 " + picture)
                    location = str(reducedWidth + 213) + "," + str(reducedHeight + 37)
                elif pindex % 4 == 0:
                    print("Pic % 0 " + picture)
                    location = leftBorderOffset + "," + str(reducedHeight + 37)
                addPicture(fileName,location)

def makeCollage():
    
    print("makeCollage - Start - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    print("Creating collage")
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
    
    print("makeCollage - Before New List - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)   
    imageList = LinkedList() 
    print("makeCollage - After New List - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    #Send message to GUI thread
    print("Calling showCollage from: " + threading.current_thread().name)
    Publisher().sendMessage("showCollage", collageName)
    print("Collage created")
    
    if checkInternetConnection():
        print("Uploading to DropBox: " + collageName + " to: " + tempName)
        dropboxThread = threading.Thread(target=sendToDropbox, args=[collageName, tempName])
        dropboxThread.start()
          
    print("makeCollage - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)  

def mimicButtonPress():
    global gpioThread
    gpioThread.beginPictureCapture()
    
def checkInternetConnection():
    try:
        response=urllib2.urlopen('http://74.125.228.100',timeout=1)
        print("Connected to internet.")
        return True
    except urllib2.URLError as err: pass
    print("Not connected to internet.")
    return False  

def sendToDropbox(fullFilePath, fileName):
    print("sendToDropbox - Start -  Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) 
    command = "/home/pi/Photobooth/Dropbox-Uploader/dropbox_uploader.sh upload " + fullFilePath + " " + fileName
    print("Uploading to Dropbox: " + command)
    p = subprocess.Popen([command], shell=True)
    p.kill()
    print("sendToDropbox - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) 

def main():
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
    if out.split(" ")[1] != " ":
        raspistillPID = out.split(" ")[1]
    else:
        raspistillPID = out.split(" ")[0]    
    proc2.stdout.close()

    print("raspistill pid = " + raspistillPID)

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
                print("Showing Collage")
                self.mainFrame.showCollageInner()
                self.mainFrame.showCollage = False
                print("Finished Showing Collage")
            elif self.mainFrame.panel.reset == True:
                self.mainFrame.panel.resetPanelInner()
            elif self.mainFrame.panel.updateCountdownImage == True:
                self.mainFrame.panel.updateCountdownInner()                
            else:    
                self.ProcessIdle()  

class CollageFrame(wx.Frame):
    def __init__(self, collagePath):  
        print("Initializing CollageFrame")
        wx.Frame.__init__(self, None, -1, "Your Picture")

        self.cbmp = wx.Image(collagePath,wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.SetPosition(wx.Point(1000,0))
        self.SetSize(self.cbmp.GetSize())
        self.bmp = wx.StaticBitmap(self,-1, self.cbmp,(0,0))
        print("CollageFrame initialized!")
        
        self.cbmp.Destroy()


class MainPanel(wx.Panel):

    takenPictureSizeWindowWidth = 300
    takenPictureSizeWindowHeight = 220
    takenPictureLeftOffset = 1560
    
    mainPanelWxObjectCount = 0

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
        #self.resetPanelInner()

        self.initCountdownTimerImage()

        self.wxBmp =  wx.Image("res/processing.jpg",wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.processingText = wx.StaticBitmap(self,-1, self.wxBmp,(85,850))
        self.processingText.Hide()
        
        self.wxBmp.Destroy()
        
        self.wxBmp =  wx.Image("res/begin.jpg",wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.beginningText = wx.StaticBitmap(self,-1, self.wxBmp,(85,850))
        self.beginningText.Show()
        
        self.wxBmp.Destroy()
        
        self.picture1 = wx.StaticBitmap(self)
        self.picture2 = wx.StaticBitmap(self)
        self.picture3 = wx.StaticBitmap(self)
        self.picture4 = wx.StaticBitmap(self)
        
        self.countdownImage = wx.StaticBitmap(self)
        
        
        #Start of the main application
        main()
        
        Publisher().subscribe(self.playSound, "playSound")
        
        self.mainPanelWxObjectCount = len(self.GetChildren())
        print "Initial Panel Children Count: " + str(self.mainPanelWxObjectCount)


    def resetPanelInner(self):
        
        self.wximg = wx.Image("res/blankPicture1.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        
        if self.picture1 is not None:
            self.picture1.Destroy()
        
        self.picture1 = wx.StaticBitmap(self,-1,self.wxbmp,(self.takenPictureLeftOffset,60))
        self.wximg.Destroy()
        self.wxbmp.Destroy()

        self.wximg = wx.Image("res/blankPicture2.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        
        if self.picture2 is not None:
            self.picture2.Destroy()
            
        self.picture2 = wx.StaticBitmap(self,-1,self.wxbmp,(self.takenPictureLeftOffset,305))
        self.wximg.Destroy()
        self.wxbmp.Destroy()

        self.wximg = wx.Image("res/blankPicture3.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
                
        if self.picture3 is not None:
            self.picture3.Destroy()
        
        self.picture3 = wx.StaticBitmap(self,-1,self.wxbmp,(self.takenPictureLeftOffset,550))
        self.wximg.Destroy()
        self.wxbmp.Destroy()

        self.wximg = wx.Image("res/blankPicture4.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        
        if self.picture4 is not None:
            self.picture4.Destroy()
        
        self.picture4 = wx.StaticBitmap(self,-1,self.wxbmp,(self.takenPictureLeftOffset,795))
        self.wximg.Destroy()
        self.wxbmp.Destroy()

        self.reset = False

    def resetPanel(self, msg):
        self.reset = True

    def onEraseBackground(self, evt):
        loc = wx.Bitmap("res/photoboothappbackground.jpg")
        dc = wx.ClientDC(self)
        dc.DrawBitmap(loc, 0, 0)

    def updatePicturePanel(self, picturePath):
        self.pictureTakenCounter += 1
        
        print "Pictures taken " + str(self.pictureTakenCounter)
        self.picturePath = picturePath
        print ("updatePicturePanel - Start - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        print ("Child count: " +  str(len(self.GetChildren())))
        print("Updating picture " + str(self.pictureTakenCounter) + " from " + threading.current_thread().name)
        
        self.twximg = wx.Image(str(self.picturePath),wx.BITMAP_TYPE_JPEG)
        self.bmp = self.twximg.Rescale(self.takenPictureSizeWindowWidth, self.takenPictureSizeWindowHeight).ConvertToBitmap()

        #self.twximg.Destroy()
        
        if self.pictureTakenCounter == 1:
            if self.picture1 is not None:
                self.picture1.Destroy()
                
            self.picture1 = wx.StaticBitmap(self, -1, self.bmp, (self.takenPictureLeftOffset,60))
            print("updatePicturePanel - 1 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        elif self.pictureTakenCounter == 2:
            if self.picture2 is not None:
                self.picture2.Destroy()
                
            self.picture2 = wx.StaticBitmap(self,-1, self.bmp, (self.takenPictureLeftOffset,305))
            print("updatePicturePanel - 2 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        elif self.pictureTakenCounter == 3:
            if self.picture3 is not None:
                self.picture3.Destroy()
            
            self.picture3 = wx.StaticBitmap(self,-1, self.bmp,(self.takenPictureLeftOffset,550))
            print("updatePicturePanel - 3 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        elif self.pictureTakenCounter == 4:
            
            if self.picture4 is not None:
                self.picture4.Destroy()
                
            self.picture4 = wx.StaticBitmap(self,-1, self.bmp,(self.takenPictureLeftOffset,795))
            self.showProcessingText()
            print("updatePicturePanel - 4 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

        #self.bmp.Destroy()
        
        print("Completed updating picture")
        print("updatePicturePanel - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        print("Child count Exit: " + str(len(self.GetChildren())))    

    def initCountdownTimerImage(self):
        
        self.wximg = wx.Image("res/countdown3.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        self.countdownImages.append(self.wxbmp)

        self.wximg = wx.Image("res/countdown2.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        self.countdownImages.append(self.wxbmp)

        self.wximg = wx.Image("res/countdown1.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        self.countdownImages.append(self.wxbmp)  
        
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
                
            print("Updating countdown: " + str(self.countdownCounter))
            
            if self.countdownImage is not None:
                self.countdownImage.Destroy()
            
            self.countdownImage = wx.StaticBitmap(self,-1, self.countdownImages[self.countdownCounter],(1025,100))
            self.countdownCounter += 1
            sleep(1)
            threading.Thread(target=self.playSound,args=["./res/beep-07.wav"]).start()
            
        else:
            self.countdownCounter = 0
            self.countdownImage.Hide()
            #Stop the countdown process
            self.updateCountdownImage = False 
            self.takePicture()
            
    def takePicture(self):
        
        global raspistillPID
        
        print ("takePicture - 6 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        
        sleep(1.5)
        #Turn on flash
        GPIO.output(GPIO_FLASH_PIN, False)
                    
        #Play photo sound
        #os.system("aplay ./res/camera-shutter-click-01.wav")
        p = subprocess.Popen(["aplay", "./res/camera-shutter-click-01.wav"])
               
        #Take picture
        subprocess.call(['kill', '-USR1' , raspistillPID])
        print ("Sending kill command to " + raspistillPID)

        sleep(1)

        #Turn off flash
        GPIO.output(GPIO_FLASH_PIN, True)
        
        sleep(2)

        outputPictureName = self.newDirName + "/pic-" + str(self.pictureTakenCounter) + ".jpg"
        shutil.copy(pictureName, outputPictureName)

        #Send message to GUI thread
        self.updatePicturePanel(outputPictureName)
            
        if self.pictureTakenCounter == 4:
            
            #Publisher().sendMessage("showProcessingText", "Nothing")
            #Stop the countdown process
            self.updateCountdownImage = False      
            print("Picture capture complete")
            
            sleep(1)
            #self.showProcessingText("")
            monitorFolder(self.newDirName)
            makeCollage()
            self.hideProcessingText("")

            wx.FutureCall(18000, self.showBeginningText)

            self.pictureTakenCounter = 0
        else:
            #Start the countdown process
            self.updateCountdownImage = True  
            
        print("takePicture 7 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)       

    def showProcessingText(self, param=""):
        print("Showing processing message...")
        self.processingText.Show()

    def hideProcessingText(self, param=""):
        print("Hiding processing message...")
        self.processingText.Hide()
        
    def showBeginningText(self, param=""):
        print("Showing beginning message...")
        self.beginningText.Show()

    def hideBeginningText(self, param=""):
        print("Hiding beginning message...")
        self.beginningText.Hide()        
        
class MainWindow(wx.Frame):

    showCollage = True
    
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, size=(wx.DisplaySize()), pos=(0,0), title="Photo Booth")
        self.panel = MainPanel(self)

        self.ShowFullScreen(True)

        Publisher().subscribe(self.showCollage, "showCollage")
        Publisher().subscribe(self.panel.resetPanel, "reset")
        Publisher().subscribe(self.panel.startCountdown, "startCountdown")
        Publisher().subscribe(self.panel.showProcessingText, "showProcessingText")
        Publisher().subscribe(self.panel.hideProcessingText, "hideProcessingText")
        Publisher().subscribe(self.panel.showBeginningText, "showBeginningText")
        Publisher().subscribe(self.panel.hideBeginningText, "hideBeginningText")

        print("MainWindow thread: " + threading.current_thread().name)

    def showCollageInner(self):
        print("showCollageInner - 8 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        print("Showing collage from GUI")
        collageWindow = CollageFrame(self.collagePath)
        collageWindow.Show()

        #Show picture for 15 seconds and close down
        wx.FutureCall(15000, collageWindow.Destroy)
        print("Collage Displayed!")
        gc.collect()
        print("showCollageInner - 9 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        

    def showCollage(self, collagePath):
        self.collagePath = collagePath.data
        self.showCollage = True
        print(self.collagePath)

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
        print(message)
        GPIO.cleanup() 
        sys.exit()
