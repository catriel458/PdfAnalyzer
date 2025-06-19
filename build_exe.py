import os
import subprocess
import shutil

def crear_ejecutable():
    print("=== CREACIÓN DE EJECUTABLE PORTABLE DEL ANALIZADOR DE PDFs ===")
    print("\nVerificando dependencias...")
   
    # Instalar PyInstaller si no está instalado
    try:
        import PyInstaller
        print("✅ PyInstaller ya está instalado.")
    except ImportError:
        print("📦 Instalando PyInstaller...")
        subprocess.check_call(['pip', 'install', 'pyinstaller'])
        print("✅ PyInstaller instalado correctamente.")
   
    # Verificar PyPDF2
    try:
        import PyPDF2
        print("✅ PyPDF2 ya está instalado.")
    except ImportError:
        print("📦 Instalando PyPDF2...")
        subprocess.check_call(['pip', 'install', 'PyPDF2'])
        print("✅ PyPDF2 instalado correctamente.")
   
    # Crear carpeta de salida si no existe
    if not os.path.exists('dist'):
        os.makedirs('dist')
   
    print("\n🔨 Creando ejecutable portable...")
    
    # Determinar el nombre del archivo Python
    python_file = 'analizador_pdfs.py'  # Cambia esto por el nombre de tu archivo
    
    if not os.path.exists(python_file):
        print(f"❌ Error: No se encontró el archivo '{python_file}'")
        print("Asegúrate de que el archivo esté en la misma carpeta que este script.")
        return
    
    # Comando PyInstaller
    cmd = [
        'pyinstaller',
        f'--name=AnalizadorPDFs',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        python_file
    ]
    
    # Agregar icono si existe
    if os.path.exists('icon.ico'):
        cmd.extend(['--icon=icon.ico', '--add-data=icon.ico;.'])
        print("🎨 Icono encontrado, será incluido en el ejecutable.")
    
    # Ejecutar PyInstaller
    try:
        subprocess.check_call(cmd)
        print("✅ Ejecutable creado correctamente.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al crear el ejecutable: {e}")
        return
   
    print("\n📁 Creando carpeta portable...")
    
    # Crear carpeta portable
    portable_dir = 'AnalizadorPDFs_Portable'
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    os.makedirs(portable_dir)
   
    # Copiar ejecutable
    exe_source = 'dist/AnalizadorPDFs.exe'
    if os.path.exists(exe_source):
        shutil.copy(exe_source, portable_dir)
        print("✅ Ejecutable copiado a la carpeta portable.")
    else:
        print("❌ Error: No se encontró el ejecutable generado.")
        return
   
    # Crear archivo README
    with open(os.path.join(portable_dir, 'INSTRUCCIONES.txt'), 'w', encoding='utf-8') as f:
        f.write("""📋 ANALIZADOR DE PDFs - VERSIÓN PORTABLE
==========================================

🎯 DESCRIPCIÓN:
Este programa permite analizar archivos PDF buscando palabras clave específicas
y mover automáticamente los archivos que cumplen criterios a una carpeta organizada.

🚀 CÓMO USAR:
1. Ejecute "AnalizadorPDFs.exe" haciendo doble clic
2. En la interfaz del programa:
   • Agregue criterios de búsqueda (conjuntos de palabras)
   • Seleccione los archivos PDF a analizar
   • Haga clic en "🔍 ANALIZAR PDFs"
3. Los PDFs que cumplan criterios se moverán a "PDFs Encontrados" en el escritorio

💡 EJEMPLOS DE CRITERIOS:
- "factura, pagada" → Busca PDFs con AMBAS palabras
- "contrato" → Busca PDFs con esta palabra
- "reporte, mensual" → Busca PDFs con AMBAS palabras

📁 ARCHIVOS GENERADOS:
- Los PDFs encontrados van a: "PDFs Encontrados" (escritorio)
- Se genera un reporte detallado del análisis

🔧 REQUISITOS:
- Windows 10 o superior
- Si hay problemas al iniciar, instale Visual C++ Redistributable:
  https://aka.ms/vs/17/release/vc_redist.x64.exe

❓ AYUDA:
Use el botón "❓ Ayuda" dentro del programa para más información.

Desarrollado con Python + tkinter + PyPDF2
""")
   
    print(f"\n🎉 ¡EJECUTABLE PORTABLE CREADO CON ÉXITO!")
    print(f"📂 Carpeta: '{portable_dir}'")
    print(f"🚀 Para usar: Ejecute 'AnalizadorPDFs.exe' dentro de la carpeta")
    print(f"📋 Lea 'INSTRUCCIONES.txt' para más detalles")

if __name__ == "__main__":
    crear_ejecutable()