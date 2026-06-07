AI_QUESTION_SOURCE_TYPE = "ai_deepseek"


def is_ai_generated_question(question: dict | None) -> bool:
    return str((question or {}).get("source_type") or "").lower().startswith("ai")


def exclude_ai_generated_questions(query, reference_table: str | None = None):
    filters = f"source_type.is.null,source_type.neq.{AI_QUESTION_SOURCE_TYPE}"
    if reference_table:
        return query.or_(filters, reference_table=reference_table)
    return query.or_(filters)
