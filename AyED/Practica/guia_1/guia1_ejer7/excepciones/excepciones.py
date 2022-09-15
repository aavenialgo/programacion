# -*- coding: utf-8 -*-
"""
Created on Wed Aug 17 15:00:01 2022

@author: alumno
"""

class NotAlturaError(Exception):
    """NO se puede ingresar Zero o negativo en la altura"""

class NotPesoError(Exception):
    """No sepuede ingresar zero o negativo en el peso"""