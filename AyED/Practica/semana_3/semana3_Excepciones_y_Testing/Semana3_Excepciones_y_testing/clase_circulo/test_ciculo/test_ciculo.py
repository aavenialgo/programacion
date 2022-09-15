# -*- coding: utf-8 -*-
"""
Created on Wed Aug 17 15:38:19 2022

@author: alumno
"""
from circulo import Circulo

import unittest

class TestCirculo ( unittest.TestCase):
    def setUp(self):
        self.c1 = Circulo(4)
        print('\nsetUp')
        
    
    def test_area(self):
        self.assertEqual(self.c1.area, 50.27)
        
    def test_perimetro(self):
        self.assertAlmostEqual(self.c1.perimetro, 25.13, 2)
        
    def test_excepciones(self):
        self.assertRaises(ValueError ,self.c1.set_radio,-4)
        
    def tearDown(self):
        print ("tearDown")
        
if __name__ == "__main__":
    
    unittest.main()