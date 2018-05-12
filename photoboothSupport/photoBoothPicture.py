#!/usr/bin/env python
import Image

class PhotoBoothPicture:


    def __init__(self, fileName, x=0, y=0, width=0, height=0):
        self.fileName = fileName
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.data = Image.open(fileName)

