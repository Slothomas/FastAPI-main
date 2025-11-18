from typing import Optional
from datetime import datetime

from sqlmodel import Session, select

from app.models.user_profile import UserProfile      
from app.schemas.profile import ProfileUpdate


# ============================================================
# Obtener perfil por user_id
# ============================================================
def get_profile_by_user_id(user_id: int, session: Session) -> Optional[UserProfile]:
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    return session.exec(stmt).first()


# ============================================================
# Crear o actualizar perfil (upsert)
# ============================================================
def upsert_profile(
    user_id: int,
    data: ProfileUpdate,
    session: Session,
) -> UserProfile:
    profile = get_profile_by_user_id(user_id, session)

    # Convertimos lista de skills → string (coma-separado) para la BD
    skills_str = None
    if data.skills is not None:
        skills_str = ",".join(s.strip() for s in data.skills if s.strip())

    if profile is None:
        # crear nuevo
        profile = UserProfile(
            user_id=user_id,
            full_name=data.full_name,
            bio=data.bio,
            years_experience=data.years_experience,
            skills=skills_str,
            avatar_url=data.avatar_url,
        )
        session.add(profile)
    else:
        # actualizar existente
        if data.full_name is not None:
            profile.full_name = data.full_name
        if data.bio is not None:
            profile.bio = data.bio
        if data.years_experience is not None:
            profile.years_experience = data.years_experience
        if data.skills is not None:
            profile.skills = skills_str
        if data.avatar_url is not None:
            profile.avatar_url = data.avatar_url

        profile.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(profile)
    return profile
