# -*- coding: utf-8 -*-
"""
Created on Wed Aug 17 13:51:33 2022

@author: alumno
"""


print ("inicio mi programa")

try : 
    arch = open ('datos/mi_archivo.txt')
    lista = [1,2,3]
    print (lista)

except FileNotFoundError:
    archi = open ('mi_archivo.txt','w')
    archi.write("escribe una linea")
    
    
except IndexError as mensaje:
    print (mensaje) 

