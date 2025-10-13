from sqlalchemy.orm import Session
from . import models, schemas

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(
        username=user.username,
        name=user.name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_favorite_places(db: Session, user_id: int):
    return db.query(models.FavoritePlace).filter(models.FavoritePlace.user_id == user_id).all()

def create_user_favorite_place(db: Session, favorite: schemas.FavoritePlaceCreate, user_id: int):
    db_favorite = models.FavoritePlace(**favorite.dict(), user_id=user_id)
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite

def get_visited_places(db: Session, user_id: int):
    return db.query(models.VisitedPlace).filter(models.VisitedPlace.user_id == user_id).all()

def create_user_visited_place(db: Session, visited: schemas.VisitedPlaceCreate, user_id: int):
    db_visited = models.VisitedPlace(**visited.dict(), user_id=user_id)
    db.add(db_visited)
    db.commit()
    db.refresh(db_visited)
    return db_visited