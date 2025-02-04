import requests

url = "http://127.0.0.1:8000/query"
query = "What are the 5 cocktails containing lemon?"

data = {"query": query, "top_k": 20}
response = requests.post(url, json=data)

print(response.json()['context'])
print(response.json()['response']['content'])

# for result in response.json():
#     print(result)
