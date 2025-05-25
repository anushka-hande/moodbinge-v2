# backend/app/models/user.py
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)  # Fixed: Added length
    username = Column(String(100), unique=True, index=True)  # Fixed: Added length
    hashed_password = Column(String(255))  # Fixed: Added length
    is_active = Column(Boolean, default=True)