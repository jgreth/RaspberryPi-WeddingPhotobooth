#!/usr/bin/env python

import RPi.GPIO as GPIO
from threading import Thread
from wx.lib.pubsub import pub as Publisher
import resource
import subprocess
import os
import datetime
import time
import logging

#GPIO Setup
#GPIO.cleanup() 
GPIO_RESET_PIN = 18
GPIO_INPUT_PIN = 24
GPIO_FLASH_PIN = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_RESET_PIN,GPIO.IN)
GPIO.setup(GPIO_INPUT_PIN,GPIO.IN)
GPIO.setup(GPIO_FLASH_PIN,GPIO.OUT)

GPIO.output(GPIO_FLASH_PIN, True)

class GPIOThread(Thread):
    '''
    This thread is in charge of handling the button presses to trigger
    the capturing of the pictures, reset button and eventually control the flash also.
    '''
    def __init__(self, outputPath, logger):
        Thread.__init__(self)
        self.busy = False
        self.outputPath = outputPath
        
        self.logger = logger
        
        
        Publisher.subscribe(self.finished, "object.finished")

    def run(self): 
        resetShutdownCounter = 0

        while True:
            inputValue = GPIO.input(GPIO_INPUT_PIN)
            if inputValue == True and (not self.busy):
                self.busy = True
                self.logger.debug("Button Pressed")
                self.beginPictureCapture()
            
            resetShutdownValue = GPIO.input(GPIO_RESET_PIN)
            if resetShutdownValue == True:
                resetShutdownCounter += 1
            elif resetShutdownValue == False and resetShutdownCounter != 0:          
                if resetShutdownCounter >= 10:
                    self.logger.debug("Shutdown Button Pressed! Shutting down system now.....")
                    os.system("sudo shutdown -h now")   
                elif resetShutdownCounter > 1:
                    self.logger.debug("Reset Button Pressed! Rebooting system now.....")
                    os.system("sudo reboot")  
                
                resetShutdownCounter = 0 
                
            time.sleep(0.25)

    def finished(self, param):
       self.busy = False      
       
    def beginPictureCapture(self):
        
        self.logger.debug("beginPictureCapture - Start - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        
        #Play sound
        p = subprocess.Popen(["aplay", os.getcwd() + "/res/smw_1-up.wav"])
        
        #Publisher.sendMessage("hideBeginningText", "Nothing")
        #Publisher.sendMessage("reset", "Nothing")
        Publisher.sendMessage("object.hideBeginningText")
        Publisher.sendMessage("object.reset", msg="")
        self.logger.debug("Remember to Smile")
        currentTime = datetime.datetime.now()
        self.logger.debug("Output path: " + self.outputPath)
        self.newDirName = self.outputPath + str(currentTime).replace(' ', '_').split('.')[0].replace(':', '-')
        os.mkdir(self.newDirName)
        subprocess.call(['chmod', '777', self.newDirName])   
        Publisher.sendMessage("object.startCountdown",param=self.newDirName)
        
        self.logger.debug("beginPictureCapture - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        
if __name__ == "__main__":        
    gpioThread = GPIOThread()
    gpioThread.setDaemon(True)
    gpioThread.start()