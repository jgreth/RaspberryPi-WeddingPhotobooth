#!/usr/bin/env python

import os
import subprocess

command = "export DISPLAY=:0;cd /home/pi/Photobooth;sudo ./photoBoothPiNew.py"

os.system(command)
