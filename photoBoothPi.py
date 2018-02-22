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
import logging

from picamera import PiCamera

#Photobooth App Imports
import GPIOThread as gpio
import PhotoboothApp as pbApp


pictureWidth = 2592
pictureHeight = 1944

currentTime = datetime.datetime.now()

#Configure sound TODO may want to move this to be set at login in the user profile type file
os.system("sudo amixer cset numid=3 2")

def mimicButtonPress():
    '''This operation mimics a "hardware" button press
    Function is used for testing purposes only'''
    global gpioThread
    gpioThread.beginPictureCapture()


def main(configurationData, camera):
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   #Need for test script, to mimic button press
    global gpioThread
    
    logger = logging.getLogger('logs/photobooth.log')
    logger.setLevel(logging.DEBUG)
    
    logger.debug("Inside photoBoothPi main operation")
    
    configuration = configurationData['configuration']
    previewWindow = configurationData['previewWindow']
    cameraResolution = configurationData['pictureSize']
    
    print("Requesting " + str(cameraResolution['width']),str(cameraResolution['height']))
    camera.resolution = (int(cameraResolution['width']),int(cameraResolution['height']))
  
    camera.start_preview()
    camera.preview.fullscreen = False
    #camera.preview.window =(previewWindow['X'],previewWindow['Y'],previewWindow['height'],previewWindow['width'])
    camera.preview.window =(int(previewWindow['X']),int(previewWindow['Y']),int(cameraResolution['height']),int(cameraResolution['width']))
    
    
    #outputPath = "/media/KINGSTON/" 
    outputPath = configuration['outputDirectory']
    os.system("mkdir " + outputPath + "photoBoothOutput")
    gpioThread = gpio.GPIOThread(outputPath)
    gpioThread.setDaemon(True)
    gpioThread.setCamera(camera)
    gpioThread.start()

def startGUI():
    '''Starts the GUI'''
    
    camera = PiCamera()
    
    configurationData = loadJson()
    configuration = configurationData['configuration']
    app = pbApp.PhotoBoothApp(camera, configuration['outputDirectory'])
    
    main(configurationData, camera)

    app.MainLoop()
    
def loadJson():
    '''Reads in the configuraiton json file that has the applications parameters'''
    fileContent = file("./res/configuration.json", "r")
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
