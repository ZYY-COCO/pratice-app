"""Shared taxonomy, quality gates, and finite-domain verification for logic questions.

The module is intentionally dependency-free so it can be reused by the FastAPI
generation route, import scripts, and read-only audit scripts.
"""

from __future__ import annotations

import itertools
import math
import re
import unicodedata
from typing import Any, Mapping


LOGIC_SUBJECT = "逻辑推理"
OPTION_FIELDS = {
    "A": "option_a",
    "B": "option_b",
    "C": "option_c",
    "D": "option_d",
}

CANONICAL_LOGIC_CATALOG: dict[str, tuple[str, ...]] = {
    "概念": ("概念种类", "概念关系", "定义", "划分"),
    "判断": ("判断种类", "判断关系"),
    "推理": ("演绎推理", "归纳推理", "类比推理", "综合推理"),
    "论证": ("加强", "削弱", "假设", "解释", "推论", "论证结构", "谬误识别"),
}

_MODULE_ALIASES = {
    "概念": "概念",
    "判断": "判断",
    "推理": "推理",
    "论证": "论证",
    "概念判断": "概念判断",
    "推理规则": "推理",
    "削弱加强": "论证",
    "加强削弱": "论证",
}

_SUBMODULE_ALIASES = {
    "概念": "概念种类",
    "概念种类": "概念种类",
    "概念关系": "概念关系",
    "定义": "定义",
    "划分": "划分",
    "判断种类": "判断种类",
    "判断关系": "判断关系",
    "加强": "加强",
    "加强论证": "加强",
    "支持": "加强",
    "支持论证": "加强",
    "削弱": "削弱",
    "削弱论证": "削弱",
    "质疑": "削弱",
    "反驳": "削弱",
    "假设": "假设",
    "前提": "假设",
    "隐含前提": "假设",
    "必要假设": "假设",
    "解释": "解释",
    "推论": "推论",
    "结论": "推论",
    "论证结构": "论证结构",
    "形式相似": "论证结构",
    "谬误": "谬误识别",
    "谬误识别": "谬误识别",
    "演绎": "演绎推理",
    "演绎推理": "演绎推理",
    "归纳": "归纳推理",
    "归纳推理": "归纳推理",
    "类比": "类比推理",
    "类比推理": "类比推理",
    "综合": "综合推理",
    "综合推理": "综合推理",
}

_SUBMODULE_TO_MODULE = {
    submodule: module
    for module, submodules in CANONICAL_LOGIC_CATALOG.items()
    for submodule in submodules
}

LOGIC_TASKS = {
    "must_be_true",
    "could_be_true",
    "cannot_be_true",
    "must_be_false",
    "could_be_false",
    "strengthen",
    "weaken",
    "assumption",
    "explain",
    "parallel_reasoning",
    "flaw",
    "inference",
    "definition",
    "classification",
}

SOLVER_TASKS = {
    "must_be_true",
    "could_be_true",
    "cannot_be_true",
    "must_be_false",
    "could_be_false",
}

STRUCTURED_MODELS = {
    "conditional",
    "categorical_quantifier",
    "assignment",
    "sequencing",
    "grouping",
    "scheduling",
    "grid",
    "code_mapping",
}

ARGUMENT_TASKS = {
    "strengthen",
    "weaken",
    "assumption",
    "explain",
    "parallel_reasoning",
    "flaw",
    "inference",
}

_ARGUMENT_SUBMODULE_TASKS = {
    "加强": "strengthen",
    "削弱": "weaken",
    "假设": "assumption",
    "解释": "explain",
    "推论": "inference",
    "论证结构": "parallel_reasoning",
    "谬误识别": "flaw",
}

MAX_FORMAL_STATES = 200_000
MAX_FORMAL_SOLUTIONS = 50_000

_ARTIFICIAL_CONTEXT_RE = re.compile(
    r"第\s*[一二三四五六七八九十\d]+\s*批|第\s*\d+\s*题中|"
    r"第\s*\d+\s*次(?:讨论|训练|测评|讲评)|"
    r"(?:逻辑专项班|综合能力冲刺营|港澳台考研逻辑训练营|备考小组|冲刺班|文史班|综合班).{0,24}(?:讨论|测评|报告|材料)|"
    r"考前(?:总结|复核)|阶段小测|专题练习中出现|"
    r"答题统计显示|学习报告显示|复盘报告显示|测评记录显示|"
    r"课堂讨论材料显示|方法比较材料显示|模拟测试材料显示|专题讲义显示|"
    r"依据(?:逻辑|本题|考纲).{0,8}(?:知识点|生成)|AI\s*生成|模型生成",
    re.I,
)

_LOW_VALUE_OPTION_EXACT = {
    "逻辑题包含多个题型。",
    "该现象可以被统计记录。",
    "相关学生对结果比较满意。",
    "参与者使用了不同品牌的笔。",
    "相关记录的表格颜色发生变化。",
    "该现象名称没有变化。",
}

_LOW_VALUE_OPTION_RE = re.compile(
    r"(?:表格|页面|封面).{0,8}(?:颜色|字体|排版)|"
    r"使用了不同品牌的(?:笔|纸)|"
    r"名称没有变化|与题干没有关系|以上说法都不",
)

_GENERIC_EXPLANATION_RE = re.compile(
    r"挑战题需要先把自然语言转为标准逻辑形式|"
    r"排除项不能同时满足.{0,20}(?:关系|条件)|"
    r"根据题意可知.{0,8}(?:故选|所以选)|"
    r"其他选项均不符合题意",
)

