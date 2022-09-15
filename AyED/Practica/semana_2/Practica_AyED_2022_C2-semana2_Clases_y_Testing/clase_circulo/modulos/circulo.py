# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 10:41:50 2022

@author: je_su
"""

import math

class Circulo:
    """clase que modela un círculo mediante su atributo radio posee métodos para 
    modificar/obtener el radio y para calcular y devolver su perímetro y su área.
    -----------
    atributos:
        radio: int. valor entero que representa el radio del círculo
    """    
    def __init__(self, radio=0):       
        self._radio = radio
        
    def get_radio(self):
        """getter de radio"""
        return self._radio
    
    def set_radio(self, valor):
        """setter de radio
        ----------
        valor : int
            valor entero positivo para modificar el radio.
        """
        if valor < 0:
            self._radio = 0
            print("no puede ingresar valores negativos")
        else:
            self._radio = valor
        
    def get_area(self):
        """calcula y retorna el valor del área con 2 decimales de precisión"""
        area = math.pi*self.get_radio()**2
        return round(area, 2)
    
    def get_perimetro(self):
        """calcula y retorna el valor del perímetro con 2 decimales de precisión"""
        perimetro = 2*math.pi*self.get_radio()
        return round(perimetro, 2)        



if __name__ == "__main__":
    
    c1 = Circulo(5)

    print(c1.get_radio())
    c1.set_radio(-4)
    
    print(c1.get_area())
    print(c1.get_perimetro())