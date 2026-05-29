from __future__ import annotations

import base64
import hashlib
import hmac
import os

from app.schemas.auth import UserProfileResponse
from app.services.sqlite_store import sqlite_store


def _hash_password(password: str, salt: bytes | None = None) -> str:
    use_salt = salt or os.urandom(16)
    iterations = 200_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), use_salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.b64encode(use_salt).decode()}${base64.b64encode(digest).decode()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algo, iter_str, salt_b64, digest_b64 = stored_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
    except Exception:
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def register_user(user_id: str, password: str, birthday: str, role: str) -> UserProfileResponse:
    if sqlite_store.get_user(user_id) is not None:
        raise ValueError("user_id_already_exists")

    password_hash = _hash_password(password)
    sqlite_store.create_user(user_id=user_id, password_hash=password_hash, birthday=birthday, role=role)
    return UserProfileResponse(user_id=user_id, birthday=birthday, role=role, first_test_completed=False)


def login_user(user_id: str, password: str) -> UserProfileResponse:
    user = sqlite_store.get_user(user_id)
    if user is None:
        raise ValueError("invalid_credentials")

    if not _verify_password(password, str(user["password_hash"])):
        raise ValueError("invalid_credentials")

    return UserProfileResponse(
        user_id=str(user["user_id"]),
        birthday=str(user["birthday"]),
        role=str(user["role"]),
        first_test_completed=bool(user["first_test_completed"]),
    )


def get_profile(user_id: str) -> UserProfileResponse:
    user = sqlite_store.get_user(user_id)
    if user is None:
        raise ValueError("user_not_found")

    return UserProfileResponse(
        user_id=str(user["user_id"]),
        birthday=str(user["birthday"]),
        role=str(user["role"]),
        first_test_completed=bool(user["first_test_completed"]),
    )


def set_first_test_completed(user_id: str, completed: bool) -> UserProfileResponse:
    user = sqlite_store.get_user(user_id)
    if user is None:
        raise ValueError("user_not_found")

    sqlite_store.update_user_first_test_completed(user_id=user_id, completed=completed)
    return get_profile(user_id)

