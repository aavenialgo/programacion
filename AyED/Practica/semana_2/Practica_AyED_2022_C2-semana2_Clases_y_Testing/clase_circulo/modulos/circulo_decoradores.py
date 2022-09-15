# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 11:14:15 2022

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
        self.radio = radio
        
    @property
    def radio(self):
        """getter de radio"""
        return self._radio
    
    @radio.setter
    def radio(self, valor):
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
            
    @property    
    def area(self):
        """calcula y retorna el valor del área con 2 decimales de precisión"""
        area = math.pi*self.radio**2
        return round(area, 2)
    
    @property
    def perimetro(self):
        """calcula y retorna el valor del perímetro con 2 decimales de precisión"""
        perimetro = 2*math.pi*self.radio
        return round(perimetro, 2)        
    
    


if __name__ == "__main__":
    
    c1 = Circulo(5)

    print(c1.radio)
    c1.radio = 4
    
    print(c1.area)
    print(c1.perimetro)
