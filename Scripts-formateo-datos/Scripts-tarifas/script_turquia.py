import os
import ftplib
import shutil
import zipfile
import pandas as pd
import mysql.connector
from datetime import datetime

# Configuración de la base de datos MySQL
DB_CONFIG = {
    'user': 'smarquez',
    'password': 'helvetia',
    'host': 'localhost',
    'database': 'app_db',
}

# Función para obtener los datos de conexión FTP desde la base de datos
def obtener_datos_ftp():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Address, Port, Protocol, User, Password FROM ftp_conn_data WHERE Id = 'TURKEY_TEST'")  # Cambia 'TURKEY_TEST' a 'TURKEY' cuando lo uses en la empresa
    row = cursor.fetchone()
    conn.close()

    if row:
        ftp_host = row['Address']
        ftp_port = row['Port']
        protocolo = row['Protocol']
        ftp_user = row['User']
        ftp_pass = row['Password']

        # Determinar si es SFTP o FTP
        is_sftp = protocolo.upper() == 'SFTP'
        if protocolo.upper() == 'NFTP':
            ftp_port = 21  # Puerto por defecto para FTP si no se especifica
        elif is_sftp:
            ftp_port = 22  # Puerto por defecto para SFTP si no se especifica

        return ftp_host, ftp_port, is_sftp, ftp_user, ftp_pass
    else:
        raise ValueError("No se encontraron datos de conexión FTP para el Id 'TURKEY_TEST'")  # Cambiar a 'TURKEY' en la red de la empresa

# Función para conectarse al servidor FTP y descargar archivos TXT
def descargar_archivos_ftp(ftp_host, ftp_user, ftp_pass, obtener_destino, is_sftp=False):
    # Conexión FTP o SFTP
    print(f"Conectando al servidor {'SFTP' if is_sftp else 'FTP'} en {ftp_host}...")

    if is_sftp:
        import paramiko
        transport = paramiko.Transport((ftp_host, ftp_port))
        transport.connect(username=ftp_user, password=ftp_pass)
        sftp = paramiko.SFTPClient.from_transport(transport)
        files = sftp.listdir()
    else:
        ftp = ftplib.FTP(ftp_host)
        ftp.login(ftp_user, ftp_pass)
        ftp.cwd('/FTP')  # Asumiendo que los archivos están en la carpeta /FTP
        files = ftp.nlst()

    for file in files:
        if file.endswith('.txt'):
            print(f"Descargando el archivo {file}...")
            nombre_marca = file.split('.')[0].upper()  # Obtener el nombre de la marca desde el nombre del archivo
            destino_dir, brand_code, procesar = obtener_destino(nombre_marca)

            if destino_dir:
                # Caso especial para la marca Ford
                if brand_code == 'FR1':
                    local_path = os.path.join(destino_dir, file)

                    if is_sftp:
                        sftp.get(file, local_path)
                        sftp.remove(file)
                    else:
                        with open(local_path, 'wb') as f:
                            ftp.retrbinary(f"RETR {file}", f.write)
                        ftp.delete(file)

                    print(f"Archivo para Ford descargado en la ruta correspondiente, debe procesarse con otra herramienta")
                    continue #Saltar el resto de procesamiento para Ford

                os.makedirs(destino_dir, exist_ok=True)
                local_path = os.path.join(destino_dir, file)

                if is_sftp:
                    sftp.get(file, local_path)
                else:
                    with open(local_path, 'wb') as f:
                        ftp.retrbinary(f"RETR {file}", f.write)

                if procesar:
                    print(f"Procesando el archivo {file} para la marca {brand_code}...")
                    procesar_archivo(local_path, brand_code)

                # Comprimir archivo después de procesar
                fecha_str = datetime.now().strftime('%Y%m%d')  # Utilizar la fecha actual para nombrar el archivo ZIP
                comprimir_txt_a_zip(local_path, fecha_str)

                # Eliminar archivo del servidor después de procesar y comprimir
                if is_sftp:
                    sftp.remove(file)
                    print(f"Archivo eliminado del servidor SFTP: {file}")
                else:
                    ftp.delete(file)
                    print(f"Archivo eliminado del servidor FTP: {file}")
            else:
                print(f"No se reconoce ese nombre de la marca en ninguna entrada de la columna Turkey_Brand_Name: {nombre_marca}")

    if is_sftp:
        sftp.close()
        transport.close()
    else:
        ftp.quit()

    print("Descarga desde el servidor y eliminación de archivos finalizada.")


