"""Login / JWT authentication skeleton."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.security import create_access_token, verify_password
from src.core.deps import get_db

router = APIRouter()


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
) -> dict[str, str]:
    """Authenticate user and return JWT token.

    TODO: Replace stub with real user lookup from database.
    """
    # Stub — replace with actual user query
    # user = await get_user_by_email(db, form_data.username)
    # if not user or not verify_password(form_data.password, user.hashed_password):
    #     raise HTTPException(status_code=401, detail="Invalid credentials")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Auth not yet implemented — wire up your user model first.",
    )

    # token = create_access_token(subject=user.id)
    # return {"access_token": token, "token_type": "bearer"}
