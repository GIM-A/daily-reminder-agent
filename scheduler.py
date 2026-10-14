from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from notifier import send_email
from agent import agent

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def daily_reminder():
    """每天 8:00 执行：生成提醒文案并发邮件。"""
    print(f"[{datetime.now()}] 开始生成每日提醒...")
    try:
        result = agent.invoke({
            "messages": [("user",
                "生成今天的提醒：查一下我的待办，按截止时间由近到远排序，"
                "给我一段简短的提醒文案。如果今天没有待办，就回复一句话说明。")]
        })
        content = result["messages"][-1].content
        today = datetime.now().strftime("%Y-%m-%d")
        send_email(f"每日提醒 {today}", content)
        print(f"[{datetime.now()}] 邮件已发送")
    except Exception as e:
        print(f"[{datetime.now()}] 出错：{e}")


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