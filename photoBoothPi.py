#!/usr/bin/env python


import os
import sys

import threading
from time import sleep
import datetime
import subprocess
import shlex
from threading import Thread

import signal
import Image
import shutil
import wx
import gc
import resource

import json

from picamera import PiCamera

#Photobooth App Imports
import GPIOThread as gpio
import PhotoboothApp as pbApp


pictureWidth = 2592
pictureHeight = 1944

currentTime = datetime.datetime.now()

camera = PiCamera()



#Configure sound TODO may want to move this to be set at login in the user profile type file
os.system("sudo amixer cset numid=3 2")

def mimicButtonPress():
    global gpioThread
    gpioThread.beginPictureCapture()


def main():
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   #Need for test script, to mimic button press
    global camera
    global gpioThread
    
    configurationData = loadJson()
    configuration = configurationData['configuration']
    previewWindow = configurationData['previewWindow']
    pictureSize = configurationData['pictureSize']
    
    camera.resolution = (pictureSize['width'],pictureSize['height'])
  
    camera.start_preview()
    camera.preview.fullscreen = False
    camera.preview.window =(previewWindow['X'],previewWindow['Y'],previewWindow['height'],previewWindow['width'])
    
    #outputPath = "/media/KINGSTON/"
    outputPath = configuration['outputDirectory']
    os.system("mkdir " + outputPath + "photoBoothOutput")
    gpioThread = gpio.GPIOThread(outputPath)
    gpioThread.setDaemon(True)
    gpioThread.setCamera(camera)
    gpioThread.start()

def startGUI():
    '''Starts the GUI'''
    app = pbApp.PhotoBoothApp(camera, outputPath)
    
    main()

    app.MainLoop()
    
def loadJson():
    '''Reads in the configuraiton json file that has the applications parameters'''
    fileContent = file("./configuration.json", "r")
    jsonFile = json.load(fileContent)
    
    return jsonFile

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
