#Node.py
#created 4/17/07
#by Alex Miller and Derek Groenendyk

import Image
import os

class Node:

    size = 128,128
    
    def __init__(self,initdata,position):

        self.data = Image.open(initdata)
        self.next = None
        self.fileName = initdata
        self.location = None
        self.width, self.height = self.data.size
        self.size = str(self.height)+","+str(self.width)
        self.position = position

    def getData(self):
        return self.data
    
    def getLocation(self):
        return self.location

    def getFileName(self):
        return self.fileName

    def getNext(self):
        return self.next

    def getSize(self):
        return self.size

    def getPosition(self):
        return self.position

    def setData(self,newdata):
        self.data = Image.open(newdata)
        
    def setNext(self,newnext):
        self.next = newnext

    def setPosition(self, position):
        self.position = position
        
    def setSize():
        self.width, self.height = self.data.size
        
    def setLocation(self, location):
        '''for i in location:
            if i == ",":
                location = location.replace(","," ")
        location = location.split(" ")'''
        self.location = [location[0],location[1]]

