# app/services/db/profile_service.py
from typing import Optional
from datetime import datetime
from sqlmodel import Session, select

from app.models.user_profile import UserProfile
from app.schemas.profile import ProfileUpdate


def get_profile_by_user_id(user_id: int, session: Session) -> Optional[UserProfile]:
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    return session.exec(stmt).first()


def upsert_profile(
    user_id: int,
    data: ProfileUpdate,
    session: Session,
) -> UserProfile:
    profile = get_profile_by_user_id(user_id, session)

    # skills lista → string para BD
    skills_str = None
    if data.skills is not None:
        skills_str = ",".join(s.strip() for s in data.skills if s.strip())

    if profile is None:
        profile = UserProfile(
            user_id=user_id,
            full_name=data.full_name,
            bio=data.bio,
            years_experience=data.years_experience,
            skills=skills_str,
            avatar_url=data.avatar_url,

            # --- nuevos campos gig ---
            region=data.region,
            comuna=data.comuna,
            availability_json=data.availability_json,
            rate_hour=data.rate_hour,
            min_shift_rate=data.min_shift_rate,
            business_name=data.business_name,
            business_type=data.business_type,
            rating_avg=data.rating_avg,
            reviews_count=data.reviews_count or 0,
        )
        session.add(profile)

    else:
        # --- campos existentes ---
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

        # --- nuevos campos gig ---
        if data.region is not None:
            profile.region = data.region
        if data.comuna is not None:
            profile.comuna = data.comuna
        if data.availability_json is not None:
            profile.availability_json = data.availability_json
        if data.rate_hour is not None:
            profile.rate_hour = data.rate_hour
        if data.min_shift_rate is not None:
            profile.min_shift_rate = data.min_shift_rate
        if data.business_name is not None:
            profile.business_name = data.business_name
        if data.business_type is not None:
            profile.business_type = data.business_type
        if data.rating_avg is not None:
            profile.rating_avg = data.rating_avg
        if data.reviews_count is not None:
            profile.reviews_count = data.reviews_count

        profile.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(profile)
    return profile