# Función para obtener el brand_code, el estado de activación, y la ruta de destino desde la base de datos
def obtener_destino(nombre_marca):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT brand_code, Activated FROM gt_brands WHERE Turkey_Brand_Name = %s", (nombre_marca,))
    row = cursor.fetchone()
    conn.close()

    if row:
        brand_code, activated = row
        if activated == 0:
            destino_dir = r'C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESCARGAS\TURQUIA\not_used'  # Cambia esta ruta a: '\\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESCARGAS\TURQUIA\not_used' en la empresa
            return destino_dir, brand_code, False
        else:
            destino_dir = os.path.join(r'C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES', brand_code, 'TUR', 'FICHEROS_ORIGINALES')  # Cambia esta ruta a: '\\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\[brand_code]\TUR\FICHEROS_ORIGINALES' en la empresa
            return destino_dir, brand_code, True
    else:
        return None, None, False

# Función para formatear las referencias de acuerdo con las reglas del grupo y marca
def formatear_referencia(referencia, brand_code):
    # Grupos y reglas específicas de formato
    grupos_formatos = {
        'FIAT': {'marcas': ['AR1', 'FI1', 'JE1', 'LA1'], 'longitud': 13, 'relleno': '0'},
        'AUDI': {'marcas': ['AU1', 'SE1', 'SK1', 'VW1'], 'longitud_min': 9, 'longitud_max': 14, 'espacios_pos': [10, 11]},
        'PSA': {'marcas': ['DS1', 'CI1', 'PE1', 'DA1', 'OP1'], 'longitud_min': 6, 'longitud_max': 11},
        'BMW': {'marcas': ['BM1', 'MI1'], 'longitud': 11, 'relleno': '0'},
        'MERCEDES': {'marcas': ['MB1', 'SM1'], 'longitud_min': 9, 'longitud_max': 17},
        'RENAULT': {'marcas': ['RE1', 'DC1'], 'longitud': 10, 'relleno': '0'},
        'FORD': {'marcas': ['FR1'], 'longitud': 7, 'relleno': '0', 'variable': True},
        'HN1': {'marcas': ['HN1'], 'longitud_min': 11, 'longitud_max': 13},
        'TOYOTA': {'marcas': ['TY1', 'LX1'], 'longitud_min': 9, 'longitud_max': 12},
        'SU1': {'marcas': ['SU1'], 'longitud': 15, 'relleno': '0'},
        'VL1': {'marcas': ['VL1'], 'remove_leading_zeros': True}
    }

    # Eliminar guiones y caracteres no alfanuméricos
    referencia = ''.join(filter(str.isalnum, referencia))

    # Buscar el grupo correspondiente
    for grupo, reglas in grupos_formatos.items():
        if brand_code in reglas['marcas']:
            # Grupo Fiat: rellenar a la izquierda con 0 hasta 13 dígitos
            if 'longitud' in reglas and 'relleno' in reglas:
                referencia = referencia.zfill(reglas['longitud'])
            # Grupo Audi: respetar espacios en posiciones específicas
            elif grupo == 'AUDI':
                if len(referencia) >= reglas['longitud_min'] and len(referencia) <= reglas['longitud_max']:
                    if len(referencia) >= 10:
                        referencia = referencia[:10] + ' ' + referencia[10:]
                # Eliminar espacios finales en eferencias del grupo Audi
                referencia = referencia.rstrip()
            # Grupo PSA, Mercedes, Toyota: referencias alfanuméricas sin guiones ni espacios
            elif 'longitud_min' in reglas and 'longitud_max' in reglas:
                referencia = referencia[:reglas['longitud_max']]
            # Grupo Ford: formato europeo o americano
            elif brand_code == 'FR1' and len(referencia) != reglas['longitud']:
                if len(referencia) < reglas['longitud']:
                    referencia = referencia.zfill(reglas['longitud'])
            # Grupo VL1: eliminar ceros a la izquierda
            elif 'remove_leading_zeros' in reglas:
                referencia = referencia.lstrip('0')

            return referencia

    # Otras marcas: referencias alfanuméricas sin guiones, longitud variable
    return referencia

