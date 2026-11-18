import json
import time
import os
import re
import base64
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from tqdm import tqdm

# =====================================================================
# 1. ALGORITMO DE EXTRACCIÓN (MÉTODOS AVANZADOS + REGEX SEGURO)
# =====================================================================

def limpieza_regex_seguro(html_crudo, autor_actual, fecha_actual):
    if fecha_actual == "No encontrada" or not fecha_actual:
        match_fecha = re.search(r'20[1-2][0-9][\-/][0-1][0-9][\-/][0-3][0-9]', html_crudo)
        if match_fecha:
            fecha_actual = match_fecha.group()

    if autor_actual in ["No encontrado", "PENDIENTE", "Sin autor", ""] or not autor_actual:
        patron_autor = re.search(r'(?:Por|Escrito por|By|Autor):\s?([A-Z][a-z]+\s[A-Z][a-z]+)', html_crudo)
        if patron_autor:
            autor_actual = patron_autor.group(1)

    return autor_actual, fecha_actual

def extraer_metadatos_avanzado(soup):
    autor = "No encontrado"
    fecha = "No encontrada"

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


# =====================================================================
# 2. LOGICA DE DECODIFICACIÓN Y FILTRADO GEOGRÁFICO DE PAÍS CORREGIDO
# =====================================================================

def decodificar_url_google_news(url_google):
    try:
        parsed = urlparse(url_google)
        if 'news.google.com' not in parsed.netloc:
            return url_google
        
        partes = parsed.path.split('/')
        if len(partes) < 4:
            return url_google
            
        codigo_b64 = partes[3]
        padding = len(codigo_b64) % 4
        if padding:
            codigo_b64 += '=' * (4 - padding)
            
        bytes_decodificados = base64.b64decode(codigo_b64)
        urls_encontradas = re.findall(r'https?://[^\s\x00-\x1f\x7f-\xff]+', bytes_decodificados.decode('utf-8', errors='ignore'))
        
        if urls_encontradas:
            return urls_encontradas[0]
    except Exception:
        pass
    return url_google

def es_noticia_colombiana(url_real, nombre_medio, html_crudo=""):
    url_low = url_real.lower()
    medio_low = str(nombre_medio).lower()
    
    try:
        dominio_limpio = urlparse(url_low).netloc
    except:
        dominio_limpio = url_low

    if dominio_limpio.endswith('.co') or '.co.' in dominio_limpio or '.com.co' in dominio_limpio:
        return True
        
    if 'colombia' in medio_low:
        return True

    dominios_co = [
        'eltiempo.com', 'elespectador.com', 'semana.com', 'elcolombiano.com', 
        'vanguardia.com', 'pulzo.com', 'infobae.com/colombia', 'las2orillas.co',
        'bluradio.com', 'caracol.com.co', 'rcnradio.com', 'zonacero.com', 'elheraldo.co'
    ]
    if any(dominio in url_low for dominio in dominios_co):
        return True

    lugares_colombia = [
        'bogota', 'medellin', 'cali', 'barranquilla', 'cartagena', 'bucaramanga',
        'pereira', 'manizales', 'armenia', 'cucuta', 'ibague', 'neiva', 'villavicencio',
        'pasto', 'popayan', 'santa-marta', 'santamarta', 'tunja', 'monteria', 'valledupar',
        'antioquia', 'cundinamarca', 'valle-del-cauca', 'atlantico', 'santander', 'tolima',
        'choco', 'quindio', 'risaralda', 'caldas', 'huila', 'meta', 'narino'
    ]

    for lugar in lugares_colombia:
        patron = rf'[/._-]{lugar}[/._-]'
        if re.search(patron, url_low):
            return True

    if html_crudo:
        soup_temp = BeautifulSoup(html_crudo, 'html.parser')
        texto_noticia = soup_temp.get_text().lower()
        
        patrones_contexto = [
            r'\bcolombia\b', r'\bbogotá\b', r'\bmedellín\b', r'\bcali\b', 
            r'\bbarranquilla\b', r'\bcartagena\b', r'\bcolombiano[s]?\b', r'\bcolombiana[s]?\b'
        ]
        
        coincidencias = sum(1 for p in patrones_contexto if re.search(p, texto_noticia))
        if coincidencias >= 2:
            return True

    return False


# =====================================================================
# 3. PROCESO PRINCIPAL
# =====================================================================

