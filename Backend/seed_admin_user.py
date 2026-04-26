from __future__ import annotations

import asyncio

from pcg.auth.security import hash_password
from pcg.storage.db import get_db
from pcg.storage.user_repository import UserRepository


TARGET_NAME = "Muhammad Umar Ilyas"
TARGET_EMAIL = "umar632708@gmail.com"
TARGET_PASSWORD = "#@portable5518"


async def main() -> None:
    async for session in get_db():
        repo = UserRepository(session)
        existing = await repo.get_by_email(TARGET_EMAIL)
        hashed = hash_password(TARGET_PASSWORD)
        if existing is None:
            user = await repo.create(TARGET_NAME, TARGET_EMAIL, hashed, is_admin=True)
            print(f"Created admin user: {user.id}")
        else:
            user = await repo.update_profile(
                existing,
                name=TARGET_NAME,
                password_hash=hashed,
                is_admin=True,
            )
            print(f"Updated admin user: {user.id}")
        return


if __name__ == "__main__":
    asyncio.run(main())
