#!/usr/bin/env python
import resource
import wx
import os
import logging


class CollageFrame(wx.Frame):
    def __init__(self, collagePath, logger):  
        logger.debug("Initializing CollageFrame")
        wx.Frame.__init__(self, None, -1, "Your Photobooth Picture")

        self.cbmp = wx.Image(collagePath, wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.SetPosition(wx.Point(800,0))
        self.SetBackgroundColour('black')
        self.Maximize(True)
        self.bmp = wx.StaticBitmap(self,-1, self.cbmp,(0,0))
        logger.debug("CollageFrame initialized!")
        
        self.cbmp.Destroy()