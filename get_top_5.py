import os
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Настройки Pinecone
INDEX_NAME = "cocktail-index"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# Инициализация модели для векторизации
model = SentenceTransformer('all-MiniLM-L6-v2')

# Пример поиска похожих коктейлей
query = "cocktail with light cream in highball glass"
query_vector = model.encode([query])[0]  # Векторизация запроса

# Преобразуем ndarray в список (для правильной сериализации)
query_vector = query_vector.tolist()

# Поиск похожих коктейлей с использованием именованных аргументов
result = index.query(vector=query_vector, top_k=5)

# Вывод результатов
for match in result['matches']:
    cocktail_id = match['id']
    cocktail_name = match
    score = match['score']
    print(f"Cocktail ID: {cocktail_id}, Score: {score}")
