# 每日提醒 Agent

一个基于 FastAPI + LangGraph 的智能待办提醒助手，支持多用户、自然语言交互、每日邮件提醒。

**🌐 在线体验**：http://8.149.236.20/

## ✨ 功能

- 🗣️ **自然语言添加待办**：说「明天下午3点交作业」，自动解析日期
- 📋 **待办管理**：查询、完成、删除、恢复
- ♻️ **软删除**：7 天内可恢复
- 👥 **多用户支持**：JWT 认证，数据隔离
- 📧 **每日提醒**：每天 8:00 自动发送邮件
- 🤖 **AI Agent**：通义千问 + LangGraph 驱动

## 🛠️ 技术栈

| 模块 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| Agent 框架 | LangGraph |
| 大模型 | 通义千问 qwen3.7-flash |
| 数据库 | MySQL 8.0 |
| 认证 | JWT + Argon2 |
| 定时任务 | APScheduler |
| 邮件 | SMTP（QQ 邮箱） |
| 前端 | 原生 HTML/CSS/JS |
| 部署 | 阿里云 ECS + Nginx + Gunicorn + systemd |

## 📐 架构
用户浏览器
↓ HTTP
Nginx（80 端口反向代理）
↓
Gunicorn（多 worker，127.0.0.1:8000）
↓
FastAPI 应用
↓
LangGraph Agent（7 个工具）
↓
MySQL

**独立的定时任务进程** `scheduler.py`：每天 8:00 遍历所有用户，调 Agent 生成提醒并发邮件。

## 🚀 本地运行

```bash
# 1. 建虚拟环境
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 2. 装依赖
pip install -r requirements.txt

# 3. 建 .env（参考 .env.example）
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY、DB_*、SMTP_*、SECRET_KEY

# 4. 启动
uvicorn main:app --reload

访问 http://127.0.0.1:8000/

📦 部署
生产环境使用 Nginx + Gunicorn + systemd。详细步骤见 NOTES.md。

📄 许可证
MIT

text

---

## 三、提交

**在 GitHub Desktop：**

1. 检查文件列表：应该只有 `NOTES.md` 和 `README.md`
2. Summary：`docs: complete deployment and production notes`
3. 点 `Commit to main`
4. 点 `Push origin`

---

## 四、可选：服务器同步

**因为 NOTES/README 不影响运行，服务器可以不同步。** 但如果你想保持一致：

```bash
cd /root/daily-reminder-agent
git pull
不用重启服务。