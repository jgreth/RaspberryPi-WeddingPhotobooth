#!/usr/bin/env python


import os
import sys

import threading
from time import sleep
import datetime
from linkedList import *
import subprocess
import shlex
from threading import Thread

import signal
import Image
import shutil
import wx
import gc
import urllib2 
import resource

from picamera import PiCamera

#Photobooth App Imports
import GPIOThread as gpio
import PhotoboothApp as pbApp


pictureWidth = 2592
pictureHeight = 1944

reducedHeight = 430
reducedWidth = 322
collageReducedPictureSize = reducedHeight, reducedWidth

pictureName= "photoBoothPic.jpg"
imageList = LinkedList()
photo = 0

img = Image.open(os.getcwd() + "/res/photoboothlayout.jpg")

outputPath = "/media/KINGSTON/"

currentTime = datetime.datetime.now()

#raspistillPID = "0"\
camera = PiCamera()



#Configure sound TODO may want to move this to be set at login in the user profile type file
os.system("sudo amixer cset numid=3 2")

        
def addPicture(fileName, location):
    global imageList
    resizePicture(fileName)
    imageList.add(fileName + "_collage",location)
    print("Added " + fileName + " to " + location)

def resizePicture(imagePath):
    global collageReducedPictureSize
    
    image = Image.open(imagePath)
    image.thumbnail(collageReducedPictureSize, Image.ANTIALIAS)
    image.save(imagePath + "_collage", "JPEG")

def monitorFolder(source):
    global reducedHeight
    global reducedWidth

    fileExtList = [".jpg"];
    tempList = os.listdir(source)

    print(tempList)
    print(len(tempList) % 4)

    topBorderOffset = "139"
    leftBorderOffset = "60" #"73"
    
    if len(tempList) % 4 == 0:
        for picture in tempList:
            if os.path.splitext(picture)[1] in fileExtList:
                fileName = os.path.join(source,picture)
                pindex = tempList.index(picture) + 1
                if pindex % 4 == 1:
                    print("Pic % 1 " + picture)
                    location = leftBorderOffset + "," + topBorderOffset
                elif pindex % 4 == 2:
                    print("Pic % 2 " + picture)
                    location = str(reducedWidth + 213) + "," + topBorderOffset
                elif pindex % 4 == 3:
                    print("Pic % 3 " + picture)
                    location = str(reducedWidth + 213) + "," + str(reducedHeight + 37)
                elif pindex % 4 == 0:
                    print("Pic % 0 " + picture)
                    location = leftBorderOffset + "," + str(reducedHeight + 37)
                addPicture(fileName,location)

def makeCollage():
    
    print("makeCollage - Start - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    print("Creating collage")
    global imageList
    global photo
    global img
    global currentTime
    
    destination = "./raw"
    fileName = outputPath + "/photoBoothOutput"
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
        #shutil.move(current.getFileName(), destination)
        subprocess.call(["mv", current.getFileName(), destination])
        current = current.getNext()
    
    imageList = LinkedList() 
    
    #Send message to GUI thread
    print("Calling showCollage from: " + threading.current_thread().name)
    Publisher.sendMessage("showCollage", collageName)
    print("Collage created")
    
    if checkInternetConnection():
        print("Uploading to DropBox: " + collageName + " to: " + tempName)
        dropboxThread = threading.Thread(target=sendToDropbox, args=[collageName, tempName])
        dropboxThread.start()
          
    print("makeCollage - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)  

def mimicButtonPress():
    global gpioThread
    gpioThread.beginPictureCapture()
    
def checkInternetConnection():
    try:
        response=urllib2.urlopen('http://74.125.228.100',timeout=1)
        print("Connected to internet.")
        return True
    except urllib2.URLError as err: pass
    print("Not connected to internet.")
    return False  

def sendToDropbox(fullFilePath, fileName):
    print("sendToDropbox - Start -  Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) 
    command = "./dropbox_uploader.sh upload " + fullFilePath + " " + fileName
    print("Uploading to Dropbox: " + command)
    p = subprocess.Popen([command], shell=True)
    print("sendToDropbox - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) 

def main():
    #global raspistillPID
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   #Need for test script, to mimic button press
    global camera
    global gpioThread
    
    #camera.resolution = (str(pictureWidth),str(pictureHeight))
    
       
    camera.start_preview()
    camera.preview.fullscreen = False
    camera.preview.window =(85,50,800,800)
    '''Using the Pi Camera API, we dont need to get the process id
    #Get raspistill process id, needed to tell camera to capture picture
    proc1 = subprocess.Popen(shlex.split('ps t'),stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(shlex.split('grep raspistill'),stdin=proc1.stdout,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc1.stdout.close() # Allow proc1 to receive a SIGPIPE if proc2 exits.
    out,err=proc2.communicate()
    print out
    if out.split(" ")[1] != " ":
        raspistillPID = out.split(" ")[1]
    else:
        raspistillPID = out.split(" ")[0]    
    proc2.stdout.close()

    print("raspistill pid = " + raspistillPID)
    '''
    
    gpioThread = gpio.GPIOThread()
    gpioThread.setDaemon(True)
    gpioThread.start()

def startGUI():
    #global mainFrame
    app = pbApp.PhotoBoothApp()

    app.MainLoop()

if __name__ == "__main__":
    try:
        with open('/sys/firmware/devicetree/base/model', 'r') as f:
            first_line = f.readline()
            print("Running on " + first_line)  
        global gpioThread #Need for test script, to mimic button press
        startGUI()
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        gpio.GPIO.cleanup() 
        sys.exit()
