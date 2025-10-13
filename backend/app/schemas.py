from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Favorite Place Schemas
class FavoritePlaceBase(BaseModel):
    poi_id: str

class FavoritePlaceCreate(FavoritePlaceBase):
    pass

class FavoritePlace(FavoritePlaceBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Visited Place Schemas
class VisitedPlaceBase(BaseModel):
    poi_id: str
    rating: Optional[float] = None
    memo: Optional[str] = None

class VisitedPlaceCreate(VisitedPlaceBase):
    pass

class VisitedPlace(VisitedPlaceBase):
    id: int
    user_id: int
    visited_at: datetime

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    username: str
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    favorites: List[FavoritePlace] = []
    visits: List[VisitedPlace] = []

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None