# -*- coding: utf-8 -*-
"""
Created on Wed Aug 17 14:40:19 2022

@author: alumno
"""
from excepciones import NotPesoError
from excepciones import NotAlturaError


class CalculadoraIMC:
    """permite calcular el indice de masa corporal
    con el peso en kg y la altura en m """
    
    def __init__(self,p_altura,p_peso):
        self._altura = p_altura
        self._peso = p_peso
    
    
    def _calculo_imc (self):
        if self.altura <0:
            raise NotAlturaError("No se puede ingresasr altura negativa")
        if self.peso < 0:
            raise ValueError ("No se puede ingresar peso negativo")
            
        return self.peso/(self.altura**2)
    
    def imc (self):
        imc = self._calculo_imc()
        if imc < 18.5:
            return f"tu IMC {imc} esta debajo de lo normal "
        elif 18.5 < imc < 25:
            return f"tu IMC {imc} es normal "
        elif 25 < imc < 30 :
            return f"tu IMC {imc} indica sobrepeso "
        else:
            return f"tu IMC {imc} indica obesidad "
            
    @property
    def altura (self):
        return self._altura
    
    @property
    def peso(self):
        return self._peso
    
if __name__ == '__main__':
    calculadora = CalculadoraIMC(1.75,80 )
    print (calculadora.imc())