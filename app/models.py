from pydantic import BaseModel
from typing import List, Optional

class Character(BaseModel):
    id: int
    name: str
    status: str
    species: str
    gender: str
    image: str
    origin: dict
    location: dict

class CharactersResponse(BaseModel):
    results: List[Character]

class HealthCheckResponse(BaseModel):
    database: bool
    redis: bool
