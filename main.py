import os
import re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

app = FastAPI()

templates = Jinja2Templates(directory="templates")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "cocktail-index"
INDEX_NAME_PREFERENCES = "user-preferences"
index = pc.Index(index_name)

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def retrieve_relevant_cocktails(query, top_k=50):
    query_vector = embedding_model.encode([query]).tolist()
    results = index.query(vector=query_vector[0], top_k=top_k, include_metadata=True)
    return [match["metadata"]["name"] for match in results["matches"]]

index_preferences = pc.Index(INDEX_NAME_PREFERENCES)

def retrieve_user_preferences(user_id):
    result = index_preferences.fetch(ids=[user_id])
    if result["vectors"]:
        user_data = result["vectors"][user_id]
        return user_data["metadata"]
    else:
        return None

def extract_preferences_from_query(query):
    like_pattern = r"(?:I like|I prefer|I love)\s+([a-zA-Z\s,]+)"
    dont_like_pattern = r"(?:I don't like|I hate)\s+([a-zA-Z\s,]+)"
    like_matches = re.findall(like_pattern, query, re.IGNORECASE)
    dont_like_matches = re.findall(dont_like_pattern, query, re.IGNORECASE)
    likes = [item.strip() for sublist in like_matches for item in sublist.split(",")]
    dislikes = [item.strip() for sublist in dont_like_matches for item in sublist.split(",")]
    return likes, dislikes

def update_user_preferences(user_id, likes, dislikes):
    result = index_preferences.fetch(ids=[user_id])
    if result["vectors"]:
        user_data = result["vectors"][user_id]
        user_vector = user_data["values"]
        current_likes = user_data["metadata"].get("likes", [])
        current_dislikes = user_data["metadata"].get("dislikes", [])
    else:
        user_vector = embedding_model.encode([""])
        user_vector = user_vector[0].tolist()
        user_vector = [float(val) for val in user_vector]
        current_likes = []
        current_dislikes = []
    for item in likes:
        if item in current_dislikes:
            current_dislikes.remove(item)
        if item not in current_likes:
            current_likes.append(item)
    for item in dislikes:
        if item in current_likes:
            current_likes.remove(item)
        if item not in current_dislikes:
            current_dislikes.append(item)
    metadata = {
        "likes": current_likes,
        "dislikes": current_dislikes
    }
    index_preferences.upsert(vectors=[(user_id, user_vector, metadata)])

llm = ChatOpenAI(model_name="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

prompt_template = PromptTemplate(
    input_variables=["context", "query", "user_id", "preferences", "asked_about_suggestions"],
    template="""Use following context if possible:
    {context}

    User ID: {user_id}
    User's preferences: {preferences}
    Don't mention the word "context" or similar while answering.

    Answer the question: {query}
    """
)

class QueryRequest(BaseModel):
    query: str
    user_id: str
    top_k: int = 50

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/query")
async def query_cocktail(request: QueryRequest):
    relevant_cocktails = retrieve_relevant_cocktails(request.query, top_k=request.top_k)
    context = "\n".join(relevant_cocktails)
    likes, dislikes = extract_preferences_from_query(request.query)
    update_user_preferences(request.user_id, likes, dislikes)
    preferences = retrieve_user_preferences(request.user_id)
    prompt = prompt_template.format(
        context=context,
        query=request.query,
        user_id=request.user_id,
        preferences=preferences
    )
    response = llm.invoke(prompt)
    return {"response": response, "context": context, "preferences": preferences}
