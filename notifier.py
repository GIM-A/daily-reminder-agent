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


def send_email(subject: str, body: str, to_email: str) -> None:
    """发送纯文本邮件。to_email 是收件人。"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = Header(subject, "utf-8")

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())


if __name__ == "__main__":
    send_email("测试邮件", "这是一封测试邮件。", to_email=os.getenv("SMTP_USER", ""))
    print("邮件已发送")