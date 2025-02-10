import os
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime
import mysql.connector

# Configuración de la base de datos MySQL
db_config = {
    'user': 'smarquez',
    'password': 'helvetia',
    'host': 'localhost',
    'database': 'prc_db',
}

# Lista de países
countries_iso = [
    "MKD", "UKR", "DEU", "FRA", "ITA", "GBR", "CHE", "NLD", "GRC", "ALB",
    "POL", "ISL", "NOR", "MLT", "HRV", "KOR", "AUT", "CZE", "FIN", "CYP", "LUX",
    "ROU", "DNK", "BEL", "BGR", "MNE", "HUN", "MDA", "SRB", "BIH", "IRL",
    "LTU", "LVA", "EST", "SVN", "SVK", "SWE", "IND", "ZAF", "TUN", "NAM",
    "AUS", "MEX"
]

# Lista de marcas
brands = [
    "ALFA ROMEO", "AUDI", "BMW", "BYD", "CITROËN", "DAEWOO/CHEVROLET", "DACIA", "DS", "FIAT", "FORD",
    "HONDA", "HYUNDAI", "ISUZU", "IVECO", "JAGUAR", "JEEP", "KIA", "LANCIA", "LAND ROVER", "LEXUS",
    "MAHINDRA", "MAN", "MAZDA", "MERCEDES BENZ", "MERCEDES TRUCKS", "MG", "MINI", "MITSUBISHI", "NISSAN", "OPEL",
    "PEUGEOT", "PORSCHE", "RENAULT", "RENAULT TRUCKS", "ROVER/MG", "SAAB", "SEAT", "SKODA", "SMART", "SUBARU", "SUZUKI",
    "TATA", "TESLA", "TOYOTA", "VOLVO", "VOLVO TRUCKS", "VOLKSWAGEN"
]

# Funciones de acceso a la base de datos
def get_latest_effective_date(country_iso, brand_name):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    query = (
        "SELECT MAX(last_file_date) FROM tariffs_dates "
        "WHERE country_iso = %s AND brand_name = %s"
    )
    cursor.execute(query, (country_iso, brand_name))
    result = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    if result and result <= datetime.now().date():
        return result.strftime("%Y-%m-%d")
    return None

def get_price_file_source(country_iso, brand_name):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(buffered=True)
    # Obtener Tariff_Id
    cursor.execute(
        "SELECT Tariff_Id FROM tariffs_dates WHERE country_iso = %s AND brand_name = %s",
        (country_iso, brand_name)
    )
    tariff_id = cursor.fetchone()
    if not tariff_id:
        cursor.close()
        connection.close()
        return ""

    # Obtener Primary_Contact_Id desde tariffs_specific_data
    cursor.execute(
        "SELECT Primary_Contact_Id FROM tariffs_specific_data WHERE Tariff_Id = %s",
        (tariff_id[0],)
    )
    primary_contact_id = cursor.fetchone()
    if not primary_contact_id:
        cursor.close()
        connection.close()
        return ""

    # Obtener Company_Name desde contacts
    cursor.execute(
        "SELECT Company_Name FROM contacts WHERE Id = %s",
        (primary_contact_id[0],)
    )
    company_name_result = cursor.fetchone()
    if not company_name_result:
        cursor.close()
        connection.close()
        return ""
    company_name = company_name_result[0]
    cursor.close()
    connection.close()
    return company_name

def get_converted_from_different_source(country_iso, brand_name):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    # Obtener Converted_From_Different_Source desde price_file_conversion_source
    cursor.execute(
        "SELECT Converted_From_Different_Source FROM price_file_conversion_source WHERE Country_ISO = %s AND brand_name = %s",
        (country_iso, brand_name)
    )
    converted_result = cursor.fetchone()
    cursor.close()
    connection.close()
    if converted_result:
        return converted_result[0]
    return ""

# Actualizar tabla price_file_report_ext
def update_price_file_report_ext(country_iso, brand_desc, effective_date, price_file_source, converted_from_different_source):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    query = (
        "REPLACE INTO price_file_report_ext (COUNTRY_ISO, BRAND_DESC, EFFECTIVE_DATE, PRICE_FILE_SOURCE, CONVERTED_FROM_DIFFERENT_SOURCE) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    cursor.execute(query, (country_iso, brand_desc, effective_date if effective_date else None, price_file_source, converted_from_different_source))
    connection.commit()
    cursor.close()
    connection.close()

# Crear o actualizar archivo XLSX
def create_or_update_xlsx():
    print("Generando informe de tarifas...")
    report_filename = "TARIFFS_REPORT_{}.xlsx".format(datetime.now().strftime("%d-%m-%Y"))
    report_path = os.path.join(
        r"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESCARGAS",
        report_filename
    )

    # Verificar si ya existe un archivo con el nombre que empieza por "TARIFFS_REPORT"
    existing_file = None
    for file in os.listdir(os.path.dirname(report_path)):
        if file.startswith("TARIFFS_REPORT"):
            existing_file = os.path.join(os.path.dirname(report_path), file)
            break

    # Crear un nuevo libro o cargar el existente
    if existing_file:
        workbook = openpyxl.load_workbook(existing_file)
        os.rename(existing_file, report_path)
    else:
        workbook = Workbook()

    # Seleccionar la hoja activa
    sheet = workbook.active
    sheet.title = "Tariffs Report"

    # Encabezados de columnas
    headers = ["COUNTRY_ISO", "BRAND DESC.", "EFFECTIVE DATE", "PRICE FILE SOURCE", "CONVERTED FROM DIFFERENT SOURCE"]
    for col_num, header in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col_num, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        cell.fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        cell.border = Border(left=Side(style="thin"),
                             right=Side(style="thin"),
                             top=Side(style="thin"),
                             bottom=Side(style="thin"))

    # Ajustar el ancho de las columnas
    column_widths = [15, 22, 15, 40, 50]
    for col_num, width in enumerate(column_widths, 1):
        sheet.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = width

    # Llenar el XLSX con los datos
    row = 2
    for country_iso in sorted(countries_iso):
        for brand in brands:
            effective_date = get_latest_effective_date(country_iso, brand)
            price_file_source = get_price_file_source(country_iso, brand) if effective_date else ""
            converted_from_different_source = get_converted_from_different_source(country_iso, brand)

            # Actualizar la tabla price_file_report_ext
            update_price_file_report_ext(country_iso, brand, effective_date, price_file_source, converted_from_different_source)

            # Escribir en el archivo XLSX
            sheet[f"A{row}"] = country_iso
            sheet[f"B{row}"] = brand
            sheet[f"C{row}"] = effective_date if effective_date else ""
            sheet[f"D{row}"] = price_file_source
            sheet[f"E{row}"] = converted_from_different_source

            # Aplicar bordes a las celdas
            for col_num in range(1, 6):
                cell = sheet.cell(row=row, column=col_num)
                cell.border = Border(left=Side(style="thin"),
                                     right=Side(style="thin"),
                                     top=Side(style="thin"),
                                     bottom=Side(style="thin"))
            row += 1

    # Guardar el libro actualizado
    workbook.save(report_path)
    print("Informe generado, cierre esta ventana para finalizar...")
    input()

# Ejecutar el script
if __name__ == "__main__":
    create_or_update_xlsx()
