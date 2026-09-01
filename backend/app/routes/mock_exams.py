from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin
from app.dependencies import get_current_user_id, require_question_admin_user
from app.schemas.mock_exams import (
    AdminMockExamPaperCreateRequest,
    AdminMockExamPaperDetailResponse,
    AdminMockExamPaperUpdateRequest,
    AdminMockExamQuestionListResponse,
    MockExamDifficultyValidation,
    MockExamPaperDetailResponse,
    MockExamPaperListResponse,
    MockExamPaperQuestion,
    MockExamPaperSummary,
    MockExamSectionValidation,
    MockExamValidationResult,
)
from app.services.answers import warm_submission_questions
from app.services.question_catalog import get_question_catalog
from app.services.question_sources import AI_QUESTION_SOURCE_TYPE, exclude_ai_generated_questions


router = APIRouter(prefix="/mock-exams", tags=["模拟卷"])
admin_router = APIRouter(prefix="/admin/mock-exams", tags=["admin-mock-exams"])

MOCK_EXAM_TOTAL_COUNT = 55
MOCK_EXAM_TOTAL_SCORE = 105
MOCK_EXAM_DIFFICULTY_TARGETS = {
    "basic": {"label": "基础", "count": 19},
    "medium": {"label": "中等", "count": 28},
    "hard": {"label": "较难", "count": 8},
}
MOCK_EXAM_SECTION_ORDER = ("culture", "english", "third")


