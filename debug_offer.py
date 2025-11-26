import sys
import os

# Agregamos la raíz del proyecto al path para poder importar 'app'
sys.path.append(os.getcwd())

try:
    from sqlmodel import Session, select
    from app.services.db.sql_server_connection import engine
    from app.models.job_offer import JobOffer
except ImportError as e:
    print("❌ ERROR DE IMPORTACIÓN: No se encuentra 'app' o 'sqlmodel'.")
    print("Asegúrate de ejecutar esto desde la carpeta raíz donde está 'app/'.")
    print(f"Detalle: {e}")
    sys.exit(1)

def test_connection():
    print("\n--- 1. PROBANDO CONEXIÓN A BASE DE DATOS ---")
    try:
        with Session(engine) as session:
            print("✅ Conexión exitosa.")
            
            print("\n--- 2. INTENTANDO LEER JOB OFFERS ---")
            # Traemos todo sin filtros para estresar el modelo
            statement = select(JobOffer).order_by(JobOffer.id.desc())
            results = session.exec(statement).all()
            
            print(f"📊 Se encontraron {len(results)} ofertas.")
            
            print("\n--- 3. ANALIZANDO FILA POR FILA (SERIALIZACIÓN) ---")
            for i, offer in enumerate(results):
                try:
                    print(f"🔹 Revisando ID: {offer.id} | Título: {offer.title[:15]}...", end=" ")
                    
                    # Prueba de acceso a ENUMS
                    # Esto forzará el error si Python no puede leer 'NORMAL' vs 'normal'
                    tipo = offer.job_type
                    urgencia = offer.urgency
                    estado = offer.status
                    
                    # Prueba de Fechas (Causa común de error 500)
                    inicio = offer.date_start
                    fin = offer.date_end
                    
                    # Prueba de conversión a string (Simula lo que hace FastAPI)
                    print(f"-> [OK] Tipo: {str(tipo)} | Urgencia: {str(urgencia)}")
                    
                    # Verificar tipos de fecha
                    if inicio:
                        print(f"   📅 Inicio: {inicio} (Tipo: {type(inicio).__name__})")
                    
                except Exception as e:
                    print(f"\n❌❌❌ ERROR FATAL EN ID {offer.id} ❌❌❌")
                    print(f"El error es: {repr(e)}")
                    print("--> Este es el registro culpable que rompe tu API.")
                    # break # Descomenta si quieres parar en el primer error
                    
    except Exception as e:
        print(f"\n❌ ERROR GENERAL DE BASE DE DATOS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()