# -*- coding: utf-8 -*-
"""
Created on Wed Aug 17 15:03:01 2022

@author: alumno
"""

from excepciones import NotAlturaError
from excepciones import NotPesoError
from calculadora_imc import CalculadoraIMC
def main ():
    try:
        altura = float(input ("Ingrese la altura en metros: "))
        peso = int(input("Ingrese el peso en kilogramos: "))
        imc = CalculadoraIMC(altura, peso)

    except NotAlturaError as msg:
        print (msg)
    except NotPesoError as msg:
        print (msg)
    else:
        print (imc.imc())

if __name__ == '__main__':
    main()