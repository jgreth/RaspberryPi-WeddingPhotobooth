#!/usr/bin/env python

import RPi.GPIO as GPIO
from threading import Thread
from wx.lib.pubsub import pub as Publisher


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
    def __init__(self):
        Thread.__init__(self)
        self.busy = False
        
        Publisher.subscribe(self.finished, "finished")

    def run(self): 
        resetShutdownCounter = 0

        while True:
            inputValue = GPIO.input(GPIO_INPUT_PIN)
            if inputValue == True and (not self.busy):
                self.busy = True
                print("Button Pressed")
                self.beginPictureCapture()
            
            resetShutdownValue = GPIO.input(GPIO_RESET_PIN)
            if resetShutdownValue == True:
                resetShutdownCounter += 1
            elif resetShutdownValue == False and resetShutdownCounter != 0:          
                if resetShutdownCounter >= 10:
                    print("Shutdown Button Pressed! Shutting down system now.....")
                    os.system("sudo shutdown -h now")   
                elif resetShutdownCounter > 1:
                    print("Reset Button Pressed! Rebooting system now.....")
                    os.system("sudo reboot")  
                
                resetShutdownCounter = 0 
                
            sleep(0.25)

    def finished(self, param):
       self.busy = False      
       
    def beginPictureCapture(self):
        
        print("beginPictureCapture - Start - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        
        #Play sound
        p = subprocess.Popen(["aplay", os.getcwd() + "/res/smw_1-up.wav"])
        
        Publisher.sendMessage("hideBeginningText", "Nothing")
        Publisher.sendMessage("reset", "Nothing")
        print("Remember to Smile")
        currentTime = datetime.datetime.now()
        self.newDirName = outputPath + str(currentTime).replace(' ', '_').split('.')[0].replace(':', '-')
        os.mkdir(self.newDirName)
        subprocess.call(['chmod', '777', self.newDirName])   
        Publisher.sendMessage("startCountdown", self.newDirName)
        
        print("beginPictureCapture - End - Memory usage: %s (kb)" % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        
if __name__ == "__main__":        
    gpioThread = GPIOThread()
    gpioThread.setDaemon(True)
    gpioThread.start()