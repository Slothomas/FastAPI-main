# app/controllers/db_controller.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, text
from app.services.db.sql_server_connection import get_session

router = APIRouter(prefix="/db", tags=["Database"])

@router.get("/test-connection")
def test_db_connection(db: Session = Depends(get_session)):
    try:
        row = db.exec(text("SELECT CAST(GETDATE() AS datetime) AS now, @@VERSION AS version")).first()
        return {
            "status": "success",
            "message": "Conexión a la base de datos exitosa",
            "database": "SQL Server",
            "server_time": str(row.now) if row else None,
            "sql_server_version": row.version if row else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": "Error al conectar con la base de datos", "error": str(e)})