def _section_rules(exam_code: str) -> dict[str, dict]:
    third_subject = "数学基础" if exam_code == "Z002" else "逻辑推理"
    return {
        "culture": {
            "label": "中华文化常识",
            "subject": "中华文化",
            "count": 20,
            "point_value": 2,
        },
        "english": {
            "label": "英语语言知识",
            "subject": "英语运用",
            "count": 20,
            "point_value": 1,
        },
        "third": {
            "label": third_subject,
            "subject": third_subject,
            "count": 15,
            "point_value": 3,
        },
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_publish_version(paper: dict) -> int:
    current_version = max(1, int(paper.get("version") or 1))
    if paper.get("status") in {"published", "archived"}:
        return current_version + 1
    return current_version


def _paper_summary(row: dict) -> MockExamPaperSummary:
    return MockExamPaperSummary(
        id=str(row.get("id") or ""),
        title=str(row.get("title") or "未命名模拟卷"),
        exam_code=str(row.get("exam_code") or "Z001"),
        description=str(row.get("description") or ""),
        duration_minutes=int(row.get("duration_minutes") or 120),
        status=str(row.get("status") or "draft"),
        version=max(1, int(row.get("version") or 1)),
        question_count=max(0, int(row.get("question_count") or 0)),
        total_score=max(0, int(row.get("total_score") or 0)),
        sort_order=max(0, int(row.get("sort_order") or 0)),
        published_at=row.get("published_at"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _get_paper_or_404(supabase, paper_id: str, *, published_only: bool = False) -> dict:
    query = supabase.table("mock_exam_papers").select("*").eq("id", paper_id)
    if published_only:
        query = query.eq("status", "published")
    response = query.limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模拟卷不存在或尚未发布")
    return response.data[0]


def _list_paper_item_rows(supabase, paper_id: str) -> list[dict]:
    response = (
        supabase.table("mock_exam_paper_items")
        .select("id,paper_id,question_id,section_key,position,point_value")
        .eq("paper_id", paper_id)
        .order("position")
        .limit(MOCK_EXAM_TOTAL_COUNT)
        .execute()
    )
    return response.data or []


def _fetch_questions_by_ids(supabase, question_ids: list[str]) -> dict[str, dict]:
    unique_ids = list(dict.fromkeys(str(value) for value in question_ids if value))
    rows: list[dict] = []
    for offset in range(0, len(unique_ids), 100):
        batch = unique_ids[offset : offset + 100]
        if not batch:
            continue
        response = supabase.table("questions").select("*").in_("id", batch).execute()
        rows.extend(response.data or [])
    return {str(row.get("id")): row for row in rows if row.get("id")}


def _normalize_stem(value: object) -> str:
    text = re.sub(r"\s+", "", str(value or ""))
    return re.sub(r"[，。！？；：,.!?;:()\[\]（）【】“”‘’\"']", "", text).lower()


def _difficulty_band(question: dict) -> str:
    try:
        value = int(question.get("difficulty") or 3)
    except (TypeError, ValueError):
        value = 3
    if value <= 2:
        return "basic"
    if value == 3:
        return "medium"
    return "hard"


def _is_reading_question(question: dict) -> bool:
    text = " ".join(
        str(question.get(field) or "")
        for field in ("module", "submodule", "stem")
    )
    return "阅读理解" in text or "阅读" in text


def _compatible_exam_codes(exam_code: str, section_key: str) -> set[str]:
    if section_key == "culture":
        return {"COMMON", "Z001", "Z002"}
    if section_key == "english":
        return {"COMMON", exam_code}
    return {exam_code}


def _normalize_question_option_classification(
    exam_code: str,
    section_key: str,
    module: str | None,
    submodule: str | None,
) -> tuple[str, str]:
    subject = _section_rules(exam_code)[section_key]["subject"]
    modules = (get_question_catalog().get(subject) or {}).get("modules") or {}
    normalized_module = str(module or "").strip()
    normalized_submodule = str(submodule or "").strip()

    if normalized_module and normalized_module not in modules:
        raise ValueError(f"{subject} 不支持分类：{normalized_module}")

    if normalized_submodule and not normalized_module:
        matching_modules = [
            name
            for name, submodules in modules.items()
            if normalized_submodule in (submodules or [])
        ]
        if len(matching_modules) != 1:
            raise ValueError("请先选择题目分类，再选择具体考点")
        normalized_module = matching_modules[0]

    if normalized_submodule and normalized_submodule not in (modules.get(normalized_module) or []):
        raise ValueError(f"{subject} / {normalized_module} 不支持考点：{normalized_submodule}")

    return normalized_module, normalized_submodule


def _question_section_error(question: dict, exam_code: str, section_key: str) -> str | None:
    rules = _section_rules(exam_code)
    rule = rules[section_key]
    question_id = str(question.get("id") or "未知题目")
    subject = str(question.get("subject") or "")
    question_exam_code = str(question.get("exam_code") or "")

    if str(question.get("source_type") or "").lower() == AI_QUESTION_SOURCE_TYPE:
        return f"题目 {question_id} 是临时 AI 训练题，不能加入固定模拟卷"
    if str(question.get("question_type") or "single_choice") != "single_choice":
        return f"题目 {question_id} 不是四选一单选题"
    if subject != rule["subject"]:
        return f"题目 {question_id} 不属于“{rule['label']}”分区"
    if question_exam_code not in _compatible_exam_codes(exam_code, section_key):
        return f"题目 {question_id} 与 {exam_code} 试卷不兼容"
    if section_key == "english" and str(question.get("module") or "") != "语言知识":
        return f"题目 {question_id} 不是英语语言知识题"
    if section_key in {"culture", "english"} and _is_reading_question(question):
        return f"题目 {question_id} 属于阅读类题目，不能加入模拟卷"
    return None


def validate_mock_exam_selection(
    exam_code: str,
    item_rows: list[dict],
    question_by_id: dict[str, dict],
    *,
    require_complete: bool,
) -> MockExamValidationResult:
    rules = _section_rules(exam_code)
    errors: list[str] = []
    section_counts: Counter[str] = Counter()
    difficulty_counts: Counter[str] = Counter()
    seen_ids: set[str] = set()
    seen_stems: set[str] = set()
    total_score = 0

    for item in item_rows:
        question_id = str(item.get("question_id") or "")
        section_key = str(item.get("section_key") or "")
        if section_key not in rules:
            errors.append(f"题目 {question_id or '未知'} 的卷面分区无效")
            continue
        if question_id in seen_ids:
            errors.append(f"题目 {question_id} 被重复选择")
            continue
        seen_ids.add(question_id)

        question = question_by_id.get(question_id)
        if not question:
            errors.append(f"题目 {question_id} 已不存在")
            continue

        stem_key = _normalize_stem(question.get("stem"))
        if stem_key and stem_key in seen_stems:
            errors.append(f"题目 {question_id} 与卷内其他题目题干重复")
        if stem_key:
            seen_stems.add(stem_key)

        section_error = _question_section_error(question, exam_code, section_key)
        if section_error:
            errors.append(section_error)

        section_counts[section_key] += 1
        difficulty_counts[_difficulty_band(question)] += 1
        total_score += int(rules[section_key]["point_value"])

    for section_key, rule in rules.items():
        selected_count = section_counts[section_key]
        if selected_count > int(rule["count"]):
            errors.append(f"{rule['label']}超过 {rule['count']} 题")
        if require_complete and selected_count != int(rule["count"]):
            errors.append(f"{rule['label']}需要 {rule['count']} 题，当前 {selected_count} 题")

    if require_complete:
        if len(seen_ids) != MOCK_EXAM_TOTAL_COUNT:
            errors.append(f"整卷需要 {MOCK_EXAM_TOTAL_COUNT} 道不重复题目，当前 {len(seen_ids)} 道")
        if total_score != MOCK_EXAM_TOTAL_SCORE:
            errors.append(f"整卷需要 {MOCK_EXAM_TOTAL_SCORE} 分，当前 {total_score} 分")
        for key, target in MOCK_EXAM_DIFFICULTY_TARGETS.items():
            actual = difficulty_counts[key]
            if actual != int(target["count"]):
                errors.append(f"{target['label']}难度需要 {target['count']} 题，当前 {actual} 题")

    deduplicated_errors = list(dict.fromkeys(errors))
    return MockExamValidationResult(
        valid=not deduplicated_errors and (not require_complete or len(seen_ids) == MOCK_EXAM_TOTAL_COUNT),
        errors=deduplicated_errors,
        question_count=len(seen_ids),
        total_score=total_score,
        sections=[
            MockExamSectionValidation(
                key=section_key,
                label=rule["label"],
                selected_count=section_counts[section_key],
                required_count=rule["count"],
                point_value=rule["point_value"],
                selected_score=section_counts[section_key] * rule["point_value"],
                required_score=rule["count"] * rule["point_value"],
            )
            for section_key, rule in rules.items()
        ],
        difficulty=[
            MockExamDifficultyValidation(
                key=key,
                label=target["label"],
                selected_count=difficulty_counts[key],
                required_count=target["count"],
            )
            for key, target in MOCK_EXAM_DIFFICULTY_TARGETS.items()
        ],
    )


def _admin_detail(supabase, paper: dict) -> AdminMockExamPaperDetailResponse:
    item_rows = _list_paper_item_rows(supabase, str(paper.get("id") or ""))
    question_by_id = _fetch_questions_by_ids(
        supabase,
        [str(item.get("question_id") or "") for item in item_rows],
    )
    items: list[dict] = []
    for item in item_rows:
        question_id = str(item.get("question_id") or "")
        question = question_by_id.get(question_id)
        if not question:
            continue
        items.append({
            **question,
            "question_id": question_id,
            "section_key": item.get("section_key"),
            "position": int(item.get("position") or 0),
            "point_value": int(item.get("point_value") or 0),
        })
    validation = validate_mock_exam_selection(
        str(paper.get("exam_code") or "Z001"),
        item_rows,
        question_by_id,
        require_complete=True,
    )
    return AdminMockExamPaperDetailResponse(
        paper=_paper_summary(paper),
        items=items,
        validation=validation,
    )


@router.get("", response_model=MockExamPaperListResponse)
def list_published_mock_exam_papers(
    exam_code: str = Query(pattern="^(Z001|Z002)$"),
) -> MockExamPaperListResponse:
    response = (
        get_supabase_admin().table("mock_exam_papers")
        .select("*")
        .eq("status", "published")
        .eq("exam_code", exam_code)
        .order("sort_order")
        .order("published_at", desc=True)
        .limit(100)
        .execute()
    )
    return MockExamPaperListResponse(items=[_paper_summary(row) for row in (response.data or [])])


@router.get("/{paper_id}", response_model=MockExamPaperDetailResponse)
def get_published_mock_exam_paper(
    paper_id: str,
    _: str = Depends(get_current_user_id),
) -> MockExamPaperDetailResponse:
    supabase = get_supabase_admin()
    paper = _get_paper_or_404(supabase, paper_id, published_only=True)
    item_rows = _list_paper_item_rows(supabase, paper_id)
    question_by_id = _fetch_questions_by_ids(
        supabase,
        [str(item.get("question_id") or "") for item in item_rows],
    )
    ordered_questions = [
        question_by_id[str(item.get("question_id"))]
        for item in item_rows
        if str(item.get("question_id")) in question_by_id
    ]
    warm_submission_questions(ordered_questions)
    rules = _section_rules(str(paper.get("exam_code") or "Z001"))
    questions: list[MockExamPaperQuestion] = []
    for item in item_rows:
        question = question_by_id.get(str(item.get("question_id") or ""))
        if not question:
            continue
        section_key = str(item.get("section_key") or "third")
        questions.append(MockExamPaperQuestion(
            **{
                **question,
                "answer": None,
                "explanation": None,
                "mock_section_key": section_key,
                "mock_section": rules[section_key]["label"],
                "point_value": int(item.get("point_value") or rules[section_key]["point_value"]),
                "position": int(item.get("position") or len(questions) + 1),
            }
        ))
    return MockExamPaperDetailResponse(paper=_paper_summary(paper), questions=questions)


@admin_router.get("/question-options", response_model=AdminMockExamQuestionListResponse)
def list_mock_exam_question_options(
    exam_code: str = Query(pattern="^(Z001|Z002)$"),
    section_key: str = Query(pattern="^(culture|english|third)$"),
    publication: str = Query(default="all", pattern="^(all|published|unpublished)$"),
    search: str | None = Query(default=None, max_length=80),
    difficulty: int | None = Query(default=None, ge=1, le=5),
    module: str | None = Query(default=None, max_length=80),
    submodule: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=40, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_question_admin_user),
) -> AdminMockExamQuestionListResponse:
    rule = _section_rules(exam_code)[section_key]
    try:
        normalized_module, normalized_submodule = _normalize_question_option_classification(
            exam_code,
            section_key,
            module,
            submodule,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    supabase = get_supabase_admin()
    query = exclude_ai_generated_questions(
        supabase.table("questions").select("*", count="exact").order("created_at", desc=True)
    )
    query = query.eq("subject", rule["subject"])
    compatible_codes = sorted(_compatible_exam_codes(exam_code, section_key))
    query = query.in_("exam_code", compatible_codes)
    if section_key == "english":
        query = query.eq("module", "语言知识")
    if normalized_module:
        query = query.eq("module", normalized_module)
    if normalized_submodule:
        query = query.eq("submodule", normalized_submodule)
    if publication == "published":
        query = query.eq("status", "active")
    elif publication == "unpublished":
        query = query.neq("status", "active")
    if difficulty is not None:
        query = query.eq("difficulty", difficulty)
    if search and search.strip():
        query = query.ilike("stem", f"%{search.strip()}%")
    response = query.range(offset, offset + limit - 1).execute()
    items = [
        row
        for row in (response.data or [])
        if _question_section_error(row, exam_code, section_key) is None
    ]
    return AdminMockExamQuestionListResponse(items=items, count=int(response.count or len(items)))


@admin_router.get("", response_model=MockExamPaperListResponse)
def list_admin_mock_exam_papers(
    paper_status: str = Query(default="all", alias="status", pattern="^(all|draft|published|archived)$"),
    _: dict = Depends(require_question_admin_user),
) -> MockExamPaperListResponse:
    query = get_supabase_admin().table("mock_exam_papers").select("*")
    if paper_status != "all":
        query = query.eq("status", paper_status)
    response = query.order("updated_at", desc=True).limit(500).execute()
    return MockExamPaperListResponse(items=[_paper_summary(row) for row in (response.data or [])])


@admin_router.post("", response_model=AdminMockExamPaperDetailResponse, status_code=status.HTTP_201_CREATED)
def create_admin_mock_exam_paper(
    payload: AdminMockExamPaperCreateRequest,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMockExamPaperDetailResponse:
    supabase = get_supabase_admin()
    response = supabase.table("mock_exam_papers").insert({
        "title": payload.title.strip(),
        "exam_code": payload.exam_code,
        "description": payload.description.strip(),
        "duration_minutes": payload.duration_minutes,
        "sort_order": payload.sort_order,
        "status": "draft",
        "created_by": admin_profile.get("id"),
    }).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="模拟卷创建失败")
    return _admin_detail(supabase, response.data[0])


@admin_router.get("/{paper_id}", response_model=AdminMockExamPaperDetailResponse)
def get_admin_mock_exam_paper(
    paper_id: str,
    _: dict = Depends(require_question_admin_user),
) -> AdminMockExamPaperDetailResponse:
    supabase = get_supabase_admin()
    return _admin_detail(supabase, _get_paper_or_404(supabase, paper_id))


@admin_router.patch("/{paper_id}", response_model=AdminMockExamPaperDetailResponse)
def update_admin_mock_exam_paper(
    paper_id: str,
    payload: AdminMockExamPaperUpdateRequest,
    _: dict = Depends(require_question_admin_user),
) -> AdminMockExamPaperDetailResponse:
    supabase = get_supabase_admin()
    existing = _get_paper_or_404(supabase, paper_id)
    existing_items = _list_paper_item_rows(supabase, paper_id)
    next_exam_code = str(payload.exam_code or existing.get("exam_code") or "Z001")

    if payload.items is None:
        next_items = existing_items
    else:
        raw_items = [item.model_dump() for item in payload.items]
        next_items = [
            item
            for section_key in MOCK_EXAM_SECTION_ORDER
            for item in raw_items
            if item["section_key"] == section_key
        ]

    question_by_id = _fetch_questions_by_ids(
        supabase,
        [str(item.get("question_id") or "") for item in next_items],
    )
    validation = validate_mock_exam_selection(
        next_exam_code,
        next_items,
        question_by_id,
        require_complete=False,
    )
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="；".join(validation.errors[:6]),
        )

    if payload.items is not None:
        rules = _section_rules(next_exam_code)
        insert_rows = [
            {
                "question_id": str(item["question_id"]),
                "section_key": str(item["section_key"]),
                "position": index + 1,
                "point_value": int(rules[str(item["section_key"])]["point_value"]),
            }
            for index, item in enumerate(next_items)
        ]
        supabase.rpc(
            "replace_mock_exam_paper_items",
            {"p_paper_id": paper_id, "p_items": insert_rows},
        ).execute()

    update_data = payload.model_dump(exclude_unset=True, exclude={"items"})
    if "title" in update_data:
        update_data["title"] = str(update_data["title"]).strip()
    if "description" in update_data:
        update_data["description"] = str(update_data["description"] or "").strip()
    update_data.update({
        "question_count": validation.question_count,
        "total_score": validation.total_score,
    })
    if existing.get("status") in {"published", "archived"} and payload.model_fields_set:
        update_data.update({
            "status": "draft",
            "version": int(existing.get("version") or 1) + 1,
            "published_at": None,
            "published_by": None,
        })
    response = supabase.table("mock_exam_papers").update(update_data).eq("id", paper_id).execute()
    paper = response.data[0] if response.data else _get_paper_or_404(supabase, paper_id)
    return _admin_detail(supabase, paper)


@admin_router.post("/{paper_id}/publish", response_model=AdminMockExamPaperDetailResponse)
def publish_admin_mock_exam_paper(
    paper_id: str,
    admin_profile: dict = Depends(require_question_admin_user),
) -> AdminMockExamPaperDetailResponse:
    supabase = get_supabase_admin()
    paper = _get_paper_or_404(supabase, paper_id)
    item_rows = _list_paper_item_rows(supabase, paper_id)
    question_by_id = _fetch_questions_by_ids(
        supabase,
        [str(item.get("question_id") or "") for item in item_rows],
    )
    validation = validate_mock_exam_selection(
        str(paper.get("exam_code") or "Z001"),
        item_rows,
        question_by_id,
        require_complete=True,
    )
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="；".join(validation.errors[:8]),
        )
    response = (
        supabase.table("mock_exam_papers")
        .update({
            "status": "published",
            "version": _next_publish_version(paper),
            "question_count": MOCK_EXAM_TOTAL_COUNT,
            "total_score": MOCK_EXAM_TOTAL_SCORE,
            "published_by": admin_profile.get("id"),
            "published_at": _now_iso(),
        })
        .eq("id", paper_id)
        .execute()
    )
    updated = response.data[0] if response.data else _get_paper_or_404(supabase, paper_id)
    return _admin_detail(supabase, updated)


@admin_router.post("/{paper_id}/archive", response_model=AdminMockExamPaperDetailResponse)
def archive_admin_mock_exam_paper(
    paper_id: str,
    _: dict = Depends(require_question_admin_user),
) -> AdminMockExamPaperDetailResponse:
    supabase = get_supabase_admin()
    _get_paper_or_404(supabase, paper_id)
    response = (
        supabase.table("mock_exam_papers")
        .update({"status": "archived", "published_at": None, "published_by": None})
        .eq("id", paper_id)
        .execute()
    )
    updated = response.data[0] if response.data else _get_paper_or_404(supabase, paper_id)
    return _admin_detail(supabase, updated)
