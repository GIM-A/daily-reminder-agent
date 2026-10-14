import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "daily_reminder"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL DEFAULT 1,
            content VARCHAR(255) NOT NULL,
            deadline DATETIME NULL,
            done TINYINT DEFAULT 0,
            deleted_at DATETIME NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.commit()
    conn.close()
    print("数据库初始化完成")

def add_todo(user_id: int, content: str, deadline: str = None) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO todos (user_id, content, deadline) VALUES (%s, %s, %s)",
        (user_id, content, deadline)
    )
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id


def list_todos(user_id: int) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, content, deadline, done FROM todos "
        "WHERE user_id = %s AND done = 0 AND deleted_at IS NULL",
        (user_id,)
    )
    rows = c.fetchall()
    conn.close()
    return list(rows)


def complete_todo(user_id: int, todo_id: int) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE todos SET done = 1 WHERE id = %s AND user_id = %s AND done = 0",
        (todo_id, user_id)
    )
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected


def delete_todo(user_id: int, todo_id: int) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE todos SET deleted_at = NOW() "
        "WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
        (todo_id, user_id)
    )
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected


def get_deleted_todos(user_id: int) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, content, deadline, deleted_at
        FROM todos
        WHERE user_id = %s
          AND deleted_at IS NOT NULL
          AND deleted_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def restore_todo(user_id: int, todo_id: int) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE todos SET deleted_at = NULL "
        "WHERE id = %s AND user_id = %s AND deleted_at IS NOT NULL",
        (todo_id, user_id)
    )
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected

def get_user_by_username(username: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, email, password_hash FROM users WHERE username = %s", (username,))
    row = c.fetchone()
    conn.close()
    return row


def create_user(username: str, email: str, password_hash: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        (username, email, password_hash)
    )
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id

if __name__ == "__main__":
    init_db()