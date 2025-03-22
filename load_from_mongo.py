from pymongo import MongoClient
import pandas as pd

# Conectar a MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Seleccionar base de datos y colección
db = client['corruption_db']
collection = db['news']

# Obtener todos los documentos de la colección
cursor = collection.find({})

# Convertir documentos a un DataFrame de pandas
df = pd.DataFrame(list(cursor))

# Opcional: eliminar la columna '_id' que genera MongoDB
if '_id' in df.columns:
    df.drop(columns=['_id'], inplace=True)

# Mostrar las primeras filas del DataFrame
print(df.head())
