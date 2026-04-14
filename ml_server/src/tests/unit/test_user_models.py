import pytest
from pydantic import ValidationError

from src.ml_server.schemas.user import UserCreate


def test_valid_user_create():
    user = UserCreate(email="igor@example.com", password="strongpass123")
    assert user.email == "igor@example.com"


def test_password_too_short():
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(email="igor@example.com", password="short")
    assert "at least 8 characters" in str(exc_info.value)


def test_password_too_long():
    with pytest.raises(ValidationError):
        UserCreate(email="igor@example.com", password="x" * 73)


def test_password_boundary_8_chars():
    user = UserCreate(email="igor@example.com", password="exactly8")
    assert user.password == "exactly8"


def test_password_boundary_72_chars():
    user = UserCreate(email="igor@example.com", password="x" * 72)
    assert len(user.password) == 72


def test_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="validpass123")
