import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, value: str) -> str:
        normalized = value.strip()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("invalid email")
        return normalized


class WorkspaceSummary(BaseModel):
    id: uuid.UUID
    name: str
    kind: str
    timezone: str
    role: str


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str


class SessionResponse(BaseModel):
    user: UserSummary
    current_workspace: WorkspaceSummary
    workspaces: list[WorkspaceSummary]


class SwitchWorkspaceRequest(BaseModel):
    workspace_id: uuid.UUID
