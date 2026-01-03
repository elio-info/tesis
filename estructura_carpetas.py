import os
from pathlib import Path

def estructura_recursiva(directorio, archivo, nivel=0):
    """
    Versión recursiva que genera la estructura completa de carpetas
    nivel: profundidad actual (para indentación)
    max_profundidad: límite para evitar recursión infinita
    """
        
    # Carpetas que NO queremos explorar
    carpetas_excluidas = {'.vscode', 'venv', '__pycache__', '.git', '.idea'}
    
    prefijo = "    " * nivel  # Indentación según el nivel
    
    try:
        elementos = sorted(directorio.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        
        for item in elementos:
            if item.is_dir():
                # Verificar si la carpeta está en la lista de excluidas
                if item.name in carpetas_excluidas:
                    archivo.write(f"{prefijo}📁 {item.name}/\n")
                    continue  # Saltar esta carpeta, no explorar su contenido
                
                archivo.write(f"{prefijo}📁 {item.name}/\n")
                # Llamada recursiva para entrar en la subcarpeta
                estructura_recursiva(item, archivo, nivel + 1)
            else:
                archivo.write(f"{prefijo}📄 {item.name}\n")
                
    except PermissionError:
        archivo.write(f"{prefijo}[Acceso denegado]\n")

def generar_estructura_completa():
    """Genera la estructura completa de carpetas"""
    directorio_actual = Path.cwd()
    archivo_salida = "estructura_completa.txt"
    
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write(f"Estructura completa de: {directorio_actual}\n")
        f.write("=" * 50 + "\n\n")
        
        # Empezar la recursión desde el directorio actual
        estructura_recursiva(directorio_actual, f)
    
    print(f"Estructura completa guardada en: {archivo_salida}")

# Ejecutar la versión recursiva
generar_estructura_completa()