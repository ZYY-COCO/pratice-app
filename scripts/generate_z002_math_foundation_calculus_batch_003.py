from __future__ import annotations

import json
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "z002_math_foundation_calculus_batch_003.json"
REVIEW_PATH = PROJECT_ROOT / "data" / "z002_math_foundation_calculus_batch_003_review.md"


MODULE_GUIDE = {
    "一元函数微分学": "解题时先判断是极限、连续、导数还是函数性质问题。遇到 0/0 型或无穷型，可优先考虑等价无穷小、泰勒展开或洛必达法则；遇到单调、极值、凹凸与渐近线，要先求导并结合定义域判断。",
    "一元函数积分学": "解题时先判断是直接积分、换元、分部积分、变上限函数还是定积分应用。定积分题要特别注意上下限、奇偶性、几何面积是否需要取绝对值，以及速度函数积分代表位移或路程。",
    "多元函数微分学": "解题时先明确自变量关系。偏导题中未求导变量看作常数；全微分题要写出两个一阶偏导；链式法则和隐函数题要逐层求导；二元函数极值题要结合驻点和 Hessian 判别。",
}

QUESTIONS: list[dict] = []
EXISTING_STEMS: set[str] = set()


def normalize_stem(value: str) -> str:
    return re.sub(r"\s+", "", value or "").strip().lower()


def load_existing_stems() -> set[str]:
    stems: set[str] = set()
    for path in (PROJECT_ROOT / "data").glob("*.json"):
        if path.resolve() == OUTPUT_PATH.resolve():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        questions = payload.get("questions") if isinstance(payload, dict) else payload
        if not isinstance(questions, list):
            continue
        for item in questions:
            if isinstance(item, dict) and isinstance(item.get("stem"), str):
                stems.add(normalize_stem(item["stem"]))
    return stems


