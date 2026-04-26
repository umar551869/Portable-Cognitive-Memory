from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from pcg.auth.security import create_access_token, hash_password, verify_password
from pcg.storage.user_repository import UserRepository
from pcg.utils.schemas import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession):
        self.users = UserRepository(session)

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        existing = await self.users.get_by_email(payload.email)
        if existing is not None:
            raise ValueError("Email already registered.")
        user = await self.users.create(payload.name, payload.email, hash_password(payload.password))
        return TokenResponse(access_token=create_access_token(str(user.id)))

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise ValueError("Invalid email or password.")
        return TokenResponse(access_token=create_access_token(str(user.id)))
