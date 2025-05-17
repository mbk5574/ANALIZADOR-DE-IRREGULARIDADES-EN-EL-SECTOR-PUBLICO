from pymongo import MongoClient
import pandas as pd

client = MongoClient('mongodb://localhost:27017/')

db = client['corruption_db']
collection = db['news']

cursor = collection.find({})

df = pd.DataFrame(list(cursor))

if '_id' in df.columns:
    df.drop(columns=['_id'], inplace=True)

print(df.head())
