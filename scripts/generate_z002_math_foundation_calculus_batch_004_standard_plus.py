from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "z002_math_foundation_calculus_batch_004_standard_plus.json"
REVIEW_PATH = PROJECT_ROOT / "data" / "z002_math_foundation_calculus_batch_004_standard_plus_review.md"

KNOWLEDGE_TREE = {
    "一元函数微分学": [
        "极限",
        "连续",
        "导数",
        "微分",
        "高阶导数",
        "洛必达法则",
        "单调性",
        "极值与最值",
        "凹凸性",
        "拐点",
        "渐近线",
    ],
    "一元函数积分学": [
        "原函数",
        "定积分",
        "变限定积分",
        "牛顿-莱布尼兹公式",
        "换元积分",
        "分部积分",
        "几何应用",
        "物理应用",
    ],
    "多元函数微分学": ["偏导数", "全微分", "二阶偏导", "链导法则", "隐函数求导", "二元函数极值"],
}

BAD_STEM_PATTERNS = [
    re.compile(r"题干若|题目若|若考查|若考察|知识点归类|依据.*考纲|考试大纲"),
    re.compile(r"\\lim|\\to|\\int|\\sqrt|\\sin|\\cos|\$"),
]


def normalize_stem(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"\s+", "", text)
    return text.strip().lower()


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
            if isinstance(item, dict) and item.get("subject") == "数学基础":
                stems.add(normalize_stem(item.get("stem", "")))
    return stems


def q(
    module: str,
    submodule: str,
    stem: str,
    options: list[str],
    answer: str,
    explanation: str,
    difficulty: int,
) -> dict:
    return {
        "exam_code": "Z002",
        "subject": "数学基础",
        "module": module,
        "submodule": submodule,
        "question_type": "single_choice",
        "stem": stem,
        "option_a": options[0],
        "option_b": options[1],
        "option_c": options[2],
        "option_d": options[3],
        "answer": answer,
        "explanation": explanation,
        "difficulty": difficulty,
        "source_type": "ai_generated",
        "source_year": 2026,
        "passage_id": None,
    }


