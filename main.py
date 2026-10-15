from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Header, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from database import update_user_password   # 加到 database import 列表里

from auth import (
    decode_access_token,
    hash_password,
    verify_password,
    create_access_token,
    generate_token,
)
from database import (
    get_user_by_username,
    create_user,
    get_user_by_email,
    create_verification_token,
    get_verification_token,
    mark_token_used,
    update_email_verified,
    update_user_password,          # ← 还没加，后面要用
)
from notifier import send_verify_email, send_reset_password_email
from agent import agent as agent_app

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

VERIFY_TOKEN_EXPIRE_MINUTES = 15
PASSWORD_RESET_EXPIRE_MINUTES = 60


class ChatRequest(BaseModel):
    message: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SendVerifyEmailRequest(BaseModel):
    email: str


class VerifyEmailRequest(BaseModel):
    token: str


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest, authorization: str = Header(None, alias="Authorization")):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.replace("Bearer ", "")

    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="token 无效或已过期")

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
    if get_user_by_email(req.email):  # ← 加这一行
        return {"error": "邮箱已被注册"}
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
    return {
        "access_token": token,
        "token_type": "bearer",
        "email": user["email"],
        "email_verified": bool(user["email_verified"]),
    }

@app.post("/send-verify-email")
def send_verify_email_api(req: SendVerifyEmailRequest):
    # 1. 按 email 查用户
    user = get_user_by_email(req.email)
    if not user:
        return {"error": "该邮箱未注册"}

    # 2. 已验证过
    if user["email_verified"]:
        return {"message": "该邮箱已验证，无需重复验证"}

    # 3. 生成 token + 过期时间
    token = generate_token()
    expires_at = datetime.now() + timedelta(minutes=VERIFY_TOKEN_EXPIRE_MINUTES)

    # 4. 存库
    create_verification_token(user["id"], token, "email_verify", expires_at)

    # 5. 发邮件
    send_verify_email(req.email, token)

    return {"message": "验证邮件已发送，请查收"}


@app.post("/verify-email")
def verify_email_api(req: VerifyEmailRequest):
    # 1. 按 token 查记录
    record = get_verification_token(req.token)
    if not record:
        return {"error": "链接无效"}

    # 2. 用途检查
    if record["purpose"] != "email_verify":
        return {"error": "链接无效"}

    # 3. 过期检查
    if record["expires_at"] < datetime.now():
        return {"error": "链接已过期，请重新发送"}

    # 4. 已用检查
    if record["used_at"] is not None:
        return {"error": "链接已使用"}

    # 5. 更新用户表 + 标记 token 已用
    update_email_verified(record["user_id"])
    mark_token_used(record["id"])

    return {"message": "邮箱验证成功"}

@app.get("/verify", response_class=HTMLResponse)
def verify_page(token: str):
    # 1. 按 token 查记录
    record = get_verification_token(token)
    if not record:
        return "<h1>链接无效</h1>"

    # 2. 用途检查
    if record["purpose"] != "email_verify":
        return "<h1>链接无效</h1>"

    # 3. 过期检查
    if record["expires_at"] < datetime.now():
        return "<h1>链接已过期，请重新发送验证邮件</h1>"

    # 4. 已用检查
    if record["used_at"] is not None:
        return "<h1>该链接已使用过</h1>"

    # 5. 更新用户表 + 标记 token 已用
    update_email_verified(record["user_id"])
    mark_token_used(record["id"])

    return "<h1>✅ 邮箱验证成功！</h1><p>现在可以关闭此页面，返回登录。</p>"

class ForgotPasswordRequest(BaseModel):
    email: str


@app.post("/forgot-password")
def forgot_password_api(req: ForgotPasswordRequest):
    # 1. 按 email 查用户
    user = get_user_by_email(req.email)

    # 2. 不存在也返回同样的提示（防止邮箱枚举）
    if not user:
        return {"message": "如果该邮箱已注册，重置邮件已发送"}

    # 3. 生成 token + 过期时间
    token = generate_token()
    expires_at = datetime.now() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)

    # 4. 存库
    create_verification_token(user["id"], token, "password_reset", expires_at)

    # 5. 发邮件
    send_reset_password_email(req.email, token)

    # 6. 返回
    return {"message": "如果该邮箱已注册，重置邮件已发送"}

@app.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(token: str):
    # 1. 按 token 查记录
    record = get_verification_token(token)
    if not record:
        return "<h1>链接无效</h1>"

    # 2. 用途检查
    if record["purpose"] != "password_reset":
        return "<h1>链接无效</h1>"

    # 3. 过期检查
    if record["expires_at"] < datetime.now():
        return "<h1>链接已过期，请重新申请</h1>"

    # 4. 已用检查
    if record["used_at"] is not None:
        return "<h1>该链接已使用过</h1>"

    # 5. 返回 HTML 表单
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>重置密码</title>
    </head>
    <body>
        <h1>重置密码</h1>
        <form method="post" action="/reset-password">
            <input type="hidden" name="token" value="{token}">
            <p>新密码：<input type="password" name="new_password" required></p>
            <p>确认密码：<input type="password" name="confirm_password" required></p>
            <button type="submit">提交</button>
        </form>
    </body>
    </html>
    """

@app.post("/reset-password", response_class=HTMLResponse)
def reset_password_api(
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    # 1. 两次密码一致？
    if new_password != confirm_password:
        return "<h1>两次密码不一致</h1>"

    # 2. 密码长度
    if len(new_password) < 6:
        return "<h1>密码至少 6 位</h1>"

    # 3. 检查 token
    record = get_verification_token(token)
    if not record:
        return "<h1>链接无效</h1>"
    if record["purpose"] != "password_reset":
        return "<h1>链接无效</h1>"
    if record["expires_at"] < datetime.now():
        return "<h1>链接已过期</h1>"
    if record["used_at"] is not None:
        return "<h1>该链接已使用过</h1>"

    # 4. 哈希新密码
    new_hash = hash_password(new_password)

    # 5. 更新数据库
    update_user_password(record["user_id"], new_hash)

    # 6. 标记 token 已用
    mark_token_used(record["id"])

    # 7. 返回
    return "<h1>✅ 密码重置成功！</h1><p>现在可以用新密码登录了。</p>"