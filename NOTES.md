# 每日提醒 Agent - 学习日志

> 项目：FastAPI + LangGraph 的每日提醒助手
> 技术栈：FastAPI / MySQL / LangGraph / 通义千问 / APScheduler / SMTP
> 目标：多人使用 + 部署阿里云 ECS

---

## 阶段 0：项目准备

**完成时间：** 2026-10-14

### 做了什么
- PyCharm 建项目 `D:\daily-reminder-agent`，解释器选 `Project venv`
- 建 `.venv` 虚拟环境
- 建 `.gitignore`、`.env`、`.env.example`、`data/` 文件夹
- 安装依赖：fastapi / uvicorn / python-dotenv / pymysql / sqlalchemy / apscheduler / langgraph / langchain-openai / langchain-core / openai / requests
- 生成 `requirements.txt`

### 问题日志
- **PowerShell 激活 `.venv` 报「禁止运行脚本」**
  - 原因：Windows 默认执行策略限制
  - 解决：`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- **`.venv` 不存在**
  - 原因：PyCharm 建项目时没勾选「创建虚拟环境」
  - 解决：`python -m venv .venv`
- **`data` 拼成了 `date`**
  - 解决：`Rename-Item -Path "date" -NewName "data"`

### 概念收获
- 虚拟环境隔离项目依赖
- `.env` 存敏感信息，不进 Git
- `requirements.txt` 记录依赖版本

---

## 阶段 1：最小 FastAPI

**完成时间：** 2026-10-14

### 做了什么
- 写 `main.py`，实现 `/` 和 `/health` 两个路由
- 用 `uvicorn main:app --reload` 启动
- 浏览器访问 `/docs` 看到 FastAPI 自动生成的接口文档

### 问题日志
- **PyCharm 里点运行按钮跑不起来**
  - 原因：直接运行 `main.py` 不会启动 Web 服务
  - 解决：用 `uvicorn main:app --reload`

### 概念收获
- FastAPI 用 `@app.get("/路径")` 装饰器定义路由
- `uvicorn main:app` 里 `main` 是文件名，`app` 是 FastAPI 实例
- `/docs` 是 FastAPI 自动生成的交互式文档

---

## 阶段 2：POST /chat + 读 .env

**完成时间：** 2026-10-14

### 做了什么
- `main.py` 顶部加 `load_dotenv()`
- 加 `POST /chat` 接口
- 加 `GET /debug-env` 接口测试环境变量
- 用 `ChatRequest(BaseModel)` 定义请求体

### 问题日志
- **`NameError: name 'app' is not defined`**
  - 原因：`@app.get("/debug-env")` 写在了 `app = FastAPI()` 之前
  - 解决：`app = FastAPI()` 必须在所有 `@app.xxx` 之前

### 概念收获
- `load_dotenv()` 必须放在其他 import 之前，让后续代码能读到 `.env`
- `BaseModel` 用于定义请求体的结构，FastAPI 自动校验
- GET 用于查询（参数在 URL），POST 用于提交（参数在 body）

---

## 阶段 3：MySQL 存储

**完成时间：** 2026-10-14

### 做了什么
- MySQL 80 改为 `LocalSystem` 账户运行
- 建 `daily_reminder` 库（utf8mb4）和 `todos` 表
- 写 `database.py`，用 pymysql 连接 MySQL
- 实现 `add_todo()` / `list_todos()`
- `main.py` 加 `POST /add` 和 `GET /list` 接口
- 用 `/docs` 测试接口，验证数据真写进了 MySQL

### 问题日志

1. **MySQL 服务启动失败，错误码 87「参数错误」**
   - 排查过程：
     1. 先怀疑端口冲突 → 排除
     2. 再怀疑服务账户权限（`NetworkService` 无法访问 D 盘）→ 改 `LocalSystem` 后仍失败
     3. `sc.exe qc MySQL80` 查看 `BINARY_PATH_NAME` → **末尾多了一个 `MySQL80`**
   - 根因：服务注册时把服务名当参数写进了 binPath，`mysqld.exe` 不认这个参数
   - 解决：`sc.exe delete MySQL80` → `mysqld.exe --install MySQL80 --defaults-file="D:\MySQL80\my.ini"`
   - 教训：服务启动失败，优先看 `sc.exe qc` 的 `BINARY_PATH_NAME` 和错误码

2. **`database.py` 函数缩进错误**
   - 现象：`add_todo` 和 `list_todos` 被缩进到 `init_db()` 内部，变成局部函数
   - 原因：Python 缩进是语法，函数不能在别的函数里（除非故意嵌套）
   - 解决：把两个函数顶格写

3. **`.env` 里缺少 `DB_NAME`**
   - 原因：漏写了
   - 解决：补上 `DB_NAME=daily_reminder`

4. **表是空的，以为没写进去**
   - 原因：接口日志显示只调过 `/chat` 和 `/list`，**从未调过 `/add`**
   - 解决：在 `/docs` 里补测 `POST /add`
   - 教训：接口返回 200 不等于数据进了库，要看数据库

### 概念收获
- `DictCursor`：查询结果返回字典，方便用 `row["content"]` 取值（默认是元组，靠下标取值容易出错）
- `CREATE TABLE IF NOT EXISTS`：保证幂等，重复执行不报错
- `SELECT` 不需要 `commit()`，`INSERT` / `UPDATE` / `DELETE` 必须 `commit()`
- `%s` 占位符防止 SQL 注入，别用字符串拼接
- MySQL `utf8mb4` 字符集能存中文和 emoji
- Windows 服务启动失败，先看 `sc.exe qc` 和错误码

---

## 阶段 4：接大模型 + LangGraph

### 4.1 概念学习（尚未开始）
- **LLM**：会理解人话的 API，但不会查数据库
- **Tool**：普通 Python 函数，加 `@tool` 装饰器让大模型认识
- **Agent**：LLM + Tools，LLM 决定调哪个工具，Python 真正执行
- **LangGraph**：管理「LLM ↔ 工具」循环的框架

### 4.2 测试 Qwen 模型

**完成时间：** 2026-10-14

#### 做了什么
- 写 `llm.py`，用 `ChatOpenAI` 调通义千问
- 模型选 `qwen3.7-flash`

#### 问题日志
- **`429 RateLimitError`，连续两次**
  - 原因：`qwen-turbo` 已于 2026-10-10 下线
  - 解决：换成 `qwen3.7-flash`
  - 教训：报错不一定是代码问题，也可能是模型/账号层面的变动

#### 概念收获
- `ChatOpenAI` 是 LangChain 提供的「兼容 OpenAI 接口」的模型类
- 通义千问的 `base_url`：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- `llm.invoke("消息")` 发消息，`response.content` 取回复
- `qwen3.7-flash` 支持 **函数调用**，是做 Agent 的关键

### 4.3 写工具

**进行中：** 2026-10-14

#### 已完成
- 写 `get_current_time` 工具（带 `@tool` 装饰器）
- 跑通 `.invoke({})` 调用方式

#### 问题日志
1. **`ZoneInfo("Asia/Beijing")` 报时区不存在**
   - 原因：IANA 时区标准里没有 `Asia/Beijing`，中国用 `Asia/Shanghai`
   - 解决：改成 `Asia/Shanghai`

2. **Windows 下 ZoneInfo 报 tzdata 缺失**
   - 原因：Windows 系统没有内置 tzdata 时区库
   - 解决：`.venv\Scripts\pip.exe install tzdata`
   - 教训：Windows 用 ZoneInfo 必须额外装 tzdata，Linux 不用

#### 概念收获
- `@tool` 装饰器：把普通函数变成大模型能识别的工具
- docstring：大模型靠它判断「什么时候用这个工具」，**写得越清楚，Agent 越聪明**
- `ZoneInfo`：Python 3.9+ 内置，处理时区
- `.invoke({})`：Tool 对象的统一调用方式，参数是字典

#### 待完成
- `get_pending_todos`
- `add_todo`
- `complete_todo`
- `delete_todo`
- `get_deleted_todos`
- `restore_todo`

### 4.3 写工具（完成）

**完成时间：** 2026-10-14

#### 完成内容
- `tools.py` 里 7 个工具全部写完：get_current_time / get_pending_todos / add_todo / complete_todo / delete_todo / get_deleted_todos / restore_todo
- `database.py` 里加 4 个数据库函数：complete_todo / delete_todo / get_deleted_todos / restore_todo
- 全流程测试通过：完成 → 删除 → 查已删除 → 恢复

#### 概念收获
- `@tool` 装饰器把普通函数包装成 LLM 可识别的「工具对象」，LLM 看不到函数体，只能看元数据（名字、参数、docstring）
- docstring 是对 LLM 下指令的唯一地方
- `.invoke({})` 是 LangChain Tool 对象的统一调用入口
- `c.rowcount` 判断 UPDATE 是否命中目标行
- 软删除：不真删数据，用 `deleted_at` 字段标记，7 天内可恢复
### 4.4 用 LangGraph 组装 Agent（完成）

**完成时间：** 2026-10-14

#### 完成内容
- 写 `agent.py`，用 StateGraph 组装 LLM + 7 个工具
- 实现 should_continue 条件边
- 实现 tools → agent 的循环
- 测试「现在几点」→ LLM 自动调 get_current_time

#### 概念收获
- State（MessagesState）：整个对话历史的列表
- Node：函数节点（call_model、tool_node）
- Edge：固定边（tools → agent）和条件边（agent → tools/END）
- Agent 是一个循环：LLM → 工具 → LLM → …直到 LLM 不再调工具
- `.bind_tools(tools)` 让 LLM 知道有哪些工具可用

### 4.5 接入 FastAPI（完成）

**完成时间：** 2026-10-14

#### 完成内容
- `agent.py`：`app = graph.compile()` 改成 `agent = graph.compile()`
- `main.py`：`from agent import agent as agent_app`
- `/chat` 接口改为调用 Agent，返回 `result["messages"][-1].content`

#### 概念收获
- 命名冲突：`agent.py` 和 `main.py` 里都有 `app` 变量，import 时要小心
- 用 `as` 起别名避免冲突，同时让语义更清楚
- Agent 返回的是完整消息列表，`[-1]` 取最终回复

#### 问题日志
- 无

#### 问题日志
- 无（这次跑得顺利）

---

## 阶段 5：定时任务 + 邮件（未开始）


### 6.1 用户表 + 密码哈希（完成）

**完成时间：** 2026-10-14

#### 完成内容
- MySQL 建 `users` 表（id / username / email / password_hash / created_at）
- 装 `pwdlib` + `python-jose` + `python-multipart`
- 写 `auth.py`：hash_password / verify_password / create_access_token / decode_access_token
- 生成 `SECRET_KEY` 放进 `.env`

#### 概念收获
- 密码哈希用 `pwdlib`（比停更的 `passlib` 更现代）
- `PasswordHash.recommended()` 默认 Argon2
- JWT 用 `python-jose`，payload 里放 user_id + 过期时间
- `SECRET_KEY` 用于签名，泄露可被伪造 token

#### 问题日志
1. **`passlib` + `bcrypt` 版本不兼容**
   - 原因：passlib 停更，新版 bcrypt 改了 API
   - 解决：改用 `pwdlib`
2. **用错了 Python（系统 Python 而不是 .venv）**
   - 现象：pip list 有 pwdlib，但 python auth.py 报 ModuleNotFoundError
   - 解决：激活 .venv 或用 `.venv\Scripts\python.exe`
3. **`from pwdlib import PasswordHashxt` 笔误**
   - 解决：改成 `PasswordHash`


### 6.2 注册 / 登录接口（完成）

**完成时间：** 2026-10-14

#### 完成内容
- `database.py` 加 `get_user_by_username` / `create_user`
- `main.py` 加 `POST /register` 和 `POST /login`
- 用 Pydantic 定义 `RegisterRequest` / `LoginRequest`
- 注册：查重 → 哈希 → 入库
- 登录：查用户 → 验证密码 → 生成 JWT

#### 概念收获
- **分层设计**：database.py 只操作数据库，auth.py 只做哈希，main.py 组织流程
- **用户名枚举漏洞**：登录失败时统一返回「用户名或密码错误」，不让攻击者区分
- **JWT 签发**：登录成功后返回 token，前端保存，后续请求带上

#### 问题日志
- 无
- ### 6.3.1 数据库层加 user_id（完成）

**完成时间：** 2026-10-14

#### 完成内容
- `database.py` 里 7 个待办相关函数全部加 `user_id` 参数
- 每个 SQL 的 `WHERE` 都加 `user_id = %s`

#### 概念收获
- **数据隔离的核心**：每个数据库操作都带 user_id，不信任应用层
- pymysql 无结果时 `fetchall()` 返回空元组 `()`，不是空列表 `[]`

#### 问题日志
- 无


### 6.3 多用户数据隔离（完成）

**完成时间：** 2026-10-14

#### 完成内容
- `database.py` 所有待办函数加 `user_id` 参数
- `tools.py` 用 `InjectedState` 自动获取 user_id
- `agent.py` 自定义 `AgentState`（继承 MessagesState + user_id）
- `main.py` 的 `/chat` 从 `Authorization: Bearer <token>` 解析 user_id

#### 概念收获
- **数据隔离必须在数据库层做**：每个 SQL 都带 `WHERE user_id = %s`
- **InjectedState**：LangGraph 自动从 state 注入参数，LLM 看不到
- **JWT 结构**：`header.payload.signature`，三段用点分隔
- **401 未认证**：HTTP 标准，表示没带 token 或 token 无效
- **Swagger UI bug**：无 body 的接口，header 输入框有时不生效

#### 问题日志
1. **`InjectedState` 导入路径变了**
   - 原因：新版 LangGraph 把 `InjectedState` 移到 `langgraph.prebuilt`
   - 解决：`from langgraph.prebuilt import InjectedState`
2. **`/docs` 里 header 一直传不到后端**
   - 现象：`/debug-header` 返回 `received: null`
   - 排查：用 curl 直接发，发现后端完全正常
   - 结论：**Swagger UI 的 bug，不是后端问题**
   - 解决：用 curl 或 Python requests 测试
3. **`/add` 和 `/list` 接口会报错**
   - 原因：`add_todo` / `list_todos` 需要 user_id 参数，旧接口没传
   - 解决：删掉这两个接口，统一走 `/chat`
## 阶段 6.5：邮箱验证 + 找回密码（QQ 邮箱发信）（未开始）

## 阶段 7：todos 加 user_id，多人数据隔离（未开始）

## 阶段 8：前端两页面（登录页 + 聊天页）（未开始）

## 阶段 9：Git + 推 GitHub（进行中）

## 阶段 10：部署阿里云 ECS（未开始）

---

## 全局问题日志（跨阶段汇总）

| 阶段 | 问题 | 根因 | 解决 |
|------|------|------|------|
| 0 | PowerShell 禁止运行脚本 | Windows 执行策略 | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| 1 | PyCharm 运行按钮跑不起来 | 直接跑 `main.py` 不启动服务 | 用 `uvicorn main:app --reload` |
| 2 | `NameError: app is not defined` | 装饰器写在 `app = FastAPI()` 前 | 把 `app` 创建放最前 |
| 3 | MySQL 服务错误码 87 | binPath 多了一个参数 | 删服务重建 |
| 3 | 表空以为没写进去 | 从未调过 `/add` | 补测接口 |
| 4.2 | 429 RateLimitError | `qwen-turbo` 已下线 | 换成 `qwen3.7-flash` |
| 4.3 | ZoneInfo 报时区不存在 | `Asia/Beijing` 不存在 | 改 `Asia/Shanghai` |
| 4.3 | ZoneInfo 报 tzdata 缺失 | Windows 无内置时区库 | `pip install tzdata` |

---

## 全局概念收获（跨阶段汇总）

- **FastAPI**：`@app.get/post` 装饰器定义路由，`/docs` 自动生成文档
- **Pydantic `BaseModel`**：定义请求体结构，自动校验
- **`.env`**：敏感信息不进代码、不进 Git
- **pymysql**：`DictCursor` 用列名取值；增删改要 `commit()`；`%s` 防注入
- **`@tool` 装饰器**：把 Python 函数变成 LLM 可调用的工具；docstring 决定 LLM 何时调用
- **`ZoneInfo`**：处理时区，Windows 需额外装 `tzdata`
- **`ChatOpenAI`**：LangChain 的通用模型类，兼容通义千问

---

## 重要约定

1. 密钥只放 `.env`，绝不进代码、不进 Git
2. 每完成一个阶段，用 GitHub Desktop 提交一次
3. 每行代码要能读懂，不懂就停下来问
4. 上下文快满时，用户会提醒，我把进度整理到这份文档

---

## 参考：项目路线图

- ✅ 阶段 0：项目准备
- ✅ 阶段 1：最小 FastAPI
- ✅ 阶段 2：POST /chat + .env
- ✅ 阶段 3：MySQL 存储
- 🔄 阶段 4：接大模型 + LangGraph
  - ✅ 4.2：测试 Qwen
  - 🔄 4.3：写工具（1/7）
- ⏳ 阶段 5：定时任务 + 邮件
- ⏳ 阶段 6：用户表 + 登录接口
- ⏳ 阶段 6.5：邮箱验证 + 找回密码
- ⏳ 阶段 7：多人数据隔离
- ⏳ 阶段 8：前端两页面
- 🔄 阶段 9：Git + GitHub
- ⏳ 阶段 10：部署阿里云 ECS


为什么密码用哈希：

不可逆：数据库泄露了，攻击者也无法反推出明文密码

即使管理员也看不到用户密码

验证方式：不是「解密后对比」，而是「用同样的算法再哈希一次，对比两个哈希值是否匹配」

「输入不同的明文都能验证成功」是错的——输入不同的明文，验证一定失败。verify_password("wrong", hash) 返回的就是 False。

第 2 题：为什么同一密码哈希结果不同，还能验证？
你说：「因为转换为哈希符合认证答案」

没说清。 这是哈希最巧妙的地方，值得搞懂。

关键概念：Salt（盐）

hash_password("test123") 每次结果都不同，是因为每次哈希时会随机生成一段字符串（salt），混进密码里一起哈希。

例如：

text
第 1 次：hash("test123" + "salt_A") → "$argon2id$...AAA"
第 2 次：hash("test123" + "salt_B") → "$argon2id$...BBB"
结果不同，但哈希结果里包含了 salt。验证时：

从存储的哈希里取出 salt

用同样的 salt + 用户输入的密码，再哈希一次

对比两个哈希是否一致

这就是为什么 verify_password 能成功——它不需要「解密」，只需要「用同样的 salt 再算一遍」。

Salt 的作用：防止「彩虹表攻击」——如果没 salt，同样的密码永远产生同样的哈希，攻击者可以用预计算表反查。

第 3 题：SECRET_KEY 干嘛用的？
你说：「用户密码泄露会导致用户资料泄露」

正确理解：

SECRET_KEY 用于 JWT 的签名（sign）。

JWT 的结构：

text
header.payload.signature
header：说明算法（HS256）

payload：放 user_id、过期时间（明文，只是 base64 编码，不算加密）

signature：用 SECRET_KEY 对 header.payload 做 HMAC 计算出来的签名

验证 token 时：

拿到 token

用 SECRET_KEY 重新算一遍签名

对比 token 里的签名是否一致

一致 → token 合法；不一致 → 被篡改过

SECRET_KEY 泄露会怎样：

攻击者能用你的 SECRET_KEY 伪造任意用户的 token

例如伪造 {"sub": "1"}，就能冒充 id=1 的用户登录

后果比密码泄露更严重

所以 SECRET_KEY 必须放在 .env，绝不进 Git。