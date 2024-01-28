import json
from typing import Optional

from pydantic import BaseModel, model_validator


class CuisineBase(BaseModel):
        name: str
        description: str
        latitude: Optional[str] = None
        longitude: Optional[str] = None

        @model_validator(mode="before")
        @classmethod
        def validate_to_json(cls, value):
                if isinstance(value, str):
                        return cls(**json.loads(value))
                return value


class CuisineUpdate(BaseModel):
        name: Optional[str] = None
        description: Optional[str] = None
        latitude: Optional[str] = None
        longitude: Optional[str] = None
