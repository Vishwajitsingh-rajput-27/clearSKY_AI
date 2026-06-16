import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.user import User

PASSWORD_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}"
        f"${base64.urlsafe_b64encode(salt).decode('ascii')}"
        f"${base64.urlsafe_b64encode(digest).decode('ascii')}"
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest = encoded_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    expected = base64.urlsafe_b64decode(digest.encode("ascii"))
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        base64.urlsafe_b64decode(salt.encode("ascii")),
        int(iterations),
    )
    return hmac.compare_digest(actual, expected)


def create_access_token(user: User) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "type": "access",
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return encode_jwt(payload), expires_at


def encode_jwt(payload: dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_segment = base64url_json(header)
    payload_segment = base64url_json(payload)
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature = hmac.new(
        settings.jwt_secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{header_segment}.{payload_segment}.{base64url_encode(signature)}"


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".", 2)
    except ValueError as exc:
        raise auth_error("Invalid authentication token.") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected_signature = hmac.new(
        settings.jwt_secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(base64url_encode(expected_signature), signature_segment):
        raise auth_error("Invalid authentication token.")

    try:
        payload = json.loads(base64url_decode(payload_segment))
    except (json.JSONDecodeError, ValueError) as exc:
        raise auth_error("Invalid authentication token.") from exc

    if payload.get("type") != "access":
        raise auth_error("Invalid token type.")

    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at < int(datetime.now(UTC).timestamp()):
        raise auth_error("Authentication token has expired.")

    return payload


def base64url_json(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64url_encode(encoded)


def base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def base64url_decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii")).decode("utf-8")


def auth_error(message: str) -> AppError:
    return AppError(message, status_code=status.HTTP_401_UNAUTHORIZED, code="unauthorized")


def get_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise auth_error("Authorization header must use Bearer token format.")

    return token


DbSession = Annotated[Session, Depends(get_db)]
AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]


def get_current_user(
    db: DbSession,
    authorization: AuthorizationHeader = None,
) -> User:
    token = get_bearer_token(authorization)
    if token is None:
        raise auth_error("Authentication required.")

    payload = decode_jwt(token)
    user_id = payload.get("sub")

    try:
        user_uuid = UUID(str(user_id))
    except ValueError as exc:
        raise auth_error("Invalid authentication token.") from exc

    user = db.get(User, user_uuid)
    if user is None or not user.is_active:
        raise auth_error("User account is inactive or unavailable.")

    return user


def get_optional_current_user(
    db: DbSession,
    authorization: AuthorizationHeader = None,
) -> User | None:
    token = get_bearer_token(authorization)
    if token is None:
        return None

    payload = decode_jwt(token)
    user_id = payload.get("sub")

    try:
        user_uuid = UUID(str(user_id))
    except ValueError as exc:
        raise auth_error("Invalid authentication token.") from exc

    return db.scalars(
        select(User).where(User.id == user_uuid, User.is_active.is_(True)).limit(1)
    ).first()
