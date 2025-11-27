# app/controllers/review_controller.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select

from app.services.db.sql_server_connection import get_session
from app.services.db.review_service import ReviewService
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewListResponse

# 🚀 Importamos lo necesario para generar el GigPayment
from app.models.job_assignment import JobAssignment
from app.services.db.gig_payments import create_gig_payment_from_assignment

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    reviewer_id: int = Query(
        ...,
        description="ID del usuario que evalúa (SIEMPRE viene por query param)."
    ),
    session: Session = Depends(get_session)
):
    """
    Crea una reseña y, al final, intenta generar el GigPayment
    para la asignación relacionada (worker + oferta).
    """

    # ---------------------------------------------------------
    # DEBUG EXTENDIDO
    # ---------------------------------------------------------
    print("\n" + "=" * 90)
    print("🔍 DEBUG /reviews/")
    print("→ reviewer_id (query):", reviewer_id)
    try:
        print("→ RAW data dict():", data.dict())
    except Exception:
        print("→ RAW data (no dict) :", data)
    print("=" * 90 + "\n")
    # ---------------------------------------------------------

    try:
        review = ReviewService.create_review(
            session=session,
            reviewer_id=int(reviewer_id),
            payload=data
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("❌ EXCEPCIÓN REAL EN ReviewService.create_review()")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado creando reseña: {str(e)}"
        )

    if not review:
        raise HTTPException(
            status_code=400,
            detail="No se pudo crear la reseña."
        )

    print("✅ Reseña creada OK:", review)

    # =========================================================================
    # 🚀 1) Después de crear la reseña, generamos el GigPayment si corresponde
    # =========================================================================
    try:
        # Paso 1: obtener la aplicación que está siendo evaluada
        application = ReviewService.get_application_from_review(
            session=session,
            review=review
        )

        if not application:
            print("⚠ No se encontró job_application, no se puede generar GigPayment.")
            return review

        # Paso 2: buscar el assignment (worker + job_offer)
        assignment = session.exec(
            select(JobAssignment).where(
                JobAssignment.job_offer_id == application.job_offer_id,
                JobAssignment.worker_id == application.user_id  # el barista
            )
        ).first()

        if not assignment:
            print(
                f"⚠ No existe JobAssignment para job_offer={application.job_offer_id} "
                f"y worker={application.user_id}. No se genera GigPayment."
            )
            return review

        # Paso 3: generar o devolver el GigPayment
        print(f"🔄 Intentando crear GigPayment para assignment_id={assignment.id}")
        payment = create_gig_payment_from_assignment(session, assignment)
        print(f"💰 GigPayment generado OK: id={payment.id}")

    except Exception as e:
        print(f"❌ ERROR generando GigPayment automáticamente: {e}")

    # =========================================================================

    return review


@router.get("/user/{user_id}", response_model=ReviewListResponse)
def get_reviews_for_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtiene todas las reseñas activas para un usuario,
    junto con su promedio y cantidad total.
    """
    reviews = ReviewService.get_reviews_for_user(session, user_id)
    avg_rating, cnt = ReviewService.get_reviews_summary_for_user(session, user_id)

    return ReviewListResponse(
        reviewee_id=user_id,
        rating_avg=avg_rating,
        reviews_count=cnt,
        reviews=reviews
    )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    requester_id: int = Query(
        ..., description="ID del usuario que solicita eliminar su propia reseña"
    ),
    session: Session = Depends(get_session)
):
    """
    Elimina (soft-delete) una reseña,
    pero SOLO si pertenece al usuario que intenta eliminarla.
    """
    ok = ReviewService.delete_review(session, review_id, requester_id)

    if not ok:
        raise HTTPException(
            status_code=404,
            detail="Review no encontrada o no tienes permiso para eliminarla."
        )

    return None
