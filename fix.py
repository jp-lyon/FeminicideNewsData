import json

with open(r'C:\Users\jjleo\Downloads\EL ARCA\Entorno\Python\Feminismo\captura_rapida copy.json', 'r', encoding='utf-8') as f:
    datos = json.load(f)

# Ver las claves reales del primer registro
print("🔑 Claves reales detectadas en el JSON:", list(datos[0].keys()))

# Inspeccionar una muestra de los textos de noticias
sample = datos[0]
for k, v in sample.items():
    print(f"  - {k}: {str(v)[:100]}...")