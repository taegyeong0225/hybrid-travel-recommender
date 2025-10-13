from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    favorites = relationship("FavoritePlace", back_populates="owner")
    visits = relationship("VisitedPlace", back_populates="owner")

class FavoritePlace(Base):
    __tablename__ = "favorite_places"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    poi_id = Column(String, index=True) # Assuming poi_id is a string, change if it's an integer
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="favorites")

class VisitedPlace(Base):
    __tablename__ = "visited_places"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    poi_id = Column(String, index=True) # Assuming poi_id is a string
    visited_at = Column(DateTime(timezone=True), server_default=func.now())
    rating = Column(Float, nullable=True)
    memo = Column(String, nullable=True)

    owner = relationship("User", back_populates="visits")