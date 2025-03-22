import json
import glob
import os
from pymongo import MongoClient

# Conexión con MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['corruption_db']  
collection = db['news']

# Ruta donde están tus JSON
ruta_json = './'  # o especifica otra ruta donde guardas los archivos JSON

# Buscar todos los archivos json generados por el scraper
json_files = glob.glob(os.path.join(ruta_json, 'corruption_data_*.json'))

documentos_insertados = 0
documentos_actualizados = 0

# Procesar cada archivo json
for json_file in json_files:
    with open(json_file, encoding='utf-8') as file:
        items = json.load(file)

    # Iterar por cada item del json actual
    for item in items:
        resultado = collection.update_one(
            {'link': item['link']},  # Evita duplicados con 'link'
            {'$set': item},
            upsert=True
        )
        
        if resultado.upserted_id:
            documentos_insertados += 1
        else:
            documentos_actualizados += 1

print(f"Documentos insertados: {documentos_insertados}")
print(f"Documentos actualizados: {documentos_actualizados}")
