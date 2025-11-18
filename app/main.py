# app/main.py
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Importar routers
from app.controllers.hello_controller import router as hello_router
from app.controllers.db_controller import router as db_router
from app.controllers.user_controller import router as user_router
from app.controllers.login_controller import router as login_router
from app.controllers.profile_controller import router as profile_router
from app.controllers.certificate_controller import router as certificate_router
from app.controllers.certificate_controller import router_download as certificate_download_router
from app.controllers.support_controller import router as support_router
from app.controllers.cv_controller import router as cv_router
from app.controllers.job_application_controller import router as job_application_router
from app.controllers.job_offer_controller import router as job_offer_router



# Crear la aplicación FastAPI
app = FastAPI(title="BaristaApp API")

# CORS (frontend SWA + local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(hello_router)
app.include_router(db_router)
app.include_router(user_router)
app.include_router(login_router)
app.include_router(profile_router)
app.include_router(certificate_router)
app.include_router(certificate_download_router)
app.include_router(support_router)
app.include_router(cv_router)
app.include_router(job_application_router)
app.include_router(job_offer_router)


# Endpoint de health y rutas disponibles
@app.get("/")
def health():
    return {
        "status": "Servicio activo",
        "Date": datetime.now().isoformat(),
        "service": "BaristaApp API",
        "version": "1.0.0",
        "rutas_disponibles": [
            {"ruta": "/", "método": "GET", "descripción": "Health check y rutas disponibles"},
            {"ruta": "/docs", "método": "GET", "descripción": "Documentación Swagger UI"},
            {"ruta": "/redoc", "método": "GET", "descripción": "Documentación ReDoc"},
            {"ruta": "/miapp", "método": "GET", "descripción": "Endpoint principal de la aplicación"},
            {"ruta": "/db/test-connection", "método": "GET", "descripción": "Probar conexión a la base de datos"},
            {"ruta": "/users", "método": "GET/POST/PUT/DELETE", "descripción": "CRUD de usuarios"},
            {"ruta": "/login", "método": "POST", "descripción": "Autenticación de usuarios"},
        ],
    }

# Endpoint principal de la aplicación
@app.get("/miapp")
def miapp():
    return {"message": "hola mundo"}
