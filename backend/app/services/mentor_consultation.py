from __future__ import annotations

from datetime import datetime
from typing import Iterable

from app.services.supabase_resilience import call_supabase


PUBLIC_PROFILE_FIELDS = (
    "id,display_name,avatar_label,avatar_url,avatar_tone,school,major,"
    "admission_year,graduation_year,exam_type,score,bio,story,price_cents,"
    "consultation_window_minutes,online_status,accepts_booking,is_featured,"
    "recommend_score,rating,rating_count,consult_count,verification_status,is_published"
)

ADMIN_PROFILE_FIELDS = (
    "id,owner_user_id,legal_name,display_name,avatar_label,avatar_url,avatar_tone,"
    "school,major,admission_year,graduation_year,exam_type,score,bio,story,"
    "price_cents,consultation_window_minutes,online_status,accepts_booking,"
    "verification_status,is_published,is_featured,recommend_score,rating,"
    "rating_count,consult_count,created_at,updated_at"
)

CONSULTATION_ORDER_FIELDS = (
    "id,order_no,applicant_user_id,mentor_id,slot_id,consultation_type,order_status,"
    "payment_status,questionnaire,price_cents,consultation_window_minutes,"
    "payment_reference,accepted_at,expires_at,started_at,ended_at,created_at,updated_at"
)

CONSULTATION_MESSAGE_FIELDS = (
    "id,order_id,sender_role,message_type,content,duration_seconds,created_at"
)


def mask_mentor_name(name: str | None) -> str:
    normalized = str(name or "").strip()
    if len(normalized) <= 1:
        return normalized
    if len(normalized) == 2:
        return f"{normalized[:1]}*"
    return f"{normalized[:1]}*{normalized[-1:]}"


def normalize_skills(skills: Iterable[str] | None) -> list[str]:
    normalized: list[str] = []
    for skill in skills or []:
        value = str(skill or "").strip()
        if value and value not in normalized:
            normalized.append(value[:40])
    return normalized[:12]


def fetch_mentor_skills(supabase, mentor_ids: Iterable[str]) -> dict[str, list[str]]:
    ids = list(dict.fromkeys(str(mentor_id) for mentor_id in mentor_ids if mentor_id))
    if not ids:
        return {}

    response = call_supabase(
        lambda: (
            supabase.table("mentor_profile_skills")
            .select("mentor_id,skill,sort_order")
            .in_("mentor_id", ids)
            .order("sort_order")
            .execute()
        ),
        operation_name="mentor profile skill lookup",
    )
    result: dict[str, list[str]] = {mentor_id: [] for mentor_id in ids}
    for row in response.data or []:
        mentor_id = str(row.get("mentor_id") or "")
        skill = str(row.get("skill") or "").strip()
        if mentor_id and skill:
            result.setdefault(mentor_id, []).append(skill)
    return result


def fetch_mentor_aggregates(supabase, mentor_ids: Iterable[str]) -> dict[str, dict]:
    ids = list(dict.fromkeys(str(mentor_id) for mentor_id in mentor_ids if mentor_id))
    if not ids:
        return {}

    result = {
        mentor_id: {"rating": 0.0, "rating_count": 0, "consult_count": 0}
        for mentor_id in ids
    }
    review_response = call_supabase(
        lambda: (
            supabase.table("mentor_reviews")
            .select("mentor_id,rating")
            .in_("mentor_id", ids)
            .eq("is_published", True)
            .execute()
        ),
        operation_name="mentor aggregate review lookup",
    )
    rating_totals: dict[str, float] = {mentor_id: 0.0 for mentor_id in ids}
    for row in review_response.data or []:
        mentor_id = str(row.get("mentor_id") or "")
        if mentor_id not in result:
            continue
        result[mentor_id]["rating_count"] += 1
        rating_totals[mentor_id] += float(row.get("rating") or 0)

    order_response = call_supabase(
        lambda: (
            supabase.table("mentor_consultation_orders")
            .select("mentor_id")
            .in_("mentor_id", ids)
            .eq("order_status", "completed")
            .execute()
        ),
        operation_name="mentor aggregate order lookup",
    )
    for row in order_response.data or []:
        mentor_id = str(row.get("mentor_id") or "")
        if mentor_id in result:
            result[mentor_id]["consult_count"] += 1

    for mentor_id, aggregate in result.items():
        rating_count = int(aggregate["rating_count"])
        aggregate["rating"] = round(rating_totals[mentor_id] / rating_count, 1) if rating_count else 0.0
    return result


