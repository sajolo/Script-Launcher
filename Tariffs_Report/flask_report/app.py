import os
import mysql.connector
from flask import Flask, request, render_template
from datetime import datetime, timedelta

app = Flask(__name__)

# DB Config
DB_CONFIG = {
    'user': 'smarquez',
    'password': 'helvetia',
    'host': 'localhost',
    'database': 'prc_db',
}

COUNTRIES = [
    "DEU", "ESP", "POR", "FRA", "ITA", "GBR", "CHE", "NLD", "GRC", "PLN", "NOR",
    "KOR", "AUT", "CZE", "FIN", "ROU", "DNK", "BEL", "HUN", "IRL",
    "SVK", "SWE", "IND", "ZAF", "TUN", "NAM", "TUR"
]
BRANDS = [
    "ALFA ROMEO", "AUDI", "BMW", "CITROEN", "DAEWOO/CHEVROLET", "DACIA", "DS", "FIAT", "FORD",
    "HONDA", "HYUNDAI", "IVECO", "JAGUAR", "JEEP", "KIA", "LANCIA", "LAND ROVER", "LEXUS",
    "MAN", "MAZDA", "MERCEDES BENZ", "MG", "MINI", "MITSUBISHI", "NISSAN", "OPEL",
    "PEUGEOT", "PORSCHE", "RENAULT", "RENAULT TRUCKS", "ROVER/MG", "SAAB", "SEAT", "SKODA", "SMART", "SUBARU", "SUZUKI",
    "TATA", "TESLA", "TOYOTA", "VOLVO", "VOLVO TRUCKS", "VOLKSWAGEN"
]

def db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def fetch_all_dates():
    """
    Consulta única con GROUP BY country_iso, brand_name para obtener la última fecha (MAX).
    Retorna big_data[(brand, c_iso)] = date or None
    """
    conn = db_connection()
    cursor = conn.cursor()
    query = """
      SELECT country_iso, brand_name, MAX(last_file_date) AS last_file_date
      FROM tariffs_dates
      GROUP BY country_iso, brand_name
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    big_data = {}
    for (c_iso, brand, dt) in rows:
        big_data[(brand, c_iso)] = dt
    return big_data

@app.route("/")
def index():
    filtro_country = request.args.get("country", "")
    filtro_brand = request.args.get("brand", "")
    filtro_highlight = request.args.get("highlight_range", "")

    used_countries = sorted(COUNTRIES)
    used_brands = sorted(BRANDS)

    if filtro_country in used_countries:
        used_countries = [filtro_country]
    if filtro_brand in used_brands:
        used_brands = [filtro_brand]

    single_country_mode = (len(used_countries) == 1)

    # Parse highlight_range a entero
    try:
        highlight_days = int(filtro_highlight)
    except ValueError:
        highlight_days = 0

    big_data = fetch_all_dates()
    today = datetime.now().date()

    data = {}
    all_countries_sorted = sorted(COUNTRIES)
    all_brands_sorted = sorted(BRANDS)

    for marca in all_brands_sorted:
        for c_iso in all_countries_sorted:
            dt_obj = big_data.get((marca, c_iso))
            highlight = False
            year_str = ""
            md_str = ""
            if dt_obj:
                year_str = str(dt_obj.year)
                md_str = f"{dt_obj.month:02d}-{dt_obj.day:02d}"
                if highlight_days > 0:
                    diff_days = (today - dt_obj).days
                    if diff_days < highlight_days:
                        highlight = True

            data[(marca, c_iso)] = {
                'year': year_str,
                'md': md_str,
                'highlight': highlight
            }

    return render_template(
        "index.html",
        all_countries=all_countries_sorted,
        all_brands=all_brands_sorted,
        used_countries=used_countries,
        used_brands=used_brands,
        single_country_mode=single_country_mode,
        filtro_country=filtro_country,
        filtro_brand=filtro_brand,
        filtro_highlight=filtro_highlight,
        data=data
    )

if __name__ == "__main__":
    # Corre en 0.0.0.0:5000 con debug
    app.run(host="0.0.0.0", port=5000, debug=True)
