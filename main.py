from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from auth import (
    decode_access_token,
    hash_password,
    verify_password,
    create_access_token,
)
from database import get_user_by_username, create_user
from agent import agent as agent_app

app = FastAPI()


class ChatRequest(BaseModel):
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
def chat(req: ChatRequest, authorization: str = Header(None, alias="Authorization")):
    # 1. 从 header 拿 token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.replace("Bearer ", "")

    # 2. 解析 token 拿 user_id
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="token 无效或已过期")

    # 3. 传给 Agent
    result = agent_app.invoke({
        "messages": [("user", req.message)],
        "user_id": user_id,
    })
    reply = result["messages"][-1].content
    return {"reply": reply}


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