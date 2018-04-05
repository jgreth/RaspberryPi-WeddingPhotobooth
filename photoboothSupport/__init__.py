#!/usr/bin/env python
import json
import os
import logging


def loadJson(jsonFilePath="./res/configuration.json"):
    '''Reads in the configuraiton json file that has the applications parameters'''
    fileContent = file(jsonFilePath, "r")
    jsonFile = json.load(fileContent)
    
    return jsonFile

def configureLogger():
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger(__name__)
    
    # create a file handler
    handler = logging.logging.handlers.RotatingFileHandler(
              'logs/photobooth.log', maxBytes=20, backupCount=5)
    handler.setLevel(logging.NOTSET)
    
    # create console handler with a higher log level
    console = logging.StreamHandler()
    console.setLevel(logging.NOTSET)
    
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    console.setFormatter(formatter)
    
    # add the handlers to the logger
    logger.addHandler(handler)
    logger.addHandler(console)
    
    return logger