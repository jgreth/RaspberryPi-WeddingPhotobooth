#!/usr/bin/env python

#import photoBoothPi2 as pb
import datetime
from time import sleep
import threading

import photoBoothGUI as gui


def run():
    print "Starting GUI"
    gui.startGUI()

def runGUI():
    print "Kicking off thread"
    runThread = threading.Thread(target=run)
    runThread.start()

def runTest():
    print "Run test"
    gui.mimicButtonPress()
    sleep(120)


if __name__ == "__main__":    
    #Main test execution
    runGUI()
    sleep(10)

    count = 0

    while(True):
        print "Running test # " + str(count)
        runTest()    
        count += 1

 
