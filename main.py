import json
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from pydantic import BaseModel
from tools_functions import *

# Initialize FastAPI app and templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize LLM with OpenAI API key
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class UserQuery(BaseModel):
    user_input: str  # Defines the expected input format


@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    """Returns the chat page with the required template."""
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post("/cocktail_request")
async def handle_cocktail_request(user_query: UserQuery, user_id: int = Depends(get_user_id)):
    """Handles user cocktail requests by parsing them with LLM and querying the database."""
    try:
        # Retrieve user's message history from the database
        with Session(engine) as session:
            user_data = session.query(UserData).filter_by(user_id=user_id).first()
            message_history = user_data.message_history if user_data else []

        # Construct conversation history for LLM
        messages = [{"role": "system", "content": "You are a cocktail assistant. "
                                                 "Your job is to provide users with information about cocktails they ask for, "
                                                 "as well as to recommend cocktails if requested."}]

        # Append previous user-bot exchanges
        for pair in message_history:
            messages.append({"role": "user", "content": pair["user"]})
            messages.append({"role": "assistant", "content": pair["bot"]})

        # Add the current user query
        messages.append({"role": "user", "content": user_query.user_input})

        # Generate response using LLM
        completion = llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )

        tool_calls = []
        retrieved_info = []
        retrieved_preferences = None
        llm_response = None

        # Process tool calls from the LLM response
        if completion.choices[0].message.tool_calls:
            for tool_call_obj in completion.choices[0].message.tool_calls:
                tool_call = tool_call_obj.function.name
                arguments = json.loads(tool_call_obj.function.arguments)
                arguments["user_id"] = user_id  # Ensure user_id is included
                tool_calls.append({"name": tool_call, "arguments": arguments})

                # Call the corresponding function based on LLM request
                if tool_call == "parse_cocktail_info_request":
                    retrieved_info.extend(parse_cocktail_info_request(**arguments))
                elif tool_call == "parse_cocktail_recommendation_request":
                    retrieved_info.extend(parse_cocktail_recommendation_request(**arguments))
                elif tool_call == "parse_cocktail_similar_request":
                    retrieved_info.extend(parse_cocktail_similar_request(**arguments))
                elif tool_call == "update_user_preferences":
                    update_user_preferences(**arguments)
                elif tool_call == "get_user_preferences":
                    retrieved_preferences = get_user_preferences(**arguments)
                elif tool_call == "clear_user_preferences":
                    clear_user_preferences(**arguments)

        # Generate LLM response based on retrieved data
        if retrieved_info:
            cocktail_text = "\n".join([f"- {c.name}: {c.instruction}" for c in retrieved_info])
            messages.append({"role": "assistant",
                             "content": f"I have found the following cocktails based on your request:\n{cocktail_text}"})
            messages.append({"role": "user", "content": "Please generate a response based on this information."})

        if retrieved_preferences:
            preferences_text = json.dumps(retrieved_preferences, indent=2)
            messages.append({"role": "assistant",
                             "content": f"The user's preferences are:\n{preferences_text}."
                                        f"Consider these preferences when generating your response."})

        # Generate final response
        llm_response = llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        ).choices[0].message.content

        # Update message history in the database
        with Session(engine) as session:
            update_message_history(session, user_id, user_query.user_input, llm_response)

        return {
            "tool_calls": tool_calls,
            "retrieved_info": [c.__dict__ for c in retrieved_info] if retrieved_info else None,
            "retrieved_preferences": retrieved_preferences if retrieved_preferences else None,
            "llm_response": llm_response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))