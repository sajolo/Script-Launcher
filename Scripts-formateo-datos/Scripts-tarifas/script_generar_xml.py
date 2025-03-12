import os
import re
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime

def encontrar_carpeta_descripciones_bbdd_mas_reciente(ruta_base):
    """
    Busca en 'ruta_base' todas las subcarpetas con
      ^YYYYMMDD - Descripciones BBDD.*$
    y selecciona la de fecha más reciente.
    """
    carpetas_candidatas = []
    patron = r'^(\d{8}) - Descripciones BBDD.*$'
    for nombre in os.listdir(ruta_base):
        ruta_completa = os.path.join(ruta_base, nombre)
        if os.path.isdir(ruta_completa):
            match = re.match(patron, nombre)
            if match:
                fecha_str = match.group(1)
                carpetas_candidatas.append((int(fecha_str), ruta_completa))

    if not carpetas_candidatas:
        return None

    carpeta_mas_reciente = max(carpetas_candidatas, key=lambda x: x[0])
    return carpeta_mas_reciente[1]

def localizar_carpeta_final_y_fecha(carpeta_base):
    """
    Si 'carpeta_base' coincide EXACTAMENTE con '^YYYYMMDD - Descripciones BBDD$',
    devolvemos (esa carpeta, fecha_str).
    Si tiene algo más => subcarpeta 'BD'.
    Devolvemos (carpeta_BD, fecha_str) o (None, None) si falla.
    """
    nombre = os.path.basename(carpeta_base)
    patron = r'^(\d{8}) - Descripciones BBDD(.*)$'
    match = re.match(patron, nombre)
    if not match:
        return (None, None)

    fecha_str = match.group(1)
    resto = match.group(2).strip()  # lo que sobra tras BBDD

    if not resto:
        # EXACTO => esa carpeta final
        return (carpeta_base, fecha_str)
    else:
        subcarpeta_bd = os.path.join(carpeta_base, "BD")
        if os.path.isdir(subcarpeta_bd):
            return (subcarpeta_bd, fecha_str)
        else:
            return (None, None)

def leer_archivo(ruta_fichero):
    """
    CSV/XLSX con 4 columnas:
      0->DIC_NUM_ID, 1->ESP, 2->ENG, 3->ISO_code
    """
    nombre = os.path.basename(ruta_fichero).lower()
    if nombre.endswith('.csv'):
        df = pd.read_csv(ruta_fichero, sep=';', encoding='utf-8')
    elif nombre.endswith('.xlsx'):
        df = pd.read_excel(ruta_fichero)
    else:
        return None

    if len(df.columns) < 4:
        return None
    return df

def extraer_fecha_iso_de_nombre_archivo(nombre_archivo):
    """
    Espera 'YYYYMMDD_Descriptions_XXX.(csv|xlsx)'
    Devuelve (fecha_str, iso_code)
    """
    # Ajusta si quieres permitir guiones, etc. En este caso:
    patron = r'^(\d{8})_Descriptions_([A-Za-z0-9\-]+)\.(csv|xlsx)$'
    match = re.match(patron, nombre_archivo, re.IGNORECASE)
    if match:
        return match.group(1), match.group(2).upper()
    return None, None

