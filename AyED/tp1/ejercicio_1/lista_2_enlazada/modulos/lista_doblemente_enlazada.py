# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 11:02:26 2022

@author: Venialgo Andres
"""
from nodo import Nodo
class lista_doblemente_enlazada:
    def __init__ (self):
        # self.__nodo = Nodo(dato_inicial)
        self.cabeza = None
        self.cola = None
        self.tamano = 0
    
        
    
    def estaVacia(self):
        return self._cabeza == None
    
    
    def agregar(self,item):
        """Agrega un elemento al principio (cabeza) de la lista """
        temp= Nodo(item)
        
        if self.tamano == 0:    
            self.cabeza = temp
            self.cola = temp
        else:
        
            temp = Nodo(item)
            temp.siguiente = self.cabeza
            self.cabeza.anterior = temp
            self.cabeza= temp
        self.tamano+=1 
        
    def anexar(self, item):
        """ Agrega un elemento al final (cola) de la lista """
        temp = Nodo(item)
        
        if self.tamano == 0:    
            self.cabeza = temp
            self.cola = temp
        else:
            self.cola.anterior.siguiente = temp
            temp.anterior = self.cola.anterior
            temp.siguiente = self.cola
            self.cola.anterior = temp
        self.tamano +=1
    
    def insertar(self, pos, item):
        """Agrega un elemento en la posicion "pos" """
        
        nuevo = Nodo(item)
        temp = self.cabeza
        for it in range(pos-1):
            temp = temp.siguiente
        nuevo.siguiente = temp.siguiente
        temp.siguiente.anterior = nuevo
        temp.siguiente = nuevo
        nuevo.anterior = temp 
        self.tamano +=1
        
    
    def extraer(self, pos ):
        dato = 0
        
        if pos == 0:
           dato = self.cabeza.dato
           self.cabeza = self.cabeza.siguiente
           self.cabeza.anterior = None
        elif pos == (self.tamano -1):
            dato = self.cola.dato
            self.cola = self.cola.anterior
            self.cola.siguiente = None
        else:
            temp = self.cabeza
            for it in range(pos-1):
                temp = temp.siguiente
            dato   = temp.dato
            temp.anterior.siguiente = temp.siguiente
            temp.siguiente.anterior = temp.anterior
        
        return dato
           
    
            
    @property
    def tamano(self):
        return self._tamano
    
    @tamano.setter
    def tamano(self,item):
        self._tamano = item 
        
    def __iter__(self):
        """metodo para iterar """
        nodo = self.cabeza
        while nodo:
            yield nodo
            nodo = nodo.siguiente
            
            
    def esta_vacia(self):
        return self.tamano == 0
        
    def __str__ (self):
        lista =[nodo for nodo in self ]
        return str(lista)
        
if __name__ == '__main__':
    lista2= lista_doblemente_enlazada()
    lista2.agregar(10)
    lista2.agregar(20)
    lista2.agregar(40)
    print(lista2)

    print("\nInserto el valor 30 en la pos 1")
    lista2.insertar(1,30)
    print(lista2)
    
    print("\nagrego el valor 50")
    lista2.agregar(50)
    print(lista2)
    
    print("\nextraigo el elemento 4")
    lista2.extraer(4)
    print (lista2)
    
    print("\nextraigo el primer elemento\n")
    lista2.extraer(0)
    print (lista2)

    print ("\nextraigo el ultimo elemento")
    lista2.extraer(lista2.tamano-1)
    print (lista2)

    
    

    