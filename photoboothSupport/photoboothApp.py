#!/usr/bin/env python

import wx
from wx.lib.pubsub import pub as Publisher
import RPi.GPIO as GPIO
import os
import threading
import resource
import subprocess
import os
from time import sleep
import Image
from linkedList import *
import datetime
import urllib2
import gc
import logging
logging.config.fileConfig(os.getcwd() + '/logging.conf')
logger = logging.getLogger(__name__)


#Photobooth Imports
import GPIOThread
import CollageFrame as collage

reducedHeight = 430
reducedWidth = 322
collageReducedPictureSize = reducedHeight, reducedWidth

photo = 0

imageList = LinkedList()
img = Image.open(os.getcwd() + "/res/photoboothlayout.jpg")

class PhotoBoothApp(wx.App):
    def __init__(self, camera, outputPath, configurationData):
        wx.App.__init__(self,0)

        self.mainFrame = MainWindow(None," ", camera, outputPath, configurationData)
        self.mainFrame.Show(True)
        self.camera = camera
        self.outputPath = outputPath
        self.configurationData = configurationData

    def MainLoop(self):

        eventLoop = wx.EventLoop()
        old = wx.EventLoop.GetActive()
        wx.EventLoop.SetActive(eventLoop)
        while True:
 
            while eventLoop.Pending():
                eventLoop.Dispatch()
                       
            if self.mainFrame.showCollage == True:
                logger.debug("Showing Collage")
                self.mainFrame.showCollageInner()
                self.mainFrame.showCollage = False
                logger.debug("Finished Showing Collage")
            elif self.mainFrame.panel.reset == True:
                self.mainFrame.panel.resetPanelInner()
            elif self.mainFrame.panel.updateCountdownImage == True:
                self.mainFrame.panel.updateCountdownInner()                
            else:    
                self.ProcessIdle()
                
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
    
    pictureName= "photoBoothPic.jpg"
    
    def __init__(self, parent, camera, outputPath, configurationData):
        wx.Panel.__init__(self,parent=parent)
        self.camera = camera
        self.outputPath = outputPath
        self.configurationData = configurationData
        
        self.frame = parent
        
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
        
        logger.debug( "App Path: " + os.getcwd() + "/res/photoboothappbackground.jpg")
        loc = wx.Bitmap(os.getcwd() + "/res/photoboothappbackground.jpg")
        dc = wx.ClientDC(self)
        dc.DrawBitmap(loc, 0, 0)

        self.initCountdownTimerImage()

        self.wxBmp =  wx.Image(os.getcwd() + "/res/processing.jpg",wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.processingText = wx.StaticBitmap(self,-1, self.wxBmp,(85,850))
        self.processingText.Hide()
        
        self.wxBmp.Destroy()
        
        self.wxBmp =  wx.Image(os.getcwd() + "/res/begin.jpg",wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.beginningText = wx.StaticBitmap(self,-1, self.wxBmp,(85,850))
        self.beginningText.Show()
        
        self.wxBmp.Destroy()
        
        self.picture1 = wx.StaticBitmap(self)
        self.picture2 = wx.StaticBitmap(self)
        self.picture3 = wx.StaticBitmap(self)
        self.picture4 = wx.StaticBitmap(self)
        
        self.countdownImage = wx.StaticBitmap(self)
        
        self.resetPanelInner()
        
        Publisher.subscribe(self.playSound, "object.playSound")
        
        self.mainPanelWxObjectCount = len(self.GetChildren())
        logger.debug("Initial Panel Children Count: " + str(self.mainPanelWxObjectCount))


    def resetPanelInner(self):
        
        #TODO: Need to see if these Bitmaps can be converted once and saved off in the class
        self.wximg = wx.Image(os.getcwd() + "/res/blankPicture1.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        
        if self.picture1 is not None:
            self.picture1.Destroy()
        
        self.picture1 = wx.StaticBitmap(self,-1,self.wxbmp,(self.takenPictureLeftOffset,60))
        self.wximg.Destroy()
        self.wxbmp.Destroy()

        self.wximg = wx.Image(os.getcwd() + "/res/blankPicture2.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        
        if self.picture2 is not None:
            self.picture2.Destroy()
            
        self.picture2 = wx.StaticBitmap(self,-1,self.wxbmp,(self.takenPictureLeftOffset,305))
        self.wximg.Destroy()
        self.wxbmp.Destroy()

        self.wximg = wx.Image(os.getcwd() + "/res/blankPicture3.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
                
        if self.picture3 is not None:
            self.picture3.Destroy()
        
        self.picture3 = wx.StaticBitmap(self,-1,self.wxbmp,(self.takenPictureLeftOffset,550))
        self.wximg.Destroy()
        self.wxbmp.Destroy()

        self.wximg = wx.Image(os.getcwd() + "/res/blankPicture4.jpg",wx.BITMAP_TYPE_JPEG)
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
        loc = wx.Bitmap(os.getcwd() + "/res/photoboothappbackground.jpg")
        dc = wx.ClientDC(self)
        dc.DrawBitmap(loc, 0, 0)

    def updatePicturePanel(self, picturePath):
        self.pictureTakenCounter += 1
        
        logger.debug("Pictures taken " + str(self.pictureTakenCounter))
        self.picturePath = picturePath
        logger.debug("updatePicturePanel - Start - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        logger.debug("Child count: " +  str(len(self.GetChildren())))
        logger.debug("Updating picture " + str(self.pictureTakenCounter) + " from " + threading.current_thread().name)
        
        self.twximg = wx.Image(str(self.picturePath),wx.BITMAP_TYPE_JPEG)
        self.bmp = self.twximg.Rescale(self.takenPictureSizeWindowWidth, self.takenPictureSizeWindowHeight).ConvertToBitmap()
        
        if self.pictureTakenCounter == 1:
            if self.picture1 is not None:
                self.picture1.Destroy()
                
            self.picture1 = wx.StaticBitmap(self, -1, self.bmp, (self.takenPictureLeftOffset,60))
            logger.debug("updatePicturePanel - 1 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        elif self.pictureTakenCounter == 2:
            if self.picture2 is not None:
                self.picture2.Destroy()
                
            self.picture2 = wx.StaticBitmap(self,-1, self.bmp, (self.takenPictureLeftOffset,305))
            logger.debug("updatePicturePanel - 2 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        elif self.pictureTakenCounter == 3:
            if self.picture3 is not None:
                self.picture3.Destroy()
            
            self.picture3 = wx.StaticBitmap(self,-1, self.bmp,(self.takenPictureLeftOffset,550))
            logger.debug("updatePicturePanel - 3 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        elif self.pictureTakenCounter == 4:
            
            if self.picture4 is not None:
                self.picture4.Destroy()
                
            self.picture4 = wx.StaticBitmap(self,-1, self.bmp,(self.takenPictureLeftOffset,795))
            self.showProcessingText()
            logger.debug("updatePicturePanel - 4 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

        logger.debug("Completed updating picture")
        logger.debug("updatePicturePanel - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        logger.debug("Child count Exit: " + str(len(self.GetChildren())))    

    def initCountdownTimerImage(self):
        
        self.wximg = wx.Image(os.getcwd() + "/res/countdown3.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        self.countdownImages.append(self.wxbmp)

        self.wximg = wx.Image(os.getcwd() + "/res/countdown2.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        self.countdownImages.append(self.wxbmp)

        self.wximg = wx.Image(os.getcwd() + "/res/countdown1.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        self.countdownImages.append(self.wxbmp)  
        
    def playSound(self, sound):
        sleep(.75)
        os.system("aplay " + sound)        

    def startCountdown(self, param):
        self.updateCountdownImage = True
        self.newDirName = param
        logger.debug("New Directory Name: " + self.newDirName)
        
    def updateCountdownInner(self):

        if self.countdownCounter < 3:
            if self.countdownCounter != 0:
                self.countdownImage.Hide()
                
            logger.debug("Updating countdown: " + str(self.countdownCounter))
            
            if self.countdownImage is not None:
                self.countdownImage.Destroy()
            
            self.countdownImage = wx.StaticBitmap(self,-1, self.countdownImages[self.countdownCounter],(1225,100))
            self.countdownCounter += 1
            sleep(.75)
            threading.Thread(target=self.playSound,args=[os.getcwd() + "/res/beep-07.wav"]).start()
            subprocess.Popen(["aplay", "./res/beep-07.wav"])
            
        else:
            self.countdownCounter = 0
            self.countdownImage.Hide()
            #Stop the countdown process
            self.updateCountdownImage = False 
            self.takePicture()
            
    def takePicture(self):
        
        global reducedHeight
        global reducedWidth
                
        logger.debug ("takePicture - 6 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        
        sleep(1.0)
        #Turn on flash
        GPIO.output(GPIOThread.GPIO_FLASH_PIN, False)
                    
        #Play photo sound
        p = subprocess.Popen(["aplay", os.getcwd() + "/res/camera-shutter-click-01.wav"])
               
        #Take picture
        self.camera.capture(self.pictureName, resize=(reducedHeight, reducedWidth))

        #sleep(1)

        #Turn off flash
        GPIO.output(GPIOThread.GPIO_FLASH_PIN, True)

        outputPictureName = self.newDirName + "/pic-" + str(self.pictureTakenCounter) + ".jpg"
        subprocess.call(["cp", self.pictureName, outputPictureName])

        #Send message to GUI thread
        self.updatePicturePanel(outputPictureName)
            
        if self.pictureTakenCounter == 4:
            
            Publisher.sendMessage("object.showProcessingText", param="Nothing")
            #Stop the countdown process
            self.updateCountdownImage = False      
            logger.debug("Picture capture complete")
            
            #sleep(1)
            self.monitorFolder(self.newDirName)
            self.makeCollage()

            wx.FutureCall(18000, self.showBeginningText)

            self.pictureTakenCounter = 0
        else:
            #Start the countdown process
            self.updateCountdownImage = True  
            
        logger.debug("takePicture 7 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)       

    def monitorFolder(self,source):
        global reducedHeight
        global reducedWidth
    
        fileExtList = [".jpg"];
        tempList = os.listdir(source)
    
        logger.debug(tempList)
        logger.debug(len(tempList) % 4)
    
        topBorderOffset = "40" #was 15
        leftBorderOffset = "60" #"73"
        
        leftBorderAdjustment = 10
        lowerPictureAdjustment = 30
        
        if len(tempList) % 4 == 0:
            for picture in tempList:
                if os.path.splitext(picture)[1] in fileExtList:
                    fileName = os.path.join(source,picture)
                    pindex = tempList.index(picture) + 1
                    if pindex % 4 == 1:
                        logger.debug("Pic % 1 " + picture)
                        location = str(int(leftBorderOffset) + leftBorderAdjustment) + "," + topBorderOffset
                    elif pindex % 4 == 2:
                        logger.debug("Pic % 2 " + picture)
                        location = str(reducedWidth + 200) + "," + topBorderOffset
                    elif pindex % 4 == 3:
                        logger.debug("Pic % 3 " + picture)
                        location = str(reducedWidth + 200) + "," + str(reducedHeight-lowerPictureAdjustment)
                    elif pindex % 4 == 0:
                        logger.debug("Pic % 0 " + picture)
                        location = str(int(leftBorderOffset) + leftBorderAdjustment) + "," + str(reducedHeight-lowerPictureAdjustment)
                    self.addPicture(fileName,location)
      
    def addPicture(self, fileName, location):
        global imageList

        imageList.add(fileName, location)
        logger.debug("Added " + fileName + " to " + location)
 
    def resizePicture(self, imagePath):
        global collageReducedPictureSize
        
        image = Image.open(imagePath)
        image.thumbnail(collageReducedPictureSize, Image.ANTIALIAS)
        image.save(imagePath + "_collage", "JPEG")
            
    def makeCollage(self):
        
        logger.debug("makeCollage - Start - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        logger.debug("Creating collage")
        global imageList
        global photo
        global img
        global currentTime
        
        destination = "./raw"
        fileName = self.outputPath + "/photoBoothOutput"
        current = imageList.selfHead()
        collageName = ""
        tempName = ""
        
        while not imageList.isEmpty() and current != None:
            pic = current.getData()
            img.paste(pic,(int(current.getLocation()[0]),int(current.getLocation()[1])))          
            if current.getPosition() % 4 == 0 :
                photo += 1
                currentTime = datetime.datetime.now()
                tempName = "Photobooth_"+ currentTime.strftime("%H_%M_%S") + ".jpg"
                collageName = fileName+ "/" + tempName
                img.save(collageName)

            subprocess.call(["mv", current.getFileName(), destination])
            current = current.getNext()
        
        imageList = LinkedList() 
        
        #Send message to GUI thread
        logger.debug("Calling showCollage from: " + threading.current_thread().name)
        Publisher.sendMessage("object.showCollage", collagePath=collageName)
        logger.debug("Collage created")
        
        if self.checkInternetConnection():
            logger.debug("Uploading to DropBox: " + collageName + " to: " + tempName)
            #Not sending collage to dropbox
            #dropboxThread = threading.Thread(target=self.sendToDropbox, args=[collageName, tempName])
            #dropboxThread.start()
              
        logger.debug("makeCollage - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)  

    def checkInternetConnection(self):
        try:
            response=urllib2.urlopen('http://216.58.192.142',timeout=1) #Google DNS
            logger.debug("Connected to internet.")
            return True
        except urllib2.URLError as err: pass
        logger.debug("Not connected to internet.")
        return False  
    
    def sendToDropbox(self, fullFilePath, fileName):
        logger.debug("sendToDropbox - Start -  Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) 
        command = "./Dropbox-Uploader/dropbox_uploader.sh upload " + fullFilePath + " " + fileName
        logger.debug("Uploading to Dropbox: " + command)
        p = subprocess.Popen([command], shell=True)
        logger.debug("sendToDropbox - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) 
        
    def showProcessingText(self, param=""):
        logger.debug("Showing processing message...")
        self.processingText.Show()

    def hideProcessingText(self, param=""):
        logger.debug("Hiding processing message...")
        self.processingText.Hide()
        
    def showBeginningText(self, param=""):
        self.hideProcessingText("")
        logger.debug("Showing beginning message...")
        self.beginningText.Show()
        
        #This will allow the application to respond to the button
        Publisher.sendMessage("object.finished", param="")

    def hideBeginningText(self, param=""):
        logger.debug("Hiding beginning message...")
        self.beginningText.Hide()        
        
class MainWindow(wx.Frame):

    showCollage = True
    
    def __init__(self, parent, title, camera, outputPath, configurationData):
        wx.Frame.__init__(self, parent, size=(wx.DisplaySize()), pos=(0,0), title="Photo Booth")
        self.panel = MainPanel(self, camera, outputPath, configurationData)
        self.camera = camera
        self.outputPath = outputPath
        self.configurationData = configurationData

        self.ShowFullScreen(True)

        Publisher.subscribe(self.showCollage, "object.showCollage")
        Publisher.subscribe(self.panel.resetPanel, "object.reset")
        Publisher.subscribe(self.panel.startCountdown, "object.startCountdown")
        Publisher.subscribe(self.panel.showProcessingText, "object.showProcessingText")
        Publisher.subscribe(self.panel.hideProcessingText, "object.hideProcessingText")
        Publisher.subscribe(self.panel.showBeginningText, "object.showBeginningText")
        Publisher.subscribe(self.panel.hideBeginningText, "object.hideBeginningText")

        logger.debug("MainWindow thread: " + threading.current_thread().name)

    def showCollageInner(self):
        logging.debug("showCollageInner - 8 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        logging.debug("Showing collage from GUI")
        self.camera.stop_preview()
        collageWindow = collage.CollageFrame(self.collagePath)
        collageWindow.Show()

        #Show picture for 15 seconds and close down
        wx.FutureCall(15000, collageWindow.Destroy)
        logging.debug("Collage Displayed!")
        gc.collect()
        logger.debug("showCollageInner - 9 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        wx.FutureCall(15001, self.restartCamera)

    def restartCamera(self):
        previewWindow = self.configurationData['previewWindow']
        cameraResolution = self.configurationData['pictureSize']
        self.camera.resolution = (int(cameraResolution['width']),int(cameraResolution['height']))
  
        self.camera.start_preview()
        self.camera.preview.fullscreen = False
        self.camera.preview.window =(int(previewWindow['X']),int(previewWindow['Y']),int(cameraResolution['height']),int(cameraResolution['width']))
    
    def showCollage(self, collagePath):
        self.collagePath = collagePath
        self.showCollage = True
        logger.debug(self.collagePath)

    def resetPanel(self):
        self.panel.resetPanel()

    def getReset(self):
        return self.panel.reset
    
    
if __name__ == "__main__":
    app = PhotoBoothApp()
    app.MainLoop()    
