import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from tools import (
    get_current_time, get_pending_todos, add_todo,
    complete_todo, delete_todo, get_deleted_todos, restore_todo
)

load_dotenv()

# 1. 7 个工具列表
tools = [
    get_current_time, get_pending_todos, add_todo,
    complete_todo, delete_todo, get_deleted_todos, restore_todo
]

# 2. ToolNode：LangGraph 提供的「执行工具」节点
tool_node = ToolNode(tools)

# 3. System Prompt：给 LLM 的角色说明
SYSTEM_PROMPT = """你是一个每日提醒助手。当前时间请务必调用 get_current_time 工具获取，不要自己编造日期。

当用户要求添加待办时：
1. 先调用 get_current_time 获取今天的日期
2. 根据用户说的"明天""后天""下周一"等，计算出准确的截止日期
3. 再调用 add_todo 工具，deadline 格式为 YYYY-MM-DD HH:MM

当用户说"完成了XX"时，先调用 get_pending_todos 找到对应的 id，再调用 complete_todo。
当用户说"删掉XX"时，先调用 get_pending_todos 找到对应的 id，再调用 delete_todo。
当用户问"我删过什么"时，调用 get_deleted_todos。
当用户说"把XX恢复回来"时，先调用 get_deleted_todos 找到 id，再调用 restore_todo。
当用户询问待办时，调用 get_pending_todos。
当用户问时间时，调用 get_current_time。"""

# 4. 创建 LLM，并绑定工具
llm = ChatOpenAI(
    model="qwen3.7-flash",
    api_key=os.getenv("DASHSCOPE_API_KEY", ""),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
).bind_tools(tools)

# 5. agent 节点：调 LLM
def call_model(state: MessagesState):
    messages = [("system", SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# 6. 条件判断：LLM 要不要调工具
def should_continue(state: MessagesState):
    last = state["messages"][-1]
    if last.tool_calls:
        return "tools"
    return END

# 7. 组装图
class AgentState(MessagesState):
    user_id: int

graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.add_node("tools", tool_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

# 8. 编译
agent = graph.compile()

# 9. 本地测试
if __name__ == "__main__":
    result = agent.invoke({
        "messages": [("user", "我有什么待办？")],
        "user_id": 52,
    })
    print(result["messages"][-1].content)
    print("\n--- 完整消息历史 ---")
    for msg in result["messages"]:
        print(f"[{msg.type}] {msg.content[:100] if msg.content else '(tool call)'}")