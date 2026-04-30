from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "z002_math_foundation_calculus_batch_001.json"
REVIEW_PATH = PROJECT_ROOT / "data" / "z002_math_foundation_calculus_batch_001_review.md"


SUBMODULES = {
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

INTERMEDIATE_SUBMODULES = {
    "洛必达法则",
    "极值与最值",
    "凹凸性",
    "拐点",
    "渐近线",
    "分部积分",
    "几何应用",
    "物理应用",
    "二阶偏导",
    "链导法则",
    "隐函数求导",
    "二元函数极值",
}

MODULE_METHODS = {
    "一元函数微分学": "解这类题时，先确定函数所在知识点，再用导数、二阶导数或极限公式进行判断，避免只凭图像直觉作答。",
    "一元函数积分学": "解这类题时，先判断是直接积分、换元、分部积分还是定积分应用，再按公式代入上下限或写出原函数。",
    "多元函数微分学": "解这类题时，要分清对哪个变量求导，其他变量暂作常数；遇到复合或隐函数时再使用链式法则。",
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
            stem = item.get("stem") if isinstance(item, dict) else None
            if isinstance(stem, str):
                stems.add(normalize_stem(stem))
    return stems


def make_options(correct: str, distractors: list[str], rng: random.Random) -> tuple[dict[str, str], str]:
    values: list[str] = []
    for value in [correct, *distractors]:
        if value not in values:
            values.append(value)
    if len(values) != 4:
        raise ValueError(f"Expected 4 unique options, got {values}")
    rng.shuffle(values)
    labels = ["A", "B", "C", "D"]
    options = dict(zip(labels, values))
    answer = next(label for label, value in options.items() if value == correct)
    return options, answer


def q(
    module: str,
    submodule: str,
    stem: str,
    correct: str,
    distractors: list[str],
    explanation: str,
    rng: random.Random,
    difficulty: int | None = None,
) -> dict:
    options, answer = make_options(correct, distractors, rng)
    if difficulty is None:
        difficulty = 3 if submodule in INTERMEDIATE_SUBMODULES else 2
    detailed_explanation = (
        f"本题考查“{submodule}”这一基础考点。正确答案为 {answer}（{correct}）。"
        f"核心步骤：{explanation}"
        f"其余选项通常是把公式系数、符号、上下限或求导变量混淆后得到的干扰项。"
        f"{MODULE_METHODS[module]}"
    )
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
        "explanation": detailed_explanation,
        "difficulty": difficulty,
        "source_type": "ai_generated",
        "source_year": 2026,
        "passage_id": None,
    }


def build_limit_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "极限"
    specs = [
        ("lim(x->0) sin(3x)/x = ?", "3", ["1", "0", "1/3"], "利用基本极限 lim(u->0) sin u / u = 1，sin(3x)/x = 3·sin(3x)/(3x)，故极限为 3。"),
        ("lim(x->0) (1-cos x)/x^2 = ?", "1/2", ["1", "0", "2"], "基本等价无穷小 1-cos x ~ x^2/2，因此极限为 1/2。"),
        ("lim(x->2) (x^2-4)/(x-2) = ?", "4", ["2", "0", "不存在"], "分子因式分解为 (x-2)(x+2)，约去 x-2 后令 x=2，得 4。"),
        ("lim(x->0) (e^(2x)-1)/x = ?", "2", ["1", "0", "1/2"], "e^(2x)-1 ~ 2x，故原式极限为 2。"),
        ("lim(x->0) ln(1+3x)/x = ?", "3", ["1", "0", "1/3"], "ln(1+3x) ~ 3x，因此极限为 3。"),
        ("lim(x->∞) (2x^2+1)/(x^2-3) = ?", "2", ["1", "0", "不存在"], "分子分母同为二次项，极限等于最高次项系数比 2/1=2。"),
        ("lim(x->∞) (3x+1)/(2x-5) = ?", "3/2", ["2/3", "1", "0"], "一次分式在无穷远处的极限等于最高次项系数比，即 3/2。"),
        ("lim(x->0) tan x / x = ?", "1", ["0", "2", "不存在"], "tan x 与 x 为等价无穷小，故 tan x / x 的极限为 1。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_continuity_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "连续"
    specs = [
        ("设 f(x)=sin x / x (x≠0)，f(0)=a。若 f 在 x=0 连续，则 a=?", "1", ["0", "-1", "不存在"], "要使 x=0 处连续，应令 f(0)=lim(x->0) sin x/x=1。"),
        ("设 f(x)=(e^x-1)/x (x≠0)，f(0)=a。若 f 在 x=0 连续，则 a=?", "1", ["0", "e", "不存在"], "连续要求函数值等于极限，而 lim(x->0)(e^x-1)/x=1。"),
        ("设 f(x)=(x^2-1)/(x-1) (x≠1)，f(1)=a。若 f 在 x=1 连续，则 a=?", "2", ["1", "0", "不存在"], "约分得 x+1，令 x=1 得极限 2，因此 a=2。"),
        ("函数 f(x)=1/(x-1) 在下列哪一点连续？", "x=0", ["x=1", "x=1 的左邻域全部点", "不存在连续点"], "有理函数在分母不为 0 的点连续，x=0 时分母不为 0。"),
        ("若函数在 x=a 处连续，则下列说法正确的是：", "lim(x->a) f(x)=f(a)", ["只需左极限存在", "只需右极限存在", "f(a) 可以不存在"], "连续的定义要求函数值存在、极限存在且二者相等。"),
        ("设 f(x)=|x|。下列判断正确的是：", "f 在 x=0 连续", ["f 在 x=0 不连续", "f 在 x=0 没有极限", "f(0) 不存在"], "|x| 在全体实数上连续，尤其在 x=0 处左右极限均为 0。"),
        ("设 f(x)=x^2。下列判断正确的是：", "f 在任意实数处连续", ["只在 x=0 连续", "只在正数处连续", "在 x=1 不连续"], "多项式函数在其定义域内处处连续。"),
        ("若 lim(x->a-)f(x)=2，lim(x->a+)f(x)=3，则 f 在 x=a 处：", "不连续", ["一定连续", "只要 f(a)=2 就连续", "只要 f(a)=3 就连续"], "左右极限不相等，极限不存在，因此不可能连续。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_derivative_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "导数"
    specs = [
        ("函数 y=x^3-2x 在 x=1 处的导数为：", "1", ["-1", "3", "0"], "y'=3x^2-2，代入 x=1 得 3-2=1。"),
        ("函数 y=ln x 在 x=e 处的导数为：", "1/e", ["1", "e", "0"], "ln x 的导数为 1/x，代入 x=e 得 1/e。"),
        ("函数 y=e^(2x) 的导数为：", "2e^(2x)", ["e^(2x)", "e^x", "2e^x"], "复合函数求导，e^(2x) 的导数为 e^(2x)·2。"),
        ("函数 y=sqrt(x) 在 x=4 处的导数为：", "1/4", ["1/2", "2", "4"], "sqrt(x)=x^(1/2)，导数为 1/(2sqrt(x))，代入 x=4 得 1/4。"),
        ("函数 y=x^2 sin x 的导数为：", "2x sin x + x^2 cos x", ["2x cos x", "x^2 cos x", "2x sin x - x^2 cos x"], "利用乘积求导法则，(x^2)'sin x + x^2(sin x)'=2x sin x+x^2 cos x。"),
        ("函数 y=1/x 的导数为：", "-1/x^2", ["1/x^2", "ln x", "-ln x"], "1/x=x^(-1)，导数为 -x^(-2)，即 -1/x^2。"),
        ("函数 y=cos x 的导数为：", "-sin x", ["sin x", "cos x", "-cos x"], "基本导数公式：cos x 的导数为 -sin x。"),
        ("若 f'(a)>0，则 f 在 x=a 附近的切线斜率：", "为正", ["为负", "为零", "不存在"], "导数的几何意义是切线斜率，f'(a)>0 表示切线斜率为正。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_differential_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "微分"
    specs = [
        ("函数 y=x^2 在 x=3 处的微分 dy 为：", "6dx", ["3dx", "9dx", "2dx"], "dy=y'dx，y'=2x，代入 x=3 得 dy=6dx。"),
        ("函数 y=ln x 的微分 dy 为：", "(1/x)dx", ["x dx", "ln x dx", "e^x dx"], "微分公式 dy=y'dx，ln x 的导数为 1/x。"),
        ("函数 y=e^x 的微分 dy 为：", "e^x dx", ["x e^x dx", "e dx", "ln x dx"], "e^x 的导数仍为 e^x，因此 dy=e^x dx。"),
        ("函数 y=sin x 的微分 dy 为：", "cos x dx", ["sin x dx", "-sin x dx", "-cos x dx"], "dy=y'dx，sin x 的导数为 cos x。"),
        ("若 y=f(x)，则一阶微分 dy 等于：", "f'(x)dx", ["f(x)dx", "f''(x)dx", "dx/f'(x)"], "一阶微分的定义为 dy=f'(x)dx。"),
        ("用微分近似计算时，Δy 与 dy 的关系通常是：", "当 Δx 很小时，Δy≈dy", ["总有 Δy=0", "总有 dy=0", "二者无关"], "微分 dy 是函数增量 Δy 的线性主部，当自变量增量很小时可近似代替 Δy。"),
        ("函数 y=x^3 在 x=2 处的微分为：", "12dx", ["6dx", "8dx", "3dx"], "y'=3x^2，代入 x=2 得 y'=12，所以 dy=12dx。"),
        ("函数 y=1+x 的微分为：", "dx", ["0", "2dx", "x dx"], "y'=1，因此 dy=dx。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_higher_derivative_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "高阶导数"
    specs = [
        ("函数 y=x^4 的二阶导数为：", "12x^2", ["4x^3", "24x", "x^2"], "先求 y'=4x^3，再求 y''=12x^2。"),
        ("函数 y=sin x 的二阶导数为：", "-sin x", ["sin x", "cos x", "-cos x"], "y'=cos x，y''=-sin x。"),
        ("函数 y=e^(2x) 的三阶导数为：", "8e^(2x)", ["2e^(2x)", "4e^(2x)", "6e^(2x)"], "每求一次导数都乘以 2，三阶导数为 2^3 e^(2x)=8e^(2x)。"),
        ("函数 y=x^3 的二阶导数在 x=1 处为：", "6", ["3", "1", "0"], "y'=3x^2，y''=6x，代入 x=1 得 6。"),
        ("函数 y=ln x 的二阶导数为：", "-1/x^2", ["1/x", "1/x^2", "-1/x"], "y'=1/x，继续求导得 y''=-1/x^2。"),
        ("函数 y=cos x 的三阶导数为：", "sin x", ["-sin x", "cos x", "-cos x"], "y'=-sin x，y''=-cos x，y'''=sin x。"),
        ("函数 y=5x+1 的二阶导数为：", "0", ["5", "1", "x"], "一次函数的一阶导数为常数，二阶导数为 0。"),
        ("函数 y=x^5 的三阶导数为：", "60x^2", ["20x^3", "120x", "5x^4"], "依次求导：5x^4、20x^3、60x^2。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_lhopital_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "洛必达法则"
    specs = [
        ("用洛必达法则求 lim(x->0) (e^x-1)/x，结果为：", "1", ["0", "e", "不存在"], "该极限为 0/0 型，分子分母分别求导得 e^x/1，令 x=0 得 1。"),
        ("用洛必达法则求 lim(x->0) ln(1+x)/x，结果为：", "1", ["0", "-1", "不存在"], "0/0 型，求导得 [1/(1+x)]/1，令 x=0 得 1。"),
        ("用洛必达法则求 lim(x->0) sin x / x，结果为：", "1", ["0", "-1", "不存在"], "0/0 型，求导得 cos x/1，代入 x=0 得 1。"),
        ("用洛必达法则求 lim(x->0) (1-cos x)/x^2，结果为：", "1/2", ["1", "0", "2"], "连续两次洛必达，得 cos x/2，代入 x=0 为 1/2。"),
        ("用洛必达法则求 lim(x->∞) x/e^x，结果为：", "0", ["1", "∞", "不存在"], "∞/∞ 型，求导得 1/e^x，x->∞ 时趋于 0。"),
        ("用洛必达法则求 lim(x->0) tan x / x，结果为：", "1", ["0", "2", "不存在"], "0/0 型，求导得 sec^2 x，代入 x=0 得 1。"),
        ("用洛必达法则求 lim(x->0) (e^(2x)-1)/(3x)，结果为：", "2/3", ["3/2", "1", "0"], "0/0 型，求导得 2e^(2x)/3，代入 x=0 得 2/3。"),
        ("用洛必达法则求 lim(x->0) (x-sin x)/x^3，结果为：", "1/6", ["-1/6", "0", "1"], "连续求导三次，分子三阶导为 cos x，分母三阶导为 6，代入 x=0 得 1/6。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_monotonicity_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "单调性"
    specs = [
        ("函数 f(x)=x^2-4x 在哪个区间上单调递增？", "(2,+∞)", ["(-∞,2)", "(-∞,+∞)", "(0,2)"], "f'(x)=2x-4，当 x>2 时 f'(x)>0，函数单调递增。"),
        ("函数 f(x)=x^3-3x 的单调递减区间为：", "(-1,1)", ["(-∞,-1)", "(1,+∞)", "(-∞,+∞)"], "f'(x)=3x^2-3=3(x-1)(x+1)，在 (-1,1) 上小于 0。"),
        ("若函数 f 在区间 I 上恒有 f'(x)>0，则 f 在 I 上：", "单调递增", ["单调递减", "一定为常数", "一定有极大值"], "导数为正表示函数随 x 增大而增大。"),
        ("函数 f(x)=ln x 在其定义域上：", "单调递增", ["单调递减", "先增后减", "不单调"], "f'(x)=1/x，在 x>0 时恒为正。"),
        ("函数 f(x)=-x^2 在区间 (0,+∞) 上：", "单调递减", ["单调递增", "先减后增", "为常数"], "f'(x)=-2x，在 x>0 时为负，因此单调递减。"),
        ("函数 f(x)=e^x 在实数范围内：", "单调递增", ["单调递减", "不单调", "有最大值"], "f'(x)=e^x>0，所以在全体实数上单调递增。"),
        ("函数 f(x)=1/x 在区间 (0,+∞) 上：", "单调递减", ["单调递增", "为常数", "先增后减"], "f'(x)=-1/x^2<0，因此在正半轴上单调递减。"),
        ("判断函数单调性时，通常优先考察：", "一阶导数的符号", ["函数值是否为正", "二阶导数是否存在", "函数图像是否过原点"], "一阶导数符号直接反映函数在区间上的增减性。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_extreme_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "极值与最值"
    specs = [
        ("函数 f(x)=x^2-4x+1 的最小值为：", "-3", ["1", "0", "3"], "配方得 f(x)=(x-2)^2-3，因此最小值为 -3。"),
        ("函数 f(x)=x^3-3x 在 x=1 处取得：", "极小值", ["极大值", "最大值", "无极值"], "f'(x)=3x^2-3，x=1 附近导数由负变正，所以取得极小值。"),
        ("函数 f(x)=x^3-3x 在 x=-1 处取得：", "极大值", ["极小值", "最小值", "无极值"], "x=-1 附近导数由正变负，因此该点为极大值点。"),
        ("函数 f(x)=x^2 在区间 [-1,2] 上的最大值为：", "4", ["0", "1", "2"], "闭区间最值比较端点和驻点，f(-1)=1，f(0)=0，f(2)=4，最大值为 4。"),
        ("函数 f(x)=x^2 在区间 [-1,2] 上的最小值为：", "0", ["1", "2", "4"], "f'(x)=2x，驻点 x=0 属于区间，且 f(0)=0 为最小值。"),
        ("若 f'(a)=0 且 f'(x) 在 a 左右由正变负，则 f 在 a 处：", "取得极大值", ["取得极小值", "一定无极值", "一定为最小值"], "一阶导数由正变负，说明函数先增后减，故为极大值。"),
        ("若 f'(a)=0 且 f''(a)>0，则 f 在 a 处通常：", "取得极小值", ["取得极大值", "无极值", "不连续"], "二阶导数大于 0 表示图像局部开口向上，驻点通常为极小值点。"),
        ("求闭区间上连续函数最值时，应比较：", "端点值和驻点值", ["只比较端点值", "只比较导数值", "只比较二阶导数"], "闭区间最值定理下，实际求最值应比较区间端点和内部驻点处的函数值。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_concavity_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "凹凸性"
    specs = [
        ("函数 f(x)=x^3 在区间 (0,+∞) 上图像为：", "凹向上", ["凹向下", "直线", "不连续"], "f''(x)=6x，在 x>0 时大于 0，图像凹向上。"),
        ("函数 f(x)=ln x 在 (0,+∞) 上图像为：", "凹向下", ["凹向上", "先上后下", "无法判断"], "f''(x)=-1/x^2<0，因此图像凹向下。"),
        ("若 f''(x)>0，则函数图像通常：", "凹向上", ["凹向下", "单调递减", "不连续"], "二阶导数为正表示曲线弯曲方向向上。"),
        ("若 f''(x)<0，则函数图像通常：", "凹向下", ["凹向上", "一定递增", "一定有极小值"], "二阶导数为负表示曲线凹向下。"),
        ("函数 f(x)=x^2 的凹凸性为：", "在全实数上凹向上", ["在全实数上凹向下", "在 x=0 不连续", "无法判断"], "f''(x)=2>0，因此处处凹向上。"),
        ("函数 f(x)=-x^2 的凹凸性为：", "在全实数上凹向下", ["在全实数上凹向上", "只在 x>0 凹向上", "不具备凹凸性"], "f''(x)=-2<0，因此处处凹向下。"),
        ("判断函数凹凸性通常使用：", "二阶导数的符号", ["函数值大小", "一阶导数是否为零", "定义域长度"], "二阶导数符号是判断曲线凹凸性的常用依据。"),
        ("函数 f(x)=e^x 的图像在全实数上：", "凹向上", ["凹向下", "无凹凸性", "只在 x<0 凹向下"], "f''(x)=e^x>0，故处处凹向上。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_inflection_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "拐点"
    specs = [
        ("函数 f(x)=x^3 的拐点为：", "(0,0)", ["(1,1)", "(-1,-1)", "不存在"], "f''(x)=6x，在 x=0 两侧变号，因此 (0,0) 为拐点。"),
        ("函数 f(x)=x^4 是否有拐点？", "没有", ["有，(0,0)", "有，(1,1)", "有，(-1,1)"], "f''(x)=12x^2，在 x=0 两侧不变号，因此没有拐点。"),
        ("若 f''(x) 在 x=a 两侧变号，则图像在 x=a 处可能：", "有拐点", ["一定有极大值", "一定不连续", "一定有最小值"], "拐点反映凹凸性改变，常通过二阶导数变号判断。"),
        ("函数 f(x)=x^3-3x 的拐点横坐标为：", "0", ["1", "-1", "3"], "f''(x)=6x，令 f''(x)=0 得 x=0，且两侧变号。"),
        ("函数 f(x)=sin x 在 x=0 附近的拐点为：", "(0,0)", ["(π/2,1)", "(π,0)", "不存在"], "f''(x)=-sin x，在 x=0 两侧变号，且 f(0)=0。"),
        ("下列说法正确的是：", "拐点处凹凸性发生改变", ["拐点一定是极值点", "拐点处一阶导数一定不存在", "拐点处函数一定不连续"], "拐点的核心特征是曲线凹凸性改变，不一定是极值点。"),
        ("函数 f(x)=x^2 的拐点情况为：", "没有拐点", ["有一个拐点", "有两个拐点", "处处为拐点"], "f''(x)=2 始终为正，凹凸性不改变。"),
        ("函数 f(x)=x^3+x 的拐点横坐标为：", "0", ["1", "-1", "不存在"], "f''(x)=6x，在 0 两侧变号，因此横坐标为 0。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_asymptote_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数微分学", "渐近线"
    specs = [
        ("函数 y=1/(x-2) 的垂直渐近线为：", "x=2", ["x=0", "y=0", "x=-2"], "分母在 x=2 处为 0，函数趋于无穷，故垂直渐近线为 x=2。"),
        ("函数 y=1/x 的水平渐近线为：", "y=0", ["x=0", "y=1", "不存在"], "当 x->∞ 或 x->-∞ 时，1/x->0，因此水平渐近线为 y=0。"),
        ("函数 y=(2x+1)/(x-3) 的垂直渐近线为：", "x=3", ["x=2", "y=2", "x=-3"], "令分母 x-3=0 得 x=3，且分子此处不为 0。"),
        ("函数 y=(3x+1)/(x+2) 的水平渐近线为：", "y=3", ["y=1/3", "x=-2", "不存在"], "分子分母同为一次，水平渐近线为最高次项系数比 y=3。"),
        ("函数 y=2x+1/x 的斜渐近线为：", "y=2x", ["y=0", "x=0", "y=x"], "当 |x| 趋于无穷时，1/x->0，函数与直线 y=2x 的差趋于 0。"),
        ("函数 y=ln x 的垂直渐近线为：", "x=0", ["y=0", "x=1", "不存在"], "当 x->0+ 时 ln x->-∞，故 x=0 为垂直渐近线。"),
        ("函数 y=e^x 在 x->-∞ 时的水平渐近线为：", "y=0", ["x=0", "y=1", "不存在"], "e^x 在 x->-∞ 时趋于 0，因此 y=0 是水平渐近线。"),
        ("判断有理函数垂直渐近线时，通常先看：", "分母为零且不能约去的点", ["分子为零的点", "最高次项系数", "函数是否为偶函数"], "有理函数的垂直渐近线通常来自分母为 0 且不可约掉的位置。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_antiderivative_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数积分学", "原函数"
    specs = [
        ("函数 f(x)=2x 的一个原函数是：", "x^2+C", ["2x^2+C", "x+C", "ln x+C"], "因为 (x^2)'=2x，所以 x^2+C 是 2x 的原函数。"),
        ("函数 f(x)=cos x 的一个原函数是：", "sin x+C", ["-sin x+C", "cos x+C", "tan x+C"], "sin x 的导数为 cos x。"),
        ("函数 f(x)=1/x (x>0) 的一个原函数是：", "ln x+C", ["x^2+C", "e^x+C", "1/x^2+C"], "ln x 的导数为 1/x。"),
        ("函数 f(x)=e^x 的一个原函数是：", "e^x+C", ["xe^x+C", "ln x+C", "1/e^x+C"], "e^x 的导数仍为 e^x。"),
        ("函数 f(x)=3x^2 的一个原函数是：", "x^3+C", ["3x^3+C", "x^2+C", "6x+C"], "x^3 的导数为 3x^2。"),
        ("若 F'(x)=f(x)，则 F(x) 称为 f(x) 的：", "原函数", ["导函数", "反函数", "极限"], "原函数的定义是导数等于给定函数。"),
        ("函数 f(x)=0 的原函数为：", "C", ["x+C", "0x^2+C", "ln x+C"], "常数函数的导数为 0，因此 0 的原函数为任意常数 C。"),
        ("函数 f(x)=sec^2 x 的一个原函数是：", "tan x+C", ["sec x+C", "sin x+C", "cos x+C"], "tan x 的导数为 sec^2 x。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_definite_integral_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数积分学", "定积分"
    specs = [
        ("定积分 ∫_0^1 x dx 的值为：", "1/2", ["1", "0", "2"], "原函数为 x^2/2，代入上下限得 1/2。"),
        ("定积分 ∫_0^π sin x dx 的值为：", "2", ["0", "1", "π"], "sin x 的原函数为 -cos x，结果为 -cosπ+cos0=2。"),
        ("定积分 ∫_-1^1 x^3 dx 的值为：", "0", ["1", "2", "-1"], "x^3 是奇函数，在对称区间 [-1,1] 上积分为 0。"),
        ("定积分 ∫_0^2 1 dx 的值为：", "2", ["1", "0", "4"], "常数 1 在区间 [0,2] 上的积分等于区间长度 2。"),
        ("定积分 ∫_0^1 3x^2 dx 的值为：", "1", ["3", "1/3", "0"], "原函数为 x^3，代入 0 到 1 得 1。"),
        ("若 f(x) 在 [a,b] 上连续，则 ∫_a^b f(x)dx 表示：", "有向面积的累积", ["函数最大值", "导数值", "极限不存在"], "定积分反映函数在区间上的累积量，可理解为有向面积。"),
        ("定积分 ∫_1^1 f(x)dx 的值为：", "0", ["1", "f(1)", "不存在"], "上下限相同的定积分为 0。"),
        ("定积分 ∫_0^1 (x+1)dx 的值为：", "3/2", ["1/2", "1", "2"], "分别积分得 ∫x dx=1/2，∫1 dx=1，总和为 3/2。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_variable_integral_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数积分学", "变限定积分"
    specs = [
        ("设 F(x)=∫_0^x t^2 dt，则 F'(x)=？", "x^2", ["2x", "x^3/3", "0"], "由变上限积分求导公式，F'(x)=被积函数在上限 x 处的值，即 x^2。"),
        ("设 F(x)=∫_1^x cos t dt，则 F'(x)=？", "cos x", ["sin x", "-sin x", "0"], "变上限积分求导，直接把上限 x 代入被积函数。"),
        ("设 F(x)=∫_0^(x^2) sin t dt，则 F'(x)=？", "2x sin(x^2)", ["sin(x^2)", "2x cos(x^2)", "x sin x"], "上限为 x^2，按链式法则得 sin(x^2)·2x。"),
        ("设 F(x)=∫_x^1 t dt，则 F'(x)=？", "-x", ["x", "1", "0"], "下限含 x 时求导取负号，F'(x)=-x。"),
        ("设 F(x)=∫_0^(3x) e^t dt，则 F'(x)=？", "3e^(3x)", ["e^(3x)", "3e^x", "0"], "上限 3x 的导数为 3，故 F'(x)=e^(3x)·3。"),
        ("设 F(x)=∫_2^x 1/t dt (x>0)，则 F'(x)=？", "1/x", ["ln x", "x", "0"], "变上限积分求导公式给出 F'(x)=1/x。"),
        ("设 F(x)=∫_0^(sqrt x) t dt，则 F'(x)=？", "1/2", ["sqrt x", "1/(2sqrt x)", "x/2"], "被积函数在上限处为 sqrt x，再乘上限导数 1/(2sqrt x)，结果为 1/2。"),
        ("变限定积分求导的核心依据是：", "微积分基本定理和链式法则", ["洛必达法则", "分部积分法", "二阶判别法"], "变上限积分求导先代入上限，再乘以上限函数的导数。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_newton_leibniz_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数积分学", "牛顿-莱布尼兹公式"
    specs = [
        ("若 F'(x)=f(x)，则 ∫_a^b f(x)dx 等于：", "F(b)-F(a)", ["F(a)-F(b)", "F(a)+F(b)", "f(b)-f(a)"], "牛顿-莱布尼兹公式表明定积分等于原函数在上下限的差。"),
        ("利用牛顿-莱布尼兹公式，∫_1^2 1/x dx = ?", "ln 2", ["1", "2", "0"], "1/x 的原函数为 ln x，代入得 ln2-ln1=ln2。"),
        ("利用牛顿-莱布尼兹公式，∫_0^1 2x dx = ?", "1", ["0", "2", "1/2"], "原函数为 x^2，代入 0 到 1 得 1。"),
        ("利用牛顿-莱布尼兹公式，∫_0^π cos x dx = ?", "0", ["1", "2", "π"], "cos x 的原函数为 sin x，sinπ-sin0=0。"),
        ("利用牛顿-莱布尼兹公式，∫_0^1 e^x dx = ?", "e-1", ["e", "1", "0"], "e^x 的原函数为 e^x，代入得 e-1。"),
        ("牛顿-莱布尼兹公式连接了：", "定积分与原函数", ["极限与连续", "偏导数与全微分", "级数与概率"], "该公式说明定积分可以通过原函数在端点的差来计算。"),
        ("若 F(x)=x^3 是 f(x)=3x^2 的原函数，则 ∫_1^2 3x^2 dx = ?", "7", ["8", "6", "3"], "由 F(2)-F(1)=8-1=7。"),
        ("利用牛顿-莱布尼兹公式，∫_0^2 (x+1)dx = ?", "4", ["2", "3", "5"], "原函数为 x^2/2+x，代入 2 得 2+2=4。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_substitution_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数积分学", "换元积分"
    specs = [
        ("不定积分 ∫ 2x cos(x^2) dx = ?", "sin(x^2)+C", ["cos(x^2)+C", "2sin(x^2)+C", "x sin(x^2)+C"], "令 u=x^2，则 du=2x dx，积分化为 ∫cos u du=sin u+C。"),
        ("不定积分 ∫ x/(1+x^2) dx = ?", "(1/2)ln(1+x^2)+C", ["ln(1+x^2)+C", "1/(1+x^2)+C", "x^2/2+C"], "令 u=1+x^2，则 du=2x dx，得到 1/2 ln(1+x^2)+C。"),
        ("不定积分 ∫ e^(3x) dx = ?", "(1/3)e^(3x)+C", ["3e^(3x)+C", "e^(3x)+C", "e^x+C"], "令 u=3x，du=3dx，因此积分为 (1/3)e^(3x)+C。"),
        ("不定积分 ∫ cos(2x) dx = ?", "(1/2)sin(2x)+C", ["2sin(2x)+C", "-(1/2)sin(2x)+C", "sin x+C"], "令 u=2x，dx=du/2，积分为 1/2 sin(2x)+C。"),
        ("不定积分 ∫ 1/(1+x) dx = ?", "ln|1+x|+C", ["1/(1+x)+C", "x/(1+x)+C", "ln|x|+C"], "令 u=1+x，则 du=dx，积分为 ln|1+x|+C。"),
        ("不定积分 ∫ 2x e^(x^2) dx = ?", "e^(x^2)+C", ["2e^(x^2)+C", "x e^(x^2)+C", "e^x+C"], "令 u=x^2，du=2x dx，积分化为 ∫e^u du。"),
        ("不定积分 ∫ sin(3x) dx = ?", "-(1/3)cos(3x)+C", ["-cos(3x)+C", "(1/3)cos(3x)+C", "cos x+C"], "令 u=3x，积分为 -1/3 cos(3x)+C。"),
        ("换元积分法主要用于处理：", "复合函数及其导数因子同时出现的积分", ["只含常数的积分", "二元函数极值", "线性方程组"], "当被积函数出现复合结构且含有内层函数导数因子时，换元法常能简化计算。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_parts_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数积分学", "分部积分"
    specs = [
        ("不定积分 ∫ x e^x dx = ?", "(x-1)e^x+C", ["xe^x+C", "(x+1)e^x+C", "e^x+C"], "用分部积分，取 u=x，dv=e^x dx，得 xe^x-∫e^x dx=(x-1)e^x+C。"),
        ("不定积分 ∫ x cos x dx = ?", "x sin x + cos x + C", ["x sin x - cos x + C", "x cos x + sin x + C", "sin x + C"], "取 u=x，dv=cos x dx，则结果为 x sin x-∫sin x dx=x sin x+cos x+C。"),
        ("不定积分 ∫ x sin x dx = ?", "-x cos x + sin x + C", ["x cos x - sin x + C", "x sin x + cos x + C", "-cos x+C"], "取 u=x，dv=sin x dx，v=-cos x，得 -x cos x+∫cos x dx。"),
        ("不定积分 ∫ ln x dx = ?", "x ln x - x + C", ["ln x + C", "x ln x + x + C", "1/x+C"], "将 ln x 看作 ln x·1，取 u=ln x，dv=dx，分部积分可得 xlnx-x+C。"),
        ("分部积分公式 ∫u dv 等于：", "uv-∫v du", ["uv+∫v du", "du/dv", "∫u∫v"], "分部积分来自乘积求导公式，是 ∫u dv=uv-∫v du。"),
        ("计算 ∫ x e^(2x) dx 时，适合使用：", "分部积分法", ["洛必达法则", "二阶判别法", "隐函数求导"], "被积函数为多项式与指数函数乘积，常用分部积分。"),
        ("不定积分 ∫ x ln x dx 通常适合：", "分部积分法", ["直接用基本公式", "二元函数极值", "求偏导数"], "x ln x 是代数函数与对数函数乘积，常用分部积分。"),
        ("分部积分中选择 u 时，通常希望 u：", "求导后更简单", ["求导后更复杂", "必须是常数", "必须为三角函数"], "分部积分选取 u 的经验是求导后简化，便于后续积分。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_geometry_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数积分学", "几何应用"
    specs = [
        ("曲线 y=x 与 x 轴在 [0,2] 围成的面积为：", "2", ["1", "4", "0"], "面积为 ∫_0^2 x dx=2。"),
        ("曲线 y=x^2 与 x 轴在 [0,1] 围成的面积为：", "1/3", ["1/2", "1", "2/3"], "面积为 ∫_0^1 x^2 dx=1/3。"),
        ("曲线 y=x 与 y=x^2 在 [0,1] 间围成的面积为：", "1/6", ["1/3", "1/2", "1"], "在 [0,1] 上 x≥x^2，面积为 ∫_0^1 (x-x^2)dx=1/2-1/3=1/6。"),
        ("曲线 y=2 与 x 轴在 [1,3] 围成的面积为：", "4", ["2", "6", "1"], "面积为矩形面积，也可算 ∫_1^3 2 dx=4。"),
        ("计算平面图形面积时，若上方曲线为 y=f(x)，下方为 y=g(x)，面积为：", "∫_a^b [f(x)-g(x)]dx", ["∫_a^b [g(x)-f(x)]dx", "f(b)-g(a)", "f'(x)-g'(x)"], "面积应取上方函数减下方函数再积分。"),
        ("曲线 y=sin x 与 x 轴在 [0,π] 围成的面积为：", "2", ["0", "1", "π"], "sin x 在 [0,π] 非负，面积为 ∫_0^π sin x dx=2。"),
        ("曲线 y=1-x 与 x 轴在 [0,1] 围成的面积为：", "1/2", ["1", "2", "0"], "面积为直角三角形面积，也可算 ∫_0^1 (1-x)dx=1/2。"),
        ("定积分的几何应用中，面积结果通常应为：", "非负数", ["一定为负数", "一定等于导数", "一定不存在"], "几何面积表示大小，应取非负；若函数在轴下方，要注意取绝对值或上下函数差。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_physics_questions(rng: random.Random) -> list[dict]:
    module, sub = "一元函数积分学", "物理应用"
    specs = [
        ("已知速度 v(t)=t，0≤t≤4，则位移为：", "8", ["4", "16", "0"], "位移为 ∫_0^4 t dt=8。"),
        ("已知速度 v(t)=2，0≤t≤3，则位移为：", "6", ["2", "3", "9"], "速度恒为 2，位移为 ∫_0^3 2dt=6。"),
        ("已知加速度 a(t)=2，且 v(0)=1，则 v(t)=？", "2t+1", ["t+1", "2t", "t^2+1"], "速度是加速度的积分，v(t)=∫2dt+C=2t+C，由 v(0)=1 得 C=1。"),
        ("若速度函数 v(t) 在 [a,b] 上非负，则路程等于：", "∫_a^b v(t)dt", ["v(b)-v(a)", "v'(t)", "0"], "速度非负时，路程等于速度对时间的积分。"),
        ("变力 F(x)=x 使物体从 x=0 移到 x=2 所做的功为：", "2", ["1", "4", "0"], "功为 ∫_0^2 x dx=2。"),
        ("若边际成本 C'(x)=2x，则产量从 0 到 3 的成本增量为：", "9", ["6", "3", "18"], "成本增量为 ∫_0^3 2x dx=9。"),
        ("已知速度 v(t)=3t^2，则 0 到 1 的位移为：", "1", ["3", "1/3", "0"], "位移为 ∫_0^1 3t^2 dt=1。"),
        ("定积分在物理应用中常表示：", "累积量", ["瞬时斜率", "函数零点", "二阶偏导"], "速度积分得到位移、力积分得到功，都是累积量思想。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_partial_questions(rng: random.Random) -> list[dict]:
    module, sub = "多元函数微分学", "偏导数"
    specs = [
        ("设 z=x^2y+sin y，则 ∂z/∂x = ?", "2xy", ["x^2+cos y", "2x+y", "x^2y"], "对 x 求偏导时把 y 看作常数，x^2y 对 x 求导为 2xy，sin y 为常数项。"),
        ("设 z=xe^y，则 ∂z/∂y = ?", "xe^y", ["e^y", "x", "ye^x"], "对 y 求偏导时 x 为常数，e^y 的导数为 e^y。"),
        ("设 z=x^2+y^2，则 ∂z/∂x = ?", "2x", ["2y", "x+y", "0"], "对 x 求偏导时 y^2 为常数，x^2 的偏导为 2x。"),
        ("设 z=ln(xy)，则 ∂z/∂x = ?", "1/x", ["1/y", "xy", "ln y"], "ln(xy)=ln x+ln y，对 x 求偏导得 1/x。"),
        ("设 z=x sin y，则 ∂z/∂x = ?", "sin y", ["x cos y", "cos y", "x sin y"], "对 x 求偏导时 sin y 为常数。"),
        ("设 z=x^3y^2，则 ∂z/∂y = ?", "2x^3y", ["3x^2y^2", "x^3", "6xy"], "对 y 求偏导，y^2 的导数为 2y，x^3 视为常数因子。"),
        ("求偏导数时，对未求导的变量应：", "看作常数", ["看作 0", "同时求导", "删除"], "偏导的核心是只对一个变量求导，其他变量暂作常数。"),
        ("设 z=e^(x+y)，则 ∂z/∂x = ?", "e^(x+y)", ["xe^(x+y)", "ye^(x+y)", "0"], "对 x 求偏导，x+y 对 x 的导数为 1，因此结果仍为 e^(x+y)。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_total_differential_questions(rng: random.Random) -> list[dict]:
    module, sub = "多元函数微分学", "全微分"
    specs = [
        ("设 z=x^2+y^2，则 dz = ?", "2x dx + 2y dy", ["2x dy + 2y dx", "x dx + y dy", "dx+dy"], "全微分 dz=z_x dx+z_y dy，本题 z_x=2x，z_y=2y。"),
        ("设 z=xy，则 dz = ?", "y dx + x dy", ["x dx + y dy", "xy dx", "dx dy"], "z_x=y，z_y=x，因此 dz=y dx+x dy。"),
        ("设 z=e^x+y，则 dz = ?", "e^x dx + dy", ["e^x dy + dx", "e^x dx", "dy"], "z_x=e^x，z_y=1，所以 dz=e^x dx+dy。"),
        ("设 z=ln x + y^2，则 dz = ?", "(1/x)dx + 2y dy", ["ln x dx + y dy", "x dx + 2y dy", "dx+dy"], "分别求偏导 z_x=1/x，z_y=2y。"),
        ("二元函数 z=f(x,y) 的全微分公式为：", "dz=f_x dx+f_y dy", ["dz=f_x+f_y", "dz=f dxdy", "dz=f_x dy+f_y dx"], "全微分由各偏导数乘对应自变量微分后相加。"),
        ("设 z=x^2+y，在点 (1,2) 处，当 dx=0.1, dy=0.2 时，dz≈？", "0.4", ["0.1", "0.2", "0.3"], "dz=2x dx+dy，在 x=1 时 dz=2·0.1+0.2=0.4。"),
        ("设 z=xy，在点 (2,3) 处的全微分为：", "3dx+2dy", ["2dx+3dy", "6dx+6dy", "dx+dy"], "z_x=y=3，z_y=x=2，因此 dz=3dx+2dy。"),
        ("全微分常用于估计：", "函数增量的线性近似", ["函数最大值", "定积分面积", "极限是否存在"], "全微分是多元函数增量的线性主部，可用于近似计算。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_second_partial_questions(rng: random.Random) -> list[dict]:
    module, sub = "多元函数微分学", "二阶偏导"
    specs = [
        ("设 z=x^2y^3，则 ∂^2z/∂x∂y = ?", "6xy^2", ["2xy^3", "6x^2y", "3x^2y^2"], "先对 x 求偏导得 2xy^3，再对 y 求导得 6xy^2。"),
        ("设 z=x^2+y^2，则 z_xx = ?", "2", ["0", "2x", "2y"], "z_x=2x，再对 x 求导得 z_xx=2。"),
        ("设 z=xy，则 z_xy = ?", "1", ["0", "x", "y"], "z_x=y，再对 y 求导得 1。"),
        ("设 z=e^(x+y)，则 z_xy = ?", "e^(x+y)", ["0", "xe^(x+y)", "ye^(x+y)"], "先对 x 或 y 求导仍为 e^(x+y)，混合偏导仍为 e^(x+y)。"),
        ("设 z=x^3y，则 z_xx = ?", "6xy", ["3x^2y", "6x", "0"], "z_x=3x^2y，继续对 x 求导得 6xy。"),
        ("设 z=sin x cos y，则 z_xy = ?", "-cos x sin y", ["cos x cos y", "-sin x sin y", "sin x cos y"], "z_x=cos x cos y，再对 y 求导得 -cos x sin y。"),
        ("若二阶混合偏导连续，通常有：", "z_xy=z_yx", ["z_x=z_y", "z_xx=0", "z_yy=0"], "在二阶偏导连续条件下，混合偏导数相等。"),
        ("设 z=ln x + y^3，则 z_yy = ?", "6y", ["3y^2", "1/x", "0"], "z_y=3y^2，继续对 y 求导得 6y。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_chain_rule_questions(rng: random.Random) -> list[dict]:
    module, sub = "多元函数微分学", "链导法则"
    specs = [
        ("设 z=u^2+v，u=x^2，v=sin x，则 dz/dx = ?", "4x^3+cos x", ["2x+cos x", "4x+sin x", "2u+v"], "z 对 x 的导数为 2u·du/dx+dv/dx=2x^2·2x+cos x=4x^3+cos x。"),
        ("设 z=e^u，u=x+y，则 ∂z/∂x = ?", "e^(x+y)", ["xe^(x+y)", "ye^(x+y)", "0"], "由链式法则，∂z/∂x=e^u·∂u/∂x=e^(x+y)。"),
        ("设 z=u^2，u=xy，则 ∂z/∂x = ?", "2xy^2", ["2xy", "2x^2y", "y"], "z=(xy)^2=x^2y^2，对 x 求偏导得 2xy^2。"),
        ("设 z=ln u，u=x^2+y^2，则 ∂z/∂x = ?", "2x/(x^2+y^2)", ["1/(x^2+y^2)", "2y/(x^2+y^2)", "2x"], "链式法则：z_x=(1/u)u_x=2x/(x^2+y^2)。"),
        ("设 z=sin u，u=x+y，则 ∂z/∂y = ?", "cos(x+y)", ["sin(x+y)", "-sin(x+y)", "0"], "z_y=cos u·u_y=cos(x+y)。"),
        ("多元复合函数求导的关键是：", "沿变量依赖关系逐层求导", ["只对外层函数求导", "只对内层变量求导", "直接代入 0"], "链导法则要求把外层导数与内层变量导数相乘并按路径相加。"),
        ("设 z=u+v^2，u=x，v=x^2，则 dz/dx = ?", "1+4x^3", ["1+2x", "2x", "4x"], "z=x+x^4，直接求导得 1+4x^3。"),
        ("设 z=e^(xy)，则 ∂z/∂x = ?", "y e^(xy)", ["x e^(xy)", "e^(xy)", "0"], "外层 e^u 求导仍为 e^u，内层 xy 对 x 求偏导为 y。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_implicit_questions(rng: random.Random) -> list[dict]:
    module, sub = "多元函数微分学", "隐函数求导"
    specs = [
        ("由方程 x^2+y^2=1 确定 y=y(x)，则 dy/dx = ?", "-x/y", ["x/y", "-y/x", "y/x"], "两边对 x 求导得 2x+2y y'=0，所以 y'=-x/y。"),
        ("由方程 xy=1 确定 y=y(x)，则 dy/dx = ?", "-y/x", ["y/x", "x/y", "-x/y"], "对 xy=1 求导：y+x y'=0，故 y'=-y/x。"),
        ("由方程 e^y+xy=1 确定 y=y(x)，则 dy/dx = ?", "-y/(e^y+x)", ["y/(e^y+x)", "-x/(e^y+y)", "0"], "求导得 e^y y' + y + x y'=0，整理 y'= -y/(e^y+x)。"),
        ("由方程 x+y+xy=0 确定 y=y(x)，则 dy/dx = ?", "-(1+y)/(1+x)", ["(1+y)/(1+x)", "-(1+x)/(1+y)", "0"], "求导得 1+y'+y+xy'=0，整理 (1+x)y'=-(1+y)。"),
        ("隐函数求导时，应把 y 看作：", "x 的函数", ["常数", "0", "独立于 x 的字母"], "y=y(x) 时，对含 y 的项求导要乘 y'。"),
        ("由方程 y^2=x 确定 y=y(x)，则 dy/dx = ?", "1/(2y)", ["2y", "1/y", "0"], "对 y^2=x 求导得 2y y'=1，所以 y'=1/(2y)。"),
        ("由方程 x^2+xy+y^2=3 确定 y=y(x)，求导后正确的是：", "2x+y+xy'+2yy'=0", ["2x+y+2y=0", "x^2+y^2=0", "2x+xy'=0"], "逐项求导：x^2 得 2x，xy 得 y+xy'，y^2 得 2yy'。"),
        ("隐函数求导的常见目标是求：", "dy/dx", ["定积分", "水平渐近线", "原函数常数 C"], "隐函数方程中 y 未显式表示为 x 的函数，但仍可通过求导求 dy/dx。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


def build_two_variable_extreme_questions(rng: random.Random) -> list[dict]:
    module, sub = "多元函数微分学", "二元函数极值"
    specs = [
        ("函数 f(x,y)=x^2+y^2 的极小值点为：", "(0,0)", ["(1,0)", "(0,1)", "不存在"], "两个平方和在 (0,0) 处取得最小值 0，因此为极小值点。"),
        ("函数 f(x,y)=x^2+y^2-2x-4y 的极小值点为：", "(1,2)", ["(2,1)", "(0,0)", "(-1,-2)"], "配方得 (x-1)^2+(y-2)^2-5，极小值点为 (1,2)。"),
        ("求二元函数驻点时，通常先解：", "f_x=0, f_y=0", ["f=0", "f_x=f_y", "x+y=0"], "二元函数可微时，内部极值点通常满足一阶偏导数同时为 0。"),
        ("二元函数二阶判别法中，D=f_xx f_yy-(f_xy)^2。若 D>0 且 f_xx>0，则驻点为：", "极小值点", ["极大值点", "鞍点", "无法判断"], "二阶判别法：D>0 且 f_xx>0 为极小值点。"),
        ("二元函数二阶判别法中，若 D>0 且 f_xx<0，则驻点为：", "极大值点", ["极小值点", "鞍点", "一定无极值"], "D>0 且 f_xx<0 表示局部向下开口，驻点为极大值点。"),
        ("二元函数二阶判别法中，若 D<0，则驻点为：", "鞍点", ["极小值点", "极大值点", "无法求偏导"], "D<0 时，驻点不是极值点，而是鞍点。"),
        ("函数 f(x,y)=-(x^2+y^2) 的极大值点为：", "(0,0)", ["(1,1)", "不存在", "(0,1)"], "函数为负平方和，在 (0,0) 处取最大值 0，因此为极大值点。"),
        ("函数 f(x,y)=x^2-y^2 在 (0,0) 附近表现为：", "鞍点", ["极小值点", "极大值点", "最大值点"], "沿 x 轴函数为正，沿 y 轴函数为负，(0,0) 不是极值点而是鞍点。"),
    ]
    return [q(module, sub, *spec, rng) for spec in specs]


BUILDERS = [
    build_limit_questions,
    build_continuity_questions,
    build_derivative_questions,
    build_differential_questions,
    build_higher_derivative_questions,
    build_lhopital_questions,
    build_monotonicity_questions,
    build_extreme_questions,
    build_concavity_questions,
    build_inflection_questions,
    build_asymptote_questions,
    build_antiderivative_questions,
    build_definite_integral_questions,
    build_variable_integral_questions,
    build_newton_leibniz_questions,
    build_substitution_questions,
    build_parts_questions,
    build_geometry_questions,
    build_physics_questions,
    build_partial_questions,
    build_total_differential_questions,
    build_second_partial_questions,
    build_chain_rule_questions,
    build_implicit_questions,
    build_two_variable_extreme_questions,
]


def build_questions(seed: int = 20260430) -> list[dict]:
    rng = random.Random(seed)
    questions: list[dict] = []
    for builder in BUILDERS:
        built = builder(rng)
        if len(built) != 8:
            raise RuntimeError(f"{builder.__name__} produced {len(built)} questions, expected 8")
        questions.extend(built)

    existing = load_existing_stems()
    seen: set[str] = set()
    for item in questions:
        key = normalize_stem(item["stem"])
        if key in seen:
            raise RuntimeError(f"Duplicate stem inside batch: {item['stem']}")
        if key in existing:
            raise RuntimeError(f"Duplicate stem in existing data: {item['stem']}")
        seen.add(key)

    rng.shuffle(questions)
    return questions


def write_review(questions: list[dict]) -> None:
    by_module = Counter(item["module"] for item in questions)
    by_submodule = Counter(item["submodule"] for item in questions)
    by_difficulty = Counter(item["difficulty"] for item in questions)
    lines = [
        "# Z002 数学基础 微积分选择题 批次 001",
        "",
        "本批次围绕港澳台考研 Z002 综合能力（二）数学基础范围生成，参考 396 经济类联考数学基础选择题的基础计算与概念判断风格。",
        "题目全部为四选一选择题，难度以基础和中等基础为主，不包含线性代数、概率统计、级数、二重积分、微分方程和空间解析几何。",
        "",
        f"- 总题数：{len(questions)}",
        "- exam_code：Z002",
        "- subject：数学基础",
        "- source_type：ai_generated",
        "- source_year：2026",
        "",
        "## 模块分布",
    ]
    for module in SUBMODULES:
        lines.append(f"- {module}：{by_module[module]} 题")
    lines.extend(["", "## 子模块分布"])
    for module, submodules in SUBMODULES.items():
        lines.append(f"### {module}")
        for submodule in submodules:
            lines.append(f"- {submodule}：{by_submodule[submodule]} 题")
    lines.extend(["", "## 难度分布"])
    for difficulty in sorted(by_difficulty):
        label = "基础" if difficulty <= 2 else "中等"
        lines.append(f"- 难度 {difficulty}（{label}）：{by_difficulty[difficulty]} 题")
    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    questions = build_questions()
    OUTPUT_PATH.write_text(json.dumps({"questions": questions}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review(questions)
    print(f"Wrote {len(questions)} questions to {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Wrote review to {REVIEW_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Modules: {dict(Counter(item['module'] for item in questions))}")
    print(f"Submodules: {dict(Counter(item['submodule'] for item in questions))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