def generar_xml(df, iso_code, fecha_str, ruta_salida, modo_especial=None):
    """
    modo_especial:
      - None => <XML_TRD> = col[3], <XML_AUX> = col[1]
      - "ESP" => TRD=col[1], AUX=col[1]
      - "ENG" => TRD=col[2], AUX=col[1]
    """
    root_tag = f"DICCIONARIO_{iso_code.upper()}"
    root = ET.Element(root_tag)
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

    for _, row in df.iterrows():
        acepcion = ET.SubElement(root, "ACEPCION")

        dic_id = ET.SubElement(acepcion, "DIC_NUM_ID")
        dic_id.text = str(row[0]) if not pd.isna(row[0]) else ""

        if modo_especial == "ESP":
            # TRD y AUX -> col[1]
            trd_text = str(row[1]) if not pd.isna(row[1]) else ""
            aux_text = trd_text
        elif modo_especial == "ENG":
            # TRD=col[2], AUX=col[1]
            trd_text = str(row[2]) if not pd.isna(row[2]) else ""
            aux_text = str(row[1]) if not pd.isna(row[1]) else ""
        else:
            # Caso estándar => TRD=col[3], AUX=col[1]
            trd_text = str(row[3]) if not pd.isna(row[3]) else ""
            aux_text = str(row[1]) if not pd.isna(row[1]) else ""

        xml_trd = ET.SubElement(acepcion, "XML_TRD")
        xml_trd.text = trd_text

        xml_aux = ET.SubElement(acepcion, "XML_AUX")
        xml_aux.text = aux_text

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    tree = ET.ElementTree(root)
    tree.write(ruta_salida, encoding='utf-8', xml_declaration=True, short_empty_elements=True)

def generar_xml_especial_ces_slk(ruta_fichero, carpeta_xml, fecha_carpeta):
    """
    Lógica especial si el archivo se llama 'YYYYMMDD_Descriptions_CES-SLK.xlsx'
    Ignoramos la col D (DEU) y tomamos:
      - col 0 => DIC_NUM_ID
      - col 1 => ESP (para AUX)
      - col 4 => CES (para TRD en XML CES)
      - col 5 => SLK (para TRD en XML SLK)
    """
    df = pd.read_excel(ruta_fichero, header=None)
    # Asumimos que la fila 0 es encabezado como:
    #   col0 = "DIC_NUM_ID"? col1="ESP"? col2=?? col3="DEU"? col4="CES"? col5="SLK"?
    # Realmente, lo importante es la data en filas 1..N

    # Data real a partir de fila 1
    # col 0 => DIC_NUM_ID
    # col 1 => ESP
    # col 4 => CES
    # col 5 => SLK

    # Generamos el XML para CES
    #   <DIC_NUM_ID> => col[0]
    #   <XML_TRD> => col[4]
    #   <XML_AUX> => col[1]
    # Generamos el XML para SLK
    #   <DIC_NUM_ID> => col[0]
    #   <XML_TRD> => col[5]
    #   <XML_AUX> => col[1]

    # Creamos un DF intermedio para iterar las filas.
    # Filas 1.. => data real
    data = df.iloc[1:, :]  # omitimos la fila 0

    # Generar CES
    root_ces = ET.Element("DICCIONARIO_CES")
    root_ces.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

    for _, row in data.iterrows():
        acepcion = ET.SubElement(root_ces, "ACEPCION")

        # DIC_NUM_ID
        dic_id = ET.SubElement(acepcion, "DIC_NUM_ID")
        dic_id.text = str(row[0]) if not pd.isna(row[0]) else ""

        # TRD => col[4]
        xml_trd = ET.SubElement(acepcion, "XML_TRD")
        if 4 in row and not pd.isna(row[4]):
            xml_trd.text = str(row[4])
        else:
            xml_trd.text = ""

        # AUX => col[1] (español)
        xml_aux = ET.SubElement(acepcion, "XML_AUX")
        if 1 in row and not pd.isna(row[1]):
            xml_aux.text = str(row[1])
        else:
            xml_aux.text = ""

    # Guardar
    ruta_xml_ces = os.path.join(carpeta_xml, f"CES_{fecha_carpeta}.xml")
    tree_ces = ET.ElementTree(root_ces)
    tree_ces.write(ruta_xml_ces, encoding='utf-8', xml_declaration=True, short_empty_elements=True)
    print(f"Generado XML especial CES => {ruta_xml_ces}")

    # Generar SLK
    root_slk = ET.Element("DICCIONARIO_SLK")
    root_slk.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

    for _, row in data.iterrows():
        acepcion = ET.SubElement(root_slk, "ACEPCION")

        dic_id = ET.SubElement(acepcion, "DIC_NUM_ID")
        dic_id.text = str(row[0]) if not pd.isna(row[0]) else ""

        # TRD => col[5]
        xml_trd = ET.SubElement(acepcion, "XML_TRD")
        if 5 in row and not pd.isna(row[5]):
            xml_trd.text = str(row[5])
        else:
            xml_trd.text = ""

        # AUX => col[1] (español)
        xml_aux = ET.SubElement(acepcion, "XML_AUX")
        if 1 in row and not pd.isna(row[1]):
            xml_aux.text = str(row[1])
        else:
            xml_aux.text = ""

    ruta_xml_slk = os.path.join(carpeta_xml, f"SLK_{fecha_carpeta}.xml")
    tree_slk = ET.ElementTree(root_slk)
    tree_slk.write(ruta_xml_slk, encoding='utf-8', xml_declaration=True, short_empty_elements=True)
    print(f"Generado XML especial SLK => {ruta_xml_slk}")

