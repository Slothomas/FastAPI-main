# app/database.py
import os
from sqlalchemy import create_engine
from sqlmodel import SQLModel
from dotenv import load_dotenv

# Carga .env solo en local (en Azure no es necesario)
load_dotenv(override=False)

DB_URL = os.getenv("DB_SQL_SERVER_GIG")
if not DB_URL:
    raise RuntimeError("Falta la variable de entorno DB_SQL_SERVER_GIG")

# mssql+pytds://...  (no requiere drivers del SO)
engine = create_engine(DB_URL, pool_pre_ping=True, echo=False, future=True)

def init_models() -> None:
    """
    Si usas SQLModel con modelos declarativos y quieres crear tablas en dev.
    En prod normalmente no se auto-crean (usa migraciones).
    """
    SQLModel.metadata.create_all(engine)