# A natural-language coherence gate for generated workflow stems.  It is
# opt-in because historical questions may use deliberately abstract contexts;
# new generated batches can require it without rewriting the old bank.  The
# lists contain only distinctive terms so ordinary words such as “记录” or
# “审核” do not create false positives.
_SCENE_CORE_ACTIONS: dict[str, set[str]] = {
    "社区健康站": {"分诊", "问询", "消毒", "配药", "观察", "回访", "统计"},
    "医院质量管理部": {"收集", "核查", "分析", "整改", "复评", "通报", "归档"},
    "校园心理咨询室": {"预约", "接待", "评估", "咨询", "记录", "回访", "转介"},
    "社区养老服务点": {"登记", "评估", "配餐", "送餐", "回访", "复核", "统计"},
    "出版社编辑部": {"初审", "校对", "排版", "配图", "核稿", "印制", "寄送"},
    "新闻资料室": {"采访", "记录", "核实", "撰稿", "编辑", "审发", "存档"},
    "地方志编纂室": {"访谈", "查档", "核实", "撰写", "校对", "编排", "出版"},
    "古籍整理工作室": {"收集", "扫描", "校勘", "注释", "编目", "装帧", "入库"},
    "档案馆数字化小组": {"扫描", "识别", "标引", "备份", "质检", "上架"},
    "海关检验部门": {"申报", "查验", "抽样", "检测", "复核", "放行", "归档"},
    "港口调度室": {"验票", "装卸", "调度", "安检", "补给", "放行", "清场"},
    "食品安全检测室": {"抽样", "称量", "检测", "复测", "封存", "出具", "送达"},
    "水质检测实验室": {"采样", "编号", "检测", "复测", "分析", "报告", "归档"},
    "乡村水利项目组": {"勘察", "设计", "论证", "施工", "监理", "验收", "移交"},
    "城市园林管理处": {"勘察", "选苗", "栽植", "灌溉", "修剪", "巡查", "养护"},
    "历史建筑测绘队": {"踏勘", "测绘", "取样", "建档", "修复", "复核", "归档"},
    "文化展览筹备组": {"布展", "灯光", "讲解", "接待", "巡查", "撤展", "清点"},
    "城市规划展厅": {"选址", "设计", "论证", "布展", "讲解", "接待", "撤展"},
    "社区应急指挥室": {"预警", "研判", "调派", "处置", "转运", "安置"},
    "自然保护区管理站": {"巡护", "监测", "预警", "处置", "复查"},
    "农产品加工厂": {"收货", "抽检", "分拣", "加工", "包装", "入库", "出货"},
    "职业培训中心": {"报名", "排课", "授课", "考核", "结业"},
    "实验动物管理室": {"申请", "编号", "饲养", "观察", "处置"},
}

# Only terms that strongly identify a professional workflow belong here.
# Generic operations such as “编号”“记录”“审核”“归档” are intentionally
# omitted because they are valid in many scenes.
_DISTINCTIVE_ACTIONS = {
    "接诊", "分诊", "会诊", "治疗", "配药", "消毒", "出院", "转介", "咨询", "送餐", "配餐",
    "排版", "配图", "核稿", "印制", "撰稿", "采访", "编辑", "审发", "校勘", "注释", "装帧", "编目", "借阅", "归还",
    "申报", "查验", "验票", "装卸", "安检", "放行", "补给", "清场",
    "抽样", "称量", "检测", "复测", "封存", "出具", "采样",
    "灌溉", "施肥", "栽植", "修剪", "养护", "采收", "播种", "覆膜", "施药", "收获", "销售",
    "施工", "监理", "验收", "移交", "勘察", "测绘", "取景", "修补", "装裱", "布展", "灯光", "讲解", "撤展", "接待",
    "扫描", "识别", "校勘", "标引", "上架", "入柜", "建模", "试验", "答辩", "复现",
    "预警", "研判", "调派", "处置", "转运", "安置", "巡护", "复查",
    "报名", "排课", "授课", "考核", "结业", "饲养",
}
_PROCESS_LABELS = {
    "接诊", "分诊", "会诊", "治疗", "配药", "验票", "装卸", "调度", "安检",
    "测绘", "取景", "修补", "装裱", "初审", "校对", "排版", "配图", "核稿",
    "建模", "试验", "分析", "答辩", "踏勘", "访谈", "取样", "编码", "汇报",
    "扫描", "识别", "标引", "备份", "质检", "上架", "灌溉", "施肥", "除草",
    "抽样", "称量", "检测", "复测", "封存", "布展", "灯光", "讲解", "接待",
    "勘察", "设计", "论证", "施工", "监理", "验收", "预警", "研判", "调派",
    "处置", "转运", "安置", "收件", "分类", "审核", "退补", "决定", "送达",
    "检修", "试车", "测压", "润滑", "换件", "采风", "撰稿", "采访", "编辑",
    "审发", "转载", "播种", "覆膜", "施药", "收获", "销售", "开题", "检索",
    "实验", "统计", "撰写", "盘点", "贴标", "入架", "领用", "退库", "报废",
}


