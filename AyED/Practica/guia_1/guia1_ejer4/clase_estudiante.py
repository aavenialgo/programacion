# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 14:34:01 2022
Implementar una clase Estudiante, para almacenar sus 
datos personales (legajo, apellido y nombre, documento 
y promedio). Leer los datos de un archivo de texto, cada 
elemento se encuentra separado por comas. Agregar cada 
registro de un objeto tipo Estudiante, almacenarlos en una
lista y mostrar los datos ordenados por legajo.
@author: Andres Venialgo
"""

class Estudiante:
    def __init__(self):
        
        self._nombre = ''
        self._apellido =''
        self._legajo = 0
        self._documento = 0
        self._promedio = 0
        
    @property
    def legajo(self):
        return self._legajo
    
    @legajo.setter
    def legajo (self, p_legajo):
        self._legajo = p_legajo
        
    @property 
    def nombre(self):
        return self._nombre
    @nombre.setter
    def nombre(self, p_nombre):
        self._nombre = p_nombre
        
    @property
    def apellido(self):
        return self._apellido
    
    @apellido.setter
    def apellido(self, p_apellido):
        self._apellido = p_apellido
        
    @property 
    def documento(self):
        return self._documento
    
    @documento.setter
    def documento(self, p_documento):
        self._documento = p_documento
        
    @property 
    def promedio(self):
        """ El promedio es
        """
        return self._promedio
     
    @promedio.setter
    def promedio(self, p_promedio):
        self._promedio = p_promedio
        
if __name__ == '__main__':
    print('hola mundo')
    alumno = Estudiante()
    alumno.legajo = 2
    print(alumno.legajo)
    alumno.promedio = 10
    print (alumno.promedio)
    # alumno.apellido('Venialgo')
    # print (alumno.apellido)
        
        