import os
import re
import pandas as pd
from datetime import datetime, timedelta

# Carpeta principal donde están las subcarpetas con formato "YYYY - MM"
BASE_FOLDER = r"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\LIQUIDACIONES - COMPRA LICENCIAS DOCUMENTACIÓN - Accounting\01_LIQUIDACIONES TARJETAS PAGOS - PALOMA"

# Prefijos de los nombres de los archivos
NOMBRE_IBE = "Detalle de movimientos de tarjeta IBC91"  # IberCaja
NOMBRE_SAN = "VISA SANTANDER"                          # Santander

def carpeta_mas_reciente(base_path):
    """
    Devuelve la subcarpeta con fecha más reciente (en formato YYYY - MM).
    """
    subfolders = []
    for entry in os.listdir(base_path):
        full_path = os.path.join(base_path, entry)
        if os.path.isdir(full_path):
            match = re.match(r'^(\d{4})\s*-\s*(\d{2})$', entry.strip())
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                subfolders.append((year, month, entry))
    if not subfolders:
        return None
    # Ordenar (año, mes) y elegir la más reciente
    subfolders.sort(key=lambda x: (x[0], x[1]))
    return subfolders[-1][2]

def col_letter_to_index(letter):
    """
    Convierte una letra de columna de Excel (ej. 'A','B','C'...) a índice entero 0-based.
    Ejemplo:
      'A' -> 0
      'B' -> 1
      'C' -> 2
      ...
      'Z' -> 25
      'AA' -> 26
      etc.
    """
    letter = letter.upper()
    result = 0
    for char in letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    # restarle 1 para que sea 0-based
    return result - 1

def leer_excel_ibercaja(ruta_excel):
    """
    Lee el archivo de IberCaja a partir de la fila 7 (skiprows=6).
    Selecciona por índice las columnas B=1, C=2, D=3, E=4, G=6, H=7, I=8, J=9.
    """
    df_raw = pd.read_excel(ruta_excel, engine='openpyxl', skiprows=6, header=0)
    col_indices = [1, 2, 3, 4, 6, 7, 8, 9]  # B,C,D,E,G,H,I,J
    max_col_index = df_raw.shape[1] - 1
    valid_cols = [c for c in col_indices if c <= max_col_index]
    df = df_raw.iloc[:, valid_cols]

    desired_names = [
        "Fecha Oper",    # B (índice 1)
        "Tipo Oper",     # C (índice 2)
        "Hora",          # D (índice 3)
        "Concepto",      # E (índice 4)
        "Importe",       # G (índice 6)
        "Dispositivo",   # H (índice 7)
        "Estado",        # I (índice 8)
        "Fecha Valor"    # J (índice 9)
    ]
    df.columns = desired_names[:len(valid_cols)]
    return df

def formatear_ibercaja(df):
    """
    - Fecha Oper, Fecha Valor: DD-MM-YYYY
    - Hora -> HH:MM
    - Importe -> 2 dec con coma
    """
    def format_hora(h):
        if pd.isna(h):
            return "00:00"
        s = str(h).strip()
        match = re.match(r'^(\d{1,2})[:\.,-]?(\d{1,2})?$', s)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            return f"{hour:02d}:{minute:02d}"
        return "00:00"
    df["Hora"] = df["Hora"].fillna("").apply(format_hora)

    def format_importe(x):
        try:
            val = float(str(x).replace(",", "."))
        except:
            val = 0.0
        s = f"{val:,.2f}"
        s = s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        return s
    if "Importe" in df.columns:
        df["Importe"] = df["Importe"].apply(format_importe)

    for col in ["Fecha Oper", "Fecha Valor"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True).dt.strftime("%d-%m-%Y")
    return df

def leer_excel_santander_consola(ruta_excel):
    """
    Pregunta al usuario la celda inicial para Fecha Oper, por ejemplo 'C22'.
    A partir de esa celda, deduce las columnas de Hora (+1 letra), Concepto (+2 letras) e
    Importe (+7 letras), con la misma fila.

    skiprows = (fila - 1)
    usecols = [col_fecha, col_hora, col_concepto, col_importe]

    Devuelve un DataFrame con columnas: Fecha Oper, Hora, Concepto, Importe
    """
    celda_inicial = input(
        "\nArchivo de SANTANDER detectado.\n"
        "Indica la celda inicial de Fecha Oper (ej: C22): "
    ).strip().upper()

    # Parsear la letra(s) de columna y el número de fila
    match = re.match(r'^([A-Z]+)(\d+)$', celda_inicial)
    if not match:
        print(f"Formato de celda no válido: '{celda_inicial}'. Se asumirá A1.")
        col_letra = "A"
        row_num = 1
    else:
        col_letra = match.group(1)
        row_num = int(match.group(2))

    # Convertir la columna a índice 0-based
    col_fecha_idx = col_letter_to_index(col_letra)

    # Calcular las columnas para Hora (col + 1), Concepto (col + 2) e Importe (col + 7)
    col_hora_idx = col_fecha_idx + 1
    col_conc_idx = col_fecha_idx + 2
    col_imp_idx  = col_fecha_idx + 7

    # skiprows = la fila - 1 => si es 22 => skiprows=21
    skip_val = row_num - 1

    # Leemos esas 4 columnas
    df = pd.read_excel(
        ruta_excel,
        engine='openpyxl',
        skiprows=skip_val,
        usecols=[col_fecha_idx, col_hora_idx, col_conc_idx, col_imp_idx],
        header=None,
        names=["Fecha Oper", "Hora", "Concepto", "Importe"]
    )
    return df

