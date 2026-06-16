from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.db.models import User
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, create_password_reset_token, decode_token
from app.schemas.user import UserCreate
from app.schemas.auth import TokenExchangeResponse
from app.core.config import settings
import jwt


class AuthService:
    async def register_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="User already exists")

        new_user = User(
            full_name=user_in.full_name,
            company_name=user_in.company_name,
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

    async def request_password_reset(self, db: AsyncSession, email: str):
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user:
            # We don't want to leak whether the email exists, just return silently or log
            print(f"Password reset requested for non-existent email: {email}")
            return {"message": "If your email is registered, you will receive a password reset link."}
        
        reset_token = create_password_reset_token(email)
        # Simulate sending email
        print("="*40)
        print(f"PASSWORD RESET LINK GENERATED FOR {email}")
        print(f"TOKEN: {reset_token}")
        print("="*40)
        return {"message": "If your email is registered, you will receive a password reset link."}

    async def reset_password(self, db: AsyncSession, token: str, new_password: str):
        try:
            payload = decode_token(token, settings.ACCESS_TOKEN_SECRET)
            if payload.get("type") != "password_reset":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")
            email = payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        await db.commit()
        return {"message": "Password successfully reset"}


auth_service = AuthService()
