from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import decode_token
from app.db.database import get_db
from app.db.models import User
from app.redis.blacklist import blacklist_service
from app.schemas.auth import TokenPayload
from sqlalchemy.future import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if await blacklist_service.is_blacklisted(token):
        raise credentials_exception

    try:
        payload = decode_token(token, settings.ACCESS_TOKEN_SECRET)
        token_data = TokenPayload(**payload)
        if token_data.type != "access":
            raise credentials_exception
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception
        
    result = await db.execute(select(User).where(User.id == uuid.UUID(token_data.sub)))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user
