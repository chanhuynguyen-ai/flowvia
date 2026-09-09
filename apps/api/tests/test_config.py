import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_requires_secure_session_cookie():
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            session_cookie_secure=False,
            cors_origins="https://flowvia.example",
            database_url="sqlite://",
        )


def test_credentialed_cors_rejects_wildcard():
    with pytest.raises(ValidationError):
        Settings(
            app_env="development",
            session_cookie_secure=False,
            cors_origins="*",
            database_url="sqlite://",
        )
