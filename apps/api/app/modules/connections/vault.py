"""Tenant scoped ciphertext; development key survives restarts in a mounted volume."""

import os
from pathlib import Path
import uuid

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select

from app.core.config import get_settings
from app.modules.connections.models import Credential


def cipher() -> Fernet:
    settings = get_settings()
    key = settings.credential_encryption_key
    if not key:
        if settings.app_env == "production":
            raise ValueError("CREDENTIAL_ENCRYPTION_KEY is required in production")
        path = Path(settings.credential_key_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            temporary = path.with_name(f".key-{uuid.uuid4()}")
            try:
                fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(Fernet.generate_key())
                    stream.flush()
                    os.fsync(stream.fileno())
                try:
                    os.link(
                        temporary, path
                    )  # Publish the complete key without replacing another process's key.
                except FileExistsError:
                    pass
            finally:
                temporary.unlink(missing_ok=True)
        key = path.read_text().strip()
    return Fernet(key.encode())


def store_credential(db, tenant_id, provider, name, secret) -> Credential:
    item = Credential(
        tenant_id=tenant_id,
        provider=provider,
        name=name,
        ciphertext=cipher().encrypt(secret.encode()).decode(),
    )
    db.add(item)
    db.flush()
    return item


def get_secret(db, tenant_id, credential_id, provider) -> str:
    try:
        ident = uuid.UUID(str(credential_id))
    except (ValueError, TypeError):
        raise ValueError("Configure a credential in Connections first") from None
    item = db.scalar(
        select(Credential).where(
            Credential.id == ident,
            Credential.tenant_id == tenant_id,
            Credential.provider == provider,
            Credential.status == "active",
        )
    )
    if item is None:
        raise ValueError("Credential is missing or revoked")
    try:
        return cipher().decrypt(item.ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError(
            "Credential cannot be decrypted with the current server key"
        ) from None
