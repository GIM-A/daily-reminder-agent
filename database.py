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

    # todos 表
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

    # email_verifications 表
    c.execute("""
        CREATE TABLE IF NOT EXISTS email_verifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            token VARCHAR(64) NOT NULL,
            purpose VARCHAR(20) NOT NULL DEFAULT 'email_verify',
            expires_at DATETIME NOT NULL,
            used_at DATETIME DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_token (token),
            INDEX idx_user_id (user_id)
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
    c.execute(
        "SELECT id, username, email, password_hash, email_verified FROM users WHERE username = %s",
        (username,)
    )
    row = c.fetchone()
    conn.close()
    return row


def get_user_by_email(email: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, email, password_hash, email_verified FROM users WHERE email = %s", (email,))
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


def get_all_users() -> list:
    """返回所有用户，包含 id 和 email。"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, email FROM users")
    rows = c.fetchall()
    conn.close()
    return rows


def create_verification_token(user_id: int, token: str, purpose: str, expires_at) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO email_verifications (user_id, token, purpose, expires_at) VALUES (%s, %s, %s, %s)",
        (user_id, token, purpose, expires_at)
    )
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id


def get_verification_token(token: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM email_verifications WHERE token = %s", (token,))
    row = c.fetchone()
    conn.close()
    return row


def mark_token_used(token_id: int) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE email_verifications SET used_at = NOW() WHERE id = %s AND used_at IS NULL",
        (token_id,)
    )
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected

def update_user_password(user_id: int, new_password_hash: str) -> int:
    """更新用户密码，返回受影响行数。"""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (new_password_hash, user_id)
    )
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected


def update_email_verified(user_id: int) -> int:
    """把用户的 email_verified 设为 1，返回受影响行数。"""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET email_verified = 1 WHERE id = %s",
        (user_id,)
    )
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected


if __name__ == "__main__":
    init_db()