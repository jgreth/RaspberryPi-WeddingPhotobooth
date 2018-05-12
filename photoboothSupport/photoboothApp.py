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
import datetime
import urllib2
import gc
import logging
from photoBoothPicture import PhotoBoothPicture


#Photobooth Imports
import GPIOThread
import CollageFrame as collage

class PhotoBoothApp(wx.App):
    def __init__(self, camera, outputPath, configurationData, logger):
        wx.App.__init__(self,0)

        self.mainFrame = MainWindow(None," ", camera, outputPath, configurationData, logger)
        self.mainFrame.Show(True)
        self.camera = camera
        self.outputPath = outputPath
        self.configurationData = configurationData
        self.logger = logger

    def MainLoop(self):

        eventLoop = wx.EventLoop()
        old = wx.EventLoop.GetActive()
        wx.EventLoop.SetActive(eventLoop)
        while True:
 
            while eventLoop.Pending():
                eventLoop.Dispatch()
                       
            if self.mainFrame.showCollage == True:
                self.logger.debug("Showing Collage")
                self.mainFrame.showCollageInner()
                self.mainFrame.showCollage = False
                self.logger.debug("Finished Showing Collage")
            elif self.mainFrame.panel.reset == True:
                self.mainFrame.panel.resetPanelInner()
            elif self.mainFrame.panel.updateCountdownImage == True:
                self.mainFrame.panel.updateCountdownInner()                
            else:    
                self.ProcessIdle()
                
