#!/usr/bin/env python

import datetime
from time import sleep
import threading
import sys

import photoBoothPiNew as gui


def run():
    print("Starting GUI")
    gui.startGUI()

def runGUI():
    print("Kicking off thread")
    runThread = threading.Thread(target=run)
    runThread.start()

def runTest():
    print("Run test")
    gui.mimicButtonPress()
    sleep(120)


if __name__ == "__main__":    
    try:
        #Main test execution
        runGUI()
        sleep(8)
    
        count = 0
    
        while(count < 500):
            print("\n\nRunning test # " + str(count)) + "\n\n"
            runTest()    
            count += 1
        
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        sys.exit()        

 
