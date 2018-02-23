#!/usr/bin/env python

import photoboothSupport as pbSupport

import unittest

class PhotoboothMethods(unittest.TestCase):

    def test_json_configuration(self):
        
        jsonFile = pbSupport.loadJson()
        configuration = jsonFile['configuration']
        self.assertEqual(configuration['outputDirectory'], '/tmp/')
        
        previewWindow = jsonFile['previewWindow']
        self.assertEqual(previewWindow['X'], '85')




if __name__ == '__main__':
    unittest.main()
