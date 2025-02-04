import os
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

INDEX_NAME = "cocktail-index"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

model = SentenceTransformer('all-MiniLM-L6-v2')

query = "cocktail with light cream in highball glass"
query_vector = model.encode([query])[0]

query_vector = query_vector.tolist()

result = index.query(vector=query_vector, top_k=5)

for match in result['matches']:
    cocktail_id = match['id']
    cocktail_name = match
    score = match['score']
    print(f"Cocktail ID: {cocktail_id}, Score: {score}")
