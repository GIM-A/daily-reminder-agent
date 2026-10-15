import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def send_email(subject: str, body: str, to_email: str) -> None:
    """发送纯文本邮件。to_email 是收件人。"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = Header(subject, "utf-8")

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())


def send_verify_email(to_email: str, token: str) -> None:
    """发送邮箱验证邮件，邮件里带验证链接。"""
    link = f"{BASE_URL}/verify?token={token}"
    body = (
        f"你好，\n\n"
        f"请点击下面的链接验证你的邮箱：\n"
        f"{link}\n\n"
        f"链接 15 分钟内有效。\n"
        f"如果这不是你本人操作，请忽略此邮件。"
    )
    send_email("【每日提醒】邮箱验证", body, to_email)

def send_reset_password_email(to_email: str, token: str) -> None:
    """发送找回密码邮件，邮件里带重置链接。"""
    link = f"{BASE_URL}/reset-password?token={token}"
    body = (
        f"你好，\n\n"
        f"请点击下面的链接重置密码：\n"
        f"{link}\n\n"
        f"链接 1 小时内有效。\n"
        f"如果这不是你本人操作，请忽略此邮件。"
    )
    send_email("【每日提醒】重置密码", body, to_email)

if __name__ == "__main__":
    send_email("测试邮件", "这是一封测试邮件。", to_email=os.getenv("SMTP_USER", ""))
