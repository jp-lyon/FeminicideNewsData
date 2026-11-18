import json
import re
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse
import pandas as pd

def es_medio_colombiano(url, nombre_medio):
    url_low = url.lower()
    medio_low = str(nombre_medio).lower()

    if '.co' in url_low or 'colombia' in medio_low:
        return True

    dominios_co = [
        'eltiempo.com', 'elespectador.com', 'semana.com', 'elcolombiano.com', 
        'vanguardia.com', 'pulzo.com', 'infobae.com/colombia'
    ]
    if any(dominio in url_low for dominio in dominios_co):
        return True

    lugares_colombia = [
        'bogota', 'medellin', 'cali', 'barranquilla', 'cartagena', 'bucaramanga',
        'pereira', 'manizales', 'armenia', 'cucuta', 'ibague', 'neiva', 'villavicencio',
        'pasto', 'popayan', 'santa-marta', 'santamarta', 'tunja', 'monteria', 'valledupar',
        'quibdo', 'riohacha', 'sincelejo', 'florencia', 'yopal', 'mocoa', 'sanjose-del-guaviare',
        'antioquia', 'cundinamarca', 'valle-del-cauca', 'atlantico', 'santander', 
        'boyaca', 'caldas', 'risaralda', 'quindio', 'tolima', 'huila', 'meta'
    ]

    for lugar in lugares_colombia:
        patron = rf'[/._-]{lugar}[/._-]'
        if re.search(patron, url_low):
            return True
        
    return False

def analizar_noticias_completo(ruta_json):
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {ruta_json}")
        return

    total = len(datos)
    if total == 0:
        print("⚠️ El archivo JSON está vacío.")
        return

    vacias = 0
    sin_autor = 0
    sin_titulo = 0
    es_colombiano = 0
    es_extranjero = 0
    
    lista_fechas = []
    lista_anios = []
    anios_no_reconocidos = 0
    lista_categorias = []

    for noticia in datos:
        # 1. Origen
        url = noticia.get("url", "")
        medio = noticia.get("medio", "")
        
        if es_medio_colombiano(url, medio):
            es_colombiano += 1
            noticia["origen_colombia"] = True 
        else:
            es_extranjero += 1
            noticia["origen_colombia"] = False

        # 2. Campos vacíos
        texto = noticia.get("texto_noticia", "")
        if not texto or str(texto).strip() == "":
            vacias += 1
        
        if noticia.get("autor") in ["No encontrado", "PENDIENTE", "", None]:
            sin_autor += 1
            
        if noticia.get("titular") in ["Sin título", "", None] or not noticia.get("titular"):
            sin_titulo += 1

        # 3. Categoría de extracción (Búsqueda en llaves alternativas)
        cat = (
            noticia.get("categoria_extraccion") 
            or noticia.get("categoria") 
            or noticia.get("seccion") 
            or noticia.get("category")
            or noticia.get("tema")
        )
        if cat and str(cat).strip() != "":
            lista_categorias.append(str(cat).strip())
        else:
            lista_categorias.append("Sin Categoría")

        # 4. Procesamiento de fechas (Solución a zonas horarias y dayfirst)
        fecha_raw = noticia.get("fecha_publicacion")
        if fecha_raw and fecha_raw != "No encontrada":
            match_anio = re.search(r'(19|20)\d{2}', str(fecha_raw))
            if match_anio:
                anio = match_anio.group()
                lista_anios.append(anio)
                try:
                    # dayfirst=True quita los UserWarning
                    dt = pd.to_datetime(fecha_raw, dayfirst=True)
                    # Quita la información de zona horaria si la tiene
                    if dt.tzinfo is not None:
                        dt = dt.tz_localize(None)
                    lista_fechas.append(dt)
                except Exception:
                    pass 
            else:
                anios_no_reconocidos += 1
        else:
            anios_no_reconocidos += 1

    # --- Generación del Reporte ---
    print("="*50)
    print("📊 REPORTE GLOBAL DE EXTRACCIÓN Y ORIGEN")
    print("="*50)
    print(f"Total de noticias en JSON:    {total}")
    print("-" * 50)
    print(f"🇨🇴 Medios Colombianos:         {es_colombiano} ({round(es_colombiano/total*100, 1)}%)")
    print(f"🌎 Medios Extranjeros/Otros:   {es_extranjero} ({round(es_extranjero/total*100, 1)}%)")
    print("-" * 50)
    print(f"❌ Títulos faltantes:           {sin_titulo}")
    print(f"👤 Autores pendientes:          {sin_autor}")
    print(f"📄 Sin texto de noticia:        {vacias}")
    print("-" * 50)

    print(f"{'CATEGORÍA DE EXTRACCIÓN':<30} | {'CANTIDAD':<10}")
    print("-" * 50)
    conteo_categorias = Counter(lista_categorias)
    for cat, cantidad in conteo_categorias.most_common():
        print(f"{cat:<30} | {cantidad:<10}")

    print("-" * 50)

    if lista_fechas:
        reciente = max(lista_fechas).strftime("%d/%m/%Y")
        antigua = min(lista_fechas).strftime("%d/%m/%Y")
        print(f"🗓️  Noticia más antigua:        {antigua}")
        print(f"🗓️  Noticia más reciente:       {reciente}")

    print("-" * 50)
    print(f"{'AÑO':<15} | {'CANTIDAD DE NOTICIAS':<20}")
    print("-" * 50)

    conteo_anios = Counter(lista_anios)
    for anio in sorted(conteo_anios.keys()):
        print(f"{anio:<15} | {conteo_anios[anio]:<20}")

    if anios_no_reconocidos > 0:
        print(f"{'Desconocido':<15} | {anios_no_reconocidos:<20}")
    
    print("="*50)

if __name__ == "__main__":
    analizar_noticias_completo(r'C:\Users\jjleo\Downloads\EL ARCA\Entorno\Python\Feminismo\Primer intento\noticias_limpias_finales.json')