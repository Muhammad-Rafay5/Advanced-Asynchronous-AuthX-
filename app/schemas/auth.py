from pydantic import BaseModel

class TokenExchangeResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: int
    jti: str

class StandardActionResponse(BaseModel):
    detail: str
