from __future__ import annotations

import html
import re
from dataclasses import dataclass

from fastapi import APIRouter, Query
from fastapi.responses import Response

router = APIRouter(prefix="/formula", tags=["formula"])


SUPERSCRIPT_MAP = str.maketrans(
    {
        "0": "\u2070",
        "1": "\u00b9",
        "2": "\u00b2",
        "3": "\u00b3",
        "4": "\u2074",
        "5": "\u2075",
        "6": "\u2076",
        "7": "\u2077",
        "8": "\u2078",
        "9": "\u2079",
        "+": "\u207a",
        "-": "\u207b",
        "n": "\u207f",
        "x": "\u02e3",
        "y": "\u02b8",
    }
)

SUBSCRIPT_MAP = str.maketrans(
    {
        "0": "\u2080",
        "1": "\u2081",
        "2": "\u2082",
        "3": "\u2083",
        "4": "\u2084",
        "5": "\u2085",
        "6": "\u2086",
        "7": "\u2087",
        "8": "\u2088",
        "9": "\u2089",
        "+": "\u208a",
        "-": "\u208b",
        "x": "\u2093",
    }
)


@dataclass
class Token:
    kind: str
    text: str = ""
    numerator: str = ""
    denominator: str = ""
    condition: str = ""
    radicand: str = ""
    lower: str = ""
    upper: str = ""
    rows: list[tuple[str, str]] | None = None


def _strip_math_delimiters(value: str) -> str:
    text = re.sub(r"\\\((.*?)\\\)", r"\1", value)
    text = re.sub(r"\\\[(.*?)\\\]", r"\1", text)
    text = re.sub(r"\$(.*?)\$", r"\1", text)
    return text