class MainPanel(wx.Panel):
    
    mainPanelWxObjectCount = 0

    pictureTakenCounter = 0

    countdownImages = []
    countdownCounter = 0

    updatePicture = False
    updateCountdownImage = False
    picturePath = ""
    reset = False
    
    pictureName= os.getcwd() + "/photoBoothPic.jpg"
    
    def __init__(self, parent, camera, outputPath, configurationData, logger):
        wx.Panel.__init__(self,parent=parent)
        self.camera = camera
        self.outputPath = outputPath
        self.configurationData = configurationData
        self.logger = logger
        
        self.frame = parent
        
        collageWindow = self.configurationData['collageImageWindow']
        self.collageWindowFirstPicturePosition = (collageWindow['firstPicture']['X'], collageWindow['firstPicture']['Y'])
        self.collageWindowSecondPicturePosition = (collageWindow['secondPicture']['X'], collageWindow['secondPicture']['Y'])
        self.collageWindowThirdPicturePosition = (collageWindow['thirdPicture']['X'], collageWindow['thirdPicture']['Y'])
        self.collageWindowFourthPicturePosition = (collageWindow['fourthPicture']['X'], collageWindow['fourthPicture']['Y'])
        
        self.photoboothLayoutPicture = Image.open(os.getcwd() + "/res/photoboothlayout.jpg")

        pictureSize = self.configurationData['pictureSize']
        self.reducedHeight = int(pictureSize['reducedHeight'])
        self.reducedWidth = int(pictureSize['reducedWidth'])
        
        countdownTimerPosition = self.configurationData['countdownTimerPosition']
        self.countdownTimerPosition = (int(countdownTimerPosition['X']), int(countdownTimerPosition['Y']))
        
        beginTextPosition = self.configurationData['beginTextPosition']
        processingTextPosition = self.configurationData['processingTextPosition']
        
        capturedPicturePosition = self.configurationData['capturedPicturePosition']
        self.capturedPictureSize = (capturedPicturePosition['width'], capturedPicturePosition['height'])
        self.capturedFirstPicturePosition = (capturedPicturePosition['firstPicture']['X'], capturedPicturePosition['firstPicture']['Y'])
        self.capturedSecondPicturePosition = (capturedPicturePosition['secondPicture']['X'], capturedPicturePosition['secondPicture']['Y'])
        self.capturedThirdPicturePosition = (capturedPicturePosition['thirdPicture']['X'], capturedPicturePosition['thirdPicture']['Y'])
        self.capturedFourthPicturePosition = (capturedPicturePosition['fourthPicture']['X'], capturedPicturePosition['fourthPicture']['Y'])
        
        self.photoCounter = 0

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
        
        self.logger.debug( "App Path: " + os.getcwd() + "/res/photoboothappbackground.jpg")
        loc = wx.Bitmap(os.getcwd() + "/res/photoboothappbackground.jpg")
        dc = wx.ClientDC(self)
        dc.DrawBitmap(loc, 0, 0)

        self.initCountdownTimerImage()

        self.wxBmp =  wx.Image(os.getcwd() + "/res/processing.jpg",wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.processingText = wx.StaticBitmap(self,-1, self.wxBmp,(int(processingTextPosition['X']), int(processingTextPosition['Y'])))
        self.processingText.Hide()
        
        self.wxBmp.Destroy()
        
        self.wxBmp =  wx.Image(os.getcwd() + "/res/begin.jpg",wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.beginningText = wx.StaticBitmap(self,-1, self.wxBmp,(int(beginTextPosition['X']), int(beginTextPosition['Y'])))
        self.beginningText.Show()
        
        self.wxBmp.Destroy()
        
        self.picture1 = wx.StaticBitmap(self)
        self.picture2 = wx.StaticBitmap(self)
        self.picture3 = wx.StaticBitmap(self)
        self.picture4 = wx.StaticBitmap(self)
        
        self.countdownImage = wx.StaticBitmap(self)
        
        self.resetPanelInner()

        self.capturedPictures = []
        
        Publisher.subscribe(self.playSound, "object.playSound")
        
        self.mainPanelWxObjectCount = len(self.GetChildren())
        self.logger.debug("Initial Panel Children Count: " + str(self.mainPanelWxObjectCount))

    def resetPanelInner(self):
        
        #TODO: Need to see if these Bitmaps can be converted once and saved off in the class
        self.wximg = wx.Image(os.getcwd() + "/res/blankPicture1.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        
        if self.picture1 is not None:
            self.picture1.Destroy()
        
        self.picture1 = wx.StaticBitmap(self,-1,self.wxbmp,self.capturedFirstPicturePosition)
        self.wximg.Destroy()
        self.wxbmp.Destroy()

        self.wximg = wx.Image(os.getcwd() + "/res/blankPicture2.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        
        if self.picture2 is not None:
            self.picture2.Destroy()
            
        self.picture2 = wx.StaticBitmap(self,-1,self.wxbmp,self.capturedSecondPicturePosition)
        self.wximg.Destroy()
        self.wxbmp.Destroy()

        self.wximg = wx.Image(os.getcwd() + "/res/blankPicture3.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
                
        if self.picture3 is not None:
            self.picture3.Destroy()
        
        self.picture3 = wx.StaticBitmap(self,-1,self.wxbmp,self.capturedThirdPicturePosition)
        self.wximg.Destroy()
        self.wxbmp.Destroy()

        self.wximg = wx.Image(os.getcwd() + "/res/blankPicture4.jpg",wx.BITMAP_TYPE_JPEG)
        self.wxbmp = wx.BitmapFromImage(self.wximg)
        
        if self.picture4 is not None:
            self.picture4.Destroy()
        
        self.picture4 = wx.StaticBitmap(self,-1,self.wxbmp,self.capturedFourthPicturePosition)
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
        
        self.logger.debug("Pictures taken " + str(self.pictureTakenCounter))
        self.picturePath = picturePath
        self.logger.debug("updatePicturePanel - Start - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        self.logger.debug("Child count: " +  str(len(self.GetChildren())))
        self.logger.debug("Updating picture " + str(self.pictureTakenCounter) + " from " + threading.current_thread().name)
        
        self.twximg = wx.Image(str(self.picturePath),wx.BITMAP_TYPE_JPEG)
        self.bmp = self.twximg.Rescale(self.capturedPictureSize[0],self.capturedPictureSize[1]).ConvertToBitmap()
        
        if self.pictureTakenCounter == 1:
            if self.picture1 is not None:
                self.picture1.Destroy()
                
            self.picture1 = wx.StaticBitmap(self, -1, self.bmp, self.capturedFirstPicturePosition)
            self.logger.debug("updatePicturePanel - 1 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        elif self.pictureTakenCounter == 2:
            if self.picture2 is not None:
                self.picture2.Destroy()
                
            self.picture2 = wx.StaticBitmap(self,-1, self.bmp, self.capturedSecondPicturePosition)
            self.logger.debug("updatePicturePanel - 2 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        elif self.pictureTakenCounter == 3:
            if self.picture3 is not None:
                self.picture3.Destroy()
            
            self.picture3 = wx.StaticBitmap(self,-1, self.bmp, self.capturedThirdPicturePosition)
            self.logger.debug("updatePicturePanel - 3 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        elif self.pictureTakenCounter == 4:
            
            if self.picture4 is not None:
                self.picture4.Destroy()
                
            self.picture4 = wx.StaticBitmap(self,-1, self.bmp, self.capturedFourthPicturePosition)
            self.showProcessingText()
            self.logger.debug("updatePicturePanel - 4 - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

        self.logger.debug("Completed updating picture")
        self.logger.debug("updatePicturePanel - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        self.logger.debug("Child count Exit: " + str(len(self.GetChildren())))    

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
        self.logger.debug("New Directory Name: " + self.newDirName)
        
    def updateCountdownInner(self):

        if self.countdownCounter < 3:
            if self.countdownCounter != 0:
                self.countdownImage.Hide()
                
            self.logger.debug("Updating countdown: " + str(self.countdownCounter))
            
            if self.countdownImage is not None:
                self.countdownImage.Destroy()
            
            self.countdownImage = wx.StaticBitmap(self,-1, self.countdownImages[self.countdownCounter],
                                                  (self.countdownTimerPosition))
            self.countdownCounter += 1
            sleep(.75)
            subprocess.Popen(["aplay", "./res/beep-07.wav"])
            
        else:
            self.countdownCounter = 0
            self.countdownImage.Hide()
            #Stop the countdown process
            self.updateCountdownImage = False 
            self.takePicture()
            
    def takePicture(self):
                
        self.logger.debug ("takePicture - 6 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        
        sleep(1.0)
        #Turn on flash
        GPIO.output(GPIOThread.GPIO_FLASH_PIN, False)
                    
        #Play photo sound
        p = subprocess.Popen(["aplay", os.getcwd() + "/res/camera-shutter-click-01.wav"])
               
        #Take picture
        self.camera.capture(self.pictureName, resize=(self.reducedHeight, self.reducedWidth))

        #sleep(1)

        #Turn off flash
        GPIO.output(GPIOThread.GPIO_FLASH_PIN, True)

        outputPictureName = self.newDirName + "/pic-" + str(self.pictureTakenCounter) + ".jpg"
        print(outputPictureName + " " + self.pictureName)
        output = subprocess.call(["cp", self.pictureName, outputPictureName])

        #Send message to GUI thread
        self.updatePicturePanel(outputPictureName)
            
        if self.pictureTakenCounter == 4:
            
            Publisher.sendMessage("object.showProcessingText", param="Nothing")
            #Stop the countdown process
            self.updateCountdownImage = False      
            self.logger.info("Picture capture complete")
            
            #sleep(1)
            self.monitorFolder(self.newDirName)
            self.makeCollage()

            wx.FutureCall(18000, self.showBeginningText)

            self.pictureTakenCounter = 0
        else:
            #Start the countdown process
            self.updateCountdownImage = True  
            
        self.logger.debug("takePicture 7 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)       

    def monitorFolder(self,source):
        '''
        This function monitors the output directory.  Every picture is positioned into the collage.
        '''
    
        fileExtList = [".jpg"];
        tempList = os.listdir(source)
    
        self.logger.debug(tempList)
        self.logger.debug(len(tempList) % 4)
        
        if len(tempList) % 4 == 0:
            for picture in tempList:
                if os.path.splitext(picture)[1] in fileExtList:
                    fileName = os.path.join(source,picture)
                    pindex = tempList.index(picture) + 1
                    if pindex % 4 == 1:
                        self.logger.debug("Top Pic % 1 " + picture)
                        location = self.collageWindowFirstPicturePosition #str(self.leftBorderOffset) + "," + str(self.topBorderOffset)
                        self.logger.debug(location)
                    elif pindex % 4 == 2:
                        self.logger.debug("Top Pic % 2 " + picture)
                        location = self.collageWindowSecondPicturePosition #str(self.leftBorderOffset + self.reducedWidth + self.secondColumnOffset) + "," + str(self.topBorderOffset)
                        self.logger.debug(location)
                    elif pindex % 4 == 3:
                        self.logger.debug("Bottom Pic % 3 " + picture)
                        location = self.collageWindowThirdPicturePosition #str(self.leftBorderOffset + self.reducedWidth + self.secondColumnOffset) + "," + str(self.topBorderOffset + self.reducedHeight + self.bottomRowAdjustment)
                        self.logger.debug(location)
                    elif pindex % 4 == 0:
                        self.logger.debug("Bottom Pic % 0 " + picture)
                        location = self.collageWindowFourthPicturePosition #str(self.leftBorderOffset) + "," + str(self.topBorderOffset + self.reducedHeight + self.bottomRowAdjustment)
                        self.logger.debug(location)
                    self.addPicture(fileName,location)
      
    def addPicture(self, fileName, location):
        pbPicture = PhotoBoothPicture(fileName, location[0], location[1])
        self.capturedPictures.append(pbPicture)
        self.logger.debug("Added " + fileName + " to " + location[0] + "," + location[1])
 
    def resizePicture(self, imagePath):
        collageReducedPictureSize = self.reducedHeight, self.reducedWidth
        
        image = Image.open(imagePath)
        image.thumbnail(collageReducedPictureSize, Image.ANTIALIAS)
        image.save(imagePath + "_collage", "JPEG")
            
    def makeCollage(self):
        
        self.logger.debug("makeCollage - Start - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        self.logger.debug("Creating collage")

        destination = "./raw"
        fileName = self.outputPath + "/photoBoothOutput"
        collageName = ""
        tempName = ""
        
        #while len(self.capturedPictures) != 0 and current != None:
        for current in self.capturedPictures:
            pic = current.getData()
            self.photoboothLayoutPicture.paste(pic,(current.x,current.y))          
            if current.getPosition() % 4 == 0 :
                self.photoCounter += 1
                currentTime = datetime.datetime.now()
                tempName = "Photobooth_"+ str(currentTime).replace(' ', '_').split('.')[0].replace(':', '-') + ".jpg"
                collageName = fileName + "/" + tempName
                self.photoboothLayoutPicture.save(collageName)

            current = current.getNext()
        
        self.capturedPictures = []
        
        #Send message to GUI thread
        self.logger.debug("Calling showCollage from: " + threading.current_thread().name)
        Publisher.sendMessage("object.showCollage", collagePath=collageName)
        self.logger.debug("Collage created")
        
        if self.checkInternetConnection():
            self.logger.info("Uploading to DropBox: " + collageName + " to: " + tempName)
            dropboxThread = threading.Thread(target=self.sendToDropbox, args=[collageName, tempName])
            dropboxThread.start()
              
        self.logger.debug("makeCollage - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)  

    def checkInternetConnection(self):
        try:
            response=urllib2.urlopen('http://216.58.192.142',timeout=1) #Google DNS
            self.logger.info("Connected to internet.")
            return True
        except urllib2.URLError as err: pass
        self.logger.error("Not connected to internet.")
        return False  
    
    def sendToDropbox(self, fullFilePath, fileName):
        self.logger.debug("sendToDropbox - Start -  Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) 
        command = "./Dropbox-Uploader/dropbox_uploader.sh upload " + fullFilePath + " " + fileName
        self.logger.info("Uploading to Dropbox: " + command)
        p = subprocess.Popen([command], shell=True)
        self.logger.debug("sendToDropbox - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) 
        
    def showProcessingText(self, param=""):
        self.logger.debug("Showing processing message...")
        self.processingText.Show()

    def hideProcessingText(self, param=""):
        self.logger.debug("Hiding processing message...")
        self.processingText.Hide()
        
    def showBeginningText(self, param=""):
        self.hideProcessingText("")
        self.logger.debug("Showing beginning message...")
        self.beginningText.Show()
        
        #This will allow the application to respond to the button
        Publisher.sendMessage("object.finished", param="")

    def hideBeginningText(self, param=""):
        self.logger.debug("Hiding beginning message...")
        self.beginningText.Hide()        
        
class MainWindow(wx.Frame):

    showCollage = True
    
    def __init__(self, parent, title, camera, outputPath, configurationData, logger):
        wx.Frame.__init__(self, parent, size=(wx.DisplaySize()), pos=(0,0), title="Photo Booth")
        self.panel = MainPanel(self, camera, outputPath, configurationData, logger)
        self.camera = camera
        self.outputPath = outputPath
        self.configurationData = configurationData
        self.logger = logger

        self.ShowFullScreen(True)

        Publisher.subscribe(self.showCollage, "object.showCollage")
        Publisher.subscribe(self.panel.resetPanel, "object.reset")
        Publisher.subscribe(self.panel.startCountdown, "object.startCountdown")
        Publisher.subscribe(self.panel.showProcessingText, "object.showProcessingText")
        Publisher.subscribe(self.panel.hideProcessingText, "object.hideProcessingText")
        Publisher.subscribe(self.panel.showBeginningText, "object.showBeginningText")
        Publisher.subscribe(self.panel.hideBeginningText, "object.hideBeginningText")

        self.logger.debug("MainWindow thread: " + threading.current_thread().name)

    def showCollageInner(self):
        logging.debug("showCollageInner - 8 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        logging.debug("Showing collage from GUI")
        self.camera.stop_preview()
        collageWindow = collage.CollageFrame(self.collagePath, self.logger)
        collageWindow.Show()

        #Show picture for 15 seconds and close down
        wx.FutureCall(15000, collageWindow.Destroy)
        logging.debug("Collage Displayed!")
        gc.collect()
        self.logger.debug("showCollageInner - 9 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
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
        self.logger.debug(self.collagePath)

    def resetPanel(self):
        self.panel.resetPanel()

    def getReset(self):
        return self.panel.reset
    
    
if __name__ == "__main__":
    app = PhotoBoothApp()
    app.MainLoop()    
