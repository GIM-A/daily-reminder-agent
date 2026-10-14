import os
from datetime import datetime, timedelta
from pwdlib import PasswordHash
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

# 用 pwdlib 的推荐配置
password_hash = PasswordHash.recommended()

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None


if __name__ == "__main__":
    pw = "test123"
    hashed = hash_password(pw)
    print("哈希:", hashed)
    print("验证正确密码:", verify_password("test123", hashed))
    print("验证错误密码:", verify_password("wrong", hashed))

    token = create_access_token(user_id=1)
    print("\nToken:", token)
    print("解析:", decode_access_token(token))
    print("解析假 token:", decode_access_token("fake"))