from dotenv import load_dotenv
load_dotenv()
# 不是「为了读.env」，而是「为了让后面所有代码都能读到.env」

import os
from fastapi import FastAPI
from pydantic import BaseModel
from database import add_todo, list_todos
from agent import agent as agent_app
from auth import hash_password, verify_password, create_access_token
from database import get_user_by_username, create_user

app = FastAPI()

class ChatRequest(BaseModel):
    #  ChatRequest是一个数据模型，它定义了「请求体长什么样」
    #  POST /chat 的请求体，必须是一个 JSON，里面有一个叫 message 的字段，类型是字符串。」
    message: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/")
def index():
    return {"message": "hello"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    result = agent_app.invoke({"messages": [("user", req.message)]})
    reply = result["messages"][-1].content
    return {"reply": reply}

@app.get("/debug-env")
def debug_env():
    return {"key_loaded": bool(os.getenv("DASHSCOPE_API_KEY"))}

@app.post("/add")
def add(req: ChatRequest):
    new_id = add_todo(req.message)
    return {"id": new_id, "message": f"已添加待办：{req.message}"}

@app.get("/list")
def list_all():
    todos = list_todos()
    return {"count": len(todos), "todos": todos}

@app.post("/register")
def register(req: RegisterRequest):
    if get_user_by_username(req.username):
        return {"error": "用户名已存在"}
    hashed = hash_password(req.password)
    user_id = create_user(req.username, req.email, hashed)
    return {"id": user_id, "username": req.username}

@app.post("/login")
def login(req: LoginRequest):
    user = get_user_by_username(req.username)
    if not user:
        return {"error": "用户名或密码错误"}
    if not verify_password(req.password, user["password_hash"]):
        return {"error": "用户名或密码错误"}
    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "bearer"}