# Validación de la fecha más reciente
def validar_fecha_reciente(fecha_reciente):
    # Verificar que la fecha tiene formato válido (YYYY-MM-DD o DD.MM.YYYY)
    try:
        fecha_dt = datetime.strptime(fecha_reciente, '%Y-%m-%d')
    except ValueError:
        try:
            fecha_dt = datetime.strptime(fecha_reciente, '%d.%m.%Y')
        except ValueError:
            raise ValueError(f"Error: Formato de fecha inválido: {fecha_reciente}")

    # Verificar que la fecha no sea futura
    if fecha_dt > datetime.now():
        raise ValueError(f"Error: La fecha {fecha_dt} es una fecha futura.")

    return fecha_dt

# Función para procesar el archivo TXT y generar un CSV en formato 1-2-3-4
def procesar_archivo_txt(ruta_archivo, brand_code):
    datos = []
    fecha_reciente = None

    with open(ruta_archivo, 'r', encoding='utf-8') as file:
        for line in file:
            partes = line.strip().split('\t')
            if len(partes) < 5:
                continue
            
            referencia = formatear_referencia(partes[0], brand_code)  # Formatear la referencia según las reglas del grupo
            precio = partes[2].replace('.', ',')  # Reemplazar punto por coma en precio
            fecha = partes[4].split(' ')[0]  # Ignorar la hora, solo fecha
            
            datos.append([referencia, '', precio, ''])  # Formato 1-2-3-4

            # Detectar la fecha más reciente
            try:
                fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
            except ValueError:
                fecha_dt = datetime.strptime(fecha, '%d.%m.%Y')

            if fecha_reciente is None or fecha_dt > fecha_reciente:
                fecha_reciente = fecha_dt

    # Validar la fecha más reciente
    if fecha_reciente:
        try:
            validar_fecha_reciente(fecha_reciente.strftime('%Y-%m-%d'))
        except ValueError as e:
            print(e)
            return None, None  # Cancelar todo si la fecha no es válida

        fecha_str = fecha_reciente.strftime('%Y%m%d')
        csv_filename = f'TUR_{brand_code}_{fecha_str}_C_tariffs_P.csv'
        return datos, csv_filename
    else:
        return None, None

# Función para guardar el CSV generado
def guardar_csv(datos, ruta_csv):
    # Crear la carpeta si no existe
    os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
    
    df = pd.DataFrame(datos, columns=['Referencia', 'Descripcion', 'Precio', 'Reemplazo'])
    df.to_csv(ruta_csv, sep=';', index=False, header=False)

# Función para guardar el archivo TXT generado
def guardar_txt(datos, ruta_txt):
    # Crear la carpeta si no existe
    os.makedirs(os.path.dirname(ruta_txt), exist_ok=True)
    
    with open(ruta_txt, 'w', encoding='utf-8') as file:
        for row in datos:
            file.write(';'.join(row) + '\n')

# Lista de marcas que no generan CSV y el TXT debe tener "_EUR" en el nombre
marcas_no_csv = ['BM1', 'MI1', 'HN1', 'JA1', 'LR1', 'MB1', 'SM1', 'RV1', 'MG1']