def fmt_fraction(value: Fraction | int) -> str:
    if isinstance(value, int):
        return str(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def make_options(correct: str, wrongs: list[str]) -> tuple[dict[str, str], str]:
    candidates: list[str] = []
    for value in [correct, *wrongs, "0", "1", "-1", "不存在"]:
        text = str(value)
        if text not in candidates:
            candidates.append(text)
    if len(candidates) < 4:
        raise ValueError(f"Not enough option candidates for {correct}")

    correct_index = len(QUESTIONS) % 4
    wrong_values = [value for value in candidates if value != correct][:3]
    ordered = wrong_values[:]
    ordered.insert(correct_index, correct)
    keys = ["A", "B", "C", "D"]
    return dict(zip(keys, ordered)), keys[correct_index]


def add(
    module: str,
    submodule: str,
    stem: str,
    correct: str,
    wrongs: list[str],
    explanation: str,
    difficulty: int,
) -> None:
    if normalize_stem(stem) in EXISTING_STEMS:
        return

    options, answer = make_options(correct, wrongs)
    QUESTIONS.append(
        {
            "exam_code": "Z002",
            "subject": "数学基础",
            "module": module,
            "submodule": submodule,
            "question_type": "single_choice",
            "stem": stem,
            "option_a": options["A"],
            "option_b": options["B"],
            "option_c": options["C"],
            "option_d": options["D"],
            "answer": answer,
            "explanation": (
                f"本题考查“{submodule}”。正确答案为 {answer}。"
                f"{explanation}"
                f"{MODULE_GUIDE[module]}"
            ),
            "difficulty": difficulty,
            "source_type": "ai_generated",
            "source_year": 2026,
            "passage_id": None,
        }
    )


def add_limit_questions() -> None:
    module = "一元函数微分学"
    for a in (2, 3, 4):
        correct = fmt_fraction(Fraction(-(a * a), 2))
        add(
            module,
            "极限",
            f"极限 lim(x→0) [ln(1+{a}x)-{a}x]/x^2 的值为：",
            correct,
            [fmt_fraction(Fraction(a * a, 2)), str(-a), "0", str(-(a * a))],
            f"利用展开 ln(1+{a}x)={a}x-({a}x)^2/2+o(x^2)，分子主项为 -{a * a}x^2/2，所以极限为 {correct}。",
            4,
        )
    for a in (2, 3, 4):
        correct = fmt_fraction(Fraction(a * a, 2))
        add(
            module,
            "极限",
            f"极限 lim(x→0) [e^({a}x)-1-{a}x]/x^2 的值为：",
            correct,
            [fmt_fraction(Fraction(-(a * a), 2)), str(a), "0", str(a * a)],
            f"由 e^({a}x)=1+{a}x+({a}x)^2/2+o(x^2)，分子主项为 {a * a}x^2/2，故极限为 {correct}。",
            4,
        )
    for a in (1, 2, 3):
        correct = fmt_fraction(Fraction(-(a**3), 6))
        add(
            module,
            "极限",
            f"极限 lim(x→0) [sin({a}x)-{a}x]/x^3 的值为：",
            correct,
            [fmt_fraction(Fraction(a**3, 6)), fmt_fraction(Fraction(-(a * a), 2)), "0", str(-a)],
            f"sin({a}x)={a}x-({a}x)^3/6+o(x^3)，所以分子主项为 -{a**3}x^3/6，极限为 {correct}。",
            4,
        )
    for a in (1, 2, 3):
        correct = fmt_fraction(Fraction(a * a, 2))
        add(
            module,
            "极限",
            f"极限 lim(x→0) [1-cos({a}x)]/x^2 的值为：",
            correct,
            [fmt_fraction(Fraction(-(a * a), 2)), str(a), "0", str(a * a)],
            f"1-cos({a}x) 与 ({a}x)^2/2 等价，所以极限为 {correct}。",
            4,
        )
    for a in (1, 2, 3):
        correct = fmt_fraction(Fraction(a**3, 3))
        add(
            module,
            "洛必达法则",
            f"极限 lim(x→0) [tan({a}x)-{a}x]/x^3 的值为：",
            correct,
            [fmt_fraction(Fraction(-(a**3), 3)), fmt_fraction(Fraction(a * a, 2)), "0", str(a)],
            f"tan u=u+u^3/3+o(u^3)。令 u={a}x，分子主项为 {a**3}x^3/3，故极限为 {correct}。",
            5,
        )


def add_continuity_questions() -> None:
    module = "一元函数微分学"
    add(module, "连续", "设 f(x)=sin(5x)/x (x≠0)，f(0)=a。若 f 在 x=0 处连续，则 a 的值为：", "5", ["1/5", "0", "1"], "连续要求 f(0)=lim(x→0)sin(5x)/x。因为 sin(5x)/(5x)→1，所以极限为 5。", 3)
    add(module, "连续", "设 f(x)=[e^(3x)-1]/x (x≠0)，f(0)=a。若 f 在 x=0 处连续，则 a 的值为：", "3", ["1/3", "0", "1"], "e^(3x)-1 与 3x 等价，所以极限为 3，连续时 a=3。", 3)
    add(module, "连续", "设 f(x)=[√(1+6x)-1]/x (x≠0)，f(0)=a。若 f 在 x=0 处连续，则 a 的值为：", "3", ["6", "1/3", "0"], "对分子有理化，原式等于 6/[√(1+6x)+1]，令 x→0 得 3。", 4)
    add(module, "连续", "设 f(x)=ln(1+kx)/x (x≠0)，f(0)=4。若 f 在 x=0 处连续，则 k 的值为：", "4", ["1/4", "2", "0"], "ln(1+kx) 与 kx 等价，极限为 k。连续要求极限等于 4，所以 k=4。", 3)
    add(module, "连续", "设 f(x)=ax+1 (x<1)，f(x)=x^2 (x≥1)。若 f 在 x=1 处连续，则 a 的值为：", "0", ["1", "-1", "2"], "左极限为 a+1，右侧函数值为 1。连续要求 a+1=1，因此 a=0。", 4)
    add(module, "连续", "设 f(x)=e^x+a (x<0)，f(x)=cos x (x≥0)。若 f 在 x=0 处连续，则 a 的值为：", "0", ["1", "-1", "2"], "左极限为 1+a，右侧函数值为 cos0=1。连续要求 1+a=1，因此 a=0。", 4)


def add_derivative_questions() -> None:
    module = "一元函数微分学"
    add(module, "导数", "函数 y=x^x 在 x=1 处的导数为：", "1", ["0", "2", "e"], "对 y=x^x 取对数，得 ln y=xlnx，所以 y'=x^x(lnx+1)，代入 x=1 得 1。", 4)
    add(module, "导数", "函数 y=x^x 在 x=e 处的导数为：", "2e^e", ["e^e", "e", "e^(e+1)"], "y'=x^x(lnx+1)。当 x=e 时，ln e=1，所以 y'=2e^e。", 5)
    add(module, "导数", "函数 y=ln(x+√(x^2+1)) 的导数为：", "1/√(x^2+1)", ["x/√(x^2+1)", "1/(x^2+1)", "√(x^2+1)"], "直接求导并通分化简，分子会化为 1，得到 y'=1/√(x^2+1)。", 4)
    add(module, "导数", "函数 y=(ln x)/x 在 x=e 处的导数为：", "0", ["1/e", "-1/e", "1/e^2"], "y'=(1-lnx)/x^2，代入 x=e 时 lne=1，所以导数为 0。", 3)
    add(module, "导数", "函数 y=e^(2x)sin x 在 x=0 处的导数为：", "1", ["0", "2", "3"], "乘积求导得 y'=2e^(2x)sinx+e^(2x)cosx，代入 x=0 得 1。", 4)
    add(module, "导数", "函数 y=arctan(x^2) 在 x=1 处的导数为：", "1", ["1/2", "2", "0"], "y'=2x/[1+x^4]，代入 x=1 得 2/2=1。", 4)
    add(module, "导数", "曲线 y=ln x 在点 (1,0) 处的切线方程为：", "y=x-1", ["y=x", "y=1-x", "y=0"], "y'=1/x，在 x=1 处斜率为 1，过 (1,0) 的切线为 y=x-1。", 3)
    add(module, "高阶导数", "函数 y=x^2e^x 的二阶导数为：", "e^x(x^2+4x+2)", ["e^x(x^2+2x)", "e^x(x^2+2)", "2e^x"], "先求 y'=e^x(x^2+2x)，再求 y''=e^x(x^2+2x)+e^x(2x+2)=e^x(x^2+4x+2)。", 4)
    add(module, "高阶导数", "函数 y=sin(3x) 的二阶导数为：", "-9sin(3x)", ["3cos(3x)", "-3sin(3x)", "9cos(3x)"], "第一次求导为 3cos(3x)，第二次求导为 -9sin(3x)。", 3)
    add(module, "高阶导数", "函数 y=ln(1+x^2) 在 x=0 处的二阶导数为：", "2", ["0", "1", "-2"], "y'=2x/(1+x^2)，继续求导 y''=2(1-x^2)/(1+x^2)^2，代入 x=0 得 2。", 4)
    add(module, "微分", "函数 y=e^(x^2) 的微分 dy 为：", "2xe^(x^2)dx", ["e^(x^2)dx", "x^2e^(x^2)dx", "2e^(x^2)dx"], "dy=y'dx。对 e^(x^2) 求导要乘内部导数 2x，所以 dy=2xe^(x^2)dx。", 3)
    add(module, "微分", "函数 y=√(1+x^2) 的微分 dy 为：", "x/√(1+x^2) dx", ["1/√(1+x^2) dx", "2x√(1+x^2) dx", "√(1+x^2) dx"], "y'=(1/2)(1+x^2)^(-1/2)·2x=x/√(1+x^2)，所以 dy=x/√(1+x^2)dx。", 3)


def add_function_property_questions() -> None:
    module = "一元函数微分学"
    add(module, "洛必达法则", "极限 lim(x→1) ln x/(x-1) 的值为：", "1", ["0", "-1", "不存在"], "这是 0/0 型，洛必达后得 (1/x)/1，代入 x=1 得 1。", 3)
    add(module, "洛必达法则", "极限 lim(x→1) (x^2-1)/ln x 的值为：", "2", ["1", "0", "不存在"], "这是 0/0 型，洛必达后得 2x/(1/x)=2x^2，代入 x=1 得 2。", 4)
    add(module, "洛必达法则", "极限 lim(x→0) (e^x-1)/sin x 的值为：", "1", ["0", "e", "不存在"], "这是 0/0 型，洛必达后为 e^x/cosx，代入 x=0 得 1。", 3)
    add(module, "单调性", "函数 f(x)=x^3-3x 的增区间为：", "(-∞,-1)∪(1,+∞)", ["(-1,1)", "(-∞,1)", "(1,+∞)"], "f'(x)=3x^2-3=3(x-1)(x+1)。当 x<-1 或 x>1 时 f'(x)>0，所以函数递增。", 4)
    add(module, "单调性", "函数 f(x)=x+1/x 在 (0,+∞) 上的减区间为：", "(0,1)", ["(1,+∞)", "(0,+∞)", "不存在"], "f'(x)=1-1/x^2。当 0<x<1 时 f'(x)<0，所以减区间为 (0,1)。", 4)
    add(module, "极值与最值", "函数 f(x)=ln x-x (x>0) 的最大值为：", "-1", ["0", "1", "不存在"], "f'(x)=1/x-1，驻点 x=1。x<1 时递增，x>1 时递减，故最大值 f(1)=-1。", 4)
    add(module, "极值与最值", "函数 f(x)=x^4-4x^2 的极小值为：", "-4", ["0", "4", "-2"], "f'(x)=4x(x^2-2)，在 x=±√2 处取极小值，f(±√2)=4-8=-4。", 5)
    add(module, "凹凸性", "函数 f(x)=ln x (x>0) 的凹凸性为：", "在 (0,+∞) 上凹", ["在 (0,+∞) 上凸", "先凸后凹", "先凹后凸"], "f''(x)=-1/x^2<0，因此函数在整个定义域上为凹函数。", 3)
    add(module, "拐点", "函数 f(x)=x^3-3x^2 的拐点横坐标为：", "1", ["0", "2", "-1"], "f''(x)=6x-6，令 f''(x)=0 得 x=1，且二阶导在该点两侧变号，所以 x=1 是拐点横坐标。", 4)
    add(module, "渐近线", "函数 y=1/x 的水平渐近线为：", "y=0", ["x=0", "y=1", "不存在"], "当 x→±∞ 时 1/x→0，所以水平渐近线为 y=0。x=0 是垂直渐近线，不是水平渐近线。", 3)
    add(module, "渐近线", "函数 y=(2x^2+1)/(x+1) 的斜渐近线为：", "y=2x-2", ["y=2x+2", "y=x-1", "不存在"], "多项式除法得 (2x^2+1)/(x+1)=2x-2+3/(x+1)，当 |x|→∞ 时余项趋于 0，斜渐近线为 y=2x-2。", 5)


def add_integral_questions() -> None:
    module = "一元函数积分学"
    add(module, "原函数", "不定积分 ∫ x e^(x^2) dx 等于：", "1/2 e^(x^2)+C", ["e^(x^2)+C", "2e^(x^2)+C", "x^2e^(x^2)+C"], "令 u=x^2，则 du=2x dx，所以 ∫x e^(x^2)dx=1/2∫e^u du=1/2e^(x^2)+C。", 3)
    add(module, "原函数", "不定积分 ∫ ln x dx 等于：", "xlnx-x+C", ["xlnx+C", "lnx/x+C", "1/x+C"], "用分部积分，取 u=lnx，dv=dx，得 ∫lnx dx=xlnx-x+C。", 4)
    add(module, "定积分", "定积分 ∫_0^1 x e^x dx 的值为：", "1", ["e-1", "0", "2"], "分部积分得 ∫x e^x dx=(x-1)e^x。代入 0 到 1，结果为 0-(-1)=1。", 4)
    add(module, "定积分", "定积分 ∫_0^π sin^2 x dx 的值为：", "π/2", ["π", "1/2", "0"], "利用 sin^2x=(1-cos2x)/2，积分为 [x/2-sin2x/4]_0^π=π/2。", 4)
    add(module, "换元积分", "定积分 ∫_0^1 2x/(1+x^2) dx 的值为：", "ln2", ["1", "1/2", "2ln2"], "令 u=1+x^2，则 du=2x dx，上下限由 1 到 2，积分为 ∫_1^2 du/u=ln2。", 3)
    add(module, "换元积分", "定积分 ∫_0^1 x/(1+x^2)^2 dx 的值为：", "1/4", ["1/2", "1", "ln2"], "令 u=1+x^2，则 xdx=du/2，积分为 1/2∫_1^2 u^(-2)du=1/4。", 4)
    add(module, "换元积分", "定积分 ∫_0^1 x√(1+x^2) dx 的值为：", "(2√2-1)/3", ["(√2-1)/3", "2√2/3", "1/3"], "令 u=1+x^2，则 xdx=du/2，积分为 1/2∫_1^2 u^(1/2)du=(2√2-1)/3。", 4)
    add(module, "牛顿-莱布尼兹公式", "定积分 ∫_1^e 1/x dx 的值为：", "1", ["e-1", "0", "ln2"], "原函数为 lnx，代入上下限得 lne-ln1=1。", 3)
    add(module, "变限定积分", "设 F(x)=∫_0^(x^2) sin t dt，则 F'(x)=：", "2xsin(x^2)", ["sin(x^2)", "2sin(x^2)", "xsin(x^2)"], "变上限为 x^2，要用链式法则：F'(x)=sin(x^2)·2x。", 4)
    add(module, "变限定积分", "设 F(x)=∫_x^(x^2) e^t dt，则 F'(x)=：", "2xe^(x^2)-e^x", ["e^(x^2)-e^x", "2xe^(x^2)+e^x", "e^x-2xe^(x^2)"], "上下限都含 x，求导为上限函数值乘上限导数减下限函数值乘下限导数，即 2xe^(x^2)-e^x。", 5)
    add(module, "分部积分", "定积分 ∫_0^1 xlnx dx 的值为：", "-1/4", ["1/4", "-1/2", "0"], "分部积分可得 ∫xlnx dx=(x^2/2)lnx-x^2/4。代入 0 到 1，结果为 -1/4。", 4)
    add(module, "分部积分", "定积分 ∫_0^1 x arctan x dx 的值为：", "π/4-1/2", ["π/8", "π/4", "1/2-π/4"], "取 u=arctanx，dv=xdx，得边界项 π/8，再减去 1/2∫_0^1 x^2/(1+x^2)dx，化简为 π/4-1/2。", 5)
    add(module, "几何应用", "曲线 y=x 与 y=x^2 在 0≤x≤1 之间所围面积为：", "1/6", ["1/2", "1/3", "1"], "在 [0,1] 上 x≥x^2，面积为 ∫_0^1 (x-x^2)dx=1/2-1/3=1/6。", 3)
    add(module, "几何应用", "曲线 y=4-x^2 与 x 轴在 [-2,2] 上所围面积为：", "32/3", ["16/3", "8", "4"], "面积为 ∫_-2^2 (4-x^2)dx=[4x-x^3/3]_-2^2=32/3。", 4)
    add(module, "物理应用", "质点速度 v(t)=3t^2+2t，0≤t≤1，则位移为：", "2", ["1", "3", "4"], "位移等于速度对时间积分：∫_0^1(3t^2+2t)dt=[t^3+t^2]_0^1=2。", 3)
    add(module, "物理应用", "质点速度 v(t)=cos t，0≤t≤π/2，则位移为：", "1", ["0", "π/2", "2"], "位移为 ∫_0^(π/2) cos t dt=sin t|_0^(π/2)=1。", 3)


def add_multivariable_questions() -> None:
    module = "多元函数微分学"
    add(module, "偏导数", "设 z=x^2y+sin(xy)，则 z 对 x 的偏导数为：", "2xy+ycos(xy)", ["2xy+xcos(xy)", "x^2+cos(xy)", "2x+ycos(xy)"], "对 x 求偏导时 y 看作常数。x^2y 的偏导为 2xy，sin(xy) 的偏导为 ycos(xy)。", 4)
    add(module, "偏导数", "设 z=ln(x^2+y^2)，则 z_x 在点 (1,1) 处的值为：", "1", ["1/2", "2", "0"], "z_x=2x/(x^2+y^2)，代入 (1,1) 得 2/2=1。", 3)
    add(module, "偏导数", "设 z=xy/(x+y)，则 z_x 在点 (1,1) 处的值为：", "1/4", ["1/2", "1", "0"], "把 y 看作常数，z_x=[y(x+y)-xy]/(x+y)^2=y^2/(x+y)^2，代入 (1,1) 得 1/4。", 4)
    add(module, "全微分", "设 z=x^2+y^2，则 dz 等于：", "2x dx+2y dy", ["x dx+y dy", "2x dy+2y dx", "dx+dy"], "全微分 dz=z_xdx+z_ydy，其中 z_x=2x，z_y=2y。", 3)
    add(module, "全微分", "设 z=e^(xy)，则 dz 等于：", "e^(xy)(y dx+x dy)", ["e^(xy)(x dx+y dy)", "xy e^(xy)(dx+dy)", "e^(xy)dxdy"], "z_x=ye^(xy)，z_y=xe^(xy)，所以 dz=e^(xy)(ydx+xdy)。", 4)
    add(module, "二阶偏导", "设 z=x^2y^3，则 z_xy 等于：", "6xy^2", ["2xy^3", "3x^2y^2", "6x^2y"], "先对 x 求偏导得 z_x=2xy^3，再对 y 求偏导得 z_xy=6xy^2。", 3)
    add(module, "二阶偏导", "设 z=ln(1+xy)，则 z_xy 在点 (1,1) 处的值为：", "1/4", ["1/2", "1", "-1/4"], "z_x=y/(1+xy)，再对 y 求偏导得 z_xy=1/(1+xy)^2，代入 (1,1) 得 1/4。", 5)
    add(module, "链导法则", "设 z=x^2+y^2，x=t，y=t^2，则 dz/dt 在 t=1 处的值为：", "6", ["2", "4", "8"], "dz/dt=2x·dx/dt+2y·dy/dt。t=1 时 x=1，y=1，dx/dt=1，dy/dt=2，所以结果为 2+4=6。", 4)
    add(module, "链导法则", "设 z=ln(u^2+v)，u=x+y，v=xy，则 z_x 在点 (1,1) 处的值为：", "1", ["1/5", "2/5", "4/5"], "z_x=[2u·u_x+v_x]/(u^2+v)。在 (1,1) 处 u=2，v=1，u_x=1，v_x=y=1，所以 z_x=(4+1)/5=1。", 5)
    add(module, "隐函数求导", "由方程 x^2+y^2=1 确定 y 为 x 的函数，则 dy/dx 等于：", "-x/y", ["x/y", "-y/x", "y/x"], "对两边关于 x 求导，得 2x+2y y'=0，所以 y'=-x/y。", 3)
    add(module, "隐函数求导", "由方程 x^2+xy+y^2=3 确定 y 为 x 的函数，则在点 (1,1) 处 dy/dx 的值为：", "-1", ["1", "0", "-2"], "两边求导得 2x+y+xy'+2yy'=0，故 y'=-(2x+y)/(x+2y)。代入 (1,1) 得 -1。", 4)
    add(module, "隐函数求导", "由方程 e^(xy)+y=x 确定 y 为 x 的函数，则 dy/dx 等于：", "[1-ye^(xy)]/[xe^(xy)+1]", ["[1+ye^(xy)]/[xe^(xy)+1]", "[ye^(xy)-1]/[xe^(xy)+1]", "[1-xy]/[x+y]"], "对 e^(xy)+y=x 求导，得 e^(xy)(y+xy')+y'=1，整理得 y'=[1-ye^(xy)]/[xe^(xy)+1]。", 5)
    add(module, "二元函数极值", "函数 f(x,y)=x^2+y^2-2x-4y 的极小值点为：", "(1,2)", ["(2,1)", "(-1,-2)", "(0,0)"], "f_x=2x-2，f_y=2y-4。令二者为 0，得驻点 (1,2)，且 Hessian 正定，所以为极小值点。", 3)
    add(module, "二元函数极值", "函数 f(x,y)=x^2+4y^2-2x+8y 的极小值点为：", "(1,-1)", ["(-1,1)", "(1,1)", "(-1,-1)"], "f_x=2x-2，f_y=8y+8，解得 x=1，y=-1。二次项正定，所以该点为极小值点。", 4)
    add(module, "二元函数极值", "函数 f(x,y)=x^2-y^2 在点 (0,0) 的性质为：", "鞍点", ["极大值点", "极小值点", "不可判定"], "沿 x 轴 f=x^2≥0，沿 y 轴 f=-y^2≤0，点 (0,0) 附近函数值有正有负，因此为鞍点。", 4)
    add(module, "二元函数极值", "函数 f(x,y)=x^3+y^3-3xy 在点 (1,1) 的性质为：", "极小值点", ["极大值点", "鞍点", "非驻点"], "f_x=3x^2-3y，f_y=3y^2-3x，(1,1) 是驻点。f_xx=6，f_yy=6，f_xy=-3，D=36-9=27>0 且 f_xx>0，所以为极小值点。", 5)


def add_extra_harder_questions() -> None:
    add("一元函数微分学", "极限", "极限 lim(x→0) [arctan(2x)-2x]/x^3 的值为：", "-8/3", ["8/3", "-4/3", "0"], "arctan u=u-u^3/3+o(u^3)，令 u=2x，分子主项为 -8x^3/3，故极限为 -8/3。", 5)
    add("一元函数微分学", "极限", "极限 lim(x→0) [x-ln(1+x)]/x^2 的值为：", "1/2", ["-1/2", "1", "0"], "ln(1+x)=x-x^2/2+o(x^2)，所以 x-ln(1+x)=x^2/2+o(x^2)，极限为 1/2。", 4)
    add("一元函数微分学", "极限", "极限 lim(x→0) [(1+x)^3-1-3x]/x^2 的值为：", "3", ["1", "6", "0"], "展开 (1+x)^3=1+3x+3x^2+x^3，分子为 3x^2+x^3，除以 x^2 后极限为 3。", 4)
    add("一元函数微分学", "极限", "极限 lim(x→0) [(1+x)^4-1-4x]/x^2 的值为：", "6", ["4", "8", "0"], "展开 (1+x)^4=1+4x+6x^2+4x^3+x^4，分子主项为 6x^2，极限为 6。", 4)
    add("一元函数微分学", "连续", "设 f(x)=[1-cos(kx)]/x^2 (x≠0)，f(0)=8。若 k>0 且 f 在 x=0 处连续，则 k 的值为：", "4", ["2", "8", "√8"], "1-cos(kx) 与 k^2x^2/2 等价，连续要求 k^2/2=8。因 k>0，所以 k=4。", 4)
    add("一元函数微分学", "导数", "函数 y=x^2lnx 在 x=e 处的导数为：", "3e", ["e", "2e", "4e"], "y'=2xlnx+x。代入 x=e，得 2e+e=3e。", 4)
    add("一元函数微分学", "导数", "函数 y=(x+1)e^x 在 x=0 处的导数为：", "2", ["1", "0", "e"], "乘积求导得 y'=e^x+(x+1)e^x=(x+2)e^x，代入 x=0 得 2。", 3)
    add("一元函数微分学", "导数", "曲线 y=x^2 在点 (2,4) 处的切线方程为：", "y=4x-4", ["y=2x", "y=4x+4", "y=x+2"], "y'=2x，在 x=2 处斜率为 4。过 (2,4) 的切线为 y-4=4(x-2)，即 y=4x-4。", 3)
    add("一元函数微分学", "导数", "曲线 y=x^2 在点 (1,1) 处的法线方程为：", "x+2y-3=0", ["2x+y-3=0", "x-2y+1=0", "x+2y+3=0"], "切线斜率为 2，法线斜率为 -1/2。法线方程 y-1=-(x-1)/2，整理得 x+2y-3=0。", 4)
    add("一元函数微分学", "高阶导数", "函数 y=x^3lnx 在 x=1 处的二阶导数为：", "5", ["3", "6", "1"], "y'=3x^2lnx+x^2，y''=6xlnx+5x，代入 x=1 得 5。", 5)
    add("一元函数微分学", "洛必达法则", "极限 lim(x→0) [1-cos x]/[x sin x] 的值为：", "1/2", ["1", "0", "2"], "分子与 x^2/2 等价，分母与 x^2 等价，所以极限为 1/2；也可用洛必达法则验证。", 4)
    add("一元函数微分学", "极值与最值", "函数 f(x)=x^2-2lnx (x>0) 的最小值为：", "1", ["0", "2", "-1"], "f'(x)=2x-2/x，令 f'(x)=0 得 x=1。二阶导 f''(x)=2+2/x^2>0，故最小值为 f(1)=1。", 4)
    add("一元函数微分学", "极值与最值", "函数 f(x)=x^3-6x^2+9x 在 x=1 处取得：", "极大值", ["极小值", "不是极值", "拐点"], "f'(x)=3(x-1)(x-3)。在 x=1 左侧 f'>0，右侧 f'<0，所以 x=1 处为极大值。", 4)
    add("一元函数微分学", "凹凸性", "函数 f(x)=x^4-6x^2 的凹区间为：", "(-1,1)", ["(-∞,-1)∪(1,+∞)", "(0,+∞)", "不存在"], "f''(x)=12x^2-12=12(x^2-1)。当 -1<x<1 时 f''(x)<0，所以函数在该区间为凹。", 5)
    add("一元函数积分学", "定积分", "定积分 ∫_0^1 (3x^2+2x+1) dx 的值为：", "3", ["2", "1", "4"], "逐项积分得 [x^3+x^2+x]_0^1=1+1+1=3。", 3)
    add("一元函数积分学", "分部积分", "定积分 ∫_0^(π/2) xsinx dx 的值为：", "1", ["π/2", "0", "2"], "分部积分可得 ∫xsinx dx=-xcosx+sinx，代入 0 到 π/2 得 1。", 4)
    add("一元函数积分学", "变限定积分", "设 F(x)=∫_(x^2)^x ln(1+t)dt，则 F'(x)=：", "ln(1+x)-2xln(1+x^2)", ["ln(1+x)+2xln(1+x^2)", "2xln(1+x)-ln(1+x^2)", "ln(1+x^2)-ln(1+x)"], "上限求导为 ln(1+x)，下限 x^2 求导时要减去 ln(1+x^2)·2x。", 5)
    add("一元函数积分学", "几何应用", "曲线 y=1-x 与 x 轴、y 轴围成的面积为：", "1/2", ["1", "2", "1/4"], "所围区域是直角三角形，两直角边均为 1，面积为 1/2；也可计算 ∫_0^1(1-x)dx=1/2。", 3)
    add("一元函数积分学", "物理应用", "质点速度 v(t)=2t+1，0≤t≤2，则位移为：", "6", ["4", "5", "8"], "位移等于 ∫_0^2(2t+1)dt=[t^2+t]_0^2=4+2=6。", 3)
    add("多元函数微分学", "偏导数", "设 z=x^2y+y^2，则 z_y 在点 (1,2) 处的值为：", "5", ["4", "6", "3"], "z_y=x^2+2y，代入 (1,2) 得 1+4=5。", 3)
    add("多元函数微分学", "全微分", "设 z=sin(x+y)，则 dz 等于：", "cos(x+y)(dx+dy)", ["sin(x+y)(dx+dy)", "cos(x+y)(dx-dy)", "cosx dx+cosy dy"], "z_x=cos(x+y)，z_y=cos(x+y)，所以 dz=cos(x+y)dx+cos(x+y)dy。", 3)
    add("多元函数微分学", "二阶偏导", "设 z=x^2y，则 z_xy 等于：", "2x", ["2y", "x^2", "2xy"], "先对 x 求偏导 z_x=2xy，再对 y 求偏导得 z_xy=2x。", 3)
    add("多元函数微分学", "链导法则", "设 z=xy，x=t^2，y=e^t，则 dz/dt 在 t=0 处的值为：", "0", ["1", "2", "e"], "z=t^2e^t，求导得 dz/dt=2te^t+t^2e^t，代入 t=0 得 0。", 4)
    add("多元函数微分学", "隐函数求导", "由方程 xy+lny=1 确定 y 为 x 的函数，则在点 (1,1) 处 dy/dx 的值为：", "-1/2", ["1/2", "-1", "0"], "两边求导得 y+xy'+y'/y=0，代入 (1,1) 得 1+2y'=0，所以 y'=-1/2。", 5)
    add("多元函数微分学", "二元函数极值", "函数 f(x,y)=x^2+y^2+2x-2y 的极小值点为：", "(-1,1)", ["(1,-1)", "(1,1)", "(-1,-1)"], "f_x=2x+2，f_y=2y-2，令二者为 0 得 (-1,1)。二次项正定，所以为极小值点。", 3)


def write_review() -> None:
    difficulty_counter = Counter(item["difficulty"] for item in QUESTIONS)
    module_counter = Counter(item["module"] for item in QUESTIONS)
    submodule_counter = Counter(f"{item['module']} / {item['submodule']}" for item in QUESTIONS)

    lines = [
        "# Z002 数学基础 batch 003 质检",
        "",
        f"- 文件：`{OUTPUT_PATH.name}`",
        f"- 题量：{len(QUESTIONS)}",
        "- 定位：中等偏难补充题，服务标准模拟卷和专项训练。",
        "",
        "## 难度分布",
        "",
    ]
    for difficulty in sorted(difficulty_counter):
        lines.append(f"- difficulty {difficulty}: {difficulty_counter[difficulty]} 题")
    lines.extend(["", "## 模块分布", ""])
    for module, count in module_counter.most_common():
        lines.append(f"- {module}: {count} 题")
    lines.extend(["", "## 子模块分布", ""])
    for key, count in submodule_counter.most_common():
        lines.append(f"- {key}: {count} 题")

    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    global EXISTING_STEMS
    EXISTING_STEMS = load_existing_stems()

    add_limit_questions()
    add_continuity_questions()
    add_derivative_questions()
    add_function_property_questions()
    add_integral_questions()
    add_multivariable_questions()
    add_extra_harder_questions()

    duplicate_count = len(QUESTIONS) - len({normalize_stem(item["stem"]) for item in QUESTIONS})
    if duplicate_count:
        raise ValueError(f"Duplicate stems generated inside file: {duplicate_count}")
    if len(QUESTIONS) < 70:
        raise ValueError(f"Generated too few questions: {len(QUESTIONS)}")

    payload = {"questions": QUESTIONS}
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review()

    print(f"Generated {len(QUESTIONS)} questions")
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Wrote {REVIEW_PATH}")


if __name__ == "__main__":
    main()
