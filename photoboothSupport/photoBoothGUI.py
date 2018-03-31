#!/usr/bin/env python

import wx
import os
import sys
import photoBoothPi
from wx.lib.pubsub import Publisher
import threading
from time import sleep

import pdb

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

        photoBoothPi.main()


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
        print "Updating picture from " + threading.current_thread().name

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

    def startCountdown(self, count):
        self.updateCountdownImage = True
        
    def updateCountdownInner(self):

        if self.countdownCounter < 3:
            if self.countdownCounter != 0:
                self.countdownImage.Hide()
            print "Updating countdown: " + str(self.countdownCounter)
            self.countdownImage = wx.StaticBitmap(self,-1, self.countdownImages[self.countdownCounter],(1025,100))
            self.countdownCounter += 1
        else:
            self.countdownCounter = 0
            self.updateCountdownImage = False
            self.countdownImage.Hide()
        
        sleep(.1)

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
        self.countdown = wx.StaticText(self.panel, label="3", pos=(1300,0), size=(500,500))
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

def mimicButtonPress():
         photoBoothPi.mimicButtonPress()

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
