"""
Script de prueba para verificar que todos los módulos se importan correctamente
"""
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Probando imports de los módulos refactorizados...")

try:
    from ui.serial_reader import SerialReader
    print("✅ SerialReader importado correctamente")
except ImportError as e:
    print(f"❌ Error importando SerialReader: {e}")

try:
    from ui.ppg_processor import PPGProcessor
    print("✅ PPGProcessor importado correctamente")
except ImportError as e:
    print(f"❌ Error importando PPGProcessor: {e}")

try:
    from ui.widgets.acquisition_controls import AcquisitionControls
    print("✅ AcquisitionControls importado correctamente")
except ImportError as e:
    print(f"❌ Error importando AcquisitionControls: {e}")

try:
    from ui.acquisition_tab import AcquisitionTab
    print("✅ AcquisitionTab importado correctamente")
except ImportError as e:
    print(f"❌ Error importando AcquisitionTab: {e}")

try:
    from ui.interfaz2_refactored import PPGAnalyzerApp
    print("✅ PPGAnalyzerApp refactorizada importada correctamente")
except ImportError as e:
    print(f"❌ Error importando PPGAnalyzerApp refactorizada: {e}")

print("\n🎉 Prueba de imports completada!")
print("Si todos los módulos se importaron correctamente, la refactorización fue exitosa.")
