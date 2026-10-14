# 每日提醒 Agent - 学习日志

> 项目：FastAPI + LangGraph 的每日提醒助手
> 技术栈：FastAPI / MySQL / LangGraph / 通义千问 / APScheduler / SMTP
> 目标：多人使用 + 部署阿里云 ECS

---

## 阶段 0：项目准备（完成）

**完成时间：** 2026-10-14

### 做了什么
- PyCharm 建项目 `D:\daily-reminder-agent`
- 建 `.venv` 虚拟环境
- 建 `.gitignore`、`.env`、`.env.example`、`data/` 文件夹
- 装全部依赖，生成 `requirements.txt`

### 问题日志
- **PowerShell 禁止运行脚本** → `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- **`.venv` 不存在** → `python -m venv .venv`
- **`data` 拼成 `date`** → `Rename-Item`

### 概念收获
- 虚拟环境隔离依赖
- `.env` 存敏感信息，不进 Git

---

## 阶段 1：最小 FastAPI（完成）

**完成时间：** 2026-10-14

### 做了什么
- `main.py` 实现 `/` 和 `/health`
- `uvicorn main:app --reload` 启动

### 问题日志
- **PyCharm 运行按钮跑不起来** → 用 uvicorn

### 概念收获
- FastAPI 用 `@app.get` 定义路由
- `uvicorn main:app` 里 `main` 是文件名，`app` 是 FastAPI 实例
- `/docs` 是自动生成的接口文档

---

## 阶段 2：POST /chat + 读 .env（完成）

**完成时间：** 2026-10-14

### 做了什么
- `main.py` 顶部加 `load_dotenv()`
- 加 `POST /chat`、`ChatRequest(BaseModel)`

### 问题日志
- **`NameError: app is not defined`** → `app = FastAPI()` 必须在 `@app.xxx` 之前

### 概念收获
- `load_dotenv()` 放最前，让后续代码读到 `.env`
- `BaseModel` 定义请求体，自动校验
- GET 查询，POST 提交

---

## 阶段 3：MySQL 存储（完成）

**完成时间：** 2026-10-14

### 做了什么
- MySQL 80 改为 `LocalSystem` 账户运行
- 建 `daily_reminder` 库、`todos` 表
- `database.py` 用 pymysql 连接
- 实现 `add_todo` / `list_todos`

### 问题日志
1. **MySQL 服务错误码 87** → binPath 末尾多了个 `MySQL80` → `sc delete` + `mysqld --install`
2. **`database.py` 函数缩进错误** → 缩进在 `init_db` 内部了，顶格
3. **`.env` 缺 `DB_NAME`** → 补上
4. **表空** → 接口日志显示从未调过 `/add`

### 概念收获
- `DictCursor` 用列名取值
- `CREATE TABLE IF NOT EXISTS` 幂等
- SELECT 不 commit，增删改要 commit
- `%s` 防 SQL 注入
- `utf8mb4` 支持中文和 emoji

---

## 阶段 4：接大模型 + LangGraph（完成）

**完成时间：** 2026-10-14

### 4.2 测试 Qwen
- `llm.py` 用 `ChatOpenAI` 调通义千问
- 模型：`qwen3.7-flash`

**问题日志：**
- **429 RateLimitError** → `qwen-turbo` 已下线 → 换 `qwen3.7-flash`

**概念收获：**
- `ChatOpenAI` 兼容通义千问
- `base_url`: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `qwen3.7-flash` 支持函数调用

### 4.3 写工具
- `tools.py` 7 个工具：get_current_time / get_pending_todos / add_todo / complete_todo / delete_todo / get_deleted_todos / restore_todo
- `database.py` 加 4 个数据库函数

**问题日志：**
- **`Asia/Beijing` 不存在** → 改 `Asia/Shanghai`
- **Windows ZoneInfo 报 tzdata 缺失** → `pip install tzdata`

**概念收获：**
- `@tool` 把普通函数变成 LLM 可识别的工具
- docstring 决定 LLM 何时调用
- `.invoke({})` 统一调用入口
- `rowcount` 判断 UPDATE 命中行数
- 软删除用 `deleted_at` 字段

### 4.4 用 LangGraph 组装 Agent
- `agent.py`：StateGraph + ToolNode + 7 个工具
- `should_continue` 条件边
- `tools → agent` 循环

**概念收获：**
- State（MessagesState）：完整对话历史
- Node / Edge / 条件边
- Agent = LLM + Tools 循环
- `.bind_tools(tools)`

### 4.5 接入 FastAPI
- `agent.py`：`app` → `agent`
- `main.py`：`from agent import agent as agent_app`
- `/chat` 改调 Agent

**概念收获：**
- 命名冲突：两个文件都有 `app`
- `[-1]` 取最终回复

---

## 阶段 5：定时任务 + 邮件（完成）

**完成时间：** 2026-10-14

### 完成内容
- `notifier.py`：smtplib 发 QQ 邮件，授权码从 .env 读
- `scheduler.py`：APScheduler + CronTrigger，每天 8:00
- `daily_reminder()`：调 Agent 生成提醒文案 + 发邮件

### 概念收获
- `BackgroundScheduler` 后台运行，不阻塞主线程
- `CronTrigger(hour=8, minute=0)` 每天 8:00
- 定时任务必须包 `try/except`

### 问题日志
- 无

---

## 阶段 6：用户表 + 登录接口（完成）

### 6.1 用户表 + 密码哈希

**完成内容：**
- MySQL 建 `users` 表
- 装 `pwdlib` + `python-jose` + `python-multipart`
- `auth.py`：hash_password / verify_password / create_access_token / decode_access_token

**概念收获：**
- 密码用哈希（不可逆），不用加密（可逆）
- Salt：同一密码每次哈希结果不同，验证时从哈希里取 salt 重算
- JWT：`header.payload.signature`，`SECRET_KEY` 用于签名
- `PasswordHash.recommended()` 默认 Argon2

**问题日志：**
1. **`passlib` + `bcrypt` 不兼容** → 改用 `pwdlib`
2. **用错 Python（系统而非 .venv）** → 激活 .venv
3. **`PasswordHashxt` 笔误** → 改成 `PasswordHash`
4. **pip 报 ProxyError** → 用清华镜像

### 6.2 注册 / 登录接口

**完成内容：**
- `database.py` 加 `get_user_by_username` / `create_user`
- `main.py` 加 `/register` 和 `/login`

**概念收获：**
- 分层设计：database 只操作数据库，auth 只做哈希，main 组织流程
- 用户名枚举漏洞：登录失败统一返回「用户名或密码错误」

### 6.3 多用户数据隔离

**完成内容：**
- `database.py` 所有待办函数加 `user_id` 参数
- `tools.py` 用 `InjectedState` 自动获取 user_id
- `agent.py` 自定义 `AgentState`（继承 MessagesState + user_id）
- `/chat` 从 `Authorization: Bearer <token>` 解析 user_id

**概念收获：**
- 数据隔离必须在数据库层做
- `InjectedState`：LangGraph 自动从 state 注入参数，LLM 看不到
- 401 Unauthorized
- Swagger UI bug：无 body 的接口，header 输入框不生效

**问题日志：**
1. **`InjectedState` 导入路径变了** → `from langgraph.prebuilt import InjectedState`
2. **`/docs` header 传不到后端** → curl 直测发现后端正常 → Swagger UI bug → 用 curl / requests 测
3. **`/add` `/list` 接口报错** → 删掉，统一走 `/chat`

## 阶段 7：前端两个页面（完成）

**完成时间：** 2026-10-14

### 完成内容
- `static/index.html`：登录表单 + 聊天界面（用 display 切换）
- `static/style.css`：卡片样式、消息气泡
- `static/app.js`：fetch 调 API、localStorage 存 token
- `main.py`：`app.mount("/static", StaticFiles(...))` + `/` 返回 index.html

### 概念收获
- **前后端分离**：前端只管展示，后端只管 API
- **localStorage**：浏览器本地存储，持久保存 token
- **fetch API**：JS 发 HTTP 请求，支持 `await`
- **Bearer token**：`Authorization: Bearer <token>` header
- **401 处理**：token 失效时清 localStorage 并切回登录页
- **静态文件挂载**：FastAPI 的 `StaticFiles` + `FileResponse`

### 问题日志
- 无

## 阶段 8：部署阿里云 ECS（完成）

**完成时间：** 2026-10-14

### 服务器信息
- 系统：Ubuntu 22.04.5 LTS
- 配置：2 核 2 GB
- 公网 IP：8.149.236.20
- 部署路径：/root/daily-reminder-agent

### 完成内容
- 装 MySQL、建库建表
- 从 GitHub clone 代码
- 建 .venv 装依赖（Python 3.10）
- 配 .env（新密钥）
- 配 Gunicorn（gunicorn_conf.py）
- 两个 systemd 服务：
  - reminder-web：Gunicorn + FastAPI
  - reminder-cron：scheduler.py 独立进程
- Nginx 反向代理 80 → 8000
- 公网访问成功

### 概念收获
- **生产架构**：Nginx → Gunicorn → FastAPI
- **scheduler 独立进程**：避免 Gunicorn 多 worker 导致重复执行
- **systemd**：开机自启 + 崩溃自动重启
- **Gunicorn + UvicornWorker**：生产级 ASGI 服务器
- **systemd 服务**：`After`、`Wants`、`Restart=always`
- **Nginx 反向代理**：`proxy_pass`、`proxy_set_header`

### 问题日志
1. **requirements.txt 在服务器上乱码** → `cat > file << 'EOF'` 重写
2. **SQLAlchemy==2.1.4 装不上**（Python 3.10） → 去掉版本锁
3. **SSH 密码不对** → 阿里云控制台重置密码



## 阶段 9：定时任务（生产级）（完成）

**完成时间：** 2026-10-14

### 完成内容
- `scheduler.py` 改成遍历所有用户发邮件
- `notifier.py` 的 `send_email` 支持指定收件人
- `database.py` 加 `get_all_users`
- `main.py` **不接入 scheduler**（生产级做法：scheduler 独立进程）

### 概念收获
- **生产级定时任务**：独立进程，不嵌入 Web 服务
- **为什么**：Web 服务用 Gunicorn 多 worker，如果 scheduler 嵌入会重复执行
- 每个用户单独 try/except，一个失败不影响其他人

### 问题日志
- 无
---

## 待做阶段

- ⏳ 阶段 6.5：邮箱验证 + 找回密码（QQ 邮箱）
- ⏳ 阶段 7：前端两页面（登录 + 聊天）
- ⏳ 阶段 8：部署阿里云 ECS
- ⏳ 阶段 9：定时任务接入 FastAPI

---

## 全局问题日志

| 阶段 | 问题 | 根因 | 解决 |
|------|------|------|------|
| 0 | PowerShell 禁止运行脚本 | Windows 执行策略 | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| 1 | PyCharm 运行按钮跑不起来 | 直接跑 main.py 不启动服务 | 用 uvicorn |
| 2 | `NameError: app is not defined` | 装饰器写在 `app = FastAPI()` 前 | 把 app 创建放最前 |
| 3 | MySQL 服务错误码 87 | binPath 多了一个参数 | 删服务重建 |
| 3 | 表空以为没写进去 | 从未调过 `/add` | 补测接口 |
| 4.2 | 429 RateLimitError | qwen-turbo 已下线 | 换 qwen3.7-flash |
| 4.3 | ZoneInfo 报时区不存在 | Asia/Beijing 不存在 | 改 Asia/Shanghai |
| 4.3 | ZoneInfo 报 tzdata 缺失 | Windows 无内置时区库 | `pip install tzdata` |
| 6.1 | passlib + bcrypt 不兼容 | passlib 停更 | 改用 pwdlib |
| 6.1 | 用错 Python | 命令行 python 指向系统 | 激活 .venv |
| 6.1 | pip 报 ProxyError | 代理干扰 PyPI | 用清华镜像 |
| 6.3 | InjectedState 导入路径变了 | 新版本移到 langgraph.prebuilt | 改 import |
| 6.3 | /docs header 传不到 | Swagger UI bug | 用 curl / requests 测 |

---

## 全局概念收获

- **FastAPI**：`@app.get/post` 装饰器定义路由，`/docs` 自动生成文档
- **Pydantic `BaseModel`**：定义请求体结构，自动校验
- **`.env`**：敏感信息不进代码、不进 Git
- **pymysql**：`DictCursor` 用列名取值；增删改要 `commit()`；`%s` 防注入
- **`@tool` 装饰器**：把函数变成 LLM 可调用的工具；docstring 决定调用时机
- **`ZoneInfo`**：处理时区，Windows 需装 `tzdata`
- **`ChatOpenAI`**：LangChain 通用模型类，兼容通义千问
- **LangGraph**：State / Node / Edge 组装 Agent
- **`InjectedState`**：自动从 state 注入参数，LLM 看不到
- **JWT**：`header.payload.signature`，`SECRET_KEY` 签名
- **哈希 vs 加密**：密码用哈希（不可逆），Salt 防彩虹表

---

## 重要约定

1. 密钥只放 `.env`，绝不进代码、不进 Git
2. 每完成一个阶段，用 GitHub Desktop 提交一次
3. 每行代码要能读懂，不懂就停下来问
4. 上下文快满时，用户会提醒，我把进度整理到这份文档

---

## 项目路线图

- ✅ 阶段 0：项目准备
- ✅ 阶段 1：最小 FastAPI
- ✅ 阶段 2：POST /chat + .env
- ✅ 阶段 3：MySQL 存储
- ✅ 阶段 4：接大模型 + LangGraph
- ✅ 阶段 5：定时任务 + 邮件
- ✅ 阶段 6：用户表 + 登录接口（含多用户隔离）
- ⏳ 阶段 6.5：邮箱验证 + 找回密码
- ⏳ 阶段 7：前端两页面
- ⏳ 阶段 8：部署阿里云 ECS
- ⏳ 阶段 9：定时任务接入 FastAPI