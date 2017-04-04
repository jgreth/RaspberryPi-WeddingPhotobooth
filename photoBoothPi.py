#!/usr/bin/env python

import sys
from picamera import PiCamera
from time import sleep
import wx
from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub as Publisher

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

class MainWindow(wx.Frame):

    showCollage = True
    
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, size=(wx.DisplaySize()), pos=(0,0), title="Photo Booth")
        self.panel = MainPanel(self)

        self.ShowFullScreen(True)

        Publisher.subscribe(self.showCollage, "showCollage")
        Publisher.subscribe(self.panel.resetPanel, "reset")
        Publisher.subscribe(self.panel.startCountdown, "startCountdown")
        Publisher.subscribe(self.panel.showProcessingText, "showProcessingText")
        Publisher.subscribe(self.panel.hideProcessingText, "hideProcessingText")
        Publisher.subscribe(self.panel.showBeginningText, "showBeginningText")
        Publisher.subscribe(self.panel.hideBeginningText, "hideBeginningText")

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
        
        self.resetPanelInner()
        
        
        #Start of the main application
        self.main()
        
        Publisher.subscribe(self.playSound, "playSound")
        
        self.mainPanelWxObjectCount = len(self.GetChildren())
        print "Initial Panel Children Count: " + str(self.mainPanelWxObjectCount)

    def main(self):
        print "Inside main"
        
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
            #p = subprocess.Popen(["aplay", "./res/beep-07.wav"])
            
        else:
            self.countdownCounter = 0
            self.countdownImage.Hide()
            #Stop the countdown process
            self.updateCountdownImage = False 
            self.takePicture()
            
    def takePicture(self):
        
        #TODO: Not needed
        #global raspistillPID
        
        print ("takePicture - 6 Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        
        sleep(1.5)
        #Turn on flash
        GPIO.output(GPIO_FLASH_PIN, False)
                    
        #Play photo sound
        p = subprocess.Popen(["aplay", "./res/camera-shutter-click-01.wav"])
               
        #Take picture
        #TODO: Need to use Camera api to capture picture
        #subprocess.call(['kill', '-USR1' , raspistillPID])
        #print ("Sending kill command to " + raspistillPID)

        sleep(1)

        #Turn off flash
        GPIO.output(GPIO_FLASH_PIN, True)
        
        #TODO is this needed
        #sleep(3)

        outputPictureName = self.newDirName + "/pic-" + str(self.pictureTakenCounter) + ".jpg"
        subprocess.call(["cp", pictureName, outputPictureName])

        #Send message to GUI thread
        self.updatePicturePanel(outputPictureName)
            
        if self.pictureTakenCounter == 4:
            
            Publisher.sendMessage("showProcessingText", "Nothing")
            #Stop the countdown process
            self.updateCountdownImage = False      
            print("Picture capture complete")
            
            sleep(1)
            monitorFolder(self.newDirName)
            makeCollage()

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
        self.hideProcessingText("")
        print("Showing beginning message...")
        self.beginningText.Show()
        
        #This will allow the application to respond to the button
        Publisher.sendMessage("finished", "")

    def hideBeginningText(self, param=""):
        print("Hiding beginning message...")
        self.beginningText.Hide()        


def startGUI():
    global camera
    
    app = PhotoBoothApp()   # Error messages go to popup window

    app.MainLoop()
    
    '''camera = PiCamera()
    #camera.resolution = (str(pictureWidth),str(pictureHeight))
   
    camera.start_preview()
    camera.preview.fullscreen = False
    camera.preview.window =(85,118,800,600)
    sleep(2)
    '''

if __name__ == "__main__":
    try:
        with open('/sys/firmware/devicetree/base/model', 'r') as f:
            first_line = f.readline()
            print("Running on " + first_line)
        startGUI()
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        #GPIO.cleanup() 
        sys.exit()