def context_coherence_issues(question: Mapping[str, object]) -> list[dict[str, str]]:
    """Find obvious scene/action and grouping-label mismatches.

    This is intentionally conservative: it reports only a strong mismatch
    (for example, medical actions inside a customs workflow), leaving nuanced
    real-world wording for human review.
    """

    stem = _clean_text(question.get("stem"))
    issues: list[dict[str, str]] = []
    for scene, expected in _SCENE_CORE_ACTIONS.items():
        if scene not in stem:
            continue
        # Do not classify a word that appears only inside the scene label as a
        # workflow action.  For example, “出版社编辑部” contains “编辑”, but that
        # does not mean the schedule itself introduced a foreign 编辑 step.
        workflow_text = stem.replace(scene, "", 1)
        present_distinctive = {term for term in _DISTINCTIVE_ACTIONS if term in workflow_text}
        foreign = present_distinctive - expected
        # Generic administrative verbs are intentionally excluded.  Requiring
        # at least one distinctive foreign term keeps this gate focused on
        # unmistakable cross-domain substitutions.
        if foreign:
            issues.append(
                _issue(
                    "scenario_action_mismatch",
                    "high",
                    f"场景“{scene}”与动作词 {', '.join(sorted(foreign))} 不属于同一工作语境。",
                    "rewrite",
                )
            )
        break

    if re.search(r"(?:成员|参与者)分为.{0,18}组", stem):
        labels = set(re.findall(r"([一-龥A-Za-z]{2,4})编入", stem))
        process_labels = labels & _PROCESS_LABELS
        if process_labels:
            issues.append(
                _issue(
                    "process_used_as_participant",
                    "high",
                    f"分组题把流程动作 {', '.join(sorted(process_labels))} 当成成员名称。",
                    "rewrite",
                )
            )
    return issues


def _count_surface_matches(text: object, expression: object) -> bool:
    """Validate the common Chinese surface form used by grouping count options."""

    surface = _clean_text(text)
    if not isinstance(expression, Mapping):
        return True
    expr: Mapping[str, object] = expression
    negated = False
    if expr.get("op") == "not" and isinstance(expr.get("arg"), Mapping):
        negated = True
        expr = expr["arg"]  # type: ignore[assignment]
    if expr.get("op") != "count":
        return True
    # Only enforce this specialized wording when the option explicitly talks
    # about members assigned to a group; other count formulations remain open.
    if not re.search(r"编入.+?的成员", surface):
        return True
    comparison = _clean_text(expr.get("comparison") or "eq")
    value = expr.get("value")
    if not isinstance(value, int):
        return False
    if not negated:
        expected = {
            "ge": f"至少有{value}人",
            "le": f"至多有{value}人",
            "eq": f"恰有{value}人",
        }.get(comparison)
    elif comparison == "ge":
        expected = f"至多有{max(value - 1, 0)}人"
    elif comparison == "le":
        expected = f"至少有{value + 1}人"
    elif comparison == "eq":
        expected = f"不是恰好{value}人"
    else:
        expected = None
    return bool(expected and expected in surface)


def _clean_text(value: object) -> str:
    return str(value or "").replace("\ufeff", "").strip()


def normalize_logic_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", _clean_text(value)).lower()
    return re.sub(r"[\s_—–\-:：()（）\[\]【】.。；;，,、？！!?“”‘’\"']", "", text)


def normalize_logic_classification(module: object, submodule: object) -> tuple[str, str]:
    """Return the V2 canonical module/submodule while preserving unknown values.

    ``概念判断`` is the only ambiguous legacy module, so the submodule decides
    whether it becomes ``概念`` or ``判断``.
    """

    raw_module = _clean_text(module)
    raw_submodule = _clean_text(submodule)
    module_key = normalize_logic_text(raw_module)
    submodule_key = normalize_logic_text(raw_submodule)

    normalized_module = next(
        (canonical for alias, canonical in _MODULE_ALIASES.items() if normalize_logic_text(alias) == module_key),
        raw_module,
    )
    normalized_submodule = next(
        (canonical for alias, canonical in _SUBMODULE_ALIASES.items() if normalize_logic_text(alias) == submodule_key),
        raw_submodule,
    )

    if normalized_module == "概念判断":
        normalized_module = _SUBMODULE_TO_MODULE.get(normalized_submodule, "概念")

    return normalized_module, normalized_submodule


def is_canonical_logic_classification(module: object, submodule: object) -> bool:
    normalized_module, normalized_submodule = normalize_logic_classification(module, submodule)
    return normalized_submodule in CANONICAL_LOGIC_CATALOG.get(normalized_module, ())


def infer_logic_task(stem: object, submodule: object = "") -> str:
    text = _clean_text(stem)
    point = _clean_text(submodule)
    pattern_tasks = (
        (r"最能(?:支持|加强)|加强上述|支持上述", "strengthen"),
        (r"最能(?:削弱|质疑|反驳)|削弱上述|质疑上述", "weaken"),
        (r"隐含的?前提|必须假设|必要假设|假设是", "assumption"),
        (r"最能解释|解释上述|解释.*(?:矛盾|现象|冲突)", "explain"),
        (r"论证(?:形式|结构).{0,8}(?:相似|相同)|形式最为相似", "parallel_reasoning"),
        (r"论证.{0,12}(?:问题|错误|谬误)|最主要的问题", "flaw"),
        (r"不可能|不能为真|必定不|一定不", "cannot_be_true"),
        (r"可能为真|可以为真|可能是|可以是", "could_be_true"),
        (r"必然为假|一定为假", "must_be_false"),
        (r"可能为假|可以为假", "could_be_false"),
        (r"一定成立|必然成立|必然正确|一定正确|可以得出|由此可知|应填入", "must_be_true"),
    )
    for pattern, task in pattern_tasks:
        if re.search(pattern, text):
            return task
    if point == "定义":
        return "definition"
    if point in {"概念种类", "概念关系", "判断种类", "判断关系", "划分"}:
        return "classification"
    if point == "加强":
        return "strengthen"
    if point == "削弱":
        return "weaken"
    if point == "假设":
        return "assumption"
    if point == "解释":
        return "explain"
    if point == "论证结构":
        return "parallel_reasoning"
    if point == "谬误识别":
        return "flaw"
    return "inference"


