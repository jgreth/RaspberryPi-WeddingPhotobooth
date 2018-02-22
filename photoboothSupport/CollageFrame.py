#!/usr/bin/env python
import resource
import wx

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