#!/usr/bin/env python
import resource
import wx
import os
import logging
logging.config.fileConfig(os.getcwd() + '/logging.conf')
logger = logging.getLogger(__name__)


class CollageFrame(wx.Frame):
    def __init__(self, collagePath):  
        logger.debug("Initializing CollageFrame")
        wx.Frame.__init__(self, None, -1, "Your Picture")

        self.cbmp = wx.Image(collagePath, wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        self.SetPosition(wx.Point(800,0))
        #self.SetSize(self.cbmp.GetSize())
        self.Maximize(True)
        self.bmp = wx.StaticBitmap(self,-1, self.cbmp,(0,0))
        logger.debug("CollageFrame initialized!")
        
        self.cbmp.Destroy()