def infer_logic_model(stem: object, question_task: str | None = None) -> str:
    text = _clean_text(stem)
    task = question_task or infer_logic_task(text)
    if re.search(r"方阵|每行.{0,12}每列|每列.{0,12}每行", text):
        return "grid"
    if re.search(r"值班|排班|周[一二三四五六日天]|星期|连续.{0,4}天", text):
        return "scheduling"
    if re.search(r"符号.{0,20}表示|三串符号|对应的?文字", text):
        return "code_mapping"
    if re.search(r"分别对应|恰好(?:选修|分配|对应)|每人(?:只|恰好)|颜色各不相同", text):
        return "assignment"
    if re.search(r"先于|晚于|早于|第[一二三四五六七八九十\d]+位|顺序|依次", text):
        return "sequencing"
    if re.search(r"分为.{0,12}组|至少.{0,8}人|至多.{0,8}人|恰有.{0,8}人", text):
        return "grouping"
    if task == "parallel_reasoning":
        return "formal_similarity"
    if re.search(r"所有.{0,20}(?:都是|都不是)|有些|并非所有|至少有一个", text):
        return "categorical_quantifier"
    if re.search(r"如果|若|则|只有|除非|只要|至多|至少", text):
        return "conditional"
    if task in ARGUMENT_TASKS:
        if re.search(r"导致|因为|原因|影响|提高|降低|增加|减少|相关", text):
            return "argument_causal"
        if re.search(r"调查|样本|数据显示|比例|人数|统计", text):
            return "argument_sampling"
        return f"argument_{task}"
    if re.search(r"定义|概念|外延|划分", text):
        return "concept_relation"
    return "general_reasoning"


def _issue(code: str, severity: str, message: str, action: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "action": action,
    }


def _unwrap_expression(value: object) -> object:
    if isinstance(value, Mapping) and "expr" in value:
        return value["expr"]
    return value


def _resolve_operand(value: object, assignment: Mapping[str, object]) -> object:
    if isinstance(value, Mapping):
        if set(value) == {"var"}:
            name = _clean_text(value.get("var"))
            if name not in assignment:
                raise ValueError(f"unknown variable: {name}")
            return assignment[name]
        if "op" in value:
            return _evaluate_expression(value, assignment)
    return value


def _expression_sides(expression: Mapping[str, object], assignment: Mapping[str, object]) -> tuple[object, object]:
    if "var" in expression:
        variable = _clean_text(expression.get("var"))
        if variable not in assignment:
            raise ValueError(f"unknown variable: {variable}")
        left = assignment[variable]
    else:
        left = _resolve_operand(expression.get("left"), assignment)

    if "value_var" in expression:
        variable = _clean_text(expression.get("value_var"))
        if variable not in assignment:
            raise ValueError(f"unknown variable: {variable}")
        right = assignment[variable]
    elif "value" in expression:
        right = expression.get("value")
    else:
        right = _resolve_operand(expression.get("right"), assignment)
    return left, right


def _compare_values(left: object, operator: str, right: object) -> bool:
    if operator in {"eq", "=="}:
        return left == right
    if operator in {"neq", "!="}:
        return left != right
    if operator in {"lt", "<"}:
        return bool(left < right)  # type: ignore[operator]
    if operator in {"le", "<="}:
        return bool(left <= right)  # type: ignore[operator]
    if operator in {"gt", ">"}:
        return bool(left > right)  # type: ignore[operator]
    if operator in {"ge", ">="}:
        return bool(left >= right)  # type: ignore[operator]
    raise ValueError(f"unsupported comparison operator: {operator}")


def _evaluate_expression(raw_expression: object, assignment: Mapping[str, object]) -> bool:
    expression = _unwrap_expression(raw_expression)
    if isinstance(expression, bool):
        return expression
    if not isinstance(expression, Mapping):
        raise ValueError("expression must be an object")

    operator = _clean_text(expression.get("op")).lower()
    if operator in {"eq", "==", "neq", "!=", "lt", "<", "le", "<=", "gt", ">", "ge", ">="}:
        left, right = _expression_sides(expression, assignment)
        return _compare_values(left, operator, right)

    if operator in {"in", "not_in"}:
        left = _resolve_operand(expression.get("left", {"var": expression.get("var")}), assignment)
        values = expression.get("values")
        if not isinstance(values, list):
            raise ValueError(f"{operator} requires a values array")
        result = left in values
        return result if operator == "in" else not result

    if operator in {"and", "or", "xor"}:
        args = expression.get("args")
        if not isinstance(args, list) or not args:
            raise ValueError(f"{operator} requires a non-empty args array")
        values = [_evaluate_expression(item, assignment) for item in args]
        if operator == "and":
            return all(values)
        if operator == "or":
            return any(values)
        return sum(bool(item) for item in values) == 1

    if operator == "not":
        return not _evaluate_expression(expression.get("arg"), assignment)

    if operator in {"implies", "iff"}:
        left = _evaluate_expression(expression.get("if", expression.get("left")), assignment)
        right = _evaluate_expression(expression.get("then", expression.get("right")), assignment)
        return (not left or right) if operator == "implies" else left == right

    if operator == "all_different":
        variables = expression.get("vars")
        if not isinstance(variables, list) or len(variables) < 2:
            raise ValueError("all_different requires at least two vars")
        values = []
        for variable in variables:
            name = _clean_text(variable)
            if name not in assignment:
                raise ValueError(f"unknown variable: {name}")
            values.append(assignment[name])
        return len(set(values)) == len(values)

    if operator in {"before", "adjacent"}:
        left, right = _expression_sides(expression, assignment)
        if operator == "before":
            return bool(left < right)  # type: ignore[operator]
        return abs(float(left) - float(right)) == 1

    if operator == "count":
        args = expression.get("args")
        if not isinstance(args, list):
            raise ValueError("count requires an args array")
        actual = sum(1 for item in args if _evaluate_expression(item, assignment))
        comparison = _clean_text(expression.get("comparison") or "eq").lower()
        expected = expression.get("value")
        if not isinstance(expected, int):
            raise ValueError("count requires an integer value")
        return _compare_values(actual, comparison, expected)

    if operator == "truthy":
        variable = _clean_text(expression.get("var"))
        if variable not in assignment:
            raise ValueError(f"unknown variable: {variable}")
        return bool(assignment[variable])

    raise ValueError(f"unsupported expression operator: {operator or '<blank>'}")


