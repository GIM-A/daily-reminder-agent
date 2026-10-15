import requests

r = requests.post(
    "http://127.0.0.1:8000/login",
    json={"username": "蒋博宇", "password": "123456"}
)
print(r.text)