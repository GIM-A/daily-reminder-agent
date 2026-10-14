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

def add_todo(content: str, deadline: str = None) -> int:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO todos (content, deadline) VALUES (%s, %s)",
            (content, deadline)
        )
        conn.commit()
        new_id = c.lastrowid
        conn.close()
        return new_id

def list_todos() -> list:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT id, content, deadline, done FROM todos WHERE done = 0 AND deleted_at IS NULL"
        )
        rows = c.fetchall()
        conn.close()
        return rows

if __name__ == "__main__":
    init_db()