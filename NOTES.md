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
- MySQL 8.0、Nginx 1.18、Python 3.10
- Gunicorn + UvicornWorker（2 worker）
- systemd 双服务：reminder-web、reminder-cron
- Nginx 反向代理 80 → 8000
- 公网访问成功

### 问题日志
1. **SQLAlchemy==2.1.4 装不上**（Python 3.10 不兼容）→ 去掉版本锁
2. **requirements.txt 编码问题** → `cat > file << 'EOF'` 重写
3. **8000 端口被旧 uvicorn 占用** → 发现旧 `reminder-agent.service` 在跑 → 停掉、disable、删除
4. **`git pull` 因未跟踪文件中止** → `rm` 后重新 pull 或 `git reset --hard origin/main`
5. **Nginx 配置冲突** → 删掉旧的 `reminder-agent` 配置
6. **本地 push 后服务器 pull 失败** → 用 `git reset --hard origin/main` 强制同步

### 概念收获
- **生产架构**：Nginx → Gunicorn → FastAPI
- **scheduler 独立进程**：避免 Gunicorn 多 worker 重复执行
- **systemd**：开机自启 + 崩溃自动重启
- **systemd 服务清理**：stop → disable → rm → daemon-reload
- **端口冲突排查**：`ss -tlnp | grep 端口`
- **SSH 提示符区分环境**：`root@server` vs `PS D:\...`
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
- ✅阶段 7：前端两页面
- ✅ 阶段 8：部署阿里云 ECS
- ✅ 阶段 9：定时任务接入 FastAPI


---

# 📚 附录：阶段 3~8 问答回顾

> 记录学习过程中提过的问题、我的回答、正确与否。方便复习和查漏补缺。

## 判定统计

| 判定 | 数量 |
|------|------|
| ✅ 完全正确 | 11 |
| ⚠️ 部分正确/需纠正 | 13 |
| ❌ 错误 | 10 |

---

## 阶段 3：MySQL 存储

### Q1：`cursorclass=pymysql.cursors.DictCursor` 有什么用？

**我的回答：** 查询结果以字典返回，方便 pymysql 数据生成

**纠正：** ⚠️ 前半句对，后半句错。

- 默认：结果是元组 `(1, '交作业', '2026-10-20 15:00')`
- 加了 DictCursor：结果是字典 `{'id': 1, 'content': '交作业', ...}`
- 好处：用 `row["content"]` 取值，**列名不变代码就不变**
- 「生成数据」说法错——是「**取值**」

### Q2：`CREATE TABLE IF NOT EXISTS` 里的 `IF NOT EXISTS` 是干嘛的？

**我的回答：** 防止原有表，如果原有表有就停止建立

**纠正：** ⚠️ 基本对，但说法不准。

- 实际是「**安静地跳过，不报错**」
- 这叫「**幂等**」（idempotent）：执行一次和执行一百次结果一样
- `init_db()` 每次启动都执行，没有它第二次启动会报 `Table already exists`

### Q3：为什么 `SELECT` 不需要 `commit()`，而 `INSERT` 需要？

**我的回答：** `SELECT` 只是读取数据，不修改数据库；`INSERT` 要改变数据库，必须提交才能生效

**判定：** ✅ 完全正确

### Q4：`%s` 占位符是干嘛的？直接用字符串拼接有什么风险？

**我的回答：** `%s` 是参数占位符，防止 SQL 注入；字符串拼接会被注入攻击

**判定：** ✅ 完全正确

### Q5：`c.rowcount` 是什么？为什么用它判断操作成功？

**我的回答：** 受影响的行数，判断数据库是否修改成功。0 表示没有，1 表示成功

**纠正：** ⚠️ 基本对，但「1 表示成功」不够普适。

- 准确说：**「大于 0」才算成功**
- 0 = 没找到符合 WHERE 条件的行
- \> 0 = 真的改了行

### Q6：为什么 `delete_todo` 是「软删除」而不是「真删除」？

**我的回答：** 因为在这个函数里定义了需要删除的数据

**纠正：** ❌ 答偏了。

- 软删除是**业务决策**，不是技术决策
- 三个理由：
  1. **误删可恢复**（7 天内）
  2. **数据可追溯**（知道用户何时删了什么）
  3. **不破坏引用**（其他表可能引用这条待办）
- 代价：表变大，每次查询要加 `deleted_at IS NULL`

