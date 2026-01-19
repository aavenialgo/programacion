"""
Script para generar documentación automática con Sphinx
"""
import os
import sys
import subprocess
import shutil

def setup_sphinx():
    """Configura Sphinx en el proyecto"""
    print("🔧 Configurando Sphinx...")
    
    # Crear directorio docs si no existe
    if not os.path.exists('docs'):
        os.makedirs('docs')
    
    # Ejecutar sphinx-quickstart con configuración automática
    os.chdir('docs')
    
    # Configuración automática
    config = {
        'project': 'Python Serial Realtime App',
        'author': 'Tu Nombre',
        'release': '1.0',
        'language': 'es',
        'sep': False,  # No separar source y build
        'dot': '_',
        'suffix': '.rst',
        'master': 'index',
        'epub': False,
        'ext_autodoc': True,
        'ext_doctest': False,
        'ext_intersphinx': True,
        'ext_todo': True,
        'ext_coverage': False,
        'ext_imgmath': False,
        'ext_mathjax': True,
        'ext_ifconfig': True,
        'ext_viewcode': True,
        'ext_githubpages': False,
        'makefile': True,
        'batchfile': True,
    }
    
    os.chdir('..')
    print("✅ Sphinx configurado")

def create_conf_py():
    """Crea el archivo de configuración conf.py personalizado"""
    print("📝 Creando conf.py...")
    
    conf_content = """
# Configuration file for the Sphinx documentation builder.

import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------
project = 'Python Serial Realtime App'
copyright = '2026, Tu Nombre'
author = 'Tu Nombre'
release = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
language = 'es'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Napoleon settings -------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# -- Autodoc settings --------------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
"""
    
    with open('docs/conf.py', 'w', encoding='utf-8') as f:
        f.write(conf_content)
    
    print("✅ conf.py creado")

def create_index_rst():
    """Crea el archivo index.rst principal"""
    print("📝 Creando index.rst...")
    
    index_content = """
Documentación de Python Serial Realtime App
============================================

Aplicación para adquisición y análisis de señales PPG en tiempo real.

.. toctree::
   :maxdepth: 2
   :caption: Contenidos:

   modules/core
   modules/data
   modules/ui

Índices y tablas
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
"""
    
    os.makedirs('docs/modules', exist_ok=True)
    
    with open('docs/index.rst', 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print("✅ index.rst creado")

def create_module_rst(module_name, submodules):
    """Crea archivos RST para cada módulo"""
    print(f"📝 Creando documentación para módulo {module_name}...")
    
    content = f"""
Módulo {module_name}
{'=' * (7 + len(module_name))}

.. automodule:: {module_name}
   :members:
   :undoc-members:
   :show-inheritance:

"""
    
    # Agregar submódulos
    if submodules:
        content += "\nSubmódulos\n----------\n\n"
        for submodule in submodules:
            content += f"""
{submodule}
{'~' * len(submodule)}

.. automodule:: {module_name}.{submodule}
   :members:
   :undoc-members:
   :show-inheritance:

"""
    
    with open(f'docs/modules/{module_name}.rst', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Documentación de {module_name} creada")

def scan_modules():
    """Escanea la estructura de módulos en src/"""
    print("🔍 Escaneando módulos en src/...")
    
    modules = {}
    src_path = 'src'
    
    for item in os.listdir(src_path):
        item_path = os.path.join(src_path, item)
        if os.path.isdir(item_path) and not item.startswith('__'):
            submodules = []
            for subitem in os.listdir(item_path):
                if subitem.endswith('.py') and subitem != '__init__.py':
                    submodules.append(subitem[:-3])
            modules[item] = submodules
    
    print(f"✅ Encontrados {len(modules)} módulos principales")
    return modules

def generate_docs():
    """Genera la documentación HTML"""
    print("🏗️  Generando documentación HTML...")
    
    os.chdir('docs')
    
    # Limpiar build anterior
    if os.path.exists('_build'):
        shutil.rmtree('_build')
    
    # Generar documentación
    result = subprocess.run(['sphinx-build', '-b', 'html', '.', '_build/html'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Documentación generada exitosamente")
        print(f"📂 Los archivos están en: docs/_build/html/index.html")
    else:
        print("❌ Error generando documentación:")
        print(result.stderr)
    
    os.chdir('..')

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 Generador de Documentación con Sphinx")
    print("=" * 60)
    
    # Verificar que estamos en la raíz del proyecto
    if not os.path.exists('src'):
        print("❌ Error: No se encuentra la carpeta 'src'")
        print("   Ejecuta este script desde la raíz del proyecto")
        sys.exit(1)
    
    # Crear estructura de documentación
    if not os.path.exists('docs/conf.py'):
        setup_sphinx()
        create_conf_py()
        create_index_rst()
    
    # Escanear y crear documentación de módulos
    modules = scan_modules()
    for module_name, submodules in modules.items():
        create_module_rst(module_name, submodules)
    
    # Generar HTML
    generate_docs()
    
    print("\n" + "=" * 60)
    print("✨ ¡Proceso completado!")
    print("=" * 60)
    print("\n💡 Para ver la documentación, abre:")
    print(f"   file:///{os.path.abspath('docs/_build/html/index.html')}")

if __name__ == '__main__':
    main()