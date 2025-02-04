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

# 🔹 Инициализация FastAPI
app = FastAPI()

# Подключаем шаблоны
templates = Jinja2Templates(directory="templates")

# 🔹 Инициализация Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "cocktail-index"  # Имя индекса с коктейлями
INDEX_NAME_PREFERENCES = "user-preferences"
index = pc.Index(index_name)

# Модель для векторизации запросов
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


# Функция для извлечения релевантных коктейлей из базы Pinecone
def retrieve_relevant_cocktails(query, top_k=50):
    query_vector = embedding_model.encode([query]).tolist()  # Преобразуем запрос в эмбеддинг
    results = index.query(vector=query_vector[0], top_k=top_k, include_metadata=True)  # Поиск в базе
    return [match["metadata"]["name"] for match in results["matches"]]


# Подключение к индексу предпочтений Pinecone
index_preferences = pc.Index(INDEX_NAME_PREFERENCES)


# Функция для извлечения предпочтений пользователя из Pinecone по user_id
def retrieve_user_preferences(user_id):
    # Выполнение запроса для извлечения вектора и метаданных пользователя по user_id
    result = index_preferences.fetch(ids=[user_id])  # Получаем данные по user_id

    if result["vectors"]:
        # Возвращаем метаданные (например, предпочтения пользователя)
        user_data = result["vectors"][user_id]
        return user_data["metadata"]
    else:
        # Если данные не найдены, возвращаем None или другое значение
        return None


# Шаблон для извлечения предпочтений из запроса
def extract_preferences_from_query(query):
    # Регулярные выражения для поиска ключевых слов
    like_pattern = r"(?:I like|I prefer|I love)\s+([a-zA-Z\s,]+)"
    dont_like_pattern = r"(?:I don't like|I hate)\s+([a-zA-Z\s,]+)"

    # Ищем все слова после ключевых фраз
    like_matches = re.findall(like_pattern, query, re.IGNORECASE)
    dont_like_matches = re.findall(dont_like_pattern, query, re.IGNORECASE)

    likes = [item.strip() for sublist in like_matches for item in sublist.split(",")]
    dislikes = [item.strip() for sublist in dont_like_matches for item in sublist.split(",")]

    return likes, dislikes


# Функция для обновления предпочтений пользователя в Pinecone
def update_user_preferences(user_id, likes, dislikes):
    # Получаем данные пользователя, включая вектор
    result = index_preferences.fetch(ids=[user_id])  # Получаем данные по user_id

    if result["vectors"]:  # Если вектор существует
        user_data = result["vectors"][user_id]
        user_vector = user_data["values"]  # Вектор извлекаем из поля "values"
        current_likes = user_data["metadata"].get("likes", [])
        current_dislikes = user_data["metadata"].get("dislikes", [])
    else:
        # Если пользователь еще не имеет предпочтений, создаем новый вектор (можно взять пустой вектор)
        user_vector = embedding_model.encode([""])  # Создаем вектор по умолчанию

        # Преобразуем двумерный массив в одномерный и в формат float
        user_vector = user_vector[0].tolist()  # Извлекаем первый (и единственный) вектор и преобразуем в список
        user_vector = [float(val) for val in user_vector]  # Убедимся, что все значения вектора - это float

        current_likes = []
        current_dislikes = []

    # Обновляем предпочтения
    for item in likes:
        if item in current_dislikes:
            current_dislikes.remove(item)  # Убираем из dislikes, если это в dislikes
        if item not in current_likes:
            current_likes.append(item)  # Добавляем в likes, если его там нет

    for item in dislikes:
        if item in current_likes:
            current_likes.remove(item)  # Убираем из likes, если это в likes
        if item not in current_dislikes:
            current_dislikes.append(item)  # Добавляем в dislikes, если его там нет

    # Обновляем метаданные для пользователя
    metadata = {
        "likes": current_likes,
        "dislikes": current_dislikes
    }

    # Обновляем или добавляем данные в Pinecone
    index_preferences.upsert(vectors=[(user_id, user_vector, metadata)])



# 🔹 Настройка модели LLM (например, OpenAI GPT)
llm = ChatOpenAI(model_name="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

# 🔹 Шаблон для промпта
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

# 🔹 Класс запроса для API
class QueryRequest(BaseModel):
    query: str
    user_id: str  # Добавляем ID пользователя
    top_k: int = 50  # Количество рекомендаций


# 🔹 Эндпоинт для отдачи HTML-страницы чата
@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


# 🔹 Эндпоинт для обработки запросов
@app.post("/query")
async def query_cocktail(request: QueryRequest):
    # Извлекаем релевантные коктейли
    relevant_cocktails = retrieve_relevant_cocktails(request.query, top_k=request.top_k)
    context = "\n".join(relevant_cocktails)  # Формируем контекст из найденных коктейлей

    # Извлекаем предпочтения из запроса
    likes, dislikes = extract_preferences_from_query(request.query)

    # Обновляем предпочтения пользователя в Pinecone
    update_user_preferences(request.user_id, likes, dislikes)

    # Получаем предпочтения пользователя по его ID
    preferences = retrieve_user_preferences(request.user_id)

    # Формируем промпт для LLM
    prompt = prompt_template.format(
        context=context,
        query=request.query,
        user_id=request.user_id,
        preferences=preferences
    )

    # Получаем ответ от LLM
    response = llm.invoke(prompt)

    return {"response": response, "context": context, "preferences": preferences}