def formatear_campos_santander(df_santander):
    """
    Reglas para Santander:
    - 'Tipo Oper' = 'VENTA'
    - 'Dispositivo' = 'Tarjeta'
    - 'Estado' = 'PAGADA                        ' (24 espacios)
    - 'Fecha Valor' = Fecha Oper + 3 días
    - Fecha Oper => DD-MM-YYYY
    - Hora => HH:MM
    - Importe => 2 dec con coma
    """
    # 1) Fecha Oper -> datetime -> string DD-MM-YYYY
    df_santander["Fecha Oper"] = pd.to_datetime(df_santander["Fecha Oper"], errors='coerce', dayfirst=True)
    df_santander["Fecha Oper"] = df_santander["Fecha Oper"].dt.strftime("%d-%m-%Y")

    # 2) Hora -> HH:MM
    def format_hora(h):
        if pd.isna(h):
            return "00:00"
        s = str(h).strip()
        match = re.match(r'^(\d{1,2})[:\.,-]?(\d{1,2})?$', s)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            return f"{hour:02d}:{minute:02d}"
        return "00:00"
    df_santander["Hora"] = df_santander["Hora"].apply(format_hora)

    # 3) Importe -> coma decimal, 2 dec
    def format_importe(x):
        try:
            val = float(str(x).replace(",", "."))
        except:
            val = 0.0
        s = f"{val:,.2f}"
        s = s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        return s
    df_santander["Importe"] = df_santander["Importe"].apply(format_importe)

    # 4) Columnas fijas
    df_santander["Tipo Oper"] = "VENTA"
    df_santander["Dispositivo"] = "Tarjeta"
    df_santander["Estado"] = "PAGADA                        "

    # 5) Fecha Valor = Fecha Oper + 3 días
    def fecha_valor_3dias(fecha_str):
        try:
            d = datetime.strptime(fecha_str, "%d-%m-%Y")
            d_valor = d + timedelta(days=3)
            return d_valor.strftime("%d-%m-%Y")
        except:
            return ""
    df_santander["Fecha Valor"] = df_santander["Fecha Oper"].apply(fecha_valor_3dias)

    return df_santander

def generar_csv_combinado(df_ib, df_sa, output_path):
    """
    Columnas finales:
    [Fecha Oper, Tipo Oper, Hora, Concepto, Importe, Dispositivo, Estado, Fecha Valor]
    Ordenar por Fecha Valor desc.
    """
    final_cols = ["Fecha Oper", "Tipo Oper", "Hora", "Concepto",
                  "Importe", "Dispositivo", "Estado", "Fecha Valor"]

    # Asegurar que ambos DF tengan esas columnas
    for c in final_cols:
        if c not in df_ib.columns:
            df_ib[c] = ""
        if c not in df_sa.columns:
            df_sa[c] = ""

    df_ib = df_ib[final_cols]
    df_sa = df_sa[final_cols]

    # Combinar
    df_final = pd.concat([df_ib, df_sa], ignore_index=True)

    # Ordenar por Fecha Valor desc
    df_final["tmpFV"] = pd.to_datetime(df_final["Fecha Valor"], format="%d-%m-%Y", errors="coerce")
    df_final.sort_values(by="tmpFV", ascending=False, inplace=True)
    df_final.drop(columns=["tmpFV"], inplace=True)

    # Guardar
    df_final.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')

def main():
    # 1) Carpeta más reciente
    folder_name = carpeta_mas_reciente(BASE_FOLDER)
    if not folder_name:
        print("No hay subcarpetas con el formato YYYY - MM.")
        return
    target_folder = os.path.join(BASE_FOLDER, folder_name)
    print(f"Carpeta más reciente: {target_folder}")

    files_in_folder = os.listdir(target_folder)

    # 2) Archivo IberCaja e identificar mes-año
    ib_file = None
    mesaa = None
    for f in files_in_folder:
        if f.startswith(NOMBRE_IBE) and f.endswith(".xlsx"):
            ib_file = f
            parts = f.split("-")
            if len(parts) > 1:
                mesaa = parts[1].strip()
            break

    # 3) Archivo Santander
    san_file = None
    if mesaa:
        for f in files_in_folder:
            # Ej: "VISA SANTANDER  FEB25 - LORENZO.xlsx"
            # Quieres que contenga mesaa en el nombre
            if f.startswith(NOMBRE_SAN) and (mesaa in f) and f.endswith(".xlsx"):
                san_file = f
                break

    # 4) Leer IberCaja
    df_ib = pd.DataFrame()
    if ib_file:
        path_ib = os.path.join(target_folder, ib_file)
        df_ib = leer_excel_ibercaja(path_ib)
        df_ib = formatear_ibercaja(df_ib)
    else:
        print("No se encontró el archivo de IberCaja.")

    # 5) Leer Santander
    df_sa = pd.DataFrame()
    if san_file:
        path_sa = os.path.join(target_folder, san_file)
        # Pedir la celda inicial al usuario
        df_sa_raw = leer_excel_santander_consola(path_sa)
        df_sa = formatear_campos_santander(df_sa_raw)
    else:
        print(f"No se encontró el archivo Santander con la parte del nombre: {mesaa}")

    # 6) Si no hay datos en ambos DF, termina
    if df_ib.empty and df_sa.empty:
        print("No hay datos en IberCaja ni en Santander para combinar.")
        return

    # 7) Nombre CSV => preferir el de IberCaja
    if ib_file:
        output_name = ib_file.replace(".xlsx", ".csv")
    elif san_file:
        output_name = san_file.replace(".xlsx", ".csv")
    else:
        output_name = "datos_combinados.csv"

    output_path = os.path.join(target_folder, output_name)
    generar_csv_combinado(df_ib, df_sa, output_path)
    print(f"Archivo generado: {output_path}")

if __name__ == "__main__":
    main()
