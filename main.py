from dotenv import load_dotenv
load_dotenv()
# 不是「为了读.env」，而是「为了让后面所有代码都能读到.env」

import os
from fastapi import FastAPI
from pydantic import BaseModel
from database import add_todo, list_todos

app = FastAPI()

class ChatRequest(BaseModel):
    #  ChatRequest是一个数据模型，它定义了「请求体长什么样」
    #  POST /chat 的请求体，必须是一个 JSON，里面有一个叫 message 的字段，类型是字符串。」
    message: str

@app.get("/")
def index():
    return {"message": "hello"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    return {"reply": f"你说的是：{req.message}"}

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