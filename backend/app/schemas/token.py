from pydantic import BaseModel
from typing import Optional

class SchwabToken(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    scope: Optional[str] = None
    created_at: Optional[float] = None
