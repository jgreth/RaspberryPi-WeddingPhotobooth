#!/usr/bin/env python
import os
import subprocess

#Old command
#command = "export DISPLAY=:0;cd /home/pi/Photobooth;sudo ./photoBoothPi.py"

command = "sudo /usr/bin/python " + os.getcwd() + "/photoBoothPi.py"

os.system(command)
