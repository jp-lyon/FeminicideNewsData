import json

# Cambia esto por la ruta de tu archivo (ej. 'C:/usuario/datos.json' o './datos.json')
ruta_archivo = r'C:\Users\jjleo\Downloads\EL ARCA\Entorno\Python\Feminismo\Primer intento\noticias_extraidas.json'

with open(ruta_archivo, 'r', encoding='utf-8') as f:
    datos = json.load(f)

# Verifica la estructura principal y cuenta
if isinstance(datos, list):
    print(f"El JSON es una lista con {len(datos)} elementos.")
elif isinstance(datos, dict):
    print(f"El JSON es un objeto con {len(datos)} claves/entradas en la raíz.")
else:
    print("El JSON contiene un valor simple (string, número, booleano), no una colección.")