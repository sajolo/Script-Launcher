import os
import shutil
import subprocess

# Directorios donde se encuentran los .py a convertir
TARIFAS_DIR = r"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\Script-Launcher\Scripts-formateo-datos\Scripts-tarifas"
AFT_DIR = r"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\Script-Launcher\Scripts-formateo-datos\Scripts-AFT"

def compile_scripts_in_folder(folder_path):
    """
    Busca todos los .py en la carpeta 'folder_path',
    genera ejecutables con PyInstaller (modo consola por defecto),
    mueve el .exe resultante a la carpeta original,
    y elimina build, dist y el archivo .spec.
    """

    # Guardamos el directorio de trabajo actual para volver al final
    original_cwd = os.getcwd()

    # Obtenemos todos los ficheros .py en la carpeta
    all_files = os.listdir(folder_path)
    python_scripts = [f for f in all_files if f.endswith(".py")]

    for script in python_scripts:
        # Cambiamos el directorio actual a la carpeta donde está el script
        os.chdir(folder_path)

        # Llamamos a PyInstaller para compilar el script
        # --onefile: genera un único ejecutable
        # (no usamos --noconsole para que aparezca ventana de consola al ejecutar .exe)
        print(f"Compilando {script} en {folder_path}...")
        subprocess.run(["pyinstaller", "--onefile", script], check=True)

        # Nombre esperado del ejecutable (igual que el .py pero con .exe)
        exe_name = os.path.splitext(script)[0] + ".exe"

        # Movemos el .exe desde dist/ a la carpeta principal
        dist_path = os.path.join(folder_path, "dist", exe_name)
        if os.path.exists(dist_path):
            print(f"Moviendo {exe_name} a {folder_path}...")
            shutil.move(dist_path, os.path.join(folder_path, exe_name))
        else:
            print(f"No se encontró el ejecutable esperado: {dist_path}")

        # Borramos la carpeta build, dist y el .spec
        build_dir = os.path.join(folder_path, "build")
        dist_dir = os.path.join(folder_path, "dist")
        spec_file = os.path.splitext(script)[0] + ".spec"

        if os.path.exists(build_dir):
            print(f"Eliminando {build_dir}...")
            shutil.rmtree(build_dir, ignore_errors=True)

        if os.path.exists(dist_dir):
            print(f"Eliminando {dist_dir}...")
            shutil.rmtree(dist_dir, ignore_errors=True)

        spec_path = os.path.join(folder_path, spec_file)
        if os.path.exists(spec_path):
            print(f"Eliminando {spec_path}...")
            os.remove(spec_path)

        print(f"Finalizado {script}.\n")

    # Volvemos al directorio de trabajo original
    os.chdir(original_cwd)

def main():
    print("Iniciando proceso de compilación de scripts en ambas carpetas...\n")

    # 1. Compilar scripts en carpeta de Tarifas
    compile_scripts_in_folder(TARIFAS_DIR)

    # 2. Compilar scripts en carpeta de AFT
    compile_scripts_in_folder(AFT_DIR)

    print("Proceso de compilación completado.")

if __name__ == "__main__":
    main()
