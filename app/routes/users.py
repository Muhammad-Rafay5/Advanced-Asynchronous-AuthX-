from fastapi import APIRouter, Depends, HTTPException, status
from app.db.models import User
from app.schemas.user import UserRegistrationResponse
from app.dependencies.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserRegistrationResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=list[UserRegistrationResponse])
async def read_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    result = await db.execute(select(User))
    return result.scalars().all()