def _parse_brace_group(value: str, start: int) -> tuple[str, int] | None:
    cursor = start
    while cursor < len(value) and value[cursor].isspace():
        cursor += 1
    if cursor >= len(value) or value[cursor] != "{":
        return None

    depth = 0
    for index in range(cursor, len(value)):
        char = value[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return value[cursor + 1 : index], index + 1
    return None


def _parse_bracket_group(value: str, start: int) -> tuple[str, int] | None:
    cursor = start
    while cursor < len(value) and value[cursor].isspace():
        cursor += 1
    if cursor >= len(value) or value[cursor] != "[":
        return None

    depth = 0
    for index in range(cursor, len(value)):
        char = value[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return value[cursor + 1 : index], index + 1
    return None


def _parse_script(value: str, start: int) -> tuple[str, str, int] | None:
    cursor = start
    while cursor < len(value) and value[cursor].isspace():
        cursor += 1
    if cursor >= len(value) or value[cursor] not in {"_", "^"}:
        return None

    marker = value[cursor]
    cursor += 1
    while cursor < len(value) and value[cursor].isspace():
        cursor += 1

    group = _parse_brace_group(value, cursor)
    if group:
        return marker, group[0], group[1]

    if cursor < len(value):
        return marker, value[cursor], cursor + 1
    return None


def _parse_scripts(value: str, start: int) -> tuple[str, str, int]:
    cursor = start
    lower = ""
    upper = ""
    for _ in range(2):
        script = _parse_script(value, cursor)
        if not script:
            break
        marker, content, cursor = script
        if marker == "_":
            lower = content
        else:
            upper = content
    return lower, upper, cursor


def _normalize_plain(value: str) -> str:
    text = _strip_math_delimiters(str(value or ""))
    text = re.sub(r"\\(?:displaystyle|textstyle|scriptstyle|scriptscriptstyle)\s*", "", text)
    text = re.sub(r"\\(?:limits|nolimits)", "", text)
    text = re.sub(r"\\[dt]frac", r"\\frac", text)
    text = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", text)
    text = text.replace("\\left.", "").replace("\\left", "").replace("\\right", "")
    replacements = [
        (r"\\to", "\u2192"),
        (r"->", "\u2192"),
        (r"\\infty", "\u221e"),
        (r"\\pi", "\u03c0"),
        (r"\\cdot", "\u00b7"),
        (r"\\times", "\u00d7"),
        (r"\\leq?", "\u2264"),
        (r"\\geq?", "\u2265"),
        (r"\\neq", "\u2260"),
        (r"\\ne(?![A-Za-z])", "\u2260"),
        (r"\\partial", "\u2202"),
        (r"\\int", "\u222b"),
        (r"\\,", " "),
        (r"\\;", " "),
        (r"\\!", ""),
        (r"\\\\", "; "),
        (r"&", ", "),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    text = re.sub(
        r"\\(arcsin|arccos|arctan|sin|cos|tan|ln|log|sec|max|min)\b",
        r"\1",
        text,
    )
    text = re.sub(r"\^\{([-+0-9nxy]+)\}", lambda match: match.group(1).translate(SUPERSCRIPT_MAP), text)
    text = re.sub(r"\^([-+0-9nxy])", lambda match: match.group(1).translate(SUPERSCRIPT_MAP), text)
    text = re.sub(r"_\{([-+0-9x]+)\}", lambda match: match.group(1).translate(SUBSCRIPT_MAP), text)
    text = re.sub(r"_([-+0-9x])", lambda match: match.group(1).translate(SUBSCRIPT_MAP), text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:?!\u3002\uff0c\uff1b\uff1a\uff1f\uff01])", r"\1", text)
    return text.strip()


def _clean_group_text(value: str) -> str:
    text = _normalize_plain(value)
    if (text.startswith("(") and text.endswith(")")) or (text.startswith("[") and text.endswith("]")):
        return text[1:-1].strip()
    return text


def _parse_cases_rows(value: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for row in re.split(r"\\\\", value):
        row = row.strip()
        if not row:
            continue
        cells = row.split("&")
        expression = _clean_group_text(cells[0])
        condition = _clean_group_text(" ".join(cells[1:])) if len(cells) > 1 else ""
        rows.append((expression, condition))
    return rows or [(_normalize_plain(value), "")]


def _split_plain_tokens(value: str) -> list[Token]:
    text = _normalize_plain(value)
    if not text:
        return []

    result: list[Token] = []
    pattern = re.compile(
        r"(\([^)]+\)|[A-Za-z0-9\u2070-\u209f\u00b9\u00b2\u00b3\u02e3\u02b8+\-]+)"
        r"\s*/\s*"
        r"(\([^)]+\)|[A-Za-z0-9\u2070-\u209f\u00b9\u00b2\u00b3\u02e3\u02b8+\-]+)"
    )
    cursor = 0
    for match in pattern.finditer(text):
        if match.start() > cursor:
            result.extend(_chars_to_tokens(text[cursor : match.start()]))
        result.append(
            Token(
                kind="fraction",
                numerator=match.group(1).strip("()"),
                denominator=match.group(2).strip("()"),
            )
        )
        cursor = match.end()
    if cursor < len(text):
        result.extend(_chars_to_tokens(text[cursor:]))
    return result


def _chars_to_tokens(value: str) -> list[Token]:
    tokens: list[Token] = []
    for char in value:
        tokens.append(Token(kind="space" if char.isspace() else "text", text=char))
    return tokens


def _tokenize(value: str) -> list[Token]:
    raw = _strip_math_delimiters(str(value or ""))[:700]
    raw = re.sub(r"\\(?:displaystyle|textstyle|scriptstyle|scriptscriptstyle)\s*", "", raw)
    raw = re.sub(r"\\(?:limits|nolimits)", "", raw)
    raw = re.sub(r"\\[dt]frac", r"\\frac", raw)
    tokens: list[Token] = []
    cursor = 0
    index = 0

    def push_text(end: int) -> None:
        nonlocal cursor
        if end > cursor:
            tokens.extend(_split_plain_tokens(raw[cursor:end]))
        cursor = end

    while index < len(raw):
        if raw.startswith(r"\begin{cases}", index):
            content_start = index + len(r"\begin{cases}")
            content_end = raw.find(r"\end{cases}", content_start)
            if content_end >= 0:
                push_text(index)
                tokens.append(Token(kind="cases", rows=_parse_cases_rows(raw[content_start:content_end])))
                index = content_end + len(r"\end{cases}")
                cursor = index
                continue

        if raw.startswith(r"\frac", index):
            numerator = _parse_brace_group(raw, index + 5)
            denominator = _parse_brace_group(raw, numerator[1]) if numerator else None
            if numerator and denominator:
                push_text(index)
                tokens.append(
                    Token(
                        kind="fraction",
                        numerator=_clean_group_text(numerator[0]),
                        denominator=_clean_group_text(denominator[0]),
                    )
                )
                index = denominator[1]
                cursor = index
                continue

        if raw.startswith(r"\sqrt", index):
            group_start = index + 5
            optional_root = _parse_bracket_group(raw, group_start)
            if optional_root:
                group_start = optional_root[1]
            radicand = _parse_brace_group(raw, group_start)
            if radicand:
                push_text(index)
                tokens.append(Token(kind="sqrt", radicand=_clean_group_text(radicand[0])))
                index = radicand[1]
                cursor = index
                continue

        if raw.startswith(r"\lim", index):
            lower, _upper, end = _parse_scripts(raw, index + 4)
            if lower:
                push_text(index)
                tokens.append(Token(kind="limit", condition=_clean_group_text(lower)))
                index = end
                cursor = index
                continue

        if raw.startswith("lim(", index):
            close_index = raw.find(")", index + 4)
            if close_index > index:
                push_text(index)
                tokens.append(Token(kind="limit", condition=_clean_group_text(raw[index + 4 : close_index])))
                index = close_index + 1
                cursor = index
                continue

        if raw.startswith(r"\int", index):
            lower, upper, end = _parse_scripts(raw, index + 4)
            push_text(index)
            tokens.append(Token(kind="integral", lower=_clean_group_text(lower), upper=_clean_group_text(upper)))
            index = end
            cursor = index
            continue

        index += 1

    push_text(len(raw))
    return tokens or [Token(kind="text", text=" ")]


def _text_width(value: str, size: int) -> float:
    total = 0.0
    for char in value:
        if "\u3400" <= char <= "\u9fff":
            total += size * 0.96
        elif char in ".,;:!?":
            total += size * 0.34
        elif char in "()[]{}":
            total += size * 0.36
        else:
            total += size * 0.56
    return max(total, size * 0.25)


def _token_width(token: Token, size: int) -> float:
    if token.kind == "space":
        return size * 0.32
    if token.kind == "fraction":
        small = int(size * 0.76)
        return max(_text_width(token.numerator, small), _text_width(token.denominator, small)) + size * 0.45
    if token.kind == "limit":
        return max(_text_width("lim", size), _text_width(token.condition, int(size * 0.52))) + size * 0.28
    if token.kind == "sqrt":
        return size * 0.78 + _text_width(token.radicand, int(size * 0.84)) + size * 0.2
    if token.kind == "integral":
        return size * 0.95 + max(_text_width(token.lower, int(size * 0.5)), _text_width(token.upper, int(size * 0.5))) + size * 0.2
    if token.kind == "cases":
        rows = token.rows or []
        widest = max((_text_width(left + ("  " + right if right else ""), int(size * 0.74)) for left, right in rows), default=size)
        return size * 0.8 + widest
    return _text_width(token.text, size)


def _token_height(token: Token, size: int) -> float:
    if token.kind == "cases":
        return max(size * 1.45, len(token.rows or []) * size * 0.9)
    if token.kind in {"fraction", "limit", "integral"}:
        return size * 1.55
    return size * 1.18


def _layout(tokens: list[Token], width: int, size: int) -> list[list[Token]]:
    max_width = max(width - 28, 80)
    lines: list[list[Token]] = [[]]
    current_width = 0.0
    for token in tokens:
        token_width = _token_width(token, size)
        if token.kind == "space" and not lines[-1]:
            continue
        if lines[-1] and current_width + token_width > max_width:
            lines.append([])
            current_width = 0.0
            if token.kind == "space":
                continue
        lines[-1].append(token)
        current_width += token_width
    return [line for line in lines if line] or [[Token(kind="text", text=" ")]]


def _render_token(token: Token, x: float, baseline: float, size: int) -> list[str]:
    elements: list[str] = []
    token_width = _token_width(token, size)
    if token.kind == "fraction":
        small = int(size * 0.74)
        center = x + token_width / 2
        line_y = baseline - size * 0.08
        elements.append(
            f'<text x="{center:.1f}" y="{baseline - size * 0.43:.1f}" text-anchor="middle" font-size="{small}">{html.escape(token.numerator)}</text>'
        )
        elements.append(
            f'<line x1="{x + 2:.1f}" y1="{line_y:.1f}" x2="{x + token_width - 2:.1f}" y2="{line_y:.1f}" stroke="#172033" stroke-width="1.8" />'
        )
        elements.append(
            f'<text x="{center:.1f}" y="{baseline + size * 0.52:.1f}" text-anchor="middle" font-size="{small}">{html.escape(token.denominator)}</text>'
        )
    elif token.kind == "limit":
        center = x + token_width / 2
        elements.append(
            f'<text x="{center:.1f}" y="{baseline - size * 0.12:.1f}" text-anchor="middle" font-size="{size}">lim</text>'
        )
        elements.append(
            f'<text x="{center:.1f}" y="{baseline + size * 0.45:.1f}" text-anchor="middle" font-size="{int(size * 0.52)}">{html.escape(token.condition)}</text>'
        )
    elif token.kind == "sqrt":
        small = int(size * 0.84)
        root_x = x + size * 0.5
        top_y = baseline - size * 0.75
        radicand_x = x + size * 0.78
        radicand_width = _text_width(token.radicand, small) + size * 0.1
        elements.append(f'<text x="{x:.1f}" y="{baseline:.1f}" font-size="{int(size * 1.12)}">\u221a</text>')
        elements.append(
            f'<line x1="{root_x:.1f}" y1="{top_y:.1f}" x2="{radicand_x + radicand_width:.1f}" y2="{top_y:.1f}" stroke="#172033" stroke-width="1.6" />'
        )
        elements.append(f'<text x="{radicand_x:.1f}" y="{baseline:.1f}" font-size="{small}">{html.escape(token.radicand)}</text>')
    elif token.kind == "integral":
        elements.append(f'<text x="{x:.1f}" y="{baseline:.1f}" font-size="{int(size * 1.25)}">\u222b</text>')
        limit_x = x + size * 0.56
        if token.upper:
            elements.append(f'<text x="{limit_x:.1f}" y="{baseline - size * 0.56:.1f}" font-size="{int(size * 0.5)}">{html.escape(token.upper)}</text>')
        if token.lower:
            elements.append(f'<text x="{limit_x:.1f}" y="{baseline + size * 0.34:.1f}" font-size="{int(size * 0.5)}">{html.escape(token.lower)}</text>')
    elif token.kind == "cases":
        rows = token.rows or []
        brace_size = int(size * max(1.6, 0.82 * len(rows)))
        elements.append(f'<text x="{x:.1f}" y="{baseline + size * 0.12:.1f}" font-size="{brace_size}">{{</text>')
        row_size = int(size * 0.74)
        row_gap = size * 0.82
        first_y = baseline - row_gap * (len(rows) - 1) / 2
        for index, (left, right) in enumerate(rows):
            y = first_y + index * row_gap
            right_text = f"  {right}" if right else ""
            elements.append(
                f'<text x="{x + size * 0.68:.1f}" y="{y:.1f}" font-size="{row_size}">{html.escape(left + right_text)}</text>'
            )
    else:
        elements.append(f'<text x="{x:.1f}" y="{baseline:.1f}" font-size="{size}">{html.escape(token.text)}</text>')
    return elements


def _render_svg(text: str, width: int, size: int) -> str:
    tokens = _tokenize(text)
    lines = _layout(tokens, width, size)
    padding_x = 14
    padding_y = 9
    line_heights = [max(_token_height(token, size) for token in line) for line in lines]
    height = int(padding_y * 2 + sum(line_heights) + max(0, len(lines) - 1) * size * 0.3)

    elements: list[str] = []
    y = padding_y
    for line, line_height in zip(lines, line_heights):
        baseline = y + line_height * 0.72
        x = padding_x
        for token in line:
            if token.kind == "space":
                x += _token_width(token, size)
                continue
            elements.extend(_render_token(token, x, baseline, size))
            x += _token_width(token, size)
        y += line_height + size * 0.3

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'color="#172033"><style>text{{font-family:"Times New Roman","STIX Two Math","Cambria Math","PingFang SC","Microsoft YaHei",serif;font-weight:700;fill:#172033;dominant-baseline:auto;}}</style>'
        + "".join(elements)
        + "</svg>"
    )


@router.get("/svg")
def render_formula_svg(
    text: str = Query(..., min_length=1, max_length=700),
    width: int = Query(default=340, ge=80, le=720),
    size: int = Query(default=24, ge=16, le=40),
) -> Response:
    svg = _render_svg(text, width=width, size=size)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )
