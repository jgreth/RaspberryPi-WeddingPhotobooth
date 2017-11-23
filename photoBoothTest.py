#!/usr/bin/env python

import datetime
from time import sleep
import threading
import sys

import photoBoothPi as gui


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
        numberOfTests = 500
        if len(sys.argv) == 2:
            numberOfTests = sys.argv[1]
            
        #Main test execution
        runGUI()
        sleep(8)
    
        count = 0
        
        print("Running a total of " + str(numberOfTests) + " tests.")
        for count in range(0,int(numberOfTests)):
            print("\n\nRunning test # " + str(count) + " out of " + str(numberOfTests) + "\n\n")
            runTest()    
        
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        sys.exit()        

 