RAW_QUESTIONS = [
    q("一元函数微分学", "极限", "lim(x→0) [sin 2x-2sin x]/x^3 的值为：", ["-1", "1", "-1/2", "0"], "A", "把 sin 2x 和 sin x 在 0 附近展开：sin 2x=2x-8x^3/6+o(x^3)，2sin x=2x-2x^3/6+o(x^3)，相减得 -x^3+o(x^3)，所以极限为 -1。", 4),
    q("一元函数微分学", "极限", "lim(x→0) [e^x-1-x]/x^2 的值为：", ["1", "1/2", "0", "不存在"], "B", "e^x=1+x+x^2/2+o(x^2)，分子主项是 x^2/2，除以 x^2 后极限为 1/2。", 3),
    q("一元函数微分学", "极限", "lim(x→0) [1-cos 3x]/x^2 的值为：", ["3/2", "3", "9/2", "9"], "C", "利用 1-cos u 与 u^2/2 等价，令 u=3x，则 1-cos 3x 与 9x^2/2 等价，所以极限为 9/2。", 3),
    q("一元函数微分学", "极限", "lim(x→0) [tan x-sin x]/x^3 的值为：", ["1/6", "1/2", "1/3", "0"], "B", "tan x=x+x^3/3+o(x^3)，sin x=x-x^3/6+o(x^3)，相减得 x^3/2+o(x^3)，所以极限为 1/2。", 4),
    q("一元函数微分学", "极限", "lim(x→0) [ln(1+x)-x+x^2/2]/x^3 的值为：", ["1/2", "1/3", "-1/3", "0"], "B", "ln(1+x)=x-x^2/2+x^3/3+o(x^3)，代入后分子主项为 x^3/3，极限为 1/3。", 4),
    q("一元函数微分学", "连续", "设 f(x)=a sin x/x(x≠0)，f(0)=2。若 f 在 x=0 连续，则 a 的值为：", ["1", "2", "1/2", "0"], "B", "当 x→0 时 sin x/x→1，所以 f(x) 的极限为 a。连续要求极限等于 f(0)=2，因此 a=2。", 3),
    q("一元函数微分学", "连续", "设 f(x)=(e^x-1)/x(x≠0)，f(0)=a。若 f 在 x=0 连续，则 a 的值为：", ["0", "1", "e", "不存在"], "B", "由 e^x-1 与 x 等价可知 x→0 时 (e^x-1)/x→1。连续要求 a=1。", 3),
    q("一元函数微分学", "连续", "设 f(x)=[√(1+x)-1]/x(x≠0)，f(0)=a。若 f 在 x=0 连续，则 a 的值为：", ["1", "1/2", "2", "0"], "B", "分子有理化得 [√(1+x)-1]/x=1/[√(1+x)+1]，令 x→0 得 1/2。", 3),
    q("一元函数微分学", "导数", "函数 y=x^2 ln x 在 x=e 处的导数为：", ["e", "2e", "3e", "e^2"], "C", "y'=2x ln x+x。代入 x=e，得 y'(e)=2e+e=3e。", 3),
    q("一元函数微分学", "导数", "函数 y=sin x/x 在 x=π 处的导数为：", ["-1/π", "1/π", "-1/π^2", "0"], "A", "商法则得 y'=(x cos x-sin x)/x^2。代入 x=π，cos π=-1，sin π=0，所以 y'(π)=-1/π。", 4),
    q("一元函数微分学", "导数", "函数 y=ln x/x 在 (0,+∞) 上取得最大值时，x 的值为：", ["1", "e", "e^2", "不存在"], "B", "y'=(1-ln x)/x^2。令 y'=0 得 x=e，且导数在 e 前为正、e 后为负，所以最大值点为 x=e。", 4),
    q("一元函数微分学", "导数", "函数 y=e^(x^2) sin x 在 x=0 处的导数为：", ["0", "1", "2", "-1"], "B", "用乘积法则：y'=e^(x^2)·2x sin x+e^(x^2)cos x。代入 x=0 得 0+1=1。", 3),
    q("一元函数微分学", "导数", "函数 y=x^x 在 x=e 处的导数为：", ["e^e", "2e^e", "e^(e+1)", "0"], "B", "对数求导得 y'=x^x(ln x+1)。代入 x=e，ln e=1，所以 y'(e)=2e^e。", 4),
    q("一元函数微分学", "微分", "若 y=ln(1+x^2)，当 x=1、dx=0.02 时，dy 等于：", ["0.01", "0.02", "0.04", "0.1"], "B", "dy=y'dx，y'=2x/(1+x^2)。在 x=1 时 y'=1，因此 dy=0.02。", 3),
    q("一元函数微分学", "微分", "若 y=√x，当 x=4、dx=0.1 时，dy 等于：", ["0.01", "0.025", "0.05", "0.1"], "B", "y'=1/(2√x)，在 x=4 时 y'=1/4，所以 dy=(1/4)×0.1=0.025。", 3),
    q("一元函数微分学", "高阶导数", "函数 y=sin 2x 的三阶导数在 x=0 处的值为：", ["8", "-8", "0", "4"], "B", "y'=2cos2x，y''=-4sin2x，y'''=-8cos2x。代入 x=0 得 -8。", 3),
    q("一元函数微分学", "高阶导数", "函数 y=e^x cos x 的二阶导数在 x=π/2 处的值为：", ["0", "2e^(π/2)", "-2e^(π/2)", "-e^(π/2)"], "C", "y'=e^x(cos x-sin x)，y''=-2e^x sin x。代入 x=π/2，得 -2e^(π/2)。", 4),
    q("一元函数微分学", "高阶导数", "函数 y=ln(1+x) 的三阶导数在 x=0 处的值为：", ["1", "-1", "2", "-2"], "C", "y'=1/(1+x)，y''=-1/(1+x)^2，y'''=2/(1+x)^3，所以 y'''(0)=2。", 4),
    q("一元函数微分学", "洛必达法则", "lim(x→0) (x-sin x)/x^3 的值为：", ["1/6", "-1/6", "1/2", "0"], "A", "这是 0/0 型极限。也可用展开 sin x=x-x^3/6+o(x^3)，故 x-sin x=x^3/6+o(x^3)，极限为 1/6。", 4),
    q("一元函数微分学", "洛必达法则", "lim(x→∞) x[ln(x+1)-ln x] 的值为：", ["0", "1", "∞", "不存在"], "B", "原式等于 ln(1+1/x)/(1/x)。令 t=1/x，则 t→0，变为 ln(1+t)/t，极限为 1。", 4),
    q("一元函数微分学", "洛必达法则", "lim(x→0) [e^(2x)-1]/sin 3x 的值为：", ["2/3", "3/2", "2", "0"], "A", "分子、分母都趋于 0。用等价无穷小 e^(2x)-1 与 2x 等价，sin 3x 与 3x 等价，所以极限为 2/3。", 3),
    q("一元函数微分学", "单调性", "函数 f(x)=x^3-3x 的单调递增区间为：", ["(-∞,-1)∪(1,+∞)", "(-1,1)", "(-∞,1)", "(1,+∞)"], "A", "f'(x)=3x^2-3=3(x-1)(x+1)。当 x<-1 或 x>1 时 f'(x)>0，所以函数递增。", 3),
    q("一元函数微分学", "单调性", "函数 f(x)=x+1/x 在 (0,+∞) 上的单调性为：", ["一直递增", "一直递减", "先减后增", "先增后减"], "C", "f'(x)=1-1/x^2。当 0<x<1 时 f'<0，当 x>1 时 f'>0，所以先减后增。", 3),
    q("一元函数微分学", "单调性", "函数 f(x)=ln x-x 在 (0,+∞) 上的单调性为：", ["先增后减", "先减后增", "一直递增", "一直递减"], "A", "f'(x)=1/x-1=(1-x)/x。0<x<1 时 f'>0，x>1 时 f'<0，所以先增后减。", 3),
    q("一元函数微分学", "极值与最值", "函数 f(x)=x^3-3x^2+1 的局部最小值为：", ["1", "-3", "0", "不存在"], "B", "f'(x)=3x(x-2)。x=2 处导数由负变正，是局部最小点，f(2)=8-12+1=-3。", 4),
    q("一元函数微分学", "极值与最值", "函数 f(x)=x^4-4x^2 的最小值为：", ["0", "-2", "-4", "不存在"], "C", "f'(x)=4x(x^2-2)，驻点为 0、±√2。代入得 f(±√2)=4-8=-4，且四次函数开口向上，最小值为 -4。", 4),
    q("一元函数微分学", "凹凸性", "函数 f(x)=x^3-3x^2 的拐点横坐标为：", ["0", "1", "2", "不存在"], "B", "f''(x)=6x-6。令 f''(x)=0 得 x=1，且二阶导数在该点左右变号，所以拐点横坐标为 1。", 3),
    q("一元函数微分学", "凹凸性", "函数 f(x)=ln x 在 (0,+∞) 上的凹凸性为：", ["上凸", "下凸", "先上凸后下凸", "无法判断"], "A", "f''(x)=-1/x^2<0，因此曲线在 (0,+∞) 上向下弯，即通常称为上凸。", 3),
    q("一元函数微分学", "拐点", "函数 f(x)=x^4-4x^3 的拐点横坐标为：", ["0", "2", "0 和 2", "不存在"], "C", "f''(x)=12x^2-24x=12x(x-2)。在 x=0 附近二阶导数由正变负，在 x=2 附近由负变正，因此两个点都对应拐点横坐标。", 4),
    q("一元函数微分学", "渐近线", "曲线 y=(2x+1)/(x-1) 的水平渐近线为：", ["x=1", "y=1", "y=2", "不存在"], "C", "分子分母同为一次，水平渐近线等于最高次项系数之比，即 y=2。", 3),
    q("一元函数积分学", "原函数", "不定积分 ∫ x e^(x^2) dx 等于：", ["e^(x^2)+C", "1/2 e^(x^2)+C", "2e^(x^2)+C", "x^2e^(x^2)+C"], "B", "令 u=x^2，则 du=2x dx，所以 ∫x e^(x^2)dx=1/2∫e^u du=1/2 e^(x^2)+C。", 3),
    q("一元函数积分学", "原函数", "不定积分 ∫(2x+1)/(x^2+x+1) dx 等于：", ["ln(x^2+x+1)+C", "2ln(x^2+x+1)+C", "1/(x^2+x+1)+C", "x^2+x+1+C"], "A", "分母的导数正好是 2x+1，因此积分为 ln(x^2+x+1)+C。", 3),
    q("一元函数积分学", "原函数", "不定积分 ∫cos(3x+1)dx 等于：", ["sin(3x+1)+C", "1/3 sin(3x+1)+C", "3sin(3x+1)+C", "-1/3 sin(3x+1)+C"], "B", "对 sin(3x+1) 求导会多出因子 3，所以原函数应乘 1/3。", 3),
    q("一元函数积分学", "定积分", "定积分 ∫_0^1 (3x^2+2x) dx 的值为：", ["1", "2", "3", "4"], "B", "原函数为 x^3+x^2，代入 0 到 1 得 1+1=2。", 3),
    q("一元函数积分学", "定积分", "定积分 ∫_0^(π/2) sin x cos x dx 的值为：", ["1", "1/2", "0", "π/4"], "B", "令 u=sin x，则 du=cos x dx，上限由 0 到 1，积分为 ∫_0^1 u du=1/2。", 3),
    q("一元函数积分学", "定积分", "定积分 ∫_-1^1 (x^3+x) dx 的值为：", ["0", "1", "2", "-1"], "A", "x^3+x 是奇函数，在对称区间 [-1,1] 上积分为 0。", 3),
    q("一元函数积分学", "定积分", "定积分 ∫_-1^1 (x^2+1) dx 的值为：", ["2", "4/3", "8/3", "3"], "C", "x^2+1 是偶函数，积分为 2∫_0^1(x^2+1)dx=2(1/3+1)=8/3。", 3),
    q("一元函数积分学", "变限定积分", "设 F(x)=∫_0^x cos(t^2)dt，则 F'(x) 等于：", ["cos x", "cos(x^2)", "2xcos(x^2)", "sin(x^2)"], "B", "由变上限积分求导公式，F'(x)=cos(x^2)。", 3),
    q("一元函数积分学", "变限定积分", "设 F(x)=∫_1^(x^2) ln t dt，则 F'(x) 等于：", ["ln x", "2xln x", "2xln(x^2)", "ln(x^2)"], "C", "上限是 x^2，按链式法则 F'(x)=ln(x^2)·2x。", 4),
    q("一元函数积分学", "变限定积分", "设 F(x)=∫_x^1 e^(t^2)dt，则 F'(x) 等于：", ["e^(x^2)", "-e^(x^2)", "2xe^(x^2)", "-2xe^(x^2)"], "B", "下限含 x，可写成 F(x)=-∫_1^x e^(t^2)dt，所以 F'(x)=-e^(x^2)。", 4),
    q("一元函数积分学", "变限定积分", "设 F(x)=∫_0^(sin x) √(1+t^2)dt，则 F'(x) 等于：", ["√(1+sin^2 x)", "cos x√(1+sin^2 x)", "sin x√(1+cos^2 x)", "cos x"], "B", "上限为 sin x，外层代入得 √(1+sin^2 x)，再乘上限导数 cos x。", 4),
    q("一元函数积分学", "牛顿-莱布尼兹公式", "定积分 ∫_1^e 1/x dx 的值为：", ["0", "1", "e", "ln 2"], "B", "1/x 的原函数为 ln x，所以 ∫_1^e 1/x dx=ln e-ln1=1。", 3),
    q("一元函数积分学", "牛顿-莱布尼兹公式", "若 F'(x)=f(x)，则 ∫_a^b f(x)dx 等于：", ["F(a)-F(b)", "F(b)-F(a)", "F(a)+F(b)", "f(b)-f(a)"], "B", "牛顿-莱布尼兹公式说明定积分等于原函数在上限和下限的差，即 F(b)-F(a)。", 3),
    q("一元函数积分学", "牛顿-莱布尼兹公式", "定积分 ∫_0^2 (3x^2-2x)dx 的值为：", ["2", "4", "6", "8"], "B", "原函数为 x^3-x^2，代入 0 到 2 得 8-4=4。", 3),
    q("一元函数积分学", "换元积分", "定积分 ∫_0^1 2x/(1+x^2) dx 的值为：", ["ln 2", "1/2 ln 2", "2ln 2", "1"], "A", "令 u=1+x^2，则 du=2x dx，上限从 1 到 2，积分为 ∫_1^2 1/u du=ln2。", 3),
    q("一元函数积分学", "换元积分", "定积分 ∫_0^1 x√(1+x^2)dx 的值为：", ["(2√2-1)/3", "(√2-1)/3", "2√2/3", "1"], "A", "令 u=1+x^2，du=2x dx，积分为 1/2∫_1^2 u^(1/2)du=(1/3)(2√2-1)。", 4),
    q("一元函数积分学", "换元积分", "定积分 ∫_0^(π/4) tan x dx 的值为：", ["ln2", "1/2 ln2", "-ln2", "0"], "B", "∫tan x dx=-ln|cos x|。代入 0 到 π/4 得 -ln(√2/2)=ln√2=1/2 ln2。", 4),
    q("一元函数积分学", "分部积分", "定积分 ∫_0^1 x e^x dx 的值为：", ["0", "1", "e-1", "e"], "B", "分部积分得 ∫x e^x dx=x e^x-e^x。代入 0 到 1 得 (e-e)-(-1)=1。", 4),
    q("一元函数积分学", "分部积分", "定积分 ∫_0^1 x ln x dx 的值为：", ["1/4", "-1/4", "-1/2", "0"], "B", "分部积分或利用公式 ∫x^a ln x dx=-1/(a+1)^2。取 a=1，结果为 -1/4。", 4),
    q("一元函数积分学", "分部积分", "不定积分 ∫x sin x dx 等于：", ["xcos x+sin x+C", "-xcos x+sin x+C", "-xsin x+cos x+C", "xsin x+cos x+C"], "B", "取 u=x，dv=sin x dx，则 v=-cos x，故 ∫xsinx dx=-xcosx+∫cosx dx=-xcosx+sinx+C。", 3),
    q("一元函数积分学", "几何应用", "曲线 y=x 与 y=x^2 在 [0,1] 围成图形的面积为：", ["1/2", "1/3", "1/6", "2/3"], "C", "在 [0,1] 上 x≥x^2，面积为 ∫_0^1(x-x^2)dx=1/2-1/3=1/6。", 3),
    q("一元函数积分学", "几何应用", "曲线 y=√x 与 x 轴、直线 x=4 围成的面积为：", ["4", "16/3", "8/3", "2"], "B", "面积为 ∫_0^4√x dx=(2/3)x^(3/2)|_0^4=16/3。", 3),
    q("一元函数积分学", "几何应用", "曲线 y=4-x^2 与 x 轴在 [0,2] 围成的面积为：", ["8", "16/3", "4", "32/3"], "B", "面积为 ∫_0^2(4-x^2)dx=8-8/3=16/3。", 3),
    q("一元函数积分学", "物理应用", "质点速度 v(t)=3t^2-2t，0≤t≤2，则位移为：", ["2", "4", "6", "8"], "B", "位移为速度积分：∫_0^2(3t^2-2t)dt=t^3-t^2|_0^2=4。", 3),
    q("一元函数积分学", "物理应用", "质点速度 v(t)=t+1，0≤t≤3，则路程为：", ["9/2", "15/2", "6", "3"], "B", "该速度在区间内恒为正，路程等于 ∫_0^3(t+1)dt=9/2+3=15/2。", 3),
    q("一元函数积分学", "物理应用", "质点加速度 a(t)=2，初速度 v(0)=1，0≤t≤2 的位移为：", ["4", "5", "6", "8"], "C", "先积分得速度 v(t)=2t+1，再求位移 ∫_0^2(2t+1)dt=4+2=6。", 4),
    q("一元函数积分学", "定积分", "函数 f(x)=x^2 在 [0,3] 上的平均值为：", ["1", "2", "3", "9"], "C", "平均值为 1/(3-0)·∫_0^3x^2dx=1/3·9=3。", 3),
    q("多元函数微分学", "偏导数", "设 z=x^2y+sin y，则 ∂z/∂x 等于：", ["2xy", "x^2+cos y", "2x+y", "x^2y"], "A", "对 x 求偏导时 y 看作常数，x^2y 对 x 的偏导为 2xy，sin y 的偏导为 0。", 3),
    q("多元函数微分学", "偏导数", "设 z=e^(xy)，则 ∂z/∂y 等于：", ["xe^(xy)", "ye^(xy)", "e^(xy)", "xye^(xy)"], "A", "对 y 求偏导时 x 是常数，xy 对 y 的导数为 x，因此 ∂z/∂y=xe^(xy)。", 3),
    q("多元函数微分学", "偏导数", "设 z=ln(x^2+y^2)，则 ∂z/∂x 等于：", ["x/(x^2+y^2)", "2x/(x^2+y^2)", "2y/(x^2+y^2)", "1/(x^2+y^2)"], "B", "由复合函数求导，∂/∂x ln(x^2+y^2)=1/(x^2+y^2)·2x。", 3),
    q("多元函数微分学", "偏导数", "设 z=x/y，则 ∂z/∂y 等于：", ["1/y", "-x/y^2", "x/y^2", "-1/y"], "B", "把 x 看作常数，x/y=x·y^(-1)，对 y 求导得 -x/y^2。", 3),
    q("多元函数微分学", "全微分", "设 z=x^2y+xy^2，则 dz 等于：", ["(2xy+y^2)dx+(x^2+2xy)dy", "(x^2+y^2)dx+2xydy", "2xydx+x^2dy", "(2x+y)dx+(x+2y)dy"], "A", "先求偏导：z_x=2xy+y^2，z_y=x^2+2xy，所以 dz=z_xdx+z_ydy。", 4),
    q("多元函数微分学", "全微分", "设 z=e^(x+y)，在 (0,0) 处 dx=0.1，dy=-0.02，则 dz 约为：", ["0.08", "0.12", "-0.08", "0"], "A", "z_x=z_y=e^(x+y)，在 (0,0) 处均为 1，所以 dz=dx+dy=0.08。", 3),
    q("多元函数微分学", "全微分", "设 z=ln(xy)，则 dz 等于：", ["dx/x+dy/y", "dx/y+dy/x", "xdy+ydx", "dx+dy"], "A", "z=lnx+lny，因此 dz=(1/x)dx+(1/y)dy。", 3),
    q("多元函数微分学", "全微分", "设 z=x^2+y^2，在点 (3,4) 处 dx=0.01，dy=-0.02，则 dz 等于：", ["0.10", "-0.10", "0.22", "-0.22"], "B", "dz=2xdx+2ydy。在 (3,4) 处 dz=6×0.01+8×(-0.02)=0.06-0.16=-0.10。", 4),
    q("多元函数微分学", "二阶偏导", "设 z=x^2y^3，则 ∂²z/(∂y∂x) 等于：", ["2xy^3", "6xy^2", "3x^2y^2", "6x^2y"], "B", "先对 x 求偏导得 z_x=2xy^3，再对 y 求偏导，得 z_xy=6xy^2。", 3),
    q("多元函数微分学", "二阶偏导", "设 z=sin(xy)，则 ∂²z/(∂y∂x) 等于：", ["cos(xy)-xy sin(xy)", "xy cos(xy)", "-sin(xy)", "cos(xy)"], "A", "先求 z_x=ycos(xy)，再对 y 求导：cos(xy)+y[-sin(xy)·x]=cos(xy)-xy sin(xy)。", 5),
    q("多元函数微分学", "二阶偏导", "设 z=x^3+y^3-3xy，则 z_xy 等于：", ["6x", "6y", "-3", "3"], "C", "z_x=3x^2-3y，再对 y 求偏导，得到 z_xy=-3。", 3),
    q("多元函数微分学", "链导法则", "设 z=f(u,v)，u=x+y，v=x-y，则 ∂z/∂x 等于：", ["f_u+f_v", "f_u-f_v", "xf_u+yf_v", "f_u f_v"], "A", "由链式法则，z_x=f_u·u_x+f_v·v_x=f_u+f_v。", 4),
    q("多元函数微分学", "链导法则", "设 z=e^u，u=xy，则 ∂z/∂x 等于：", ["xe^(xy)", "ye^(xy)", "e^(xy)", "xye^(xy)"], "B", "z=e^(xy)，对 x 求偏导时 y 是常数，故 ∂z/∂x=ye^(xy)。", 3),
    q("多元函数微分学", "链导法则", "设 z=ln(u^2+v^2)，u=x，v=y^2，则 ∂z/∂y 等于：", ["2y/(x^2+y^4)", "4y^3/(x^2+y^4)", "2x/(x^2+y^4)", "1/(x^2+y^4)"], "B", "z=ln(x^2+y^4)，对 y 求导得 1/(x^2+y^4)·4y^3。", 5),
    q("多元函数微分学", "链导法则", "设 z=sin(x^2+y)，则 ∂z/∂x 等于：", ["cos(x^2+y)", "2xcos(x^2+y)", "2xsin(x^2+y)", "-2xcos(x^2+y)"], "B", "外层 sin 的导数是 cos，内层 x^2+y 对 x 的导数是 2x，所以 ∂z/∂x=2xcos(x^2+y)。", 3),
    q("多元函数微分学", "隐函数求导", "由方程 x^2+y^2=1 确定 y=y(x)，则 dy/dx 等于：", ["x/y", "-x/y", "y/x", "-y/x"], "B", "两边对 x 求导：2x+2yy'=0，因此 y'=-x/y。", 3),
    q("多元函数微分学", "隐函数求导", "由方程 e^y+xy=1 确定 y=y(x)，则 dy/dx 等于：", ["-y/(e^y+x)", "y/(e^y+x)", "-x/(e^y+y)", "1/(e^y+x)"], "A", "两边求导：e^y y'+y+xy'=0，整理得 (e^y+x)y'=-y，所以 y'=-y/(e^y+x)。", 4),
    q("多元函数微分学", "隐函数求导", "由方程 xy+ln y=x^2 确定 y=y(x)，则 dy/dx 等于：", ["(2x-y)/(x+1/y)", "(2x+y)/(x+1/y)", "(y-2x)/(x+1/y)", "2x-y"], "A", "两边求导：y+xy'+y'/y=2x，整理得 (x+1/y)y'=2x-y。", 5),
    q("多元函数微分学", "隐函数求导", "由方程 y^2=x+y 确定 y=y(x)，则 dy/dx 等于：", ["1/(2y-1)", "1/(2y+1)", "2y-1", "2y+1"], "A", "两边求导得 2yy'=1+y'，因此 (2y-1)y'=1，故 y'=1/(2y-1)。", 4),
    q("多元函数微分学", "二元函数极值", "函数 f(x,y)=x^2+y^2 的极值情况为：", ["在 (0,0) 取得极小值", "在 (0,0) 取得极大值", "(0,0) 为鞍点", "无驻点"], "A", "梯度为 (2x,2y)，驻点为 (0,0)。函数值非负且只在 (0,0) 为 0，所以该点为极小值点。", 3),
    q("多元函数微分学", "二元函数极值", "函数 f(x,y)=x^2-y^2 在 (0,0) 的性质为：", ["极小值点", "极大值点", "鞍点", "无法判断"], "C", "沿 x 轴 f=x^2≥0，沿 y 轴 f=-y^2≤0，邻域内既有正值又有负值，所以 (0,0) 是鞍点。", 4),
    q("多元函数微分学", "二元函数极值", "函数 f(x,y)=x^2+xy+y^2 在 (0,0) 的性质为：", ["极小值点", "极大值点", "鞍点", "不是驻点"], "A", "二阶偏导 f_xx=2，f_yy=2，f_xy=1，判别式 D=2×2-1^2=3>0 且 f_xx>0，所以是极小值点。", 4),
    q("多元函数微分学", "二元函数极值", "函数 f(x,y)=x^3+y^3-3xy 的局部极小值点为：", ["(0,0)", "(1,1)", "(0,1)", "(1,0)"], "B", "驻点由 3x^2-3y=0、3y^2-3x=0 得 (0,0)、(1,1)。在 (1,1) 处 D=6×6-(-3)^2=27>0 且 f_xx=6>0，故为局部极小值点。", 5),
    q("多元函数微分学", "二元函数极值", "函数 f(x,y)=x^2+4y^2-4x+8y 的极小值点为：", ["(2,-1)", "(-2,1)", "(2,1)", "(-2,-1)"], "A", "令 f_x=2x-4=0 得 x=2；f_y=8y+8=0 得 y=-1。二次型正定，所以 (2,-1) 为极小值点。", 3),
]


