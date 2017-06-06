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

from picamera import PiCamera

#Photobooth App Imports
import GPIOThread as gpio
import PhotoboothApp as pbApp


pictureWidth = 2592
pictureHeight = 1944

#outputPath = "/media/KINGSTON/"
outputPath = "/tmp/"
os.system("mkdir " + outputPath + "photoBoothOutput")

currentTime = datetime.datetime.now()

camera = PiCamera()

gpioThread = gpio.GPIOThread(outputPath)

#Configure sound TODO may want to move this to be set at login in the user profile type file
os.system("sudo amixer cset numid=3 2")

def mimicButtonPress():
    global gpioThread
    gpioThread.beginPictureCapture()


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
    
    gpioThread.setDaemon(True)
    gpioThread.setCamera(camera)
    gpioThread.start()

def startGUI():
    #global mainFrame
    app = pbApp.PhotoBoothApp(camera, outputPath)

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
