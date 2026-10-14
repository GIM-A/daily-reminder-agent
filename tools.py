from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_core.tools import tool
from database import list_todos as db_list_todos
from database import add_todo as db_add_todo
from database import complete_todo as db_complete_todo
from database import delete_todo as db_delete_todo
from database import get_deleted_todos as db_get_deleted_todos
from database import restore_todo as db_restore_todo


@tool
def get_current_time() -> str:
    """获取当前日期和时间。当用户问「今天几号」「现在几点」，或需要判断「明天」「后天」是哪天时使用。"""
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    return now.strftime("%Y-%m-%d %H:%M:%S")

@tool
def get_pending_todos() -> str:
    """查询所有未完成的待办事项。当用户问「我还有什么没做」「看看我的待办」「我的待办列表」时使用"""
    todos = db_list_todos()
    if not todos:
        return "当前没有未完成的待办事项。"
    lines = []
    for t in todos:
        deadline = t["deadline"] or "无"
        lines.append(f"[{t['id']}] {t['content']} (截止: {deadline})")
    return "\n".join(lines)
@tool
def add_todo(content: str, deadline: str = "") -> str:
    """添加一条新的待办事项。当用户说「帮我记一下」「提醒我」「添加待办」时使用。
    content 是待办内容。
    deadline 是截止时间，格式必须是 YYYY-MM-DD HH:MM，没有截止时间就留空字符串。"""
    todo_id = db_add_todo(content, deadline or None)
    if deadline:
        return f"已添加待办：{content}（截止 {deadline}），id={todo_id}"
    return f"已添加待办：{content}，id={todo_id}"

@tool
def complete_todo(todo_id: int) -> str:
    """把某条待办标记为已完成。当用户说「我完成XX了」「XX做完了」时使用。
    todo_id 是待办的 id（整数）。如果用户说的内容对应哪条待办不确定，先调用 get_pending_todos 找到 id。"""
    affected = db_complete_todo(todo_id)
    if affected:
        return f"已完成待办 {todo_id}"
    return f"未找到待办 {todo_id}，或它已经是完成状态"

@tool
def delete_todo(todo_id: int) -> str:
    """删除某条待办。当用户说「把XX删掉」「删除XX这条」时使用。
    todo_id 是待办的 id（整数）。如果用户说的内容对应哪条待办不确定，先调用 get_pending_todos 找到 id。
    注意：这是软删除，7 天内可以通过 get_deleted_todos 查看并 restore_todo 恢复。"""
    affected = db_delete_todo(todo_id)
    if affected:
        return f"已删除待办 {todo_id}（7 天内可以恢复）"
    return f"未找到待办 {todo_id}，或它已经被删除了"

@tool
def get_deleted_todos() -> str:
    """查询最近 7 天内删除的待办。当用户问「我删过什么」「之前删掉的待办」时使用。"""
    rows = db_get_deleted_todos()
    if not rows:
        return "最近 7 天内没有删除过待办。"
    lines = []
    for r in rows:
        deadline = r["deadline"] or "无"
        lines.append(f"[{r['id']}] {r['content']} (截止: {deadline}, 删除于: {r['deleted_at']})")
    return "\n".join(lines)

@tool
def restore_todo(todo_id: int) -> str:
    """恢复一条已删除的待办。当用户说「把XX恢复回来」「撤销删除」时使用。
    todo_id 是待办的 id（整数）。如果不确定 id，先调用 get_deleted_todos 查看。"""
    affected = db_restore_todo(todo_id)
    if affected:
        return f"已恢复待办 {todo_id}"
    return f"未找到已删除的待办 {todo_id}"



if __name__ == "__main__":
    print("--- 完成 id=2 ---")
    print(complete_todo.invoke({"todo_id": 2}))
    print("\n--- 查待办 ---")
    print(get_pending_todos.invoke({}))
    print("\n--- 删除 id=3 ---")
    print(delete_todo.invoke({"todo_id": 3}))
    print("\n--- 查已删除 ---")
    print(get_deleted_todos.invoke({}))
    print("\n--- 恢复 id=3 ---")
    print(restore_todo.invoke({"todo_id": 3}))
    print("\n--- 再查待办 ---")
    print(get_pending_todos.invoke({}))