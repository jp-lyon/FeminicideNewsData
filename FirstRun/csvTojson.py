import json
import time
import os
import csv
import re
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from tqdm import tqdm

def limpieza_regex_seguro(html_crudo, autor_actual, fecha_actual):
    """
    Si el autor o fecha fallaron, intenta buscarlos con patrones de texto 
    directamente en el HTML crudo.
    """
    # 1. Intento de rescate de Fecha (Busca patrones YYYY-MM-DD o DD/MM/YYYY)
    if fecha_actual == "No encontrada":
        # Busca años entre 2010 y 2029
        match_fecha = re.search(r'20[1-2][0-9][\-/][0-1][0-9][\-/][0-3][0-9]', html_crudo)
        if match_fecha:
            fecha_actual = match_fecha.group()

    # 2. Intento de rescate de Autor
    if autor_actual == "No encontrado":
        # Busca patrones comunes como "Por: Nombre", "Escrito por: Nombre", etc.
        # Limitamos la búsqueda para no traer basura del HTML
        patron_autor = re.search(r'(?:Por|Escrito por|By|Autor):\s?([A-Z][a-z]+\s[A-Z][a-z]+)', html_crudo)
        if patron_autor:
            autor_actual = patron_autor.group(1)

    return autor_actual, fecha_actual

def extraer_metadatos_avanzado(soup):
    autor = "No encontrado"
    fecha = "No encontrada"

    # Capa 1: JSON-LD
    scripts_json = soup.find_all('script', type='application/ld+json')
    for script in scripts_json:
        try:
            if not script.string: continue
            data = json.loads(script.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if fecha == "No encontrada":
                    fecha = item.get('datePublished') or item.get('dateCreated') or item.get('uploadDate')
                if autor == "No encontrado":
                    autor_data = item.get('author')
                    if isinstance(autor_data, dict): autor = autor_data.get('name')
                    elif isinstance(autor_data, list) and len(autor_data) > 0:
                        autor = autor_data[0].get('name') if isinstance(autor_data[0], dict) else autor_data[0]
            if autor != "No encontrado" and fecha != "No encontrada": break
        except: continue

    # Capa 2: Meta Tags
    if autor == "No encontrado":
        for n in ["author", "article:author", "og:article:author", "dc.creator"]:
            tag = soup.find("meta", {"name": n}) or soup.find("meta", {"property": n})
            if tag and tag.get("content"):
                autor = tag["content"]; break

    if fecha == "No encontrada":
        for n in ["article:published_time", "publication_date", "date", "og:article:published_time"]:
            tag = soup.find("meta", {"name": n}) or soup.find("meta", {"property": n})
            if tag and tag.get("content"):
                fecha = tag["content"]; break

    return str(autor), str(fecha)

def extraer_noticias():
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_csv = os.path.join(directorio_actual, 'archivo_principal_scraping.csv')
    ruta_salida = os.path.join(directorio_actual, 'noticias_extraidas.json')
    ruta_gecko = r"C:\Users\jjleo\Downloads\EL ARCA\Entorno\Python\Feminismo\geckodriver.exe"

    options = Options()
    options.add_argument("--headless")
    options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
    options.set_preference("permissions.default.image", 2)

    service = Service(executable_path=ruta_gecko)
    driver = None

    try:
        if not os.path.exists(ruta_csv): return

        urls = []
        with open(ruta_csv, mode='r', encoding='utf-8') as f:
            lector = csv.DictReader(f)
            for fila in lector:
                url = fila.get('url') or fila.get('URL') or list(fila.values())[0]
                if url and str(url).startswith('http'): urls.append(url.strip())

        driver = webdriver.Firefox(service=service, options=options)
        resultados = []

        for url in tqdm(urls, desc="Procesando con seguro HTML", unit="noticia"):
            try:
                driver.get(url)
                time.sleep(2)
                
                html_crudo = driver.page_source
                soup = BeautifulSoup(html_crudo, 'html.parser')
                
                # Extracción base
                titulo = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Sin título"
                parrafos = soup.find_all('p')
                texto_limpio = "\n".join([p.get_text(strip=True) for p in parrafos if len(p.get_text()) > 20])
                
                # Extracción estructurada
                autor, fecha = extraer_metadatos_avanzado(soup)
                
                # --- APLICACIÓN DEL SEGURO (REGEX SOBRE CRUDO) ---
                # Si fallaron los métodos normales, intentamos pescar en el río revuelto del HTML
                if autor == "No encontrado" or fecha == "No encontrada":
                    autor, fecha = limpieza_regex_seguro(html_crudo, autor, fecha)
                
                resultados.append({
                    "url": url,
                    "titulo": titulo,
                    "autor": autor,
                    "fecha_publicacion": fecha,
                    "texto_noticia": texto_limpio,
                    "html_crudo": html_crudo  # <--- AQUÍ GUARDAMOS EL SEGURO
                })
                
            except Exception as e:
                tqdm.write(f"⚠️ Error en {url}: {e}")

        with open(ruta_salida, 'w', encoding='utf-8') as jf:
            json.dump(resultados, jf, ensure_ascii=False, indent=4)
        
        print(f"\n✅ Proceso terminado con respaldo HTML.")

    except Exception as e: print(f"❌ Error: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    extraer_noticias()
