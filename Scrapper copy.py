import os
import json
import pandas as pd
from pygooglenews import GoogleNews
from tqdm import tqdm
import time
import random
# --- COMPONENTES DEL BLINDAJE DE RED CONTRA CRASHES ---
from http.client import RemoteDisconnected
from urllib.error import URLError

# --- CONFIGURACIÓN DE RUTAS ---
DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
DB_JSON = os.path.join(DIRECTORIO, "captura_rapida.json")

# --- DICCIONARIO COMPLETO ---
DICCIONARIO = {
    'A': ['feminicidio', 'femicidio', 'feminicida', 'crimen de género', 'violencia de género mujer asesinada', 'homicidio por razones de género', 'asesinato de mujer', 'transfeminicidio', 'femicidio transfóbico'],
    'B': ['crimen pasional', 'tragedia pasional', 'crimen familiar mujer muerta', 'drama familiar mujer', 'riña de pareja mujer muerta', 'problema conyugal mujer', 'celos mujer asesinada', 'hombre mata a su pareja', 'ex pareja mata mujer'],
    'C': ['mujer asesinada', 'mujer hallada sin vida', 'mujer encontrada muerta', 'cuerpo de mujer', 'madre asesinada', 'joven asesinada', 'mujer ultimada', 'mujer occisa', 'mujer embarazada asesinada', 'niña asesinada violencia'],
    'D': ['mujer indígena asesinada', 'mujer campesina asesinada', 'lideresa asesinada', 'defensora derechos humanos asesinada', 'mujer afrocolombiana asesinada', 'mujer migrante venezolana asesinada', 'mujer desaparecida', 'trabajadora sexual asesinada'],
    'E': ['Ley Rosa Elvira Cely', 'condena feminicidio', 'sentencia feminicidio', 'capturado feminicidio', 'alerta feminicidio', 'medida de protección feminicidio', 'ruta atención violencia mujer', 'Fiscalia feminicidio', 'defensoría mujer asesinada', 'violencia intrafamiliar mujer muerta'],
    'F': ['mujer asesinada paramilitares', 'mujer asesinada guerrilla', 'violencia sexual conflicto mujer', 'mujer asesinada zona rural', 'lideresa social asesinada', 'reincorporada asesinada']
}

def captura_veloz_completa():
    gn = GoogleNews(lang='es', country='CO')
    
    # --- 1. CARGAR HISTÓRICO Y AUTO-RECUPERACIÓN ---
    if os.path.exists(DB_JSON):
        with open(DB_JSON, 'r', encoding='utf-8') as f:
            historico = json.load(f)
        print(f"📦 Checkpoint detectado. Reanudando con {len(historico)} noticias salvadas.")
    else:
        historico = []
        print("🆕 No se detectó historial previo. Iniciando desde cero.")
    
    urls_vistas = {n['url'] for n in historico}
    
    # Valores por defecto para el inicio de la línea de tiempo
    ultimo_anio = 2013
    ultimo_mes = 1
    
    # Calcular dinámicamente dónde retomar basándose en los datos salvados
    if historico:
        ultimo_anio = max(n['anio'] for n in historico)
        noticias_ultimo_anio = [n for n in historico if n['anio'] == ultimo_anio]
        if noticias_ultimo_anio:
            ultimo_mes = max(n['mes'] for n in noticias_ultimo_anio)

    # Aplanamos el diccionario para iterar fácilmente
    lista_terminos = []
    for cat, palabras in DICCIONARIO.items():
        for p in palabras:
            lista_terminos.append((cat, p))

    # Barra principal por años
    anios = range(2013, 2027)
    pbar_global = tqdm(anios, desc="🚀 Progreso Global")

    for anio in pbar_global:
        # Si el año ya fue completado e indexado, saltarlo
        if anio < ultimo_anio:
            continue
            
        for mes in range(1, 13):
            # Si estamos en el año del corte pero el mes ya se guardó, saltarlo
            if anio == ultimo_anio and mes <= ultimo_mes:
                continue
                
            pbar_global.set_postfix({"Año": anio, "Mes": mes, "Total": len(historico)})
            
            # Barra secundaria por términos del diccionario
            for cat, word in tqdm(lista_terminos, desc=f"🔎 Buscando en {mes}/{anio}", leave=False):
                search = None
                
                # --- SUB-BUCLE DE TOLERANCIA A FALLOS DE RED (3 Intentos con backoff) ---
                for intento in range(3):
                    try:
                        search = gn.search(f'"{word}" Colombia', from_=f"{anio}-{mes:02d}-01", to_=f"{anio}-{mes:02d}-28")
                        break  # Si tiene éxito, salimos de los reintentos
                    except (RemoteDisconnected, URLError, Exception) as e:
                        # Si Google o la red nos desconecta, esperamos un tiempo progresivo
                        tiempo_espera = 15 * (intento + 1)
                        tqdm.write(f"⚠️ Error de red ({type(e).__name__}) en '{word}'. Reintentando en {tiempo_espera}s...")
                        time.sleep(tiempo_espera)
                
                # Si fallaron los reintentos o no hay entradas, pasamos al siguiente término
                if not search or not search.get('entries'):
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
                            "categoria": cat,
                            "termino_busqueda": word,
                            "autor": "PENDIENTE",
                            "texto_noticia": "" 
                        })
                        urls_vistas.add(entry.link)
                
                # Delay variable anti-bloqueo aleatorio
                time.sleep(random.uniform(0.4, 0.9))
            
            # Guardar progreso después de cada mes (Checkpoint seguro y atómico)
            with open(DB_JSON, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=4, ensure_ascii=False)
                
    print(f"\n✅ CAPTURA FINALIZADA: {len(historico)} registros únicos encontrados.")

if __name__ == "__main__":
    try:
        captura_veloz_completa()
    except KeyboardInterrupt:
        print("\n🛑 Proceso pausado de forma segura por el usuario. El checkpoint del último mes está intacto.")