def validate(item: dict, index: int, seen: set[str], existing: set[str]) -> str | None:
    stem = item["stem"]
    normalized = normalize_stem(stem)
    if item["module"] not in KNOWLEDGE_TREE:
        raise ValueError(f"Question #{index} unknown module: {item['module']}")
    if item["submodule"] not in KNOWLEDGE_TREE[item["module"]]:
        raise ValueError(f"Question #{index} unknown submodule: {item['module']} / {item['submodule']}")
    if item["answer"] not in {"A", "B", "C", "D"}:
        raise ValueError(f"Question #{index} invalid answer: {item['answer']}")
    if not isinstance(item["difficulty"], int) or not 1 <= item["difficulty"] <= 5:
        raise ValueError(f"Question #{index} invalid difficulty: {item['difficulty']}")
    options = [item["option_a"], item["option_b"], item["option_c"], item["option_d"]]
    if len(set(options)) != 4:
        raise ValueError(f"Question #{index} has duplicated options: {stem}")
    if normalized in seen:
        raise ValueError(f"Question #{index} duplicated in this batch: {stem}")
    for pattern in BAD_STEM_PATTERNS:
        if pattern.search(stem):
            raise ValueError(f"Question #{index} has low-quality/raw stem: {stem}")
    seen.add(normalized)
    if normalized in existing:
        return "skip_existing"
    return None


