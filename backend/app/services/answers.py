from datetime import datetime, timezone

from fastapi import HTTPException, status
from supabase import Client

from app.db import get_supabase_admin

VERSION_EXAM_CODES = {"Z001", "Z002"}
PUBLIC_SUBJECTS = {"中华文化", "英语运用"}


def get_question_or_404(supabase: Client, question_id: str) -> dict:
    response = supabase.table("questions").select("*").eq("id", question_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return response.data[0]


def resolve_stats_exam_code(
    supabase: Client,
    user_id: str,
    question: dict,
    requested_exam_code: str | None = None,
) -> str:
    """COMMON 公共题按用户当前版本写入能力统计，避免报告里出现 COMMON 分组。"""
    question_exam_code = question["exam_code"]
    if question.get("subject") in PUBLIC_SUBJECTS and requested_exam_code in VERSION_EXAM_CODES:
        return requested_exam_code

    if question_exam_code != "COMMON":
        return question_exam_code

    if requested_exam_code in VERSION_EXAM_CODES:
        return requested_exam_code

    response = supabase.table("users").select("exam_target").eq("id", user_id).limit(1).execute()
    profile = response.data[0] if response.data else {}
    exam_target = profile.get("exam_target")
    return exam_target if exam_target in VERSION_EXAM_CODES else "Z001"


def record_wrong_question(supabase: Client, user_id: str, question_id: str) -> None:
    existing = (
        supabase.table("wrong_questions")
        .select("id, wrong_count")
        .eq("user_id", user_id)
        .eq("question_id", question_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        row = existing.data[0]
        supabase.table("wrong_questions").update(
            {"wrong_count": int(row["wrong_count"]) + 1, "last_wrong_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", row["id"]).execute()
        return

    supabase.table("wrong_questions").insert({"user_id": user_id, "question_id": question_id}).execute()


def update_ability_stats(supabase: Client, user_id: str, question: dict, is_correct: bool) -> dict:
    filters = {
        "user_id": user_id,
        "exam_code": question["exam_code"],
        "subject": question["subject"],
        "module": question["module"],
        "submodule": question["submodule"],
    }
    query = supabase.table("ability_stats").select("*")
    for key, value in filters.items():
        query = query.eq(key, value)
    current = query.limit(1).execute()

    if current.data:
        row = current.data[0]
        total_count = int(row["total_count"]) + 1
        correct_count = int(row["correct_count"]) + (1 if is_correct else 0)
        accuracy = round(correct_count / total_count * 100, 2)
        updated = (
            supabase.table("ability_stats")
            .update({"total_count": total_count, "correct_count": correct_count, "accuracy": accuracy})
            .eq("id", row["id"])
            .execute()
        )
        return updated.data[0]

    total_count = 1
    correct_count = 1 if is_correct else 0
    accuracy = round(correct_count / total_count * 100, 2)
    inserted = (
        supabase.table("ability_stats")
        .insert({**filters, "total_count": total_count, "correct_count": correct_count, "accuracy": accuracy})
        .execute()
    )
    return inserted.data[0]


def get_current_ability_stats(supabase: Client, user_id: str, question: dict) -> dict | None:
    filters = {
        "user_id": user_id,
        "exam_code": question["exam_code"],
        "subject": question["subject"],
        "module": question["module"],
        "submodule": question["submodule"],
    }
    query = supabase.table("ability_stats").select("*")
    for key, value in filters.items():
        query = query.eq(key, value)
    current = query.limit(1).execute()
    return current.data[0] if current.data else None


def calculate_next_accuracy(current: dict | None, is_correct: bool) -> float:
    if current:
        total_count = int(current["total_count"]) + 1
        correct_count = int(current["correct_count"]) + (1 if is_correct else 0)
    else:
        total_count = 1
        correct_count = 1 if is_correct else 0
    return round(correct_count / total_count * 100, 2)


def persist_answer_submission(
    user_id: str,
    question: dict,
    selected_answer: str,
    used_time: int,
    is_correct: bool,
) -> None:
    try:
        supabase = get_supabase_admin()
        question_id = question["id"]

        supabase.table("user_answers").insert(
            {
                "user_id": user_id,
                "question_id": question_id,
                "selected_answer": selected_answer,
                "is_correct": is_correct,
                "used_time": used_time,
            }
        ).execute()

        if not is_correct:
            record_wrong_question(supabase, user_id, question_id)

        update_ability_stats(supabase, user_id, question, is_correct)
    except Exception as exc:  # noqa: BLE001
        print(f"persist_answer_submission failed for user_id={user_id}, question_id={question['id']}: {exc}")


def submit_answer(
    supabase: Client,
    user_id: str,
    question_id: str,
    selected_answer: str,
    used_time: int,
    requested_exam_code: str | None = None,
) -> dict:
    question = get_question_or_404(supabase, question_id)
    stats_exam_code = resolve_stats_exam_code(supabase, user_id, question, requested_exam_code)
    stats_question = {**question, "exam_code": stats_exam_code}
    is_correct = selected_answer == question["answer"]
    current_ability = get_current_ability_stats(supabase, user_id, stats_question)

    return {
        "question_id": question_id,
        "exam_code": stats_exam_code,
        "subject": question["subject"],
        "module": question["module"],
        "submodule": question["submodule"],
        "selected_answer": selected_answer,
        "correct_answer": question["answer"],
        "is_correct": is_correct,
        "explanation": question["explanation"],
        "added_to_wrong_questions": not is_correct,
        "ability_accuracy": calculate_next_accuracy(current_ability, is_correct),
    }


def list_answer_history(
    supabase: Client,
    user_id: str,
    status_filter: str = "all",
    subject: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> dict:
    """Return recent answer records with question details for the practice history page."""

    query = (
        supabase.table("user_answers")
        .select("id, question_id, selected_answer, is_correct, used_time, created_at, questions(*)")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )

    if status_filter == "correct":
        query = query.eq("is_correct", True)
    elif status_filter == "wrong":
        query = query.eq("is_correct", False)

    response = query.execute()
    items: list[dict] = []
    for row in response.data or []:
        question = row.get("questions")
        if subject and question and question.get("subject") != subject:
            continue
        items.append(
            {
                "id": row["id"],
                "question_id": row["question_id"],
                "selected_answer": row["selected_answer"],
                "is_correct": row["is_correct"],
                "used_time": row.get("used_time", 0),
                "created_at": row["created_at"],
                "question": question,
            }
        )

    return {"items": items, "count": len(items)}
