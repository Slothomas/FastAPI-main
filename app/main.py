import sys
import traceback
from datetime import datetime
import time
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


# =================================================================
# IMPORTACIÓN DE ROUTERS
# =================================================================
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
from app.controllers.review_controller import router as review_router
from app.controllers.favorites_controller import router as favorite_router
from app.controllers.notification_controller import router as notification_router
from app.controllers.event_log_controller import router as event_log_router
from app.controllers.assignment_controller import router as assignment_router
from app.controllers.business_controller import router as business_router
from app.controllers.analytics_controller import router as analytics_router

# Crear la aplicación FastAPI
app = FastAPI(title="BaristaApp API")



# =================================================================
# MIDDLEWARE DE DEPURACION (Captura errores ocultos)
# =================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    ms = (time.time() - start) * 1000

    logging.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({ms:.1f} ms)"
    )
    return response


# Handler de excepciones estándar de FastAPI
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("\n--- ERROR 500 EN BACKEND (HANDLER) ---")
    print("URL:", request.url)
    print("EXC:", repr(exc))
    traceback.print_exc()
    print("--- FIN ERROR ---\n")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "error": repr(exc)},
    )


# CORS (frontend SWA + local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",   # dejarlo por si usas algún otro origen local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =================================================================
# INCLUSIÓN DE ROUTERS
# =================================================================
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
app.include_router(review_router)
app.include_router(favorite_router)
app.include_router(notification_router)
app.include_router(event_log_router)
app.include_router(assignment_router)
app.include_router(business_router)
app.include_router(analytics_router)



# =================================================================
# ENDPOINTS GENERALES
# =================================================================

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