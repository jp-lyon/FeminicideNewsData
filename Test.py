import json
import random
import os

def generar_muestra_testing():
    # --- CONFIGURACIÓN DE RUTAS ---
    directorio = r'C:\Users\jjleo\Downloads\EL ARCA\Entorno\Python\Feminismo'
    ruta_entrada = os.path.join(directorio, 'captura_rapida.json')
    ruta_salida = os.path.join(directorio, 'TESTING_100_MUESTRAS.json')

    if not os.path.exists(ruta_entrada):
        print(f"❌ No se encontró el archivo: {ruta_entrada}")
        return

    # Leer el archivo principal
    with open(ruta_entrada, 'r', encoding='utf-8') as f:
        datos = json.load(f)

    # Verificar si tenemos suficientes noticias
    cantidad_muestras = min(100, len(datos))
    
    print(f"🎲 Seleccionando {cantidad_muestras} muestras aleatorias de un total de {len(datos)}...")

    # Selección aleatoria
    muestra_aleatoria = random.sample(datos, cantidad_muestras)

    # Filtrar solo las llaves deseadas: url, autor, fecha_publicacion
    datos_test = []
    for noticia in muestra_aleatoria:
        datos_test.append({
            "url": noticia.get("url"),
            "autor": noticia.get("autor"),
            "fecha": noticia.get("fecha_publicacion")
        })

    # Guardar el archivo de test
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(datos_test, f, ensure_ascii=False, indent=4)

    print(f"\n✅ ¡Muestra de testing lista!")
    print(f"📂 Archivo: {ruta_salida}")
    print(f"💡 Consejo: Abre este JSON y ve haciendo clic en las URLs para verificar los datos.")

if __name__ == "__main__":
    generar_muestra_testing()