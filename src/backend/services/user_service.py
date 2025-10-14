import uuid
from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.db.repositories.user_repo import UserRepository
from adapters.db.repositories.base import NotFoundError as RepoNotFound
from adapters.db.session_context import get_async_session
from .errors import ServiceError, ConflictError


class UserService:
    """Business logic for users. Does not hash passwords; expects pass_hash from caller."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)

    # Registration with uniqueness checks
    async def register(self, *, login: str, email: str, pass_hash: str, is_admin: bool = False):
        if await self.users.get_by_login(login):
            raise ConflictError("login is already taken")
        if await self.users.get_by_email(email):
            raise ConflictError("email is already taken")
        return await self.users.create(login=login, email=email, pass_hash=pass_hash, is_admin=is_admin)

    async def get(self, user_id: uuid.UUID):
        user = await self.users.get_by_id(user_id)
        if not user:
            raise RepoNotFound("User not found")
        return user

    async def get_by_login(self, login: str):
        user = await self.users.get_by_login(login)
        if not user:
            raise RepoNotFound("User not found")
        return user

    async def set_password(self, user_id: uuid.UUID, new_pass_hash: str):
        return await self.users.set_password(user_id, new_pass_hash)

    async def set_admin(self, user_id: uuid.UUID, is_admin: bool):
        return await self.users.set_admin(user_id, is_admin)

    async def delete(self, user_id: uuid.UUID) -> None:
        await self.users.delete(user_id)



async def get_user_service(session: AsyncSession = Depends(get_async_session)) -> UserService:
    return UserService(session)