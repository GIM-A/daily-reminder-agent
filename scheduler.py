from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from notifier import send_email
from agent import agent
from database import get_all_users

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def send_reminder_to_user(user_id: int, email: str):
    """给单个用户生成提醒并发送。"""
    result = agent.invoke({
        "messages": [("user",
            "生成今天的提醒：查一下我的待办，按截止时间由近到远排序，"
            "给我一段简短的提醒文案。如果今天没有待办，就回复一句话说明。")],
        "user_id": user_id,
    })
    content = result["messages"][-1].content
    today = datetime.now().strftime("%Y-%m-%d")
    send_email(f"每日提醒 {today}", content, to_email=email)


def daily_reminder():
    """每天 8:00：给所有用户发提醒邮件。"""
    print(f"[{datetime.now()}] 开始生成每日提醒...")
    users = get_all_users()
    for u in users:
        try:
            send_reminder_to_user(u["id"], u["email"])
            print(f"[{datetime.now()}] 已发送给 {u['username']} ({u['email']})")
        except Exception as e:
            print(f"[{datetime.now()}] 发送给 {u['username']} 失败：{e}")


def start_scheduler():
    scheduler.add_job(
        daily_reminder,
        CronTrigger(hour=8, minute=0),
        id="daily_reminder",
        replace_existing=True,
    )
    scheduler.start()
    print(f"[{datetime.now()}] Scheduler started: daily reminder at 08:00")


if __name__ == "__main__":
    import time
    start_scheduler()
    while True:
        time.sleep(60)