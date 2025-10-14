import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.db.models.user import User
from .base import BaseRepository, NotFoundError


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create(
            self,
            *,
            login: str,
            email: str,
            pass_hash: str,
            is_admin: bool = False,
    ) -> User:
        user = User(login=login, email=email, pass_hash=pass_hash, is_admin=is_admin)
        async with self._transaction():
            self.session.add(user)
            await self._flush_refresh(user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        res = await self.session.execute(select(User).where(User.id == user_id))
        return res.scalars().first()

    async def require_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def get_by_login(self, login: str) -> Optional[User]:
        res = await self.session.execute(select(User).where(User.login == login))
        return res.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        res = await self.session.execute(select(User).where(User.email == email))
        return res.scalars().first()

    async def set_password(self, user_id: uuid.UUID, new_pass_hash: str) -> User:
        user = await self.require_by_id(user_id)
        user.pass_hash = new_pass_hash
        async with self._transaction():
            await self._flush_refresh(user)
        return user

    async def set_admin(self, user_id: uuid.UUID, is_admin: bool) -> User:
        user = await self.require_by_id(user_id)
        user.is_admin = is_admin
        async with self._transaction():
            await self._flush_refresh(user)
        return user

    async def delete(self, user_id: uuid.UUID) -> None:
        user = await self.require_by_id(user_id)
        async with self._transaction():
            await self.session.delete(user)