# Función para procesar el archivo descargado
def procesar_archivo(ruta_archivo, brand_code):
    datos, csv_filename = procesar_archivo_txt(ruta_archivo, brand_code)

    if datos:
        # Si la marca NO está en la lista de marcas que generan CSV
        if brand_code not in marcas_no_csv:
            pend_dir = r'C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESATENDIDA\Pendientes'
            os.makedirs(pend_dir, exist_ok=True)

            # Guardar el archivo CSV en la carpeta de _DESATENDIDA\Pendientes
            ruta_csv_pendientes = os.path.join(pend_dir, csv_filename)
            guardar_csv(datos, ruta_csv_pendientes)

        # Guardar el archivo TXT en la carpeta de la marca correspondiente
        if brand_code in marcas_no_csv:
            txt_filename = f'TARIFA_{brand_code}_TUR_EUR.txt'
        else:
            txt_filename = f'TARIFA_{brand_code}_TUR.txt'

        ruta_txt_tur = os.path.join(r'C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES', brand_code, 'TUR', txt_filename)
        guardar_txt(datos, ruta_txt_tur)

        # Obtener el grupo de la marca
        grupo = obtener_grupos_marca(brand_code)
        if grupo:
            for marca in grupo:
                if marca != brand_code:  # Evitar duplicados
                    # Guardar también el archivo TXT en las carpetas de las marcas del grupo
                    if marca in marcas_no_csv:
                        txt_filename_grupo = f'TARIFA_{marca}_TUR_EUR.txt'
                    else:
                        txt_filename_grupo = f'TARIFA_{marca}_TUR.txt'

                    ruta_txt_grupo = os.path.join(r'C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES', marca, 'TUR', txt_filename_grupo)
                    guardar_txt(datos, ruta_txt_grupo)

                    # Guardar también una copia del CSV en _DESATENDIDA\Pendientes si la marca lo requiere
                    if marca not in marcas_no_csv:
                        ruta_csv_pendientes_grupo = os.path.join(pend_dir, csv_filename.replace(brand_code, marca))
                        guardar_csv(datos, ruta_csv_pendientes_grupo)


# Función para obtener los grupos de marcas
def obtener_grupos_marca(brand_code):
    grupos = {
        'AR1': ['AR1', 'FI1', 'JE1', 'LA1'],
        'AU1': ['AU1', 'SE1', 'SK1', 'VW1'],
        'BM1': ['BM1', 'MI1'],
        'CI1': ['CI1', 'PE1', 'DA1', 'DS1', 'OP1'],
        'MB1': ['MB1', 'SM1'],
        'DC1': ['DC1', 'RE1'],
        'TY1': ['TY1', 'LX1'],
        'RV1': ['RV1', 'MG1'],
    }
    for grupo in grupos.values():
        if brand_code in grupo:
            return grupo
    return None

# Función para comprimir los TXT descargados desde el FTP a ZIP
def comprimir_txt_a_zip(ruta_txt, fecha):
    ruta_zip = ruta_txt.replace('.txt', f'_{fecha}.zip')
    with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(ruta_txt, os.path.basename(ruta_txt))
    os.remove(ruta_txt)  # Eliminar el archivo TXT original después de comprimir
    print(f"Archivo comprimido")


# Función principal
def main():
    print("Iniciando proceso de descarga y procesamiento de archivos...")

    # Obtener los datos de conexión FTP desde la base de datos
    try:
        ftp_host, ftp_port, is_sftp, ftp_user, ftp_pass = obtener_datos_ftp()
    except ValueError as e:
        print(f"Error al obtener datos de conexión FTP: {e}")
        return
    
    descargar_archivos_ftp(ftp_host, ftp_user, ftp_pass, obtener_destino, is_sftp)

    print("Proceso terminado. Pulse Enter para finalizar.")
    input()

if __name__ == "__main__":
    main()
