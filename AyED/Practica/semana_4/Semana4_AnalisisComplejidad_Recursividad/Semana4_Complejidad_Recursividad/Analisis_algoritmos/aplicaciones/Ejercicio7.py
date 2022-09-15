# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 10:09:34 2022

@author: je_su
"""

# 10: 10/10 = 1 , 10%10 = 0  --> 1 + 0
# 120: 120//10 = 12, 120%10 = 0;  12//10 = 1, 12%10=2; 1//10 = 0  
# 250: 250//10 = 25, 250%10 = 0;  25//10 = 2, 25%10=5; 2//10 = 0

# f(n) = f(n//10) + n%10

def suma_digitos(numero):
    if numero == 0:
        return 0
    return suma_digitos(numero//10) + numero%10


if __name__ == '__main__':
    
    print(suma_digitos(250))