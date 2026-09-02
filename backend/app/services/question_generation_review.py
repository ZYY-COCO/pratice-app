"""Blind second-pass review for online generated non-logic questions."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping

from fastapi import HTTPException, status

from app.services.ai_client import call_deepseek_chat
from app.services.subject_question_quality import (
    CULTURE_SUBJECT,
    ENGLISH_SUBJECT,
    MATH_SUBJECT,
    V2_SUBJECTS,
)


REVIEW_CHUNK_SIZE = 10


def _text(value: object, max_length: int = 2000) -> str:
    return str(value or "").strip()[:max_length]


def _extract_json_object(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("review response does not contain a JSON object")
    payload = json.loads(text[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("review response root must be an object")
    return payload


def _subject_review_rules(subject: str) -> str:
    if subject == CULTURE_SUBJECT:
        return (
            "逐题独立核对人物、时代、作品、制度、典籍、概念或器物的对应事实。"
            "先检查题干所问的语义类型是否与 A-D 一致：题干若问主张，四项都应是主张；"
            "不能把传入时间、历史作用、组织名称和思想特征混成同一组选项。"
            "遇到冷僻、争议、时代错置、人物作品错配、设问正反方向不清或干扰项不同域时拒收。"
        )
    if subject == ENGLISH_SUBJECT:
        return (
            "不要看任何预设答案，逐个把 A-D 填回空格，核对词义、词性、固定搭配、时态语态、"
            "非谓语、从句、语域和上下文自然度。两个选项都能成立或四项都不自然时拒收。"
        )
    if subject == MATH_SUBJECT:
        return (
            "不要猜答案，独立重新计算；检查定义域、条件、符号、系数、上下限、链式法则和选项唯一性。"
            "超出 Z002 三个允许微积分模块、需要证明、计算过繁或题面信息不足时拒收。"
        )
    return "逐题独立求解并检查唯一答案。"


def build_quality_review_messages(rows: list[dict], subject: str) -> list[dict[str, str]]:
    candidates = []
    for index, row in enumerate(rows, start=1):
        candidates.append(
            {
                "index": index,
                "stem": _text(row.get("stem")),
                "option_a": _text(row.get("option_a"), 800),
                "option_b": _text(row.get("option_b"), 800),
                "option_c": _text(row.get("option_c"), 800),
                "option_d": _text(row.get("option_d"), 800),
            }
        )

    return [
        {
            "role": "system",
            "content": (
                "你是港澳台考研题目的独立复核老师。候选数据故意不提供模型声明的答案和解析，"
                "你必须先独立作答，再判断题目是否只有一个最佳答案。宁可拒收存疑题，也不要替题目圆场。"
                "只输出合法 JSON，不要输出 Markdown、代码块或前后说明。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"科目：{subject}\n"
                f"专项复核规则：{_subject_review_rules(subject)}\n"
                "对每个 index 都必须返回一条 review。accept 只有在题面完整、范围正确、事实或计算成立、"
                "且恰好一个选项正确时才为 true；independent_answer 填你独立求得的 A/B/C/D。"
                "有任何问题时 accept=false，issues 用简体中文写具体原因。\n"
                "固定输出结构："
                '{"reviews":[{"index":1,"accept":true,"independent_answer":"A","issues":[]}]}\n'
                f"候选题：{json.dumps(candidates, ensure_ascii=False, separators=(',', ':'))}"
            ),
        },
    ]


def build_culture_explanation_review_messages(rows: list[dict]) -> list[dict[str, str]]:
    """Build the second review after the answer has passed blind checking."""

    candidates = []
    for index, row in enumerate(rows, start=1):
        candidates.append(
            {
                "index": index,
                "stem": _text(row.get("stem")),
                "option_a": _text(row.get("option_a"), 800),
                "option_b": _text(row.get("option_b"), 800),
                "option_c": _text(row.get("option_c"), 800),
                "option_d": _text(row.get("option_d"), 800),
                "answer": _text(row.get("answer"), 8),
                "explanation": _text(row.get("explanation"), 1800),
                "culture_v3": row.get("_culture_v3_review")
                if isinstance(row.get("_culture_v3_review"), Mapping)
                else None,
            }
        )

    return [
        {
            "role": "system",
            "content": (
                "你是中华文化刷题解析的独立教学质检老师。候选题答案已经完成不看解析的独立核对；"
                "本轮只检查解析能否让学生理解为什么，并核对解析中的每条文化事实。"
                "只输出合法 JSON，不要输出 Markdown、代码块或前后说明。"
            ),
        },
        {
            "role": "user",
            "content": (
                "逐题检查以下标准：\n"
                "1. 解题思路必须包含题干线索、中间文化事实、答案结论；中间事实要直接点名题干对象并补出关系依据，不能只是‘典型特征是’‘创作时期是’‘X对应Y’等答案换写。\n"
                "2. 检查桥接事实是否完整、可核对：不得以‘他’‘该书’‘这句诗’无指代开头，不得粘连两条资料、保留问句或截断句，也不得用宣传性绝对表述代替稳定事实。\n"
                "3. 同时检查 culture_v3 原始字段：fact_anchor.object 必须等于正确选项原文；evidence_excerpt 必须真正支持 bridge，不能只复述答案或用无关同主题事实；difficulty_features 必须是本题真实难点。不要把 verification_status=cross_checked 当成事实正确证明。\n"
                "4. 逆向题必须在 clue 中保留设问方向；evidence_excerpt 要明确写出纠正后的对象和不属于/不在/并非/不同等边界，不能把错误选项原句或双重否定当证据。\n"
                "5. 选项解析必须覆盖 A-D；每项 fact 要明确包含本选项对象及其真实知识，不能拿无关轶事充数；fit 要说明具体错配维度，不能三个错项重复同一句模板。\n"
                "6. 知识点必须继续围绕题干对象或正确知识扩展独立事实，不能重复解题思路、复制错项 fact 或写通用做题步骤。\n"
                "7. 记忆方法允许省略；如果出现，必须是完整、有用的关键词、对比组或知识链。\n"
                "8. 逐条核对人物、作品、时代、地点、引语和最高级表述；引语须区分原文与后人概括。解析应短而完整，不堆百科背景，不含机械模板、事实错误或模块重复。\n"
                "全部满足且文化事实准确时 accept=true；否则 accept=false，并在 issues 中逐条写明具体缺陷。\n"
                "固定输出结构："
                '{"reviews":[{"index":1,"accept":true,"issues":[]}]}\n'
                f"候选解析：{json.dumps(candidates, ensure_ascii=False, separators=(',', ':'))}"
            ),
        },
    ]


def _strict_review_map(
    raw_reviews: object,
    row_count: int,
    *,
    label: str,
) -> dict[int, Mapping[str, object]]:
    if not isinstance(raw_reviews, list):
        raise ValueError(f"{label} response is missing reviews array")

    review_map: dict[int, Mapping[str, object]] = {}
    for position, item in enumerate(raw_reviews, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"{label} review {position} must be an object")
        raw_index = item.get("index")
        if isinstance(raw_index, int) and not isinstance(raw_index, bool):
            index = raw_index
        elif isinstance(raw_index, str) and re.fullmatch(r"[0-9]+", raw_index.strip()):
            index = int(raw_index.strip())
        else:
            raise ValueError(f"{label} review {position} has an invalid index")
        if not 1 <= index <= row_count:
            raise ValueError(f"{label} review index {index} is out of range")
        if index in review_map:
            raise ValueError(f"{label} review index {index} is duplicated")
        review_map[index] = item

    missing = sorted(set(range(1, row_count + 1)) - set(review_map))
    if missing:
        raise ValueError(f"{label} response is missing review indexes: {missing}")
    return review_map


def parse_quality_reviews(content: str, rows: list[dict]) -> tuple[list[dict], list[str], dict]:
    payload = _extract_json_object(content)
    review_map = _strict_review_map(payload.get("reviews"), len(rows), label="answer review")

    accepted: list[dict] = []
    feedback: list[str] = []
    for index, row in enumerate(rows, start=1):
        review = review_map.get(index)
        preview = _text(row.get("stem"), 36)
        if not review:
            feedback.append(f"二次复核缺少第 {index} 题结果：{preview}")
            continue

        declared_answer = _text(row.get("answer"), 8).upper()
        independent_answer = _text(review.get("independent_answer"), 8).upper()
        issues = review.get("issues")
        issue_texts = [_text(item, 180) for item in issues] if isinstance(issues, list) else ["复核未返回 issues 数组"]
        issue_texts = [item for item in issue_texts if item]
        accept = review.get("accept") is True

        if accept and independent_answer == declared_answer and not issue_texts:
            accepted.append(row)
            continue

        reasons = list(issue_texts)
        if independent_answer not in {"A", "B", "C", "D"}:
            reasons.append("复核老师未给出有效的唯一答案")
        elif independent_answer != declared_answer:
            reasons.append(f"独立复核答案为 {independent_answer}，与生成答案 {declared_answer} 不一致")
        if not accept and not reasons:
            reasons.append("独立复核拒收但未说明原因")
        feedback.append(f"二次复核拒收第 {index} 题（{preview}）：{'；'.join(reasons)}")

    return accepted, feedback[:30], payload


def parse_culture_explanation_reviews(content: str, rows: list[dict]) -> tuple[list[dict], list[str], dict]:
    payload = _extract_json_object(content)
    review_map = _strict_review_map(
        payload.get("reviews"),
        len(rows),
        label="explanation review",
    )

    accepted: list[dict] = []
    feedback: list[str] = []
    for index, row in enumerate(rows, start=1):
        review = review_map.get(index)
        preview = _text(row.get("stem"), 36)
        if not review:
            feedback.append(f"解析复核缺少第 {index} 题结果：{preview}")
            continue
        issues = review.get("issues")
        issue_texts = [_text(item, 180) for item in issues] if isinstance(issues, list) else ["解析复核未返回 issues 数组"]
        issue_texts = [item for item in issue_texts if item]
        if review.get("accept") is True and not issue_texts:
            accepted.append(row)
            continue
        if not issue_texts:
            issue_texts.append("解析教学质量复核未通过")
        feedback.append(f"解析复核拒收第 {index} 题（{preview}）：{'；'.join(issue_texts)}")

    return accepted, feedback[:30], payload


async def review_culture_explanation_rows(rows: list[dict]) -> tuple[list[dict], list[str], dict]:
    if not rows:
        return [], [], {"skipped": True, "reason": "no_blind_review_passes"}
    result = await call_deepseek_chat(
        build_culture_explanation_review_messages(rows),
        temperature=0.0,
        max_tokens=max(1000, min(3200, len(rows) * 240)),
        timeout_seconds=60,
    )
    try:
        accepted, feedback, parsed = parse_culture_explanation_reviews(result["reply"], rows)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI 解析质量复核返回格式异常，已停止写入题目",
        ) from exc
    return accepted, feedback, {"model": result.get("model"), "review": parsed}


async def review_generated_question_rows(rows: list[dict], subject: str) -> tuple[list[dict], list[str], dict]:
    if not rows or subject not in V2_SUBJECTS:
        return rows, [], {"skipped": True, "reason": "no_rows_or_non_v2_subject"}

    accepted: list[dict] = []
    feedback: list[str] = []
    review_payloads: list[dict] = []
    for start in range(0, len(rows), REVIEW_CHUNK_SIZE):
        chunk = rows[start : start + REVIEW_CHUNK_SIZE]
        result = await call_deepseek_chat(
            build_quality_review_messages(chunk, subject),
            temperature=0.0,
            max_tokens=max(1200, min(3600, len(chunk) * 260)),
            timeout_seconds=60,
        )
        try:
            chunk_accepted, chunk_feedback, parsed = parse_quality_reviews(result["reply"], chunk)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI 二次复核返回格式异常，已停止写入题目",
            ) from exc
        explanation_review = {"skipped": True, "reason": "subject_not_culture"}
        if subject == CULTURE_SUBJECT:
            chunk_accepted, explanation_feedback, explanation_review = await review_culture_explanation_rows(chunk_accepted)
            chunk_feedback.extend(explanation_feedback)
        accepted.extend(chunk_accepted)
        feedback.extend(chunk_feedback)
        review_payloads.append(
            {
                "answer_review": {
                    "model": result.get("model"),
                    "review": parsed,
                },
                "explanation_review": explanation_review,
            }
        )

    return accepted, feedback[:40], {"chunks": review_payloads}