def _normalized_source_is_present(source_text: object, target_text: object) -> bool:
    source = normalize_logic_text(source_text)
    target = normalize_logic_text(target_text)
    return bool(source and target and (source in target or target in source))


def _task_accepts(truth_values: list[bool], task: str) -> bool:
    if task == "must_be_true":
        return all(truth_values)
    if task == "could_be_true":
        return any(truth_values)
    if task == "cannot_be_true":
        return not any(truth_values)
    if task == "must_be_false":
        return not any(truth_values)
    if task == "could_be_false":
        return any(not value for value in truth_values)
    raise ValueError(f"unsupported solver task: {task}")


def verify_formal_spec(
    formal_spec: object,
    *,
    answer: object = None,
    stem: object = None,
    options: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    """Exhaustively verify a finite-domain logic specification.

    The function never evaluates source code. It accepts a small declarative
    expression language and returns errors instead of raising them to callers.
    """

    result: dict[str, Any] = {
        "ok": False,
        "errors": [],
        "task": None,
        "state_count": 0,
        "solution_count": 0,
        "valid_labels": [],
        "counterexamples": {},
    }
    try:
        if not isinstance(formal_spec, Mapping):
            raise ValueError("formal_spec must be an object")

        domains = formal_spec.get("domains")
        constraints = formal_spec.get("constraints")
        formal_options = formal_spec.get("options")
        task = _clean_text(formal_spec.get("task"))
        result["task"] = task

        if task not in SOLVER_TASKS:
            raise ValueError(f"formal_spec task is not solver-supported: {task or '<blank>'}")
        if not isinstance(domains, Mapping) or not domains:
            raise ValueError("formal_spec.domains must be a non-empty object")
        if not isinstance(constraints, list):
            raise ValueError("formal_spec.constraints must be an array")
        if not isinstance(formal_options, Mapping) or set(formal_options) != set(OPTION_FIELDS):
            raise ValueError("formal_spec.options must contain exactly A, B, C, D")

        variable_names = [_clean_text(name) for name in domains]
        if any(not name for name in variable_names) or len(set(variable_names)) != len(variable_names):
            raise ValueError("formal_spec domain variable names must be non-empty and unique")
        if len(variable_names) > 20:
            raise ValueError("formal_spec has too many variables")

        domain_values: list[list[object]] = []
        for original_name, normalized_name in zip(domains, variable_names, strict=True):
            values = domains[original_name]
            if not isinstance(values, list) or not values:
                raise ValueError(f"domain for {normalized_name} must be a non-empty array")
            if len(values) > 20:
                raise ValueError(f"domain for {normalized_name} is too large")
            if any(isinstance(value, (dict, list)) for value in values):
                raise ValueError(f"domain for {normalized_name} must contain scalar values")
            domain_values.append(values)

        state_count = math.prod(len(values) for values in domain_values)
        result["state_count"] = state_count
        if state_count > MAX_FORMAL_STATES:
            raise ValueError(f"formal_spec state space {state_count} exceeds {MAX_FORMAL_STATES}")

        if stem is not None:
            for index, constraint in enumerate(constraints, start=1):
                if not isinstance(constraint, Mapping):
                    raise ValueError(f"constraint #{index} must be an object")
                source_text = constraint.get("source_text")
                if not _normalized_source_is_present(source_text, stem):
                    raise ValueError(f"constraint #{index} source_text is not traceable to the stem")

        if options is not None:
            for label in OPTION_FIELDS:
                option_spec = formal_options[label]
                if not isinstance(option_spec, Mapping):
                    raise ValueError(f"formal option {label} must be an object")
                if not _normalized_source_is_present(option_spec.get("source_text"), options.get(label)):
                    raise ValueError(f"formal option {label} source_text does not match option text")

        solutions: list[dict[str, object]] = []
        option_truth: dict[str, list[bool]] = {label: [] for label in OPTION_FIELDS}
        for values in itertools.product(*domain_values):
            assignment = dict(zip(variable_names, values, strict=True))
            if not all(_evaluate_expression(constraint, assignment) for constraint in constraints):
                continue
            if len(solutions) >= MAX_FORMAL_SOLUTIONS:
                raise ValueError(f"formal_spec has more than {MAX_FORMAL_SOLUTIONS} solutions")
            solutions.append(assignment)
            for label in OPTION_FIELDS:
                option_truth[label].append(_evaluate_expression(formal_options[label], assignment))

        result["solution_count"] = len(solutions)
        if not solutions:
            raise ValueError("formal_spec constraints have no satisfying solution")

        valid_labels = [label for label, values in option_truth.items() if _task_accepts(values, task)]
        result["valid_labels"] = valid_labels
        if len(valid_labels) != 1:
            raise ValueError(f"formal_spec produces {len(valid_labels)} valid options: {valid_labels}")

        declared_answer = _clean_text(answer).upper()
        if declared_answer and valid_labels[0] != declared_answer:
            raise ValueError(
                f"formal_spec answer {valid_labels[0]} conflicts with declared answer {declared_answer}"
            )

        counterexamples: dict[str, object] = {}
        for label, truth_values in option_truth.items():
            if label in valid_labels:
                continue
            witness_index: int | None = None
            if task in {"must_be_true"}:
                witness_index = next((index for index, value in enumerate(truth_values) if not value), None)
            elif task in {"could_be_true"}:
                # A wrong option for “could be true” is false in every
                # satisfying state.  Keep a concrete satisfying assignment so
                # the review explanation can show that counterexample instead
                # of the unhelpful “no qualifying witness” marker.
                witness_index = next((index for index, value in enumerate(truth_values) if not value), None)
            elif task in {"cannot_be_true", "must_be_false"}:
                witness_index = next((index for index, value in enumerate(truth_values) if value), None)
            elif task == "could_be_false":
                # A wrong option for “could be false” is true in every
                # satisfying state.  Any one of those states is a useful
                # counterexample to the claim that it can be false.
                witness_index = next((index for index, value in enumerate(truth_values) if value), None)
            if witness_index is None:
                counterexamples[label] = "no_qualifying_witness"
            else:
                counterexamples[label] = solutions[witness_index]
        result["counterexamples"] = counterexamples
        result["ok"] = True
    except (TypeError, ValueError, KeyError, OverflowError) as exc:
        result["errors"].append(str(exc))
    return result


def _answer_option_text(question: Mapping[str, object]) -> str:
    label = _clean_text(question.get("answer")).upper()
    field = OPTION_FIELDS.get(label)
    return _clean_text(question.get(field)) if field else ""


def _clean_categorical_label(value: object) -> str:
    text = re.sub(r"^(所有|有些|一些|某些)", "", _clean_text(value))
    text = re.sub(r"(的人|的员工|的同学|的运动员|者|人)$", "", text)
    return normalize_logic_text(text)


def _categorical_risk_issues(question: Mapping[str, object]) -> list[dict[str, str]]:
    stem = re.sub(r"\s+", "", _clean_text(question.get("stem")))
    correct = normalize_logic_text(_answer_option_text(question))
    issues: list[dict[str, str]] = []

    positive = re.search(
        r"所有(?P<a>[^。；，,]{1,24}?)都(?:是|具备|属于)(?P<b>[^。；，,]{1,24}?)。"
        r"有些(?P<b2>[^。；，,]{1,24}?)是(?P<c>[^。；，,]{1,24}?)(?:。|，|由此)",
        stem,
    )
    if positive:
        a = _clean_categorical_label(positive.group("a"))
        c = _clean_categorical_label(positive.group("c"))
        if all(part in correct for part in ("有些", a, "是", c)):
            issues.append(
                _issue(
                    "categorical_invalid_middle_term_leap",
                    "high",
                    "“所有A是B、有些B是C”不能直接推出“有些A是C”。",
                    "manual_review",
                )
            )

    negative = re.search(
        r"所有(?P<a>[^。；，,]{1,24}?)都(?:是|具备|属于)(?P<b>[^。；，,]{1,24}?)。"
        r"有些(?P<b2>[^。；，,]{1,24}?)不是(?P<c>[^。；，,]{1,24}?)(?:。|，|由此)",
        stem,
    )
    if negative:
        a = _clean_categorical_label(negative.group("a"))
        c = _clean_categorical_label(negative.group("c"))
        if all(part in correct for part in ("有些", a, "不是", c)):
            issues.append(
                _issue(
                    "categorical_invalid_negative_middle_term_leap",
                    "high",
                    "“所有A是B、有些B不是C”不能直接推出“有些A不是C”。",
                    "manual_review",
                )
            )
    return issues


def audit_logic_question(
    question: Mapping[str, object],
    *,
    metadata: object = None,
    require_v2_metadata: bool = False,
    require_context_coherence: bool = False,
) -> dict[str, Any]:
    """Audit one logic question and return a machine-readable V2 result."""

    issues: list[dict[str, str]] = []
    raw_module = _clean_text(question.get("module"))
    raw_submodule = _clean_text(question.get("submodule"))
    module, submodule = normalize_logic_classification(raw_module, raw_submodule)
    task = infer_logic_task(question.get("stem"), submodule)
    logic_model = infer_logic_model(question.get("stem"), task)

    if _clean_text(question.get("subject")) != LOGIC_SUBJECT:
        issues.append(_issue("invalid_subject", "high", "逻辑题 subject 必须为逻辑推理。", "format_fix"))
    if _clean_text(question.get("exam_code")) != "Z001":
        issues.append(_issue("invalid_exam_code", "high", "逻辑题 exam_code 必须为 Z001。", "format_fix"))
    if _clean_text(question.get("question_type")) != "single_choice":
        issues.append(_issue("invalid_question_type", "high", "题型必须为 single_choice。", "format_fix"))

    if (module, submodule) != (raw_module, raw_submodule) and is_canonical_logic_classification(module, submodule):
        issues.append(
            _issue(
                "legacy_taxonomy",
                "low",
                f"历史分类 {raw_module}/{raw_submodule} 应转换为 {module}/{submodule}。",
                "format_fix",
            )
        )
    if submodule not in CANONICAL_LOGIC_CATALOG.get(module, ()):
        issues.append(
            _issue(
                "invalid_taxonomy",
                "high",
                f"分类 {raw_module}/{raw_submodule} 未命中逻辑 V2 目录。",
                "manual_review",
            )
        )

    stem = _clean_text(question.get("stem"))
    explanation = _clean_text(question.get("explanation"))
    if len(normalize_logic_text(stem)) < 10:
        issues.append(_issue("stem_too_short", "high", "题干信息不足。", "rewrite"))
    if _ARTIFICIAL_CONTEXT_RE.search(stem):
        issues.append(
            _issue(
                "artificial_context_residue",
                "medium",
                "题干包含批次、备考报告、讲义来源或生成过程元描述。",
                "rewrite",
            )
        )

    answer = _clean_text(question.get("answer")).upper()
    if answer not in OPTION_FIELDS:
        issues.append(_issue("invalid_answer", "high", "答案必须是 A、B、C、D 之一。", "manual_review"))

    normalized_options: list[str] = []
    option_map: dict[str, str] = {}
    for label, field in OPTION_FIELDS.items():
        option = _clean_text(question.get(field))
        option_map[label] = option
        normalized = normalize_logic_text(option)
        normalized_options.append(normalized)
        if not normalized:
            issues.append(_issue("blank_option", "high", f"选项 {label} 为空。", "rewrite"))
        if option in _LOW_VALUE_OPTION_EXACT or _LOW_VALUE_OPTION_RE.search(option):
            issues.append(
                _issue(
                    "low_value_distractor",
                    "high",
                    f"选项 {label} 是与推理无关或一眼可排除的占位干扰项。",
                    "rewrite",
                )
            )
    nonempty_options = [option for option in normalized_options if option]
    if len(set(nonempty_options)) != len(nonempty_options):
        issues.append(_issue("duplicate_options", "high", "A—D 选项存在重复。", "rewrite"))

    if not explanation:
        issues.append(_issue("missing_explanation", "high", "缺少解析。", "content_fix"))
    elif len(normalize_logic_text(explanation)) < 35:
        issues.append(_issue("short_explanation", "medium", "解析过短，未形成可复核推导。", "content_fix"))
    if explanation and _GENERIC_EXPLANATION_RE.search(explanation):
        issues.append(
            _issue(
                "generic_explanation",
                "medium",
                "解析使用模板化结论，未具体对应本题条件和错项。",
                "content_fix",
            )
        )
    explanation_answer = re.search(r"(?:答案|故选|应选)\s*[:：]?\s*([A-D])", explanation, re.I)
    if explanation_answer and answer in OPTION_FIELDS and explanation_answer.group(1).upper() != answer:
        issues.append(
            _issue(
                "answer_explanation_conflict",
                "high",
                "解析中声明的答案与 answer 字段冲突。",
                "manual_review",
            )
        )

    issues.extend(_categorical_risk_issues(question))
    if require_context_coherence:
        issues.extend(context_coherence_issues(question))

    logic_metadata = metadata
    if logic_metadata is None and isinstance(question.get("logic_v2"), Mapping):
        logic_metadata = question.get("logic_v2")

    formal_verification: dict[str, Any] | None = None
    if require_v2_metadata and not isinstance(logic_metadata, Mapping):
        issues.append(
            _issue(
                "missing_logic_v2_metadata",
                "high",
                "在线逻辑题缺少 logic_v2 审核元数据。",
                "rewrite",
            )
        )
    elif isinstance(logic_metadata, Mapping):
        required_fields = {
            "version",
            "logic_model",
            "question_task",
            "premise_form",
            "variables",
            "constraints",
            "distractor_types",
            "source_fragment_ids",
            "shared_stem_id",
            "verification_status",
            "counterexamples",
            "difficulty_features",
            "formal_spec",
        }
        missing_fields = sorted(field for field in required_fields if field not in logic_metadata)
        if missing_fields:
            issues.append(
                _issue(
                    "incomplete_logic_v2_metadata",
                    "high",
                    f"logic_v2 缺少字段：{', '.join(missing_fields)}。",
                    "rewrite",
                )
            )

        if _clean_text(logic_metadata.get("version")) != "2.0":
            issues.append(_issue("invalid_logic_v2_version", "high", "logic_v2.version 必须为 2.0。", "rewrite"))

        metadata_task = _clean_text(logic_metadata.get("question_task"))
        metadata_model = _clean_text(logic_metadata.get("logic_model"))
        if metadata_task not in LOGIC_TASKS:
            issues.append(_issue("invalid_question_task", "high", "question_task 不在 V2 允许值中。", "rewrite"))
        elif task != "inference" and metadata_task != task:
            issues.append(
                _issue(
                    "question_task_mismatch",
                    "high",
                    f"题干识别任务为 {task}，元数据声明为 {metadata_task}。",
                    "manual_review",
                )
            )
        if not metadata_model:
            issues.append(_issue("missing_logic_model", "high", "logic_model 不能为空。", "rewrite"))
        elif logic_model in STRUCTURED_MODELS and metadata_model != logic_model:
            issues.append(
                _issue(
                    "logic_model_mismatch",
                    "high",
                    f"题面识别母题为 {logic_model}，元数据声明为 {metadata_model}。",
                    "manual_review",
                )
            )

        if metadata_task in ARGUMENT_TASKS and module != "论证":
            issues.append(
                _issue(
                    "argument_taxonomy_mismatch",
                    "high",
                    "论证类设问必须归入论证模块。",
                    "manual_review",
                )
            )
        expected_task = _ARGUMENT_SUBMODULE_TASKS.get(submodule)
        if expected_task and metadata_task != expected_task:
            issues.append(
                _issue(
                    "submodule_task_mismatch",
                    "high",
                    f"考点 {submodule} 要求 question_task={expected_task}，当前为 {metadata_task}。",
                    "manual_review",
                )
            )

        list_fields = ("premise_form", "variables", "constraints", "source_fragment_ids", "difficulty_features")
        for field in list_fields:
            if field in logic_metadata and not isinstance(logic_metadata.get(field), list):
                issues.append(_issue("invalid_metadata_shape", "high", f"{field} 必须为数组。", "rewrite"))
        for field in ("premise_form", "variables", "constraints"):
            if isinstance(logic_metadata.get(field), list) and not logic_metadata.get(field):
                issues.append(_issue("incomplete_reasoning_metadata", "high", f"{field} 不能为空。", "rewrite"))
        if isinstance(logic_metadata.get("difficulty_features"), list) and not logic_metadata.get("difficulty_features"):
            issues.append(_issue("missing_difficulty_features", "medium", "未说明难度构成。", "content_fix"))

        distractor_types = logic_metadata.get("distractor_types")
        counterexamples = logic_metadata.get("counterexamples")
        wrong_labels = set(OPTION_FIELDS) - ({answer} if answer in OPTION_FIELDS else set())
        for field_name, values in (("distractor_types", distractor_types), ("counterexamples", counterexamples)):
            if not isinstance(values, Mapping):
                issues.append(_issue("invalid_metadata_shape", "high", f"{field_name} 必须为对象。", "rewrite"))
                continue
            missing_labels = sorted(label for label in wrong_labels if not _clean_text(values.get(label)))
            if missing_labels:
                issues.append(
                    _issue(
                        f"incomplete_{field_name}",
                        "high",
                        f"{field_name} 缺少错项 {', '.join(missing_labels)} 的说明。",
                        "rewrite",
                    )
                )

        verification_status = _clean_text(logic_metadata.get("verification_status"))
        needs_solver = metadata_task in SOLVER_TASKS and (
            metadata_model in STRUCTURED_MODELS or logic_model in STRUCTURED_MODELS
        )
        if needs_solver:
            if verification_status != "solver_verified":
                issues.append(
                    _issue(
                        "invalid_verification_status",
                        "high",
                        "结构题 verification_status 必须为 solver_verified。",
                        "manual_review",
                    )
                )
            formal_spec = logic_metadata.get("formal_spec")
            if isinstance(formal_spec, Mapping):
                formal_options = formal_spec.get("options")
                if isinstance(formal_options, Mapping):
                    # Count claims are especially easy to mistranslate: a
                    # formal ``ge/le/eq`` expression can silently drift from
                    # wording such as “至少/至多/恰有”.  Check the visible
                    # option text against the declarative expression before
                    # invoking the solver so both gates share the same
                    # interpretation.
                    for label in OPTION_FIELDS:
                        option_spec = formal_options.get(label)
                        if not isinstance(option_spec, Mapping):
                            continue
                        if not _count_surface_matches(
                            option_map.get(label), option_spec.get("expr")
                        ):
                            issues.append(
                                _issue(
                                    "count_option_surface_mismatch",
                                    "high",
                                    f"形式化选项 {label} 的人数表述与题面文字不一致。",
                                    "manual_review",
                                )
                            )
            formal_verification = verify_formal_spec(
                formal_spec,
                answer=answer,
                stem=stem,
                options=option_map,
            )
            if not formal_verification["ok"]:
                issues.append(
                    _issue(
                        "formal_spec_invalid",
                        "high",
                        "；".join(formal_verification.get("errors") or ["形式化规格未通过验证"]),
                        "manual_review",
                    )
                )
        elif metadata_task in ARGUMENT_TASKS and verification_status != "rubric_verified":
            issues.append(
                _issue(
                    "invalid_verification_status",
                    "high",
                    "论证题 verification_status 必须为 rubric_verified。",
                    "manual_review",
                )
            )

    severity_penalty = {"critical": 40, "high": 25, "medium": 10, "low": 3}
    score = max(0, 100 - sum(severity_penalty.get(issue["severity"], 5) for issue in issues))
    actions = {issue["action"] for issue in issues}
    if "manual_review" in actions:
        decision = "manual_review"
    elif "rewrite" in actions:
        decision = "rewrite"
    elif "content_fix" in actions:
        decision = "content_fix"
    elif "format_fix" in actions:
        decision = "format_fix"
    else:
        decision = "keep"

    blocking_codes = [issue["code"] for issue in issues if issue["severity"] in {"critical", "high"}]
    return {
        "valid_for_generation": not blocking_codes,
        "decision": decision,
        "quality_score": score,
        "canonical_module": module,
        "canonical_submodule": submodule,
        "inferred_task": task,
        "inferred_logic_model": logic_model,
        "verification_status": (
            _clean_text(logic_metadata.get("verification_status"))
            if isinstance(logic_metadata, Mapping)
            else "not_machine_verified"
        ),
        "formal_verification": formal_verification,
        "blocking_codes": blocking_codes,
        "issues": issues,
    }
