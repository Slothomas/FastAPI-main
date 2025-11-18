from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import NVARCHAR, VARCHAR, DateTime, SmallInteger

class AppUser(SQLModel, table=True):
    """
    Modelo de la tabla app_user en la base de datos.
    Representa un usuario de la aplicación.
    """
    __tablename__ = "app_user"

    id: Optional[int] = Field(default=None, primary_key=True)
    user: str = Field(sa_column=Column(NVARCHAR(50), nullable=False))
    email: str = Field(sa_column=Column(NVARCHAR(254), nullable=False, unique=True, index=True))
    password: str = Field(sa_column=Column(NVARCHAR(200), nullable=False))
    clave: Optional[str] = Field(default=None, sa_column=Column(VARCHAR(512), nullable=True))

    question1_id: Optional[int] = Field(default=None, sa_column=Column(SmallInteger, nullable=True))
    question1_answ: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(255), nullable=True))
    question2_id: Optional[int] = Field(default=None, sa_column=Column(SmallInteger, nullable=True))
    question2_answ: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(255), nullable=True))

    is_active: int = Field(default=1, nullable=False)
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime, nullable=False))
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime, nullable=False))
