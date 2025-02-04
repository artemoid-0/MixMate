import os
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

df = pd.read_csv('data/final_cocktails.csv')

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME_COCKTAILS = "cocktail-index"
INDEX_NAME_PREFERENCES = "user-preferences"

pc = Pinecone(api_key=PINECONE_API_KEY)

if INDEX_NAME_COCKTAILS in pc.list_indexes().names():
    pc.delete_index(INDEX_NAME_COCKTAILS)
    print(f"Индекс {INDEX_NAME_COCKTAILS} удален.")

if INDEX_NAME_PREFERENCES in pc.list_indexes().names():
    pc.delete_index(INDEX_NAME_PREFERENCES)
    print(f"Индекс {INDEX_NAME_PREFERENCES} удален.")

pc.create_index(
    name=INDEX_NAME_COCKTAILS,
    dimension=384,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
index_cocktails = pc.Index(INDEX_NAME_COCKTAILS)

pc.create_index(
    name=INDEX_NAME_PREFERENCES,
    dimension=384,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
index_preferences = pc.Index(INDEX_NAME_PREFERENCES)

model = SentenceTransformer('all-MiniLM-L6-v2')

df['text_combined'] = df['ingredients'] + " " + df['instructions'] + " " + df['alcoholic'] + " " + df['category'] + " " + df['glassType'] + " " + df['text']

cocktail_vectors = model.encode(df['text_combined'].tolist())

upsert_cocktails_data = []
for i, row in df.iterrows():
    metadata = {
        "name": row["name"],
        "ingredients": row["ingredients"],
        "alcoholic": row["alcoholic"],
        "category": row["category"],
        "glassType": row["glassType"],
        "text": row["text"],
        "instructions": row["instructions"],
    }
    upsert_cocktails_data.append((str(row['id']), cocktail_vectors[i].tolist(), metadata))

index_cocktails.upsert(vectors=upsert_cocktails_data)
print("Данные коктейлей успешно загружены в Pinecone!")

example_preferences = [
    {
        "user_id": "1",
        "likes": ["lemon", "vodka", "sugar"],
        "dislikes": ["mint", "ginger"],
    },
    {
        "user_id": "2",
        "likes": ["lime", "vodka", "orange juice"],
        "dislikes": ["soda", "bitter"],
    }
]

preferences_texts = [f"Likes: {', '.join(user['likes'])}. Dislikes: {', '.join(user['dislikes'])}." for user in example_preferences]
preference_vectors = model.encode(preferences_texts)

upsert_preferences_data = []
for i, user in enumerate(example_preferences):
    metadata = {
        "likes": user["likes"],
        "dislikes": user["dislikes"]
    }
    upsert_preferences_data.append((user["user_id"], preference_vectors[i].tolist(), metadata))

index_preferences.upsert(vectors=upsert_preferences_data)
print("Данные предпочтений пользователей успешно загружены в Pinecone!")
