# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 11:03:18 2022

@author: alumno
"""

class Nodo:
    def __init__(self,datoInicial):
        self.dato = datoInicial
        self.siguiente = None
        self.anterior = None
        
    
    
    
    @property
    def dato(self):
        return self._dato
    
    @dato.setter
    def dato(self,nuevodato):
        self._dato = nuevodato
    
    @property
    def siguiente(self):
        return self._siguiente

    
    @siguiente.setter
    def siguiente(self,nuevosiguiente):
        self._siguiente = nuevosiguiente
        
    @property
    def anterior(self):
        return self._anterior
    @anterior.setter
    def anterior(self, item):
        self._anterior = item
        
    def __str__(self):
        return  str(self.dato)
    
    def __repr__(self):
        return  str(self.dato)
