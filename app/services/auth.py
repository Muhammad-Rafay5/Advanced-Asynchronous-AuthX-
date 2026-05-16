from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.db.models import User
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.schemas.user import UserCreate
from app.schemas.auth import TokenExchangeResponse

class AuthService:
    async def register_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="User already exists")
        
        new_user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password)
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> TokenExchangeResponse:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
        
        return TokenExchangeResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id)
        )

auth_service = AuthService()