def main() -> None:
    existing = load_existing_stems()
    seen: set[str] = set()
    questions = []
    skipped = 0

    for index, item in enumerate(RAW_QUESTIONS, start=1):
        result = validate(item, index, seen, existing)
        if result == "skip_existing":
            skipped += 1
            continue
        questions.append(item)

    payload = {"questions": questions}
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    difficulty_counts = Counter(q["difficulty"] for q in questions)
    module_counts = Counter(q["module"] for q in questions)
    submodule_counts = Counter(f"{q['module']} / {q['submodule']}" for q in questions)

    lines = [
        "# Z002 数学基础 batch 004 质检",
        "",
        f"- 文件：`{OUTPUT_PATH.name}`",
        f"- 题量：{len(questions)}",
        f"- 跳过已存在题干：{skipped}",
        "- 定位：标准卷偏中等补强，重点提高微积分题目的综合性和选项干扰度。",
        "- 公式策略：使用 `lim(x→0)`、`∫_0^1`、`x^2`、`1/x` 等可被前端 MathText 渲染的写法。",
        "",
        "## 难度分布",
        "",
    ]
    for difficulty, count in sorted(difficulty_counts.items()):
        lines.append(f"- difficulty {difficulty}: {count} 题")
    lines.extend(["", "## 模块分布", ""])
    for module, count in module_counts.most_common():
        lines.append(f"- {module}: {count} 题")
    lines.extend(["", "## 子模块分布", ""])
    for submodule, count in submodule_counts.most_common():
        lines.append(f"- {submodule}: {count} 题")

    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(questions)} questions to {OUTPUT_PATH}")
    print(f"Wrote review to {REVIEW_PATH}")


if __name__ == "__main__":
    main()
