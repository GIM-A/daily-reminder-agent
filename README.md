# 每日提醒 Agent

一个基于 FastAPI + LangGraph 的智能待办提醒助手。

**在线体验**：http://8.149.236.20/

## 功能

- 自然语言添加待办（自动解析日期）
- 查询、完成、删除待办
- 软删除机制：7 天内可恢复
- 多用户支持（JWT 认证）
- 每天 8:00 自动邮件提醒

## 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | FastAPI + Gunicorn |
| Agent | LangGraph + 通义千问 |
| 数据库 | MySQL 8.0 |
| 认证 | JWT + Argon2 |
| 定时任务 | APScheduler |
| 邮件 | SMTP（QQ 邮箱） |
| 部署 | 阿里云 ECS + Nginx + systemd |

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 创建 .env，填入：
# DASHSCOPE_API_KEY / DB_* / SMTP_* / SECRET_KEY

uvicorn main:app --reload

##  部署
生产环境用 Gunicorn + Nginx + systemd。
详细步骤见 NOTES.md。


---

## 提交步骤

**在 GitHub Desktop 里：**

1. **确认文件列表**应该有 3 个：
   - ✅ `NOTES.md`（已修改）
   - ✅ `gunicorn_conf.py`（新增，你还没建）
   - ✅ `README.md`（修改）

2. **Summary 填**：`feat: production deployment`

3. **点 `Commit to main`**

4. **点 `Push origin`**（推送到 GitHub）

---

## 然后服务器更新

**因为服务器是从 GitHub clone 的，本地推上去后，服务器上要拉最新的：**

```bash
cd /root/daily-reminder-agent
git pull

systemctl restart reminder-web
systemctl restart reminder-cron
systemctl status reminder-web
curl http://127.0.0.1:8000/health
