import subprocess
import sys
import os
import glob

def run_command(cmd):
    """Ejecuta un comando y maneja errores."""
    print(f"Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error al ejecutar: {cmd}")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        sys.exit(1)
    print(result.stdout)
    return result

def eliminar_archivos():
    """Elimina los archivos de base de datos y migraciones iniciales."""
    
    # Eliminar db.sqlite3
    db_file = "db.sqlite3"
    if os.path.exists(db_file):
        print(f"Eliminando: {db_file}")
        os.remove(db_file)
        print(f"✓ {db_file} eliminado")
    else:
        print(f"ℹ {db_file} no encontrado, continuando...")
    
    # Buscar y eliminar 0001_initial.py en cualquier carpeta migrations
    # Primero buscar en la ruta específica app/migrations
    initial_migration_specific = "app/migrations/0001_initial.py"
    
    if os.path.exists(initial_migration_specific):
        print(f"Eliminando: {initial_migration_specific}")
        os.remove(initial_migration_specific)
        print(f"✓ {initial_migration_specific} eliminado")
    else:
        # Buscar en todas las carpetas migrations del proyecto
        initial_migrations = glob.glob("**/migrations/0001_initial.py", recursive=True)
        
        for migration_file in initial_migrations:
            print(f"Eliminando: {migration_file}")
            os.remove(migration_file)
            print(f"✓ {migration_file} eliminado")
        
        if not initial_migrations:
            print("ℹ No se encontraron archivos 0001_initial.py, continuando...")
    
    # También eliminar cualquier archivo __pycache__ en migraciones para limpieza completa
    pycache_dirs = glob.glob("**/migrations/__pycache__", recursive=True)
    for pycache_dir in pycache_dirs:
        print(f"Limpiando: {pycache_dir}")
        # Eliminar todos los archivos .pyc en __pycache__
        pyc_files = glob.glob(os.path.join(pycache_dir, "*.pyc"))
        for pyc_file in pyc_files:
            os.remove(pyc_file)
        print(f"✓ {pycache_dir} limpiado")

def main():
    print("=== LIMPIEZA Y MIGRACIÓN DE BASE DE DATOS ===\n")
    
    # Paso 0: Eliminar archivos antiguos
    print("1. Limpiando archivos antiguos...")
    eliminar_archivos()
    print()
    
    # Paso 1: makemigrations
    print("2. Creando nuevas migraciones...")
    run_command("python manage.py makemigrations")
    print()
    
    # Paso 2: migrate
    print("3. Aplicando migraciones...")
    run_command("python manage.py migrate")
    print()
    
    # Paso 3: loaddata
    print("4. Cargando datos iniciales...")
    run_command("python manage.py loaddata datos.json")
    print()
    
    print("¡Proceso completado con éxito!")
    print("Base de datos reiniciada con datos iniciales.")

if __name__ == "__main__":
    main()