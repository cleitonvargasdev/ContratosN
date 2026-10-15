import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from app.tenancy.context import current_tenant, tenant_key


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, str], secret_key: str, algorithm: str, expires_minutes: int) -> str:
    payload = data.copy()
    tenant_key()
    tenant = current_tenant.get()
    if tenant is not None:
        payload["tenant_id"] = tenant.id
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload.update({"exp": expire})
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def generate_api_key_value() -> str:
    return f"ctr_{secrets.token_urlsafe(32)}"


def build_api_key_prefix(api_key: str) -> str:
    return api_key[:12]


def hash_api_key_value(api_key: str, secret_key: str | None = None) -> str:
    key = tenant_key()
    if key != "__legacy__":
        api_key = f"{key}:{api_key}"
    secret = (secret_key or "").encode("utf-8")
    return hmac.new(secret, api_key.encode("utf-8"), hashlib.sha256).hexdigest()
