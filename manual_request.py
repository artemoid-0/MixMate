import requests

# Base URL of the FastAPI server
BASE_URL = "http://localhost:8000"  # Ensure your server is running on this port

def get_recommendations(user_input: str):
    url = f"{BASE_URL}/cocktail_request"
    payload = {"user_input": user_input}
    headers = {
        "Content-Type": "application/json",
        "X-User-ID": "1"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed with status code {response.status_code}", "details": response.text}

# Uncomment one of the user_input lines below to test different scenarios
# user_input = "Suggest some cocktail similar to margarita, but not daiquiri, with sugar in it"
# user_input = "Please provide information for the following 2 cocktails: [Margarita, Corpse Reviver]."
# user_input = "How are you today?"
# user_input = "What do you think about margarita?"
# user_input = "Recommend me a cocktail containing these ingredients: dark rum, lemon juice and grenadine"
# user_input = "Suggest me a cocktail containing triple sec and lemon juice"
# user_input = "Suggest me a cocktail containing sugar, but without alcohol"
# user_input = "Recommend me a cocktail with sugar"
# user_input = "Find cocktails similar to Margarita, but with no lime juice"
# user_input = "Find cocktails similar to Daiquiri, and give me information about Caipirinha"
# user_input = "Find cocktails similar to Daiquiri, and give me information about Casa Blanca"
# user_input = "I like lime juice"
# user_input = "Show me my preferences"
# user_input = "Please, erase my preferences. Let's start from the very beginning!"
# user_input = "I like margarita"
# user_input = "Suggest me a cocktail containing tequila"
# user_input = "I want to know about a cocktail with name something like vampire, can't recall it"
user_input = "I like sugar, could you recommend me something with it?"

result = get_recommendations(user_input)

print(result)
if "tool_calls" in result:
    print(result["tool_calls"])
if "retrieved_info" in result and result["retrieved_info"]:
    print("GOT RETRIEVED INFO")
    for c in result["retrieved_info"]:
        print(c["id"], c["name"])
if "llm_response" in result:
    print(result["llm_response"])
