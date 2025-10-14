from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    id: UUID
    login: str
    email: EmailStr
    pass_hash: str
    is_admin: bool = Field(False)
