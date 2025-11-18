from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class UserProfile(SQLModel, table=True):
    __tablename__ = "app_user_profile"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="app_user.id", index=True)

    full_name: Optional[str] = Field(default=None, max_length=150)
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    skills: Optional[str] = None
    avatar_url: Optional[str] = Field(default=None, max_length=500)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
