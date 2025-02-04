# Cocktail Recommendation System

## Description
This project is a cocktail recommendation system built using the FastAPI framework, Pinecone vector database, and machine learning models like SentenceTransformer and OpenAI's GPT. The system recommends cocktails based on user queries and preferences stored in a Pinecone index. The user's likes and dislikes are processed to tailor recommendations, and the system leverages embeddings to match queries to relevant cocktails.

## Features
- Recommends cocktails based on user preferences.
- Stores user preferences (likes and dislikes) in Pinecone.
- Uses a machine learning model (SentenceTransformer) to generate cocktail embeddings.
- Allows users to chat with the system to get cocktail suggestions.

## Installation

To run the project locally, follow the steps below:

1. Clone the repository:
    ```
    git clone https://github.com/artemoid-0/test_task.git
    cd test_task
    ```

2. Create a virtual environment (optional but recommended):
    ```
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install dependencies:
    ```
    pip install -r requirements.txt
    ```

4. Set up your environment variables:
    - `PINECONE_API_KEY` - Your Pinecone API key.
    - `OPENAI_API_KEY` - Your OpenAI API key.
    - (Optional) Set up any other necessary environment variables as required.

5. Populate the Pinecone knowledge base:
    - Before running the application, you'll need to populate the Pinecone index with cocktail data.
    - To do this, run the `populate_knowledge_base.py` script:
      ```
      python populate_knowledge_base.py
      ```
    - This will create the necessary Pinecone indexes (`cocktail-index` and `user-preferences`) and populate them with cocktail data and user preferences.

6. Run the application:
    ```
    uvicorn main:app --reload
    ```

    This will start the FastAPI server on `http://localhost:8000`.

## Usage

- Open your browser and go to `http://localhost:8000`.
- You'll see a chat interface where you can type cocktail queries. The system will respond with recommendations based on your query and preferences.
- The user's preferences (likes and dislikes) are stored and updated automatically in the system.
