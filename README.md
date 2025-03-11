# Cocktail Recommendation System

## Description
This project is a cocktail recommendation system built using the FastAPI framework, PostgreSQL as the database, and OpenAI's GPT for processing user queries. The system recommends cocktails based on user preferences, stores liked and disliked cocktails, and allows users to interact with the system through a chat interface.

## Features
- Recommends cocktails based on user preferences.
- Stores user preferences (liked and disliked cocktails and ingredients) in a PostgreSQL database.
- Uses OpenAI's GPT model to process user queries and generate recommendations.
- Allows users to chat with the system to get cocktail suggestions.
- Maintains a limited history of user interactions for better context-aware responses.

## Installation

To run the project locally, follow the steps below:

1. Clone the repository:
    ```
    git clone https://github.com/artemoid-0/MixMate.git
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
    - `DATABASE_URL` - Your PostgreSQL database connection string.
    - `OPENAI_API_KEY` - Your OpenAI API key.
    - (Optional) Set up any other necessary environment variables as required.

5. Initialize the database:
    - Before running the application, set up the PostgreSQL database schema.
    - Run the database migration script:
      ```
      python create_db.py
      ```
    - This will create the necessary tables for storing cocktail data, user preferences, and message history.

6. Run the application:
    ```
    uvicorn main:app --reload
    ```

    This will start the FastAPI server on `http://localhost:8000`.

## Usage

- Open your browser and go to `http://localhost:8000`.
- You'll see a chat interface where you can type cocktail queries. The system will respond with recommendations based on your query and preferences.
- The user's preferences (liked and disliked cocktails and ingredients) are stored and updated automatically in the system.
- The system keeps track of the last few interactions to provide more relevant responses.
