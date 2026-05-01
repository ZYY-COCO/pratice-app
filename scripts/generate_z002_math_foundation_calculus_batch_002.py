from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "z002_math_foundation_calculus_batch_002.json"
REVIEW_PATH = PROJECT_ROOT / "data" / "z002_math_foundation_calculus_batch_002_review.md"


MODULE_GUIDE = {
    "一元函数微分学": "先判断极限、连续、导数还是函数性质问题，再选择等价无穷小、求导、二阶导数或渐近线方法。中等题通常会把两个公式连在一起考，计算时要先化简再代入。",
    "一元函数积分学": "先判断是直接积分、换元、分部积分、变限定积分还是定积分应用。中等题容易在上下限、符号和复合上限处设置干扰。",
    "多元函数微分学": "偏导时其他变量看作常数；全微分要分别求两个一阶偏导；复合函数和隐函数题要先写清链式法则或对两边同时求导。",
}


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


def q(
    module: str,
    submodule: str,
    stem: str,
    options: dict[str, str],
    answer: str,
    explanation: str,
    difficulty: int,
) -> dict:
    answer = answer.upper()
    if set(options) != {"A", "B", "C", "D"}:
        raise ValueError(f"Options must be A-D: {stem}")
    if answer not in options:
        raise ValueError(f"Invalid answer {answer}: {stem}")
    if len(set(options.values())) != 4:
        raise ValueError(f"Duplicate options: {stem}")

    return {
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


QUESTIONS = [
    q(
        "一元函数微分学",
        "极限",
        "极限 lim(x->0) [ln(1+x)-x]/x^2 的值为：",
        {"A": "-1/2", "B": "1/2", "C": "0", "D": "-1"},
        "A",
        "利用展开 ln(1+x)=x-x^2/2+o(x^2)，分子 ln(1+x)-x=-x^2/2+o(x^2)，除以 x^2 后极限为 -1/2。",
        4,
    ),
    q(
        "一元函数微分学",
        "极限",
        "极限 lim(x->0) [e^x-1-x]/x^2 的值为：",
        {"A": "1", "B": "1/2", "C": "0", "D": "-1/2"},
        "B",
        "e^x=1+x+x^2/2+o(x^2)，所以 e^x-1-x=x^2/2+o(x^2)，极限为 1/2。",
        4,
    ),
    q(
        "一元函数微分学",
        "极限",
        "极限 lim(x->0) [sin x-x]/x^3 的值为：",
        {"A": "1/6", "B": "-1/6", "C": "0", "D": "-1/3"},
        "B",
        "sin x=x-x^3/6+o(x^3)，因此 sin x-x=-x^3/6+o(x^3)，极限为 -1/6。",
        4,
    ),
    q(
        "一元函数微分学",
        "极限",
        "极限 lim(x->∞) x/e^x 的值为：",
        {"A": "1", "B": "∞", "C": "0", "D": "不存在"},
        "C",
        "指数函数 e^x 的增长速度快于一次函数 x，也可用洛必达法则得 lim 1/e^x=0。",
        3,
    ),
    q(
        "一元函数微分学",
        "连续",
        "设 f(x)=sin(ax)/x (x≠0)，f(0)=3。若 f 在 x=0 处连续，则 a 的值为：",
        {"A": "1", "B": "2", "C": "3", "D": "-3"},
        "C",
        "连续要求 f(0)=lim(x->0) sin(ax)/x。因为 sin(ax)/(ax)->1，所以极限为 a，故 a=3。",
        3,
    ),
    q(
        "一元函数微分学",
        "连续",
        "设 f(x)=(e^(kx)-1)/x (x≠0)，f(0)=4。若 f 在 x=0 处连续，则 k 的值为：",
        {"A": "1", "B": "2", "C": "4", "D": "1/4"},
        "C",
        "e^(kx)-1 与 kx 等价，故极限为 k。连续要求极限等于 f(0)=4，所以 k=4。",
        3,
    ),
    q(
        "一元函数微分学",
        "连续",
        "下列关于函数 f(x)=|x| 在 x=0 处的说法正确的是：",
        {"A": "连续且可导", "B": "连续但不可导", "C": "不连续但可导", "D": "既不连续也不可导"},
        "B",
        "|x| 在 0 处左右极限都等于 0，所以连续；但左右导数分别为 -1 和 1，不相等，所以不可导。",
        3,
    ),
    q(
        "一元函数微分学",
        "导数",
        "函数 y=x^x 在 x=1 处的导数为：",
        {"A": "0", "B": "1", "C": "e", "D": "2"},
        "B",
        "对 y=x^x 取对数得 ln y=x ln x，求导可得 y'=x^x(ln x+1)。代入 x=1 得 1。",
        4,
    ),
    q(
        "一元函数微分学",
        "导数",
        "函数 y=ln(x+√(x^2+1)) 的导数为：",
        {"A": "1/(x^2+1)", "B": "1/√(x^2+1)", "C": "x/√(x^2+1)", "D": "√(x^2+1)"},
        "B",
        "该函数是反双曲正弦函数的常见形式。直接求导并通分化简，可得 y'=1/√(x^2+1)。",
        4,
    ),
    q(
        "一元函数微分学",
        "导数",
        "函数 y=(ln x)/x 在 x=e 处的导数为：",
        {"A": "0", "B": "1/e", "C": "-1/e", "D": "1/e^2"},
        "A",
        "y'=(1-ln x)/x^2，代入 x=e 时 ln e=1，所以 y'=0。",
        3,
    ),
    q(
        "一元函数微分学",
        "导数",
        "曲线 y=ln x 在点 (1,0) 处的切线方程为：",
        {"A": "y=x", "B": "y=x-1", "C": "y=1-x", "D": "y=0"},
        "B",
        "y'=1/x，在 x=1 处斜率为 1。过点 (1,0) 的切线为 y=x-1。",
        3,
    ),
    q(
        "一元函数微分学",
        "微分",
        "用微分近似计算 √4.04，最接近的结果为：",
        {"A": "2.001", "B": "2.01", "C": "2.04", "D": "2.1"},
        "B",
        "取 f(x)=√x，在 x=4 处 f(4)=2，f'(4)=1/4，Δx=0.04，故 Δy≈(1/4)×0.04=0.01，结果约 2.01。",
        3,
    ),
    q(
        "一元函数微分学",
        "微分",
        "函数 y=e^(x^2) 的微分 dy 为：",
        {"A": "e^(x^2)dx", "B": "2xe^(x^2)dx", "C": "x^2e^(x^2)dx", "D": "2e^(x^2)dx"},
        "B",
        "dy=y'dx。对 e^(x^2) 求导要用链式法则，导数为 2xe^(x^2)，所以 dy=2xe^(x^2)dx。",
        3,
    ),
    q(
        "一元函数微分学",
        "高阶导数",
        "函数 y=x^2e^x 的二阶导数为：",
        {"A": "e^x(x^2+2x)", "B": "e^x(x^2+4x+2)", "C": "e^x(x^2+2)", "D": "2e^x"},
        "B",
        "先求 y'=e^x(x^2+2x)，再求导得 y''=e^x(x^2+2x)+e^x(2x+2)=e^x(x^2+4x+2)。",
        4,
    ),
    q(
        "一元函数微分学",
        "高阶导数",
        "函数 y=sin(2x) 的二阶导数为：",
        {"A": "2cos(2x)", "B": "-2sin(2x)", "C": "-4sin(2x)", "D": "4cos(2x)"},
        "C",
        "y'=2cos(2x)，继续求导 y''=-4sin(2x)，注意第二次求导仍要乘内部导数 2。",
        3,
    ),
    q(
        "一元函数微分学",
        "洛必达法则",
        "极限 lim(x->0) [x-sin x]/x^3 的值为：",
        {"A": "1/6", "B": "-1/6", "C": "1/3", "D": "0"},
        "A",
        "这是 0/0 型，也可用展开。sin x=x-x^3/6+o(x^3)，所以 x-sin x=x^3/6+o(x^3)，极限为 1/6。",
        4,
    ),
    q(
        "一元函数微分学",
        "洛必达法则",
        "极限 lim(x->0) [tan x-x]/x^3 的值为：",
        {"A": "1/6", "B": "1/3", "C": "1/2", "D": "0"},
        "B",
        "tan x=x+x^3/3+o(x^3)，因此 tan x-x=x^3/3+o(x^3)，极限为 1/3。",
        4,
    ),
    q(
        "一元函数微分学",
        "单调性",
        "函数 f(x)=x^3-3x 的单调递增区间为：",
        {"A": "(-∞,-1)∪(1,∞)", "B": "(-1,1)", "C": "(-∞,1)", "D": "(-1,∞)"},
        "A",
        "f'(x)=3x^2-3=3(x-1)(x+1)。当 x<-1 或 x>1 时 f'(x)>0，所以函数递增。",
        3,
    ),
    q(
        "一元函数微分学",
        "单调性",
        "若 f'(x)=(x-1)^2(x+2)，则 f(x) 的单调递减区间为：",
        {"A": "(-∞,-2)", "B": "(-2,1)", "C": "(1,∞)", "D": "(-∞,1)"},
        "A",
        "(x-1)^2 非负，符号主要由 x+2 决定。x<-2 时 f'(x)<0，所以函数递减。",
        4,
    ),
    q(
        "一元函数微分学",
        "极值与最值",
        "函数 f(x)=x^3-3x 的局部极大值点为：",
        {"A": "x=-1", "B": "x=0", "C": "x=1", "D": "x=3"},
        "A",
        "f'(x)=3(x^2-1)，在 x=-1 左正右负，因此 x=-1 为局部极大值点；x=1 为局部极小值点。",
        3,
    ),
    q(
        "一元函数微分学",
        "极值与最值",
        "函数 f(x)=x+1/x (x>0) 的最小值为：",
        {"A": "1", "B": "2", "C": "0", "D": "不存在"},
        "B",
        "f'(x)=1-1/x^2，令 f'(x)=0 得 x=1。此时 f(1)=2，也可由均值不等式得到最小值 2。",
        3,
    ),
    q(
        "一元函数微分学",
        "凹凸性",
        "函数 f(x)=ln x 在 (0,∞) 上的凹凸性为：",
        {"A": "凹向上", "B": "凹向下", "C": "先上后下", "D": "无凹凸性"},
        "B",
        "f''(x)=-1/x^2<0，所以函数在 (0,∞) 上凹向下。",
        3,
    ),
    q(
        "一元函数微分学",
        "凹凸性",
        "函数 f(x)=x^4-2x^2 在 x=0 附近的凹凸性判断正确的是：",
        {"A": "f''(0)<0，凹向下", "B": "f''(0)>0，凹向上", "C": "f''(0)=0，不能仅凭该点二阶导判断", "D": "一定无拐点"},
        "A",
        "f''(x)=12x^2-4，f''(0)=-4；并且当 |x|<1/√3 时 f''(x)<0，所以在 x=0 的足够小邻域内函数凹向下。",
        4,
    ),
    q(
        "一元函数微分学",
        "拐点",
        "函数 f(x)=x^3-3x^2 的拐点横坐标为：",
        {"A": "0", "B": "1", "C": "2", "D": "3"},
        "B",
        "f''(x)=6x-6，令 f''(x)=0 得 x=1，且二阶导在 x=1 两侧变号，因此拐点横坐标为 1。",
        3,
    ),
    q(
        "一元函数微分学",
        "渐近线",
        "曲线 y=(2x^2+1)/(x-1) 的斜渐近线为：",
        {"A": "y=2x", "B": "y=2x+2", "C": "y=x+2", "D": "y=2x-1"},
        "B",
        "多项式除法：(2x^2+1)/(x-1)=2x+2+3/(x-1)，当 x 趋于无穷时余项趋于 0，所以斜渐近线为 y=2x+2。",
        4,
    ),
    q(
        "一元函数微分学",
        "渐近线",
        "曲线 y=ln(x-1) 的垂直渐近线为：",
        {"A": "x=0", "B": "x=1", "C": "y=0", "D": "y=1"},
        "B",
        "ln(x-1) 的定义域为 x>1，当 x->1+ 时函数趋于 -∞，所以 x=1 是垂直渐近线。",
        3,
    ),
    q(
        "一元函数积分学",
        "原函数",
        "不定积分 ∫ x e^(x^2) dx 等于：",
        {"A": "e^(x^2)+C", "B": "(1/2)e^(x^2)+C", "C": "2e^(x^2)+C", "D": "x^2e^(x^2)+C"},
        "B",
        "令 u=x^2，则 du=2x dx，所以 ∫x e^(x^2)dx=(1/2)∫e^u du=(1/2)e^(x^2)+C。",
        3,
    ),
    q(
        "一元函数积分学",
        "原函数",
        "不定积分 ∫ ln x dx 等于：",
        {"A": "x ln x-x+C", "B": "x ln x+C", "C": "1/x+C", "D": "ln^2 x+C"},
        "A",
        "用分部积分，取 u=ln x，dv=dx，得 ∫ln x dx=x ln x-∫1 dx=x ln x-x+C。",
        3,
    ),
    q(
        "一元函数积分学",
        "定积分",
        "定积分 ∫_0^1 x e^(x^2) dx 的值为：",
        {"A": "e-1", "B": "(e-1)/2", "C": "e/2", "D": "1/2"},
        "B",
        "令 u=x^2，du=2x dx，上下限由 0 到 1，原式=(1/2)∫_0^1 e^u du=(e-1)/2。",
        3,
    ),
    q(
        "一元函数积分学",
        "定积分",
        "定积分 ∫_0^(π/2) sin^2 x dx 的值为：",
        {"A": "π/2", "B": "π/4", "C": "1/2", "D": "1"},
        "B",
        "利用 sin^2 x=(1-cos2x)/2，积分得 x/2-sin2x/4，代入 0 与 π/2 得 π/4。",
        4,
    ),
    q(
        "一元函数积分学",
        "变限定积分",
        "设 F(x)=∫_1^(x^2) ln t dt，则 F'(x)=：",
        {"A": "ln(x^2)", "B": "2x ln(x^2)", "C": "2ln x", "D": "x ln x"},
        "B",
        "变上限为 x^2，按链式法则 F'(x)=ln(x^2)·(x^2)'=2x ln(x^2)。",
        3,
    ),
    q(
        "一元函数积分学",
        "变限定积分",
        "设 F(x)=∫_(sin x)^1 t^2 dt，则 F'(x)=：",
        {"A": "sin^2x cosx", "B": "-sin^2x cosx", "C": "cos^2x", "D": "-cos^2x"},
        "B",
        "下限是 sin x。对变下限积分求导要带负号，所以 F'(x)=-(sin x)^2·cos x。",
        4,
    ),
    q(
        "一元函数积分学",
        "变限定积分",
        "设 F(x)=∫_x^(x^2) e^t dt，则 F'(x)=：",
        {"A": "e^(x^2)-e^x", "B": "2xe^(x^2)-e^x", "C": "2xe^x-e^(x^2)", "D": "e^x+e^(x^2)"},
        "B",
        "上限 x^2 贡献 2xe^(x^2)，下限 x 贡献 -e^x，因此 F'(x)=2xe^(x^2)-e^x。",
        4,
    ),
    q(
        "一元函数积分学",
        "牛顿-莱布尼兹公式",
        "定积分 ∫_1^e 1/x dx 的值为：",
        {"A": "0", "B": "1", "C": "e-1", "D": "ln(e-1)"},
        "B",
        "原函数为 ln x，代入上下限得 ln e-ln1=1-0=1。",
        3,
    ),
    q(
        "一元函数积分学",
        "牛顿-莱布尼兹公式",
        "定积分 ∫_0^1 (3x^2+2x) dx 的值为：",
        {"A": "1", "B": "2", "C": "3", "D": "4"},
        "B",
        "原函数为 x^3+x^2，代入 1 与 0 得 1+1=2。",
        3,
    ),
    q(
        "一元函数积分学",
        "换元积分",
        "定积分 ∫_0^1 2x/(1+x^2)^2 dx 的值为：",
        {"A": "1/4", "B": "1/2", "C": "1", "D": "2"},
        "B",
        "令 u=1+x^2，则 du=2x dx，上下限由 1 到 2，积分为 ∫_1^2 u^(-2)du=[-1/u]_1^2=1/2。",
        4,
    ),
    q(
        "一元函数积分学",
        "换元积分",
        "定积分 ∫_0^(π/2) sin x cos^2 x dx 的值为：",
        {"A": "1/2", "B": "1/3", "C": "2/3", "D": "1"},
        "B",
        "令 u=cos x，du=-sin x dx，积分变为 ∫_0^1 u^2 du=1/3。",
        3,
    ),
    q(
        "一元函数积分学",
        "分部积分",
        "定积分 ∫_0^1 x e^x dx 的值为：",
        {"A": "1", "B": "e-1", "C": "e", "D": "0"},
        "A",
        "分部积分得 ∫x e^x dx=x e^x-e^x。代入 0 到 1：0-(-1)=1。",
        4,
    ),
    q(
        "一元函数积分学",
        "分部积分",
        "定积分 ∫_0^1 x ln x dx 的值为：",
        {"A": "1/4", "B": "-1/4", "C": "-1/2", "D": "0"},
        "B",
        "分部积分或公式 ∫x^a ln x dx=-1/(a+1)^2，取 a=1 得 -1/4。",
        4,
    ),
    q(
        "一元函数积分学",
        "分部积分",
        "定积分 ∫_0^π x sin x dx 的值为：",
        {"A": "0", "B": "1", "C": "π", "D": "2π"},
        "C",
        "取 u=x，dv=sin x dx，则 v=-cos x。结果为 [-x cos x]_0^π+∫_0^π cos x dx=π。",
        4,
    ),
    q(
        "一元函数积分学",
        "几何应用",
        "曲线 y=x 与 y=x^2 在 [0,1] 围成的面积为：",
        {"A": "1/2", "B": "1/3", "C": "1/6", "D": "1"},
        "C",
        "在 [0,1] 上 x≥x^2，面积为 ∫_0^1 (x-x^2)dx=1/2-1/3=1/6。",
        3,
    ),
    q(
        "一元函数积分学",
        "几何应用",
        "曲线 y=4-x^2 与 x 轴围成的面积为：",
        {"A": "16/3", "B": "32/3", "C": "8", "D": "4π"},
        "B",
        "交点为 x=±2，面积为 ∫_-2^2 (4-x^2)dx=2∫_0^2(4-x^2)dx=32/3。",
        4,
    ),
    q(
        "一元函数积分学",
        "物理应用",
        "质点速度 v(t)=3t^2，0≤t≤2，则位移为：",
        {"A": "4", "B": "6", "C": "8", "D": "12"},
        "C",
        "位移等于速度对时间的积分：∫_0^2 3t^2dt=[t^3]_0^2=8。",
        3,
    ),
    q(
        "一元函数积分学",
        "物理应用",
        "变力 F(x)=2x 使物体从 x=0 到 x=3 所做的功为：",
        {"A": "6", "B": "9", "C": "12", "D": "18"},
        "B",
        "功等于力对位移积分：W=∫_0^3 2x dx=[x^2]_0^3=9。",
        3,
    ),
    q(
        "一元函数积分学",
        "定积分",
        "函数 f(x)=x^2 在 [0,3] 上的平均值为：",
        {"A": "1", "B": "2", "C": "3", "D": "9"},
        "C",
        "平均值为 1/(3-0)∫_0^3 x^2dx=(1/3)·9=3。",
        3,
    ),
    q(
        "多元函数微分学",
        "偏导数",
        "设 z=x^2y+y^3，则 ∂z/∂y 为：",
        {"A": "2xy", "B": "x^2+3y^2", "C": "x^2+y^2", "D": "2x+3y^2"},
        "B",
        "对 y 求偏导时 x 看作常数，x^2y 的偏导为 x^2，y^3 的偏导为 3y^2。",
        3,
    ),
    q(
        "多元函数微分学",
        "偏导数",
        "设 z=ln(x^2+y^2)，则 ∂z/∂x 为：",
        {"A": "1/(x^2+y^2)", "B": "2x/(x^2+y^2)", "C": "2y/(x^2+y^2)", "D": "ln(2x)"},
        "B",
        "把 x^2+y^2 看作整体，求 x 偏导得 2x，再除以原整体，所以结果为 2x/(x^2+y^2)。",
        3,
    ),
    q(
        "多元函数微分学",
        "全微分",
        "设 z=x^2y+e^y，则 dz 为：",
        {"A": "2xy dx+(x^2+e^y)dy", "B": "x^2 dx+e^y dy", "C": "2x dx+3y^2 dy", "D": "(2xy+e^y)dx"},
        "A",
        "z_x=2xy，z_y=x^2+e^y，因此 dz=z_x dx+z_y dy=2xy dx+(x^2+e^y)dy。",
        3,
    ),
    q(
        "多元函数微分学",
        "全微分",
        "设 z=xy，在点 (2,3) 处 dx=0.1，dy=-0.2，则 dz 约为：",
        {"A": "0.1", "B": "-0.1", "C": "0.5", "D": "-0.5"},
        "B",
        "dz=y dx+x dy。代入 (2,3) 得 dz=3×0.1+2×(-0.2)=0.3-0.4=-0.1。",
        3,
    ),
    q(
        "多元函数微分学",
        "二阶偏导",
        "设 z=x^3y^2，则 ∂²z/(∂y∂x) 为：",
        {"A": "3x^2y^2", "B": "6x^2y", "C": "6xy^2", "D": "x^3y"},
        "B",
        "先对 x 求偏导得 z_x=3x^2y^2，再对 y 求偏导得 z_xy=6x^2y。",
        3,
    ),
    q(
        "多元函数微分学",
        "二阶偏导",
        "设 z=sin(xy)，则 ∂²z/(∂y∂x) 为：",
        {"A": "cos(xy)-xy sin(xy)", "B": "cos(xy)+xy sin(xy)", "C": "y cos(xy)", "D": "-xy cos(xy)"},
        "A",
        "先求 z_x=y cos(xy)，再对 y 求导：cos(xy)+y·[-sin(xy)·x]=cos(xy)-xy sin(xy)。",
        4,
    ),
    q(
        "多元函数微分学",
        "链导法则",
        "设 z=u^2+v，u=x+y，v=xy，则 ∂z/∂x 为：",
        {"A": "2x+y", "B": "2x+3y", "C": "2(x+y)+y", "D": "x+2y"},
        "C",
        "z_u=2u，u_x=1，z_v=1，v_x=y，所以 z_x=2u·1+1·y=2(x+y)+y。",
        4,
    ),
    q(
        "多元函数微分学",
        "链导法则",
        "设 z=e^u，u=x^2+y^2，则 ∂z/∂x 为：",
        {"A": "e^(x^2+y^2)", "B": "2xe^(x^2+y^2)", "C": "2ye^(x^2+y^2)", "D": "(x^2+y^2)e^u"},
        "B",
        "z_x=e^u·u_x=e^(x^2+y^2)·2x=2xe^(x^2+y^2)。",
        3,
    ),
    q(
        "多元函数微分学",
        "隐函数求导",
        "由方程 x^2+y^2=1 确定 y=y(x)，则 dy/dx 为：",
        {"A": "x/y", "B": "-x/y", "C": "-y/x", "D": "y/x"},
        "B",
        "两边对 x 求导：2x+2y y'=0，故 y'=-x/y。",
        3,
    ),
    q(
        "多元函数微分学",
        "隐函数求导",
        "由方程 e^y+xy=1 确定 y=y(x)，则 dy/dx 为：",
        {"A": "-y/(e^y+x)", "B": "y/(e^y+x)", "C": "-x/(e^y+y)", "D": "-e^y/x"},
        "A",
        "两边对 x 求导：e^y y'+y+xy'=0，即 (e^y+x)y'=-y，所以 y'=-y/(e^y+x)。",
        4,
    ),
    q(
        "多元函数微分学",
        "二元函数极值",
        "函数 f(x,y)=x^2+y^2-2x+4y 的极值点为：",
        {"A": "(1,-2)，极小值点", "B": "(-1,2)，极小值点", "C": "(1,2)，极大值点", "D": "(0,0)，鞍点"},
        "A",
        "令 f_x=2x-2=0 得 x=1，f_y=2y+4=0 得 y=-2。Hessian 为正定矩阵，所以是极小值点。",
        3,
    ),
    q(
        "多元函数微分学",
        "二元函数极值",
        "函数 f(x,y)=x^2-y^2 在 (0,0) 处为：",
        {"A": "极大值", "B": "极小值", "C": "鞍点", "D": "不可判定且不是驻点"},
        "C",
        "沿 x 轴 f=x^2≥0，沿 y 轴 f=-y^2≤0，函数值在任意邻域内有正有负，因此 (0,0) 为鞍点。",
        3,
    ),
    q(
        "多元函数微分学",
        "二元函数极值",
        "函数 f(x,y)=x^2+xy+y^2 在 (0,0) 处为：",
        {"A": "极大值", "B": "极小值", "C": "鞍点", "D": "不存在驻点"},
        "B",
        "Hessian 矩阵为 [[2,1],[1,2]]，其主子式 2>0、行列式 3>0，正定，所以 (0,0) 为极小值点。",
        4,
    ),
]


def build_review(questions: list[dict]) -> str:
    module_counts = Counter(item["module"] for item in questions)
    submodule_counts = Counter((item["module"], item["submodule"]) for item in questions)
    difficulty_counts = Counter(item["difficulty"] for item in questions)

    lines = [
        "# Z002 数学基础 微积分选择题 批次 002",
        "",
        "本批次继续围绕港澳台考研 Z002 综合能力（二）数学基础范围生成，难度较 batch 001 提升，重点覆盖复合求导、等价无穷小、变限定积分、分部积分、二阶偏导、隐函数求导和二元函数极值判别。",
        "题目全部为四选一选择题，不包含线性代数、概率统计、级数、二重积分、微分方程和空间解析几何。",
        "",
        f"- 总题数：{len(questions)}",
        "- exam_code：Z002",
        "- subject：数学基础",
        "- source_type：ai_generated",
        "- source_year：2026",
        "",
        "## 模块分布",
    ]

    for module, count in module_counts.items():
        lines.append(f"- {module}：{count} 题")

    lines.extend(["", "## 子模块分布"])
    for (module, submodule), count in submodule_counts.items():
        lines.append(f"- {module} / {submodule}：{count} 题")

    lines.extend(["", "## 难度分布"])
    for difficulty in sorted(difficulty_counts):
        label = "中等" if difficulty == 3 else "中等偏上"
        lines.append(f"- 难度 {difficulty}（{label}）：{difficulty_counts[difficulty]} 题")

    return "\n".join(lines) + "\n"


def main() -> int:
    existing = load_existing_stems()
    seen: set[str] = set()
    duplicates: list[str] = []
    for item in QUESTIONS:
        key = normalize_stem(item["stem"])
        if key in seen or key in existing:
            duplicates.append(item["stem"])
        seen.add(key)

    if duplicates:
        print("Duplicate stems found. Generation aborted.")
        for stem in duplicates[:20]:
            print(f"  - {stem}")
        return 1

    OUTPUT_PATH.write_text(
        json.dumps({"questions": QUESTIONS}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REVIEW_PATH.write_text(build_review(QUESTIONS), encoding="utf-8")
    print(f"Generated {len(QUESTIONS)} questions -> {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Generated review -> {REVIEW_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
