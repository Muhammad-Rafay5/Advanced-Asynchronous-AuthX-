from pydantic import BaseModel

class TokenExchangeResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str = None
    type: str = None
    exp: int = None

class StandardActionResponse(BaseModel):
    detail: str
