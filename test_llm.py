import requests
import json
from datetime import datetime, timedelta

url = "http://localhost:8000/v1/chat/completions"
headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}

model = "mistralai/Mistral-Small-24B-Instruct-2501"

messages = [
    {
        "role": "system",
        "content": "You are a conversational agent that always answers straight to the point, always end your accurate response with an ASCII drawing of a cat."
    },
    {
        "role": "user",
        "content": "Give me 5 non-formal ways to say 'See you later' in French."
    },
]

data = {"model": model, "messages": messages}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json()["choices"][0]["message"]["content"])

# Sure, here are five non-formal ways to say "See you later" in French:
#
# 1. À plus tard
# 2. À plus
# 3. Salut
# 4. À toute
# 5. Bisous
#
# ```
#  /\_/\
# ( o.o )
#  > ^ <
# ```
