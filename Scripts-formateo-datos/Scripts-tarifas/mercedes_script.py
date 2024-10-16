import os
import zipfile
import rarfile
import py7zr
import xml.etree.ElementTree as ET
import pandas as pd
import shutil
import mysql.connector 

# Directorios (CAMBIAR RUTAS PARA QUE FUNCIONE EN LA RED)
"""
BASE_DIR = r'\\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESCARGAS\MERCEDES'
MB1_DIR = r'\\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\MB1'
SM1_DIR = r'\\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\SM1'
PEND_DIR = r'\\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESATENDIDA\Pendientes'
"""

BASE_DIR = r'C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESCARGAS\MERCEDES'
MB1_DIR = r'C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\MB1'
SM1_DIR = r'C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\SM1'
PEND_DIR = r'C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESATENDIDA\Pendientes'

# Configuración de la base de datos MySQL <-- ACTUALIZAR CONFIGURACIÓN EN LA BBDD
DB_CONFIG = {
    'user': 'root',
    'password': 'GHIbln209-',
    'host': 'localhost',
    'database': 'app_db',
}

# Función para descomprimir archivos
def descomprimir_archivos(base_dir):
    print("Descomprimiendo archivos...")
    for archivo in os.listdir(base_dir):
        archivo_path = os.path.join(base_dir, archivo)
        if archivo.endswith('.zip'):
            with zipfile.ZipFile(archivo_path, 'r') as zip_ref:
                zip_ref.extractall(base_dir)
        elif archivo.endswith('.rar'):
            with rarfile.RarFile(archivo_path, 'r') as rar_ref:
                rar_ref.extractall(base_dir)
        elif archivo.endswith('.7z'):
            with py7zr.SevenZipFile(archivo_path, 'r') as zip_ref:
                zip_ref.extractall(base_dir)

# Función para intentar procesar archivos sin extensión como si fuesen XML
def procesar_archivo_sin_extension(file_path):
    with open(file_path, 'r', encoding='ISO-8859-1') as file:
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            return root
        except ET.ParseError:
            return None

# Función para procesar el archivo XML
def procesar_xml(root):
    datos = []

    # Procesar cada conjunto de datos (SET) en el archivo XML
    for set_element in root.findall('SET'):
        referencia = set_element.find('TNR').text.replace(' ', '')
        descripcion = ''
        precio = set_element.find('PLA').text.replace('.', ',')
        reemplazo = set_element.find('NTN').text.replace(' ', '') if set_element.find('NTN').text else ''
        datos.append([referencia, descripcion, precio, reemplazo])

    fecha = root.find('DATE').text.split()[0]
    fecha = fecha[-4:] + fecha[3:5] + fecha[:2]  # Convertir DD.MM.YYYY a YYYYMMDD
    gt_code = root.find('COUNTRY').text  # <-- ASEGURAR QUE gt_code SE OBTIENE CORRECTAMENTE EN LA FUNCIÓN procesar_xml
    return datos, fecha, gt_code

# Función para obtener el Country_ISO desde la base de datos <-- ACTUALIZAR ESTA FUNCIÓN SEGÚN LA ESTRUCTURA DE LA TABLA
def obtener_iso_code(gt_code):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT Country_ISO FROM gt_countries WHERE Mercedes_Country_Code = %s", (gt_code,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Función para generar el archivo CSV utilizando el módulo pandas
def generar_csv(datos, fecha, pais):
    csv_filename = f'{pais}_MB1_{fecha}_C_tariffs_P.csv'
    csv_path = os.path.join(PEND_DIR, csv_filename)
    df = pd.DataFrame(datos, columns=['Referencia', 'Descripcion', 'Precio', 'Reemplazo'])
    df.to_csv(csv_path, sep=';', index=False, header=False)
    return csv_path

# Función para generar el archivo TXT
def generar_txt(datos, fecha, base_dir, pais):
    txt_filename = f'TARIFA_MB1-SM1_{pais}.txt'
    txt_path = os.path.join(base_dir, pais, txt_filename)
    os.makedirs(os.path.join(base_dir, pais), exist_ok=True)
    with open(txt_path, mode='w', encoding='utf-8') as file:
        for row in datos:
            file.write(';'.join(row) + '\n')
    return txt_path

# Función para gestionar los archivos generados
def gestionar_archivos(csv_path, txt_path, pend_dir, pais):
    # Crear directorios si no existen
    os.makedirs(pend_dir, exist_ok=True)
    
    # Copiar CSV a _DESATENDIDA\Pendientes
    pendientes_csv_dest = os.path.join(pend_dir, os.path.basename(csv_path))
    if csv_path != pendientes_csv_dest:
        shutil.copy(csv_path, pendientes_csv_dest)
    
    # Renombrar y copiar CSV a _DESATENDIDA\Pendientes con SM1
    sm1_csv_dest = pendientes_csv_dest.replace('MB1', 'SM1')
    if pendientes_csv_dest != sm1_csv_dest:
        shutil.copy(pendientes_csv_dest, sm1_csv_dest)

    # Copiar TXT a MB1 y SM1
    mb1_txt_dest = os.path.join(MB1_DIR, pais, os.path.basename(txt_path))
    sm1_txt_dest = os.path.join(SM1_DIR, pais, os.path.basename(txt_path))
    
    os.makedirs(os.path.join(MB1_DIR, pais), exist_ok=True)
    os.makedirs(os.path.join(SM1_DIR, pais), exist_ok=True)
    
    if txt_path != mb1_txt_dest:
        shutil.copy(txt_path, mb1_txt_dest)
    if txt_path != sm1_txt_dest:
        shutil.copy(txt_path, sm1_txt_dest)

# Función principal
def main():
    descomprimir_archivos(BASE_DIR)
    
    for archivo in os.listdir(BASE_DIR):
        archivo_path = os.path.join(BASE_DIR, archivo)
        if archivo.endswith('.xml'):
            tree = ET.parse(archivo_path)
            root = tree.getroot()
        elif not archivo.endswith(('.zip', '.rar', '.7z', '.py')):
            root = procesar_archivo_sin_extension(archivo_path)
        else:
            root = None

        if root:
            datos, fecha, gt_code = procesar_xml(root)
            pais = obtener_iso_code(gt_code)
            if not pais:
                print(f"No se encontró el código ISO para el código Mercedes {gt_code}")
                continue
            print(f"Generando archivos para {pais}...")
            csv_path = generar_csv(datos, fecha, pais)
            txt_path = generar_txt(datos, fecha, MB1_DIR, pais)
            gestionar_archivos(csv_path, txt_path, PEND_DIR, pais)

    print("Archivos listos, presione Enter para finalizar")
    input()

if __name__ == "__main__":
    main()