def obtener_copias_idioma_principal(iso_principal):
    """
    Ej: 'ENG' => [ENG, EN1, EN2, EN3, EN4, EN5]
        'FRA' => [FRA, FR1, FR2], etc.
    """
    copias = {
        'ENG': ['ENG','EN1','EN2','EN3','EN4','EN5'],
        'FRA': ['FRA','FR1','FR2'],
        'ESP': ['ESP','ES1','ES2'],
        'DEU': ['DEU','DE1','DE2'],
        'NLD': ['NLD','NL1']
    }
    iso_up = iso_principal.upper()
    return copias.get(iso_up, [iso_up])

def main():
    # Ajusta a tu entorno
    # ruta_base = r"\\s02-ean\DataAcquisition\TRANSLATIONS\01_Descriptions & Resources"
    ruta_base = r"C:\Users\Saul\Desktop\s02-ean\DataAcquisition\TRANSLATIONS\01_Descriptions & Resources"

    # 1) Buscar la carpeta con '^YYYYMMDD - Descripciones BBDD.*$' más reciente
    carpeta_encontrada = encontrar_carpeta_descripciones_bbdd_mas_reciente(ruta_base)
    if not carpeta_encontrada:
        print("No se halló carpeta con 'YYYYMMDD - Descripciones BBDD'. Saliendo...")
        return

    # 2) Obtener carpeta final y la fecha real
    carpeta_final, fecha_carpeta = localizar_carpeta_final_y_fecha(carpeta_encontrada)
    if not carpeta_final:
        print("No se pudo localizar la carpeta final ni extraer fecha. Saliendo...")
        return

    # 3) Buscar 'Recibidos'
    carpeta_recibidos = os.path.join(carpeta_final, "Recibidos")
    if not os.path.isdir(carpeta_recibidos):
        print(f"No existe la carpeta 'Recibidos' en: {carpeta_final}. Saliendo...")
        return

    # 4) Crear (o verificar) carpeta "XML finales"
    carpeta_xml = os.path.join(carpeta_final, "XML finales")
    os.makedirs(carpeta_xml, exist_ok=True)

    # 5) Recorrer ficheros CSV/XLSX en 'Recibidos'
    for fichero in os.listdir(carpeta_recibidos):
        if not (fichero.lower().endswith('.csv') or fichero.lower().endswith('.xlsx')):
            continue

        fecha_str_arch, iso_from_name = extraer_fecha_iso_de_nombre_archivo(fichero)
        if not fecha_str_arch:
            print(f"El archivo '{fichero}' no cumple 'YYYYMMDD_Descriptions_XXX'. Se ignora.")
            continue

        ruta_fich = os.path.join(carpeta_recibidos, fichero)

        # CASO ESPECIAL: "CES-SLK"
        if iso_from_name.upper() == "CES-SLK":
            # Hacemos la lógica normal (por si acaso) + la lógica adicional
            # 1) Lógica normal
            df_standard = leer_archivo(ruta_fich)
            if df_standard is not None:
                # Se generan (1) => iso principal + copias
                isos_principales = obtener_copias_idioma_principal(iso_from_name)
                for iso_code in isos_principales:
                    xml_filename = f"{iso_code}_{fecha_carpeta}.xml"
                    ruta_xml_salida = os.path.join(carpeta_xml, xml_filename)
                    # modo_especial=None => TRD=col[3], AUX=col[1]
                    # Aunque en este Excel no sea relevante, no pasa nada
                    if df_standard is not None:
                        generar_xml(df_standard, iso_code, fecha_carpeta, ruta_xml_salida, modo_especial=None)
                        print(f"Generado (normal) => {ruta_xml_salida}")

                # 2) Especial ESP
                esp_copias = ['ESP','ES1','ES2']
                for iso_esp in esp_copias:
                    xml_filename = f"{iso_esp}_{fecha_carpeta}.xml"
                    ruta_xml_salida = os.path.join(carpeta_xml, xml_filename)
                    generar_xml(df_standard, iso_esp, fecha_carpeta, ruta_xml_salida, modo_especial="ESP")
                    print(f"Generado (normal) => {ruta_xml_salida}")

                # 3) Especial ENG
                eng_copias = ['ENG','EN1','EN2','EN3','EN4','EN5']
                for iso_eng in eng_copias:
                    xml_filename = f"{iso_eng}_{fecha_carpeta}.xml"
                    ruta_xml_salida = os.path.join(carpeta_xml, xml_filename)
                    generar_xml(df_standard, iso_eng, fecha_carpeta, ruta_xml_salida, modo_especial="ENG")
                    print(f"Generado (normal) => {ruta_xml_salida}")

            # Ahora la lógica "adicional" => extraer col[4]=CES, col[5]=SLK, AUX=col[1]
            print(f"Generando XMLs especiales para CES-SLK ignorando la col DEU...")
            generar_xml_especial_ces_slk(ruta_fich, carpeta_xml, fecha_carpeta)

        else:
            # No es "CES-SLK", => Lógica normal 100%
            df = leer_archivo(ruta_fich)
            if df is None:
                print(f"No se pudo leer correctamente: {fichero}")
                continue

            # (1) Generar XML p/ idioma principal + copias
            isos_principales = obtener_copias_idioma_principal(iso_from_name)
            for iso_code in isos_principales:
                xml_filename = f"{iso_code}_{fecha_carpeta}.xml"
                ruta_xml_salida = os.path.join(carpeta_xml, xml_filename)
                generar_xml(df, iso_code, fecha_carpeta, ruta_xml_salida, modo_especial=None)
                print(f"Generado => {ruta_xml_salida}")

            # (2) Especial ESP => TRD=col[1], AUX=col[1]
            esp_copias = ['ESP','ES1','ES2']
            for iso_esp in esp_copias:
                xml_filename = f"{iso_esp}_{fecha_carpeta}.xml"
                ruta_xml_salida = os.path.join(carpeta_xml, xml_filename)
                generar_xml(df, iso_esp, fecha_carpeta, ruta_xml_salida, modo_especial="ESP")
                print(f"Generado => {ruta_xml_salida}")

            # (3) Especial ENG => TRD=col[2], AUX=col[1]
            eng_copias = ['ENG','EN1','EN2','EN3','EN4','EN5']
            for iso_eng in eng_copias:
                xml_filename = f"{iso_eng}_{fecha_carpeta}.xml"
                ruta_xml_salida = os.path.join(carpeta_xml, xml_filename)
                generar_xml(df, iso_eng, fecha_carpeta, ruta_xml_salida, modo_especial="ENG")
                print(f"Generado => {ruta_xml_salida}")

    print("\n¡Proceso de generación de XML finalizado!")

if __name__ == "__main__":
    main()
