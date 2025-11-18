from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DB_SQL_SERVER_GIG")

if not DATABASE_URL:
    raise ValueError("No se encontró la variable DB_SQL_SERVER_GIG en el entorno.")

engine = create_engine(
    DATABASE_URL,
    echo=True,        
    pool_pre_ping=True  
)

def get_session():
    """
    Genera una sesión de base de datos por request y la cierra automáticamente.
    Se usa con: session: Session = Depends(get_session)
    """
    with Session(engine) as session:
        yield session