---

## 阶段 4：LangGraph + 工具

### Q7：`@tool` 装饰器的作用是什么？

**我的回答：** 让 LLM 能读懂 Python 普通函数，能调用工具

**纠正：** ⚠️ 措辞要修正。

- LLM **看不到函数体**，只能看**元数据**
- 元数据是 JSON schema：`{"name": "...", "description": "...", "parameters": {...}}`
- 真正执行的是 Python，LLM 只负责「**说要调哪个工具、传什么参数**」

### Q8：docstring 为什么很重要？

**我的回答：** 相当于小型 prompt，给模型提供调用场景

**判定：** ✅ 完全正确

### Q9：为什么调用工具要 `.invoke({})` 而不是 `get_current_time()`？

**我的回答：** 让模型生成回答

**纠正：** ❌ 错。

- `.invoke()` 是 **LangChain 给所有 Tool 对象的统一调用入口**
- 加了 `@tool` 后，函数变成 `StructuredTool` 对象，**不能直接 `()` 调用**
- 为什么需要统一入口：Agent 内部要**动态调用工具**（不知道是哪个），只能通过 `.invoke(tool_input)`

### Q10：为什么 `get_pending_todos` 返回字符串，而不是 Python 列表？

**我的回答：** 用 `str` 限定了参数类型

**纠正：** ❌ 方向错了。

- 这不是「参数类型」，是**返回值类型**
- 原因是：**LLM 只能读文本，不能读 Python 对象**
- 转成字符串后，简洁、可读、LLM 直接能理解

### Q11：`t["deadline"] or "无"` 里的 `or` 是干嘛的？

**我的回答：** 逻辑或让模型能读懂如果没有 todo 就回答无

**纠正：** ⚠️ 一半对。

- 判断的不是「有没有 todo」，而是「**这条待办的 deadline 字段是不是空**」
- `A or B` 规则：A 是真值返回 A，A 是假值（`None`/`""`/`0`）返回 B
- 目的：避免输出里出现难看的 `None`，让 LLM 好读

### Q12：为什么 `add_todo` 的 docstring 强调「格式必须是 YYYY-MM-DD HH:MM」？

**我的回答：** 只有在 docstring 里，才能强制模型使用我们需要的格式

**判定：** ✅ 正确

**补充：** 不止「强制」——LLM **看不到 Python 代码**，docstring 是**对 LLM 下指令的唯一地方**。

### Q13：`deadline or None` 为什么能起作用？它把空字符串转成了什么？

**我的回答：** 因为总有内容给数据库，将空字符转成 None

**纠正：** ⚠️ 方向对，但要精确。

- `deadline = ""`（空字符串）→ `deadline or None` 返回 `None`
- 因为：**数据库的 DATETIME NULL 列不接受空字符串，只接受 `None`（即 SQL NULL）**
- 为什么参数默认值用 `""` 而不是 `None`：LLM 传参时更自然

### Q14：`StateGraph` 的 State 在这里是什么？它保存了什么数据？

**我的回答：** langgraph 的状态，保存之前调用的工具的数据

**纠正：** ⚠️ 对一半。

- State 是 `MessagesState`，本质是**完整对话历史列表**
- 里面包含：**用户消息 + LLM 回复 + 工具结果**，不只工具数据
- 为什么重要：LLM 每次决策看**完整历史**，所以知道「我刚刚调过什么」

### Q15：`should_continue` 函数的作用是什么？

**我的回答：** 判断 LLM 是否需要调工具。根据最后一条回复的 message

**判定：** ✅ 完全正确

### Q16：`graph.add_edge("tools", "agent")` 这行是干嘛的？

**我的回答：** 回到 agent 节点，把工具结果给 LLM 看，让 LLM 继续决策，循环

**判定：** ✅ 完全正确

**补充：** 循环不会死循环，LLM 自己判断何时退出。

### Q17：为什么 `from agent import agent as agent_app` 要起别名？

**我的回答：** main 和 agent 的对象不一样，main.py 是 fastapi，agent.py 是 agent

**纠正：** ⚠️ 对，但不完整。

- 真正原因：**`main.py` 里已经有 `app = FastAPI()`**
- 如果写 `from agent import app`，会**覆盖掉** FastAPI 的 `app`，服务就废了
- `as` 是**避免命名冲突 + 让语义更清楚**

