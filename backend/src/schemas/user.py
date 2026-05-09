"""Response schemas for the User auth identity."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    """Public-facing user shape (never includes hashed_password or is_admin)."""

    id: UUID
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
