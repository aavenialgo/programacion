# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 12:00:03 2022

@author: je_su
"""

archivo = open("./datos/archivo_texto.txt")
contenido = archivo.read()
print(contenido)
archivo.close()

#%%
with open("./datos/archivo_texto.txt") as arch:
    contenido = arch.readline()
    print(contenido)
    contenido = arch.readline()
    print(contenido)

print("mensaje adicional")

#%%

with open("./datos/archivo_texto.txt") as arch:
    for linea in arch:
        print(linea,end="")

#%%

with open("./datos/nombre.txt") as arch:
    l_arch = list(arch)

print(l_arch)     



#%%

with open("./datos/nombre.txt") as arch:
    l_arch = arch.readlines()

print(l_arch)


#%%
# mode 'w' y 'a' si no existe el archivo, lo crea

with open("./datos/archivo_nuevo.txt", mode='w') as arch:
    n=arch.write("Este es un archivo nuevo.\nArchivo de prueba.")
print(n)

#%% 

with open("./datos/archivo_nuevo.txt", mode='a') as arch:
    n=arch.write("\nAgrego una línea.")
print(n)
   
#%%

with open("./datos/archivo_nuevo.txt", mode='r+') as arch:
    arch.read()
    n=arch.write("\nAgrego contenido al final del archivo.")
print(n)       
        
#%%

with open("./datos/nombre.txt") as arch:
    for nro_linea,linea in enumerate(arch):
        print(f" {nro_linea}: {linea.strip()}")
