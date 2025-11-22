from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List

from app.services.db.sql_server_connection import get_session
from app.services.db.favorites_service import FavoritesService
from app.schemas.favorites import (
    FavoriteOfferResponse,
    FavoriteWorkerResponse,
    FavoriteOfferWithInfo,
    FavoriteWorkerWithInfo
)

router = APIRouter(prefix="/favorites", tags=["Favorites"])


# ==========================================================
# FAVORITE OFFERS (worker)
# ==========================================================

@router.post("/offers/{job_offer_id}", response_model=FavoriteOfferResponse, status_code=status.HTTP_201_CREATED)
def add_favorite_offer(
    job_offer_id: int,
    user_id: int = Query(..., description="Worker que guarda la oferta"),
    session: Session = Depends(get_session)
):
    try:
        fav = FavoritesService.add_favorite_offer(session, user_id, job_offer_id)
        if not fav:
            raise HTTPException(status_code=400, detail="No se pudo guardar favorito")
        return fav
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando favorito: {str(e)}")


@router.delete("/offers/{job_offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_offer(
    job_offer_id: int,
    user_id: int = Query(..., description="Worker dueño del favorito"),
    session: Session = Depends(get_session)
):
    try:
        ok = FavoritesService.remove_favorite_offer(session, user_id, job_offer_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Favorito no encontrado")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error quitando favorito: {str(e)}")


@router.get("/offers", response_model=List[FavoriteOfferWithInfo])
def list_favorite_offers(
    user_id: int = Query(..., description="Worker dueño de favoritos"),
    session: Session = Depends(get_session)
):
    try:
        return FavoritesService.list_favorite_offers(session, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando favoritos: {str(e)}")


# ==========================================================
# FAVORITE WORKERS (client)
# ==========================================================

@router.post("/workers/{worker_user_id}", response_model=FavoriteWorkerResponse, status_code=status.HTTP_201_CREATED)
def add_favorite_worker(
    worker_user_id: int,
    client_user_id: int = Query(..., description="Cliente que guarda al worker"),
    session: Session = Depends(get_session)
):
    try:
        fav = FavoritesService.add_favorite_worker(session, client_user_id, worker_user_id)
        if not fav:
            raise HTTPException(status_code=400, detail="No se pudo guardar favorito")
        return fav
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando favorito: {str(e)}")


@router.delete("/workers/{worker_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_worker(
    worker_user_id: int,
    client_user_id: int = Query(..., description="Cliente dueño del favorito"),
    session: Session = Depends(get_session)
):
    try:
        ok = FavoritesService.remove_favorite_worker(session, client_user_id, worker_user_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Favorito no encontrado")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error quitando favorito: {str(e)}")


@router.get("/workers", response_model=List[FavoriteWorkerWithInfo])
def list_favorite_workers(
    client_user_id: int = Query(..., description="Cliente dueño de favoritos"),
    session: Session = Depends(get_session)
):
    try:
        return FavoritesService.list_favorite_workers(session, client_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando favoritos: {str(e)}")
