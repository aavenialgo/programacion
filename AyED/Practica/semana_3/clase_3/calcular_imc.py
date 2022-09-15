# -*- coding: utf-8 -*-
"""
Created on Wed Aug 17 14:05:20 2022

@author: alumno
# """
# from excepciones_imc import NotZeroError
import excepciones_imc

def calcular_imc(peso, altura):
    if altura <=0:
        raise ValueError("Error al ingresar la altura")
    if peso <=0:
        raise NotZeroError("El peso no puede ser cero o negativo")
        
    imc = peso/(altura**2)
    return imc

if __name__ == '__main__':
    
    peso = int (input('ingrese el valor del peso (kg): '))
    
    altura = float (input ('Ingrese el valor de la altura (m): '))
    try:
        imc = calcular_imc(peso, altura)
    
    except ValueError as msg:
        print (msg)
    else:
        print (f"Indice de masa corporal es {imc}")
    
    