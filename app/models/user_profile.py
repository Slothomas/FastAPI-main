# app/models/user_profile.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import NVARCHAR, TEXT, DateTime, DECIMAL, Integer

class UserProfile(SQLModel, table=True):
    __tablename__ = "app_user_profile"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)

    full_name: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(150), nullable=True))
    bio: Optional[str] = Field(default=None, sa_column=Column(TEXT, nullable=True))
    years_experience: Optional[int] = Field(default=None, nullable=True)
    skills: Optional[str] = Field(default=None, sa_column=Column(TEXT, nullable=True))
    avatar_url: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(500), nullable=True))

    region: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(100), nullable=True))
    comuna: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(100), nullable=True))

    availability_json: Optional[str] = Field(default=None, sa_column=Column(TEXT, nullable=True))
    rate_hour: Optional[float] = Field(default=None, sa_column=Column(DECIMAL(10, 2), nullable=True))
    min_shift_rate: Optional[float] = Field(default=None, sa_column=Column(DECIMAL(10, 2), nullable=True))

    business_name: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(200), nullable=True))
    business_type: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(100), nullable=True))

    rating_avg: Optional[float] = Field(default=None, sa_column=Column(DECIMAL(3, 2), nullable=True))
    reviews_count: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))

    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))
