import os
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# Загрузка данных из CSV для коктейлей
df = pd.read_csv('data/final_cocktails.csv')

# Настройки
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME_COCKTAILS = "cocktail-index"  # Для коктейлей
INDEX_NAME_PREFERENCES = "user-preferences"  # Для предпочтений пользователей

# Инициализация Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Удаление существующего индекса коктейлей (если есть)
if INDEX_NAME_COCKTAILS in pc.list_indexes().names():
    pc.delete_index(INDEX_NAME_COCKTAILS)
    print(f"Индекс {INDEX_NAME_COCKTAILS} удален.")

# Удаление существующего индекса предпочтений пользователей (если есть)
if INDEX_NAME_PREFERENCES in pc.list_indexes().names():
    pc.delete_index(INDEX_NAME_PREFERENCES)
    print(f"Индекс {INDEX_NAME_PREFERENCES} удален.")

# Создание индекса для коктейлей
pc.create_index(
    name=INDEX_NAME_COCKTAILS,
    dimension=384,  # Размерность эмбеддингов all-MiniLM-L6-v2
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
index_cocktails = pc.Index(INDEX_NAME_COCKTAILS)

# Создание индекса для предпочтений пользователей
pc.create_index(
    name=INDEX_NAME_PREFERENCES,
    dimension=384,  # Размерность эмбеддингов all-MiniLM-L6-v2
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
index_preferences = pc.Index(INDEX_NAME_PREFERENCES)

# Инициализация модели для векторизации
model = SentenceTransformer('all-MiniLM-L6-v2')

# Объединяем все поля коктейлей для векторизации
df['text_combined'] = df['ingredients'] + " " + df['instructions'] + " " + df['alcoholic'] + " " + df['category'] + " " + df['glassType'] + " " + df['text']

# Векторизация коктейлей
cocktail_vectors = model.encode(df['text_combined'].tolist())

# Подготовка данных для загрузки коктейлей в Pinecone
upsert_cocktails_data = []
for i, row in df.iterrows():
    # Формируем метаданные для коктейля
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

# Загрузка коктейлей в Pinecone
index_cocktails.upsert(vectors=upsert_cocktails_data)
print("Данные коктейлей успешно загружены в Pinecone!")

# Пример предпочтений пользователей
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

# Векторизация предпочтений пользователей
preferences_texts = [f"Likes: {', '.join(user['likes'])}. Dislikes: {', '.join(user['dislikes'])}." for user in example_preferences]
preference_vectors = model.encode(preferences_texts)

# Подготовка данных для загрузки предпочтений пользователей в Pinecone
upsert_preferences_data = []
for i, user in enumerate(example_preferences):
    # Формируем метаданные для предпочтений без user_id
    metadata = {
        "likes": user["likes"],
        "dislikes": user["dislikes"]
    }
    # Используем user_id как ID в индексе
    upsert_preferences_data.append((user["user_id"], preference_vectors[i].tolist(), metadata))

# Загрузка предпочтений пользователей в Pinecone
index_preferences.upsert(vectors=upsert_preferences_data)
print("Данные предпочтений пользователей успешно загружены в Pinecone!")
