import json
import re
import os
from bs4 import BeautifulSoup
from tqdm import tqdm

def extraer_info_infalible(html):
    """
    Extrae autor y fecha buscando en metadatos JSON-LD, Meta Tags y selectores específicos.
    Este es el estándar más alto de precisión.
    """
    soup = BeautifulSoup(html, 'html.parser')
    info = {"autor": None, "fecha": None}

    # 1. BUSCAR EN JSON-LD (El estándar de oro de Google/Schema.org)
    json_ld = soup.find_all('script', type='application/ld+json')
    for script in json_ld:
        try:
            data = json.loads(script.string)
            # El JSON-LD puede ser una lista o un objeto
            items = data if isinstance(data, list) else [data]
            for item in items:
                # Buscar Fecha
                if not info["fecha"]:
                    info["fecha"] = item.get("datePublished") or item.get("dateModified") or item.get("uploadDate")
                
                # Buscar Autor
                if not info["autor"]:
                    author_data = item.get("author")
                    if isinstance(author_data, dict):
                        info["autor"] = author_data.get("name")
                    elif isinstance(author_data, list) and len(author_data) > 0:
                        info["autor"] = author_data[0].get("name")
        except:
            continue

    # 2. BUSCAR EN META TAGS (Open Graph, Twitter, Artículos)
    if not info["autor"] or not info["fecha"]:
        meta_tags = {
            "autor": [
                "author", "article:author", "og:author", "twitter:creator", 
                "sailthru.author", "parsely-author"
            ],
            "fecha": [
                "article:published_time", "publication_date", "date", 
                "og:article:published_time", "sailthru.date", "parsely-pub-date"
            ]
        }

        for clave, nombres in meta_tags.items():
            if not info[clave]:
                for nombre in nombres:
                    tag = soup.find("meta", {"name": nombre}) or soup.find("meta", {"property": nombre})
                    if tag and tag.get("content"):
                        info[clave] = tag["content"]
                        break

    # 3. ÚLTIMO RECURSO: Atributo datetime de la etiqueta <time>
    if not info["fecha"]:
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            info["fecha"] = time_tag['datetime']

    return info["autor"], info["fecha"]

def ejecutor_limpieza_profunda():
    directorio = r'C:\Users\jjleo\Downloads\EL ARCA\Entorno\Python\Feminismo'
    ruta_entrada = os.path.join(directorio, 'noticias_extraidas.json')
    ruta_salida = os.path.join(directorio, 'noticias_limpias_finales.json')

    if not os.path.exists(ruta_entrada):
        print(f"❌ No existe el archivo: {ruta_entrada}")
        return

    with open(ruta_entrada, 'r', encoding='utf-8') as f:
        datos = json.load(f)

    print(f"🚀 Procesando {len(datos)} noticias mediante Metadatos Estándar...")
    
    recuperados_a = 0
    recuperados_f = 0

    for noticia in tqdm(datos):
        if not noticia.get("html_crudo"):
            continue

        autor_meta, fecha_meta = extraer_info_infalible(noticia["html_crudo"])

        # Solo sobreescribimos si encontramos algo real
        if autor_meta:
            noticia["autor"] = str(autor_meta).strip()
            recuperados_a += 1
        
        if fecha_meta:
            noticia["fecha_publicacion"] = str(fecha_meta).strip()
            recuperados_f += 1

        # OPCIONAL: Eliminar el HTML crudo para que el archivo pese 100 veces menos
        # noticia.pop("html_crudo", None)

    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

    print(f"\n✅ EXTRACCIÓN COMPLETADA")
    print(f"📊 Autores detectados: {recuperados_a}")
    print(f"📅 Fechas detectadas:  {recuperados_f}")
    print(f"📂 Archivo generado: {ruta_salida}")

if __name__ == "__main__":
    ejecutor_limpieza_profunda()