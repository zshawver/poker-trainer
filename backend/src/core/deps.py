"""FastAPI dependencies — database session, current user, etc."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import decode_access_token
from src.db.session import async_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, auto-closing on exit."""
    async with async_session() as session:
        yield session


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decode JWT and return the current user.

    TODO: Replace stub with real user lookup from database.
    """
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # TODO: Query user from DB
    # user = await db.get(User, user_id)
    # if user is None:
    #     raise HTTPException(status_code=401, detail="User not found")
    # return user

    return {"id": user_id}