### Q18：`result["messages"][-1].content` 里的 `[-1]` 是取什么？

**我的回答：** 最后一条消息，agent 根据此做出回答

**纠正：** ⚠️ 说反了。

- `[-1]` 取**最后一条消息**
- 但这条**就是 Agent 已经做完回答后的最终回复**
- 不是「Agent 根据此做回答」——是「**我们取出 Agent 的回答**」

### Q19：`AgentState(MessagesState)` 为什么要继承 `MessagesState`？

**我的回答：** 因为我们代码上还要加一个 userid

**纠正：** ⚠️ 对，但不完整。

- 核心原因：**继承是为了保留 `messages` 字段**
- 如果不继承，`state["messages"]` 会报 KeyError，LangGraph 消息机制会崩

### Q20：如果 `invoke` 时不传 `user_id` 会怎样？

**我的回答：** 会导致 invoke 乱读取用户数据

**纠正：** ❌ 错。

- 不会「乱读」，会**直接报错**：`KeyError: 'user_id'`
- `AgentState` 定义了 `user_id: int`（没默认值），不传就报错

### Q21：为什么 `state` 参数要放最后并且要有默认值 `= None`？

**我的回答：** 让模型知道谁是谁，如果没有默认值代码跑不了，因为模型会分不清用户

**纠正：** ❌ 前半句错。

- **「放最后 + `= None`」是 Python 语法要求**（有默认值的参数必须在无默认值参数之后）
- 跟「让模型知道谁是谁」无关
- 实际上：LLM **看不到** state 参数

### Q22：`get_current_time` 为什么不需要 `state`？

**我的回答：** 因为 `def get_current_time() -> str:` 不需要操作用户

**判定：** ✅ 正确

---

## 阶段 6：多用户 + JWT

### Q23：为什么密码要「哈希」而不是「加密」？

**我的回答：** 哈希更安全，输入不同的明文转换成哈希都能验证成功

**纠正：** ❌ 后半句完全错。

- **输入不同明文，验证一定失败**（`verify_password("wrong", hash)` 返回 `False`）
- **哈希 vs 加密**：
  - 加密：**可逆**（有密钥能解回明文）
  - 哈希：**不可逆**（无法反推明文）
- 为什么用哈希：数据库泄露了攻击者也无法反推
- 验证方式：不是解密对比，是「**用同样算法再哈希一次，对比两个哈希是否一致**」

### Q24：为什么每次 `hash_password("test123")` 结果都不同，但 `verify_password` 还能验证成功？

**我的回答：** 因为转换为哈希符合认证答案

**纠正：** ❌ 没说清。

- 核心是 **Salt（盐）**
- 每次哈希时随机生成一段字符串（salt），混进密码里
- 哈希结果里**包含了 salt**
- 验证时：从存储的哈希里**取出 salt**，用同样 salt + 用户输入密码**再算一遍**，对比
- Salt 作用：**防彩虹表攻击**（没 salt，同样密码永远同样哈希，可被预计算表反查）

### Q25：JWT 的 `SECRET_KEY` 是干嘛用的？泄露会怎样？

**我的回答：** 用户密码泄露会导致用户资料泄露

**纠正：** ❌ 答非所问。

- `SECRET_KEY` 用于 **JWT 的签名（sign）**
- JWT 结构：`header.payload.signature`
- `signature` = 用 `SECRET_KEY` 对 `header.payload` 做 HMAC 计算
- 验证：重新算一遍签名，对比是否一致 → 一致合法，不一致被篡改
- **泄露后果**：攻击者能**伪造任意用户的 token**，冒充任何人登录，**比密码泄露更严重**

### Q26：为什么失败时统一返回「用户名或密码错误」？

**我的回答：** 通用 token 花费更少，代码不必执行多步骤

**纠正：** ❌ 答错了。

- 这是**安全设计**，不是性能优化
- 防「**用户名枚举漏洞**」（username enumeration）
- 如果分开返回：
  - 「用户名不存在」 → 攻击者知道**这个用户名没注册**
  - 「密码错误」 → 攻击者知道**用户名存在，继续猜密码**

### Q27：为什么 `hash_password` 在 `main.py` 调用，不在 `database.py`？

**我的回答：** 因为这样符合哈希验证方式，用同样的算法再哈希一次

**纠正：** ❌ 答偏了。

