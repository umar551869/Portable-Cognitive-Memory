from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pcg.storage.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.scalar(select(User).where(User.id == user_id))

    async def create(self, name: str, email: str, password_hash: str, is_admin: bool = False) -> User:
        user = User(id=uuid4(), name=name, email=email, password_hash=password_hash, is_admin=1 if is_admin else 0)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_profile(
        self,
        user: User,
        *,
        name: str | None = None,
        password_hash: str | None = None,
        is_admin: bool | None = None,
    ) -> User:
        if name is not None:
            user.name = name
        if password_hash is not None:
            user.password_hash = password_hash
        if is_admin is not None:
            user.is_admin = 1 if is_admin else 0
        await self.session.commit()
        await self.session.refresh(user)
        return user
