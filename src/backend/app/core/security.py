import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.settings import config  # expects SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(*, sub: uuid.UUID, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=expires_minutes or config.security.access_token_expire_minute
    )
    payload = {"sub": str(sub), "exp": int(expire.timestamp())}
    return jwt.encode(payload, config.security.secret_key, algorithm=config.security.algorithm)


def decode_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token, config.security.secret_key, algorithms=[config.security.algorithm]
        )
        return uuid.UUID(payload.get("sub"))
    except (JWTError, ValueError) as e:
        raise ValueError("Invalid token") from e
