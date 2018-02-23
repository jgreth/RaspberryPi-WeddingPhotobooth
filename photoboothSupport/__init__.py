#!/usr/bin/env python
import json

def loadJson(jsonFilePath="../res/configuration.json"):
    '''Reads in the configuraiton json file that has the applications parameters'''
    fileContent = file(jsonFilePath, "r")
    jsonFile = json.load(fileContent)
    
    return jsonFile