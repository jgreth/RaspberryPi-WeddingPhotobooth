#!/usr/bin/env python

import wx



class MainPanel(wx.Panel):

    takenPictureSizeWindowWidth = 300
    takenPictureSizeWindowHeight = 220
    takenPictureLeftOffset = 1560
    
    def __init__(self, parent):
        wx.Panel.__init__(self,parent=parent)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.frame = parent
        
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

        wximg = wx.Image("/home/pi/MyProjects/2014-01-06_04-00-08/pic-0.jpg",wx.BITMAP_TYPE_JPEG)
        wximg = wximg.Rescale(self.takenPictureSizeWindowWidth, self.takenPictureSizeWindowHeight)
        wxbmp = wximg.ConvertToBitmap()
        self.picture2 = wx.StaticBitmap(self,-1,wxbmp,(self.takenPictureLeftOffset,60))

        wximg = wx.Image("/home/pi/MyProjects/2014-01-06_04-00-08/pic-1.jpg",wx.BITMAP_TYPE_JPEG)
        wximg = wximg.Rescale(self.takenPictureSizeWindowWidth, self.takenPictureSizeWindowHeight)
        wxbmp = wximg.ConvertToBitmap()
        self.picture2 = wx.StaticBitmap(self,-1,wxbmp,(self.takenPictureLeftOffset,305))

        wximg = wx.Image("/home/pi/MyProjects/2014-01-06_04-00-08/pic-2.jpg",wx.BITMAP_TYPE_JPEG)
        wximg = wximg.Rescale(self.takenPictureSizeWindowWidth, self.takenPictureSizeWindowHeight)
        wxbmp = wximg.ConvertToBitmap()
        self.picture3 = wx.StaticBitmap(self,-1,wxbmp,(self.takenPictureLeftOffset,550))

        wximg = wx.Image("/home/pi/MyProjects/2014-01-06_04-00-08/pic-3.jpg",wx.BITMAP_TYPE_JPEG)
        wximg = wximg.Rescale(self.takenPictureSizeWindowWidth, self.takenPictureSizeWindowHeight)
        wxbmp = wximg.ConvertToBitmap()
        self.picture4 = wx.StaticBitmap(self,-1,wxbmp,(self.takenPictureLeftOffset,795))


    def OnEraseBackground(self, evt):
        loc = wx.Bitmap("res/photoboothappbackground.jpg")
        dc = wx.ClientDC(self)
        dc.DrawBitmap(loc, 0, 0)

class MainWindow(wx.Frame):
    
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, size=(wx.DisplaySize()), pos=(0,0), title="Photo Booth")
        self.panel = MainPanel(self)
        
        print wx.DisplaySize()

        self.countdownFont = wx.Font(500, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.countdown = wx.StaticText(self.panel, label="3", pos=(1025,0), size=(500,500))
        self.countdown.SetFont(self.countdownFont)

        self.ShowFullScreen(True)

app = wx.App(False)
frame = MainWindow(None," ")
frame.Show(True)

app.MainLoop()
