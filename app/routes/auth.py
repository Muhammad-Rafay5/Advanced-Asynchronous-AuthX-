from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.user import UserCreate, UserRegistrationResponse
from app.schemas.auth import TokenExchangeResponse, TokenPayload, StandardActionResponse
from app.services.auth import auth_service
from app.redis.blacklist import blacklist_service
from app.dependencies.auth import oauth2_scheme
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.config import settings
from app.core.rate_limit import limiter
from datetime import datetime, timezone
import jwt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db, user_in)


@router.post("/login", response_model=TokenExchangeResponse)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    return await auth_service.authenticate(db, form_data.username, form_data.password)


@router.post("/refresh", response_model=TokenExchangeResponse)
@limiter.limit("10/minute")
async def refresh_token(request: Request, refresh_token: str = Body(..., embed=True)):
    try:
        payload = decode_token(refresh_token, settings.REFRESH_TOKEN_SECRET)
        token_data = TokenPayload(**payload)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Type check BEFORE blacklist check (correct order)
    if token_data.type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if await blacklist_service.is_blacklisted(token_data.jti):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    # Rotate: blacklist old JTI, issue new token pair
    remaining = token_data.exp - int(datetime.now(timezone.utc).timestamp())
    await blacklist_service.add(token_data.jti, max(remaining, 0))

    return TokenExchangeResponse(
        access_token=create_access_token(token_data.sub),
        refresh_token=create_refresh_token(token_data.sub)
    )


@router.post("/logout", response_model=StandardActionResponse)
async def logout(
    token: str = Depends(oauth2_scheme),
    refresh_token: str = Body(..., embed=True)
):
    # Blacklist the access token
    try:
        payload = decode_token(token, settings.ACCESS_TOKEN_SECRET)
        token_data = TokenPayload(**payload)
        remaining = token_data.exp - int(datetime.now(timezone.utc).timestamp())
        await blacklist_service.add(token_data.jti, max(remaining, 0))
    except Exception:
        pass  # Already expired — nothing to blacklist

    # Blacklist the refresh token
    try:
        r_payload = decode_token(refresh_token, settings.REFRESH_TOKEN_SECRET)
        r_data = TokenPayload(**r_payload)
        r_remaining = r_data.exp - int(datetime.now(timezone.utc).timestamp())
        await blacklist_service.add(r_data.jti, max(r_remaining, 0))
    except Exception:
        pass  # Already expired — nothing to blacklist

    return StandardActionResponse(detail="Revocation complete")
