import os
import json
import pandas as pd
from pygooglenews import GoogleNews
from tqdm import tqdm
import time
import random

# Configuración básica
DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
DB_JSON = os.path.join(DIRECTORIO, "captura_rapida.json")

def captura_veloz():
    gn = GoogleNews(lang='es', country='CO')
    
    # Cargar histórico para no repetir
    if os.path.exists(DB_JSON):
        with open(DB_JSON, 'r', encoding='utf-8') as f:
            historico = json.load(f)
    else:
        historico = []
    
    urls_vistas = {n['url'] for n in historico}
    
    # Reducimos el diccionario a lo esencial para ganar velocidad
    terminos = ['feminicidio', 'mujer asesinada', 'transfeminicidio', 'crimen pasional']
    
    pbar = tqdm(range(2013, 2027), desc="🚀 Captura Relámpago")
    
    for anio in pbar:
        for mes in range(1, 13):
            for word in terminos:
                try:
                    # Búsqueda directa sin entrar a la web todavía
                    search = gn.search(f'"{word}" Colombia', from_=f"{anio}-{mes:02d}-01", to_=f"{anio}-{mes:02d}-28")
                    
                    if not search or not search['entries']:
                        continue

                    for entry in search['entries']:
                        if entry.link not in urls_vistas:
                            historico.append({
                                "id": len(historico) + 1,
                                "titular": entry.title,
                                "medio": entry.source.title,
                                "url": entry.link,
                                "fecha_publicacion": entry.published,
                                "anio": anio,
                                "mes": mes,
                                "termino_busqueda": word,
                                "autor": "PENDIENTE", # Se llenará en la etapa 2
                                "descripcion_extracto": "PENDIENTE" # Se llenará en la etapa 2
                            })
                            urls_vistas.add(entry.link)
                    
                    # Pausa mínima solo para no saturar a Google
                    time.sleep(0.5)
                except:
                    time.sleep(5) # Si hay error, pausa de seguridad
                    continue
            
            # Guardar progreso por mes
            with open(DB_JSON, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=4, ensure_ascii=False)
                
    print(f"✅ Captura finalizada. Tienes {len(historico)} noticias listas para procesar.")

if __name__ == "__main__":
    captura_veloz()