def serialize_mentor_public(
    row: dict,
    skills: Iterable[str] | None = None,
    aggregate: dict | None = None,
) -> dict:
    mentor_id = str(row.get("id") or "")
    price_cents = max(0, int(row.get("price_cents") or 0))
    metrics = aggregate or {
        "rating": float(row.get("rating") or 0),
        "rating_count": int(row.get("rating_count") or 0),
        "consult_count": int(row.get("consult_count") or 0),
    }
    return {
        "id": mentor_id,
        "display_name": str(row.get("display_name") or "前辈"),
        "avatar": str(row.get("avatar_label") or "研"),
        "avatar_url": row.get("avatar_url") or None,
        "avatar_tone": str(row.get("avatar_tone") or "blue"),
        "school": str(row.get("school") or ""),
        "major": str(row.get("major") or ""),
        "admission_year": int(row.get("admission_year") or 0),
        "graduation_year": int(row["graduation_year"]) if row.get("graduation_year") is not None else None,
        "exam_type": str(row.get("exam_type") or "Z001"),
        "score": int(row.get("score") or 0),
        "rating": float(metrics.get("rating") or 0),
        "rating_count": int(metrics.get("rating_count") or 0),
        "consult_count": int(metrics.get("consult_count") or 0),
        "price": round(price_cents / 100, 2),
        "consultation_window_minutes": int(row.get("consultation_window_minutes") or 60),
        "online_status": str(row.get("online_status") or "offline"),
        "accepts_booking": bool(row.get("accepts_booking", True)),
        "is_featured": bool(row.get("is_featured")),
        "recommend_score": int(row.get("recommend_score") or 0),
        "bio": str(row.get("bio") or ""),
        "story": str(row.get("story") or ""),
        "skills": normalize_skills(skills),
        "verified": str(row.get("verification_status") or "") == "verified",
    }


def serialize_mentor_admin(
    row: dict,
    skills: Iterable[str] | None = None,
    aggregate: dict | None = None,
) -> dict:
    payload = serialize_mentor_public(row, skills, aggregate)
    payload.update({
        "legal_name": str(row.get("legal_name") or ""),
        "owner_user_id": str(row.get("owner_user_id")) if row.get("owner_user_id") else None,
        "verification_status": str(row.get("verification_status") or "unverified"),
        "is_published": bool(row.get("is_published")),
        "created_at": row.get("created_at") or None,
        "updated_at": row.get("updated_at") or None,
    })
    return payload


def serialize_mentor_review(row: dict) -> dict:
    created_at = row.get("created_at")
    date = None
    if isinstance(created_at, str):
        try:
            date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            date = created_at[:10]
    return {
        "id": str(row.get("id") or ""),
        "author": str(row.get("reviewer_display_name") or "匿名用户"),
        "rating": float(row.get("rating") or 0),
        "date": date,
        "content": str(row.get("content") or ""),
    }


def serialize_mentor_slot(row: dict) -> dict:
    return {
        "id": str(row.get("id") or ""),
        "starts_at": row.get("starts_at") or None,
        "ends_at": row.get("ends_at") or None,
        "price": round(max(0, int(row.get("price_cents") or 0)) / 100, 2) if row.get("price_cents") is not None else None,
        "status": str(row.get("status") or "available"),
    }


def serialize_mentor_order(row: dict) -> dict:
    questionnaire = row.get("questionnaire") if isinstance(row.get("questionnaire"), dict) else {}
    return {
        "id": str(row.get("id") or ""),
        "order_no": str(row.get("order_no") or ""),
        "applicant_user_id": str(row.get("applicant_user_id") or ""),
        "mentor_id": str(row.get("mentor_id") or ""),
        "slot_id": str(row.get("slot_id")) if row.get("slot_id") else None,
        "consultation_type": str(row.get("consultation_type") or "instant"),
        "order_status": str(row.get("order_status") or "draft"),
        "payment_status": str(row.get("payment_status") or "unpaid"),
        "questionnaire": {
            "name": str(questionnaire.get("name") or "未填写"),
            "school": str(questionnaire.get("school") or "未填写"),
            "major": str(questionnaire.get("major") or "未填写"),
            "grade": str(questionnaire.get("grade") or "其他"),
            "graduation_year": questionnaire.get("graduation_year"),
            "question": str(questionnaire.get("question") or ""),
        },
        "price": round(max(0, int(row.get("price_cents") or 0)) / 100, 2),
        "consultation_window_minutes": int(row.get("consultation_window_minutes") or 60),
        "payment_reference": row.get("payment_reference") or None,
        "accepted_at": row.get("accepted_at") or None,
        "expires_at": row.get("expires_at") or None,
        "started_at": row.get("started_at") or None,
        "ended_at": row.get("ended_at") or None,
        "created_at": row.get("created_at") or None,
        "updated_at": row.get("updated_at") or None,
    }


def serialize_mentor_message(row: dict) -> dict:
    return {
        "id": str(row.get("id") or ""),
        "sender_role": str(row.get("sender_role") or "system"),
        "message_type": str(row.get("message_type") or "text"),
        "content": str(row.get("content") or ""),
        "duration_seconds": int(row["duration_seconds"]) if row.get("duration_seconds") is not None else None,
        "created_at": row.get("created_at") or None,
    }
