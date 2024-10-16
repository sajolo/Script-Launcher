import os
import pandas as pd
from collections import defaultdict

# Función para unir las partes de un archivo CSV en un solo archivo
def join_csv_files(base_dir):
    # Diccionario para agrupar las partes del mismo archivo
    grouped_files = defaultdict(list)

    # Buscar todos los archivos CSV en el directorio
    for file in os.listdir(base_dir):
        if file.endswith('.csv') and (file.startswith('1') or file.startswith('2') or file.startswith('3') or file.startswith('4')):
            # Eliminar el prefijo de número para obtener el nombre base del archivo
            base_name = file[1:]
            grouped_files[base_name].append(file)
    
    # Unir las partes de cada archivo y guardarlas en un nuevo archivo
    for base_name, parts in grouped_files.items():
        # Ordenar las partes por el prefijo numérico para asegurar el orden correcto
        parts.sort(key=lambda x: int(x[0]))

        # Lista para almacenar los DataFrames de las partes
        df_list = []
        
        for part in parts:
            part_path = os.path.join(base_dir, part)
            df = pd.read_csv(part_path, delimiter=';', encoding='latin1', low_memory=False)
            df_list.append(df)
        
        # Concatenar todas las partes en un solo DataFrame
        joined_df = pd.concat(df_list, ignore_index=True)
        
        # Guardar el DataFrame unido en un nuevo archivo CSV
        joined_filename = os.path.join(base_dir, f"joined_{base_name}")
        joined_df.to_csv(joined_filename, index=False, sep=';', encoding='latin1')
        
        # Imprimir un mensaje indicando que el archivo ha sido unido correctamente
        print(f"El archivo {joined_filename} ha sido creado exitosamente a partir de {len(parts)} partes.")

# Definir la función principal
def main():
    # Definir la ruta base (debe ser la misma que _DIVIDIR_FICHEROS)
    base_dir = os.path.expanduser("~/Desktop/s02-ean/DataAcquisition/AFTERMARKET/_DIVIDIR_FICHEROS") # Sustituir por: r"//s02-ean/DataAcquisition/AFTERMARKET/_DIVIDIR_FICHEROS"
    
    # Llamar a la función para unir los archivos CSV
    join_csv_files(base_dir)

# Ejecutar la función principal si este archivo es el archivo principal ejecutado
if __name__ == "__main__":
    main()
