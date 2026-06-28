from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user as crud
from app.db.session import get_session
from app.idgen.base import IdIssuer
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


def get_issuer(request: Request) -> IdIssuer:
    return cast(IdIssuer, request.app.state.issuer)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
    issuer: IdIssuer = Depends(get_issuer),
) -> UserRead:
    user_id = issuer.issue()
    try:
        user = await crud.create_user(session, user_id=user_id, name=data.name)
    except IntegrityError as exc:
        # 一意制約は「衝突の検出器」であって一意性の保証手段ではない。
        # アプリ側ロジックが衝突しなければ、ここには到達しない。
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="user id collision"
        ) from exc
    return UserRead.model_validate(user, from_attributes=True)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: str, session: AsyncSession = Depends(get_session)
) -> UserRead:
    user = await crud.get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user, from_attributes=True)
