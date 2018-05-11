#!/usr/bin/env python

import photoboothSupport as pbSupport
import photoboothSupport.photoboothApp as pbApp

import unittest

class PhotoboothMethods(unittest.TestCase):

    def test_json_configuration(self):
        
        jsonFile = pbSupport.loadJson()
        configuration = jsonFile['configuration']
        self.assertEqual(configuration['outputDirectory'], '/media/pi/KINGSTON1/photoBoothOutput/')
        
        previewWindow = jsonFile['previewWindow']
        self.assertEqual(previewWindow['X'], '85')

    
'''
TODO: How can I do this, need to pass in multiple parameters to class, can I mock them?
class PhotoboothMainPanelMethods(unittest.TestCase):

    def test_monitorFoldern(self):
        
        mainPanel = pbApp.MainPanel(None, None, None,None,None)
        mainPanel.monitorFolder("./testPictures/")
'''
    

if __name__ == '__main__':
    unittest.main()
