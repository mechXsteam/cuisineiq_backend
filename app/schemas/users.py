from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
        name: str
        phone_number: str
        email: Optional[str] = None
