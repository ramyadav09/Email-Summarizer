from pydantic import BaseModel

class TokenStatus(BaseModel):
    access_token: str
    token_type: str = "Bearer"
