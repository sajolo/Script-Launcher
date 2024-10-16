import zipfile
import os
import pandas as pd
import py7zr
import rarfile

# Función para eliminar el archivo .csv después de procesarlo
def remove_csv_file(csv_file):
    if os.path.isfile(csv_file):
        os.remove(csv_file)
        print(f"El archivo CSV {csv_file} ha sido eliminado.")

# Función para procesar un archivo comprimido
def process_compressed_file(compressed_file, original_dir, target_dir):
    # Extraer el contenido del archivo comprimido basado en su tipo
    if compressed_file.endswith('.zip'):
        with zipfile.ZipFile(compressed_file, 'r') as zip_ref:
            zip_ref.extractall(original_dir)  # Extraer todos los archivos en el directorio original
    elif compressed_file.endswith('.7z'):
        with py7zr.SevenZipFile(compressed_file, mode='r') as z:
            z.extractall(path=original_dir)  # Extraer todos los archivos en el directorio original
    elif compressed_file.endswith('.rar'):
        with rarfile.RarFile(compressed_file, 'r') as rar_ref:
            rar_ref.extractall(original_dir)  # Extraer todos los archivos en el directorio original
    
    # Buscar el archivo CSV extraído en el directorio original
    csv_file = None
    for file in os.listdir(original_dir):
        if file.endswith('.csv'):  # Verificar si el archivo tiene extensión .csv
            csv_file = os.path.join(original_dir, file)  # Obtener la ruta completa del archivo CSV
            break  # Salir del bucle una vez encontrado el archivo CSV
    
    # Si no se encuentra ningún archivo CSV, imprimir un mensaje y salir de la función
    if not csv_file:
        print(f"No se encontró ningún archivo CSV después de la extracción de {compressed_file}.")
        return

    # Leer el archivo CSV utilizando pandas
    df = pd.read_csv(csv_file, delimiter=';', encoding='latin1', low_memory=False)
    
    # Dividir el archivo CSV en 4 partes iguales
    num_rows = len(df)  # Obtener el número total de filas en el archivo CSV
    part_size = num_rows // 4  # Calcular el tamaño de cada parte (número de filas por parte)
    
    # Crear y guardar las 4 partes del archivo CSV
    for i in range(4):
        start_index = i * part_size  # Calcular el índice de inicio para esta parte
        if i == 3:  # Para la última parte, tomar todas las filas restantes
            end_index = num_rows
        else:
            end_index = (i + 1) * part_size  # Calcular el índice de fin para esta parte
        
        part_df = df.iloc[start_index:end_index]  # Obtener el subconjunto de filas para esta parte
        part_filename = os.path.join(target_dir, f"{i+1}{os.path.basename(csv_file)}")  # Definir el nombre del archivo de salida
        part_df.to_csv(part_filename, index=False, sep=';', encoding='latin1')  # Guardar esta parte como un nuevo archivo CSV
    
    # Imprimir un mensaje indicando que el proceso ha finalizado correctamente
    print(f"Archivo CSV extraído de {compressed_file} y dividido exitosamente en 4 partes.")
    
    # Eliminar el archivo CSV después de procesarlo
    remove_csv_file(csv_file)

# Definir la función principal
def main():
    # Definir la ruta base
    base_dir = os.path.expanduser("~/Desktop/s02-ean/DataAcquisition/AFTERMARKET/_DIVIDIR_FICHEROS") # Sustituir por: r"//s02-ean/DataAcquisition/AFTERMARKET/_DIVIDIR_FICHEROS"
    
    # Definir la ruta donde se encuentran los archivos comprimidos originales
    original_dir = os.path.join(base_dir, "FICHERO_ORIGINAL") # Sustituir por: r"//s02-ean/DataAcquisition/AFTERMARKET/_DIVIDIR_FICHEROS/FICHERO_ORIGINAL"
    
    # Definir la ruta de destino donde se guardarán los archivos divididos
    target_dir = base_dir

    # Buscar y procesar todos los archivos comprimidos (zip, 7z, rar) en el directorio original
    compressed_files = [os.path.join(original_dir, file) for file in os.listdir(original_dir) if file.endswith(('.zip', '.7z', '.rar'))]
    
    if not compressed_files:
        print("No se encontró ningún archivo comprimido en FICHERO_ORIGINAL.")
        return
    
    for compressed_file in compressed_files:
        process_compressed_file(compressed_file, original_dir, target_dir)

# Ejecutar la función principal si este archivo es el archivo principal ejecutado
if __name__ == "__main__":
    main()
