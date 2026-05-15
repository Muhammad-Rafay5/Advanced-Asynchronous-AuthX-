from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.user import UserCreate, UserRegistrationResponse
from app.schemas.auth import TokenExchangeResponse, TokenPayload, StandardActionResponse
from app.services.auth import auth_service
from app.redis.blacklist import blacklist_service
from app.dependencies.auth import oauth2_scheme
from app.core.security import create_access_token, decode_token
from app.core.config import settings
import jwt

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db, user_in)

@router.post("/login", response_model=TokenExchangeResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    return await auth_service.authenticate(db, form_data.username, form_data.password)

@router.post("/refresh", response_model=TokenExchangeResponse)
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    try:
        payload = decode_token(refresh_token, settings.REFRESH_TOKEN_SECRET)
        token_data = TokenPayload(**payload)
        if token_data.type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    return TokenExchangeResponse(
        access_token=create_access_token(token_data.sub),
        refresh_token=refresh_token
    )

@router.post("/logout", response_model=StandardActionResponse)
async def logout(token: str = Depends(oauth2_scheme)):
    await blacklist_service.add(token, 3600)
    return StandardActionResponse(detail="Revocation complete")
