#!/usr/bin/env python

import os

command = "export DISPLAY=:0;cd /home/pi/Photobooth;sudo ./photoBoothGUI.py"

os.system(command)
