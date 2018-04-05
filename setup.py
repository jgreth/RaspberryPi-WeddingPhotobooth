#!/usr/bin/env python


import os
import subprocess

#If if a verison of the uploader exists, it f it does remove it
if os.path.exists("Dropbox-Uploader"):
    print("Removing old copy of Dropbox-Uploader")
    subprocess.call("rm -rf Dropbox-Uploader".split(" "))
    
#Retreive a fresh copy
print("Pulling new version of Dropbox-Uploader from github")
subprocess.call("git clone https://github.com/andreafabrizi/Dropbox-Uploader Dropbox-Uploader".split(" "))

#Check if the access token has already been configured for this script
configFilePath = "/home/" + os.environ['USER'] + "/.dropbox_uploader" 
print(configFilePath)    
if not os.path.exists(configFilePath):
    print("Running dropbox_uploader.sh for initial configuration")
    subprocess.call("./Dropbox-Uploader/dropbox_uploader.sh".split(" "))
else:
    print("dropbox_uploader.sh is already configured, if you would like to reconfigure run: " + configFilePath)
    