def re_scrapear_e_imputar_completo(ruta_json):
    ruta_gecko = r"C:\Users\jjleo\Downloads\EL ARCA\Entorno\Python\Feminismo\geckodriver.exe"
    options = Options()
    options.add_argument("--headless")
    options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
    options.set_preference("permissions.default.image", 2)
    
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo JSON: {ruta_json}")
        return

    total = len(datos)
    print(f"📋 Archivo cargado con {total} noticias totales.")

    noticias_para_reparar = []
    for idx, noticia in enumerate(datos):
        autor = noticia.get("autor", "No encontrado")
        if autor in ["No encontrado", "PENDIENTE", "Sin autor", ""] or not autor:
            noticias_para_reparar.append(idx)

    total_a_reparar = len(noticias_para_reparar)
    print(f"🔍 Se detectaron {total_a_reparar} noticias que requieren extracción activa de HTML/Autor.")

    if total_a_reparar > 0:
        print("🌐 Iniciando Firefox Webdriver en modo Headless...")
        service = Service(executable_path=ruta_gecko)
        driver = webdriver.Firefox(service=service, options=options)
        
        autores_rescatados = 0
        fechas_rescatadas = 0

        try:
            for idx in tqdm(noticias_para_reparar, desc="Extrayendo datos y asignando país", unit="noticia"):
                noticia = datos[idx]
                url_google = noticia.get("url", "")
                medio = noticia.get("medio", "")
                url_destino = decodificar_url_google_news(url_google)

                try:
                    driver.get(url_destino)
                    time.sleep(2)
                    
                    html_crudo = driver.page_source
                    soup = BeautifulSoup(html_crudo, 'html.parser')
                    
                    nuevo_autor, nueva_fecha = extraer_metadatos_avanzado(soup)
                    if nuevo_autor == "No encontrado" or nueva_fecha == "No encontrada":
                        nuevo_autor, nueva_fecha = limpieza_regex_seguro(html_crudo, nuevo_autor, nueva_fecha)
                    
                    noticia["html_crudo"] = html_crudo
                    
                    if nuevo_autor != "No encontrado":
                        noticia["autor"] = nuevo_autor
                        autores_rescatados += 1
                    else:
                        noticia["autor"] = "No encontrado"
                        
                    if noticia.get("fecha") in ["No encontrada", ""] or not noticia.get("fecha"):
                        if nueva_fecha != "No encontrada":
                            noticia["fecha"] = nueva_fecha
                            fechas_rescatadas += 1

                    # Asignación directa enderezada
                    noticia["origen_colombia"] = es_noticia_colombiana(url_destino, medio, html_crudo=html_crudo)

                except Exception as e:
                    tqdm.write(f"⚠️ Error procesando la URL {url_destino}: {e}")
                    noticia["origen_colombia"] = es_noticia_colombiana(url_destino, medio, html_crudo=noticia.get("html_crudo", ""))
                    continue

        finally:
            print("🔒 Cerrando el navegador...")
            driver.quit()

        print(f"✨ Proceso de raspado completo. Autores obtenidos de forma activa: +{autores_rescatados}")
    else:
        print("✅ No se requirió encender el navegador.")

    # --- RE-VALIDACIÓN GEOGRÁFICA COMPLETA DE SEGURIDAD EN DISCO ---
    print("\n💾 Ejecutando escaneo profundo de texto y guardando actualizaciones en el JSON...")
    
    for noticia in datos:
        url_real = decodificar_url_google_news(noticia.get("url", ""))
        html_almacenado = noticia.get("html_crudo", "")
        # Forzar sobreescritura limpia de la bandera origen_colombia
        noticia["origen_colombia"] = es_noticia_colombiana(url_real, noticia.get("medio", ""), html_crudo=html_almacenado)

    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    print("✅ Archivo JSON sobreescrito con éxito.")

    # =====================================================================
    # 4. GENERACIÓN DEL REPORTE ESTADÍSTICO FINAL CORREGIDO
    # =====================================================================
    print("\n" + "="*50)
    print("📊 REPORTE DE EXTRACCIÓN Y GEOLOCALIZACIÓN GLOBAL (ENDEREZADO)")
    print("="*50)
    
    es_colombiano, es_extranjero = 0, 0
    vacias, sin_autor, sin_titulo = 0, 0, 0
    lista_fechas, lista_anios = [], []
    anios_no_reconocidos = 0

    for noticia in datos:
        # Lógica estricta de conteo según el booleano corregido
        if noticia.get("origen_colombia") is True:
            es_colombiano += 1
        else:
            es_extranjero += 1

        texto = noticia.get("texto_noticia", "")
        if not texto or str(texto).strip() == "":
            vacias += 1
        if noticia.get("autor") in ["No encontrado", "PENDIENTE", ""]:
            sin_autor += 1
        if noticia.get("titular") == "Sin título" or not noticia.get("titular"):
            sin_titulo += 1

        fecha_final = noticia.get("fecha")
        if fecha_final and fecha_final != "No encontrada":
            match_anio = re.search(r'(19|20)\d{2}', str(fecha_final))
            if match_anio:
                anio = match_anio.group()
                lista_anios.append(anio)
                try:
                    dt = pd.to_datetime(fecha_final, format='mixed')
                    if dt.tz is not None:
                        dt = dt.tz_localize(None)
                    lista_fechas.append(dt)
                except:
                    pass
            else:
                anios_no_reconocidos += 1
        else:
            anios_no_reconocidos += 1

    print(f"Total de registros analizados: {total}")
    print("-" * 50)
    print(f"🇨🇴 Hechos en Colombia:         {es_colombiano} ({round(es_colombiano/total*100, 1)}%)")
    print(f"🌎 Hechos Internacionales:     {es_extranjero} ({round(es_extranjero/total*100, 1)}%)")
    print("-" * 50)
    print(f"❌ Títulos vacíos:              {sin_titulo}")
    print(f"👤 Autores sin recuperar:       {sin_autor}")
    print(f"📄 Registros sin texto base:    {vacias}")
    print("-" * 50)

    if lista_fechas:
        reciente = max(lista_fechas).strftime("%d/%m/%Y")
        antigua = min(lista_fechas).strftime("%d/%m/%Y")
        print(f"🗓️  Noticia más antigua:        {antigua}")
        print(f"🗓️  Noticia más reciente:       {reciente}")

    print("-" * 50)
    print(f"{'AÑO':<15} | {'NOTICIAS ENCONTRADAS':<20}")
    print("-" * 50)

    conteo_anios = Counter(lista_anios)
    for anio in sorted(conteo_anios.keys()):
        print(f"{anio:<15} | {conteo_anios[anio]:<20}")

    if anios_no_reconocidos > 0:
        print(f"{'Desconocido':<15} | {anios_no_reconocidos:<20}")
    print("="*50)


if __name__ == "__main__":
    ruta_del_json = r'C:\Users\jjleo\Downloads\EL ARCA\Entorno\Python\Feminismo\captura_rapida.json'
    re_scrapear_e_imputar_completo(r'C:\Users\jjleo\Downloads\EL ARCA\Entorno\Python\Feminismo\captura_rapida.json')