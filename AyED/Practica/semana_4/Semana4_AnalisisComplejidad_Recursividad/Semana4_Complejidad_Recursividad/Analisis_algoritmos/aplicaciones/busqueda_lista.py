# -*- coding: utf-8 -*-
"""
Created on Wed Aug 24 13:26:15 2022

@author: je_su
"""

import random
import time
import matplotlib.pyplot as plt

valores_n = [10**i for i in range(1,7)]
tiempos = [[],[]]

def buscar_item(lista, item):
    encontrado = False
    i = 0
    while i < len(lista) and not encontrado:
        if item == lista[i]:
            encontrado = True
        i += 1
        
    return encontrado 


def busqueda_binaria(lista, item):
    encontrado = False
    primero = 0
    ultimo = len(lista)-1
    
    while primero<= ultimo and not encontrado:
        
        punto_medio = (primero + ultimo) //2
        if lista[punto_medio] == item:
            encontrado == True
        elif lista[punto_medio] < item:
            primero = punto_medio + 1
        else:
            ultimo = punto_medio -1
    
    return encontrado
        

for n in valores_n:
    
    lista = sorted([random.randint(-100, 100) for _ in range(n)])
    tic = time.perf_counter()
    buscar_item(lista, 500)
    toc = time.perf_counter()
    tiempos[0].append(toc-tic)
    
    tic = time.perf_counter()
    busqueda_binaria(lista, 500)
    toc = time.perf_counter()
    tiempos[1].append(toc-tic)
    


plt.clf()
plt.plot(valores_n, tiempos[0], label="búsqueda secuencial")
plt.plot(valores_n, tiempos[1], label="búsqueda binaria")
#plt.yscale('log')
plt.xlabel("tamaños de la lista")
plt.ylabel("tiempos del algoritmo")
plt.title("Tiempos en fn. del nro de elementos")
plt.legend()
