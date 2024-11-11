import os
import tarfile
import csv
import pyxlsb
import mysql.connector
from datetime import datetime
import shutil

# Configuración para la conexión a la base de datos
DB_CONFIG = {
    'user': 'smarquez',
    'password': 'helvetia',
    'host': 'localhost',
    'database': 'app_db'
}

# Rutas de las carpetas principales
DOWNLOADS_PATH = r"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESCARGAS\PSA-OPEL"
PENDING_PATH = r"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESATENDIDA\Pendientes"
BASE_TARIFAS_PATH = r"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES"
TARIFA_POLICIA_PATH = r"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\CI1\ESP\FICHEROS_ORIGINALES\TARIFA_POLICIA.csv"
BRANDS = ['DS1', 'CI1', 'PE1', 'DA1', 'OP1']  # Lista de marcas del grupo PSA

# Conexión a la base de datos
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Obtener códigos ISO de la base de datos
def get_country_iso(psa_code):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT Country_ISO, PSA_Country_Code FROM gt_countries WHERE PSA_Country_Code = %s"
    cursor.execute(query, (psa_code,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result if result else (None, None)

# Obtener brand_code de la base de datos
def get_brand_code():
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT brand_code FROM gt_brands WHERE brand_name = 'Citroen'"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result[0] if result else None

# Extraer archivos tar.gz
def extract_tar_gz(file_path, extract_path):
    print(f"Descomprimiendo archivo {os.path.basename(file_path)}...")
    with tarfile.open(file_path, 'r:gz') as tar:
        tar.extractall(path=extract_path)

# Procesar referencia y reemplazo eliminando los primeros cuatro ceros bajo condiciones
def process_code(code):
    if code.startswith("0000") and len(code) > 6:
        code = code[4:]
    return code

# Procesar archivos XLSB y extraer los datos
def process_xlsb(file_path):
    data = []
    with pyxlsb.open_workbook(file_path) as wb:
        with wb.get_sheet(1) as sheet:
            for row in sheet.rows():
                referencia = row[1].v.strip() if row[1] else ''
                if referencia and referencia.isalnum() and 6 <= len(referencia) <= 11:
                    referencia = process_code(referencia)
                    precio = str(row[4].v).replace('.', ',') if row[4] else ''
                    reemplazo = row[6].v.strip() if row[6] and row[6].v.isalnum() else ''
                    reemplazo = process_code(reemplazo) if reemplazo else ''
                    data.append([referencia, '', precio, reemplazo])
    return data

# Cargar datos del archivo TARIFA_POLICIA.csv si el país es España (ESP)
def load_tarifa_policia():
    data = []
    if os.path.exists(TARIFA_POLICIA_PATH):
        with open(TARIFA_POLICIA_PATH, mode='rb') as file:
            try:
                reader = csv.reader(file.read().decode('ISO-8859-1').splitlines(), delimiter=';')
                for row in reader:
                    data.append(row)
            except UnicodeDecodeError:
                print("Error al leer TARIFA_POLICIA.csv. Revisa la codificación.")
    return data

# Guardar datos en archivo CSV y TXT
def save_data(data, country_iso, brand_code, date_str):
    csv_filename = f"{country_iso}_{brand_code}_{date_str}_C_tariffs_P.csv"
    csv_path = os.path.join(PENDING_PATH, csv_filename)

    # Guardar CSV
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerows(data)

    # Guardar TXT
    txt_filename = f"TARIFA_{brand_code}_{country_iso}.txt"
    txt_path = os.path.join(rf"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\{brand_code}\{country_iso}", txt_filename)
    os.makedirs(os.path.dirname(txt_path), exist_ok=True)
    with open(txt_path, mode='w', encoding='utf-8') as txt_file:
        for row in data:
            txt_file.write(';'.join(row) + '\n')

# Mover el archivo tar.gz a la carpeta de FICHEROS_ORIGINALES correspondiente
def move_tar_file(file_path, country_iso):
    dest_dir = os.path.join(rf"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\CI1\{country_iso}\FICHEROS_ORIGINALES")
    os.makedirs(dest_dir, exist_ok=True)
    shutil.move(file_path, dest_dir)
    print(f"Archivo {os.path.basename(file_path)} movido a {dest_dir}")

# Procesar archivos en la carpeta PSA-OPEL
def main():
    extract_path = os.path.join(DOWNLOADS_PATH, 'extracted')
    os.makedirs(extract_path, exist_ok=True)
    
    for file_name in os.listdir(DOWNLOADS_PATH):
        if file_name.endswith('.tar.gz'):
            file_path = os.path.join(DOWNLOADS_PATH, file_name)

            # Obtener el código de país y la fecha del nombre del archivo
            parts = file_name.split('_')
            if len(parts) < 5:
                print(f"Nombre de archivo no esperado: {file_name}")
                continue

            country_code = parts[3]
            date_str = file_name[18:26]

            try:
                date_obj = datetime.strptime(date_str, '%Y%m%d')
            except ValueError as e:
                print(f"Error de formato de fecha en el archivo {file_name}: {e}")
                continue

            if date_obj > datetime.today():
                print(f"Fecha en el archivo {file_name} es superior a la fecha actual.")
                continue

            # Obtener el código ISO del país y mostrar un mensaje una sola vez
            country_iso, _ = get_country_iso(country_code)
            if not country_iso:
                print(f"Código de país no encontrado para {country_code}")
                continue
            
            print(f"Procesando archivos para {country_iso}...")

            brand_code = get_brand_code()
            if not brand_code:
                print("Código de marca no encontrado.")
                continue

            extract_tar_gz(file_path, extract_path)

            for extracted_file in os.listdir(extract_path):
                if extracted_file.endswith('.xlsb'):
                    xlsb_path = os.path.join(extract_path, extracted_file)
                    data = process_xlsb(xlsb_path)
                    
                    if country_iso == "ESP":
                        data.extend(load_tarifa_policia())

                    if data:
                        # Guardar en la carpeta _DESATENDIDA\Pendientes y en cada marca de PSA
                        save_data(data, country_iso, brand_code, date_str)
                        for brand in BRANDS:
                            save_data(data, country_iso, brand, date_str)

            move_tar_file(file_path, country_iso)

    shutil.rmtree(extract_path)
    print("Proceso terminado, pulse ENTER para finalizar")
    input()

# Ejecutar el script
if __name__ == "__main__":
    main()
