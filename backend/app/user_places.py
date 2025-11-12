from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas
from .database import get_db
from .auth import get_current_user

router = APIRouter(
    tags=["user_places"],
    dependencies=[Depends(get_current_user)] # All routes in this router require authentication
)

@router.post("/favorites/add", response_model=schemas.FavoritePlace)
def add_favorite(
    favorite: schemas.FavoritePlaceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_user_favorite_place(db=db, favorite=favorite, user_id=current_user.id)

@router.get("/favorites", response_model=List[schemas.FavoritePlace])
def get_favorites(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_favorite_places(db=db, user_id=current_user.id)

@router.post("/visited/add", response_model=schemas.VisitedPlace)
def add_visited(
    visited: schemas.VisitedPlaceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_user_visited_place(db=db, visited=visited, user_id=current_user.id)

@router.get("/visited", response_model=List[schemas.VisitedPlace])
def get_visited(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_visited_places(db=db, user_id=current_user.id)
