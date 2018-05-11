#!/usr/bin/env python

import os
import subprocess

#Old command
command = "cd /home/pi/RaspberryPi-WeddingPhotobooth;sudo python ./photoBoothPi.py"

#command = "sudo /usr/bin/python " + os.getcwd() + "/photoBoothPi.py"

os.system(command)
