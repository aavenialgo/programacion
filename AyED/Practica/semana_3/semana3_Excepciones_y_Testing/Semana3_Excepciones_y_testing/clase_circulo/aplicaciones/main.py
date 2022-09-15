# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 12:32:05 2022

@author: je_su
"""

from circulo import Circulo

def main():
    try:
        radio = int (input ("ingrese el valir del radio: "))
        c1 = Circulo(radio)
        
    except ValueError as msg:
        print (msg)
    except KeyError as msg:
        print (msg)
    else:
        print(c1.radio)
        print("área del círculo:", c1.area)
        print("perímetro del círculo:", c1.perimetro)

    
if __name__ == "__main__":
    
    main()
    