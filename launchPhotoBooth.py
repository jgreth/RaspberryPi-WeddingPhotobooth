#!/usr/bin/env python

import os
import subprocess

#Old command
#command = "export DISPLAY=:0;cd /home/pi/Photobooth;sudo ./photoBoothPi.py"
command = "sudo python ./photoBoothPi.py"

os.system(command)