- 这是**分层设计**：
  - `database.py`：只操作数据库（增删改查）
  - `auth.py`：只做哈希和 JWT
  - `main.py`：组织流程（先哈希，再存库）
- 如果 `database.py` 内部做哈希：数据库层会依赖认证层，**层次混乱**

---

## 阶段 5：定时任务

### Q28：为什么邮件授权码要放 `.env` 而不是写代码里？

**我的回答：** 防止授权码泄露

**纠正：** ⚠️ 对，但不完整。

- 还有三个理由：
  1. **好改**：换授权码只改一处
  2. **多环境**：本地和服务器可用不同配置
  3. **分工清晰**：代码是逻辑，`.env` 是配置

### Q29：`BackgroundScheduler` 和 `BlockingScheduler` 有什么区别？

**我的回答：** BackgroundScheduler 后台运行不影响主线程；BlockingScheduler 是代码唯一要运行时使用的调度器；AsyncIOScheduler 是异步调用用的

**判定：** ✅ 基本正确

### Q30：`CronTrigger(second="*/30")` 是什么意思？

**我的回答：** 没答

**补充：**

- `CronTrigger` 是按 cron 语法触发
- `second="*/30"` 表示**每 30 秒**
- `*/n` = 每 n 个单位
- 常用：`hour=8, minute=0`（每天 8:00）、`minute="*/5"`（每 5 分钟）

### Q31：为什么定时任务里要用 `try/except`？不用会怎样？

**我的回答：** 让函数加入异常处理，避免代码跑崩

**判定：** ✅ 正确

**补充：** 不用的话，异常冒泡到调度器，一次失败整个任务崩，**没有日志**。用了之后：一次失败 + 日志，下次任务照常。

### Q32：`CronTrigger(hour=8, minute=0)` 和 `CronTrigger(second="*/30")` 的区别？

**我的回答：** 是 cron 的语法，一个是每天 8 点 0 分，一个是每 30 秒

**判定：** ✅ 完全正确

---

## 阶段 6.3：多用户隔离

### Q33：为什么每个数据库函数的 `WHERE` 都要加 `user_id = %s`？

**我的回答：** 让模型明白当前用户是谁，标注唯一 id，不加 langgraph 不会传递数据

**纠正：** ❌ 答偏了。

- 这是**数据库层的隔离**，跟「模型明不明白」无关
- 不加会怎样：
  - `UPDATE todos SET done=1 WHERE id=3` → 任何用户都能改别人待办（**越权**）
  - `SELECT * FROM todos` → 看到所有人的待办
- 核心思想：**数据隔离必须在数据库层做，不信任应用层**
- 这叫「**纵深防御**」

### Q34：`InjectedState` 是什么？它和普通参数有什么区别？

**我的回答：** 让工具自动从 state 里取值，LLM 看不到这个参数，也不用传

**判定：** ✅ 完全正确

---

## 🎯 重点复习清单

**你答对的核心概念：**

- SQL 的 `commit()` 机制
- `%s` 防 SQL 注入
- docstring 的作用
- `should_continue` 和 `add_edge` 的逻辑
- `get_current_time` 不需要 state
- Cron 语法
- `try/except` 的作用
- `InjectedState` 的机制

**需要重看的重点：**

1. **哈希 vs 加密、Salt、JWT 的 `SECRET_KEY`**（Q23~Q25）
2. **`.invoke({})` 的作用**（Q9）
3. **`DictCursor` 的用途**（Q1）：取值，不是生成
4. **数据库层数据隔离**的意义（Q33）
5. **分层设计**（database / auth / main 的职责）（Q27）
6. **`@tool` 的元数据机制**（Q7）：LLM 看不到函数体
7. **`InjectedState` 的语法要求**（Q21）：Python 参数顺序

---

## 📖 学习方法建议

1. **每答完一题就判断**：不要猜，答不上就说「不知道」
2. **答错不要紧**：理解错误比「以为自己懂」好 100 倍
3. **复习用间隔**：今天的内容，明天、三天后、一周后各看一遍
4. **用自己的话重写**：不看答案，复述一遍，检验是否真懂

---

# 📅 每日复盘模板

```markdown
## YYYY-MM-DD

### ✅ 今天完成了什么
-

### ❓ 遇到的卡点
-

### 💡 学到的概念
-

### 🎯 明天要做
-
```