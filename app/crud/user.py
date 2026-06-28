from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User


async def create_user(session: AsyncSession, *, user_id: str, name: str) -> User:
    user = User(id=user_id, name=name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: str) -> User | None:
    return await session.get(User, user_id)


async def list_users(
    session: AsyncSession, limit: int = 100, offset: int = 0
) -> list[User]:
    result = await session.execute(
        select(User).order_by(User.id).offset(offset).limit(limit)
    )
    return list(result.scalars().all())
