"""Structured teaching contract for Chinese-culture explanations.

V3 separates factual planning from learner-facing rendering.  The model emits
one auditable contract and the backend renders the existing four product
blocks.  This prevents the display copy and the review metadata from drifting
apart, while keeping the current ExplanationPanel protocol unchanged.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from difflib import SequenceMatcher


OPTION_LABELS = ("A", "B", "C", "D")
OPTION_FIELDS = {
    "A": "option_a",
    "B": "option_b",
    "C": "option_c",
    "D": "option_d",
}

CULTURE_V3_FORMS = {
    "direct_identification",
    "relationship_match",
    "negative_identification",
    "odd_one_out",
}

# ``question_form`` describes the direction of the question.  ``reasoning_mode``
# describes the factual bridge the learner must build, so the prompt does not
# force a person, chronology and place question through the same wording shell.
CULTURE_V3_REASONING_MODES = {
    "person_event_effect",
    "person_school_claim",
    "work_author_era",
    "concept_definition",
    "chronology",
    "place_object_mapping",
    "category_comparison",
    "quote_meaning",
    "institution_function",
    "direct_fact",
}

CULTURE_V3_MEMORY_STRATEGIES = {"none", "keyword", "contrast", "chain"}

CULTURE_V3_REQUIRED_FIELDS = {
    "version",
    "question_form",
    "reasoning_mode",
    "fact_anchor",
    "reasoning_steps",
    "evidence_excerpt",
    "knowledge_extension",
    "memory_strategy",
    "memory_hook",
    "option_analysis",
    "scope_level",
    "controversy_status",
    "verification_status",
    "difficulty_features",
}

_SELECTION_RE = re.compile(r"(?:选|选择|应选|答案(?:为|是)?)\s*[A-D](?=$|[。；，,、:“”‘’（）()\s])", re.I)
_PROCEDURAL_KNOWLEDGE_RE = re.compile(
    r"做题时|答题时|先圈|先分|再看|可?按.{0,18}(?:辨析|判断|建立对应|区分|串联)|"
    r"建立对应|掌握题干|知识点定位|回到题干|排除干扰项|要区分|需区分|常考|"
    r"建立时间线|要按"
)
_GENERIC_FACT_RE = re.compile(
    r"^(?:该项|此项|这一项|这个选项|该说法|题干对象|正确选项|错误选项|干扰项)|"
    r"(?:不符合|符合)(?:题干|本题|要求|共同限定|所列范围)|"
    r"与(?:题干|本题).{0,12}不符|属于[“\"][^”\"]{1,36}[”\"]范围"
)
_GENERIC_FIT_RE = re.compile(
    r"^(?:符合|不符合)(?:题干|本题|要求|共同限定|所列范围)[，。；]?$|"
    r"^(?:故|所以|因此)?(?:不选|排除|应选此项)[，。；]?$|"
    r"^与(?:本题|题干)(?:所问|所述|要求的?)?(?:对象|内容|范围|关系)?不符[，。；]?$"
)
_GENERIC_MEMORY_RE = re.compile(
    r"^(?:记住|牢记|注意|掌握)(?:这|该|本)?(?:组)?(?:对应)?关系[。！!]?$|"
    r"^(?:先看题干|认真审题|排除干扰项)[。！!]?$"
)
_MEMORY_CONTRAST_SIGNAL_RE = re.compile(
    r"易混|混淆|对比|对照|区分(?:人物|时代|朝代|作品|典籍|学派|流派|地点|概念|类别|门类)"
)
_MEMORY_WORK_ATTRIBUTION_RE = re.compile(
    r"作者|曲作者|创作者|撰写|著有|代表作|作品有|出自|典出"
)
_MEMORY_FIXED_DATE_QUESTION_RE = re.compile(
    r"(?:农历|阴历|节日|佳节|节期)[^，。；！？]{0,16}"
    r"(?:几月(?:初)?几|哪(?:一)?天|日期|日子)|"
    r"(?:几月(?:初)?几|哪(?:一)?天|日期|日子)[^，。；！？]{0,16}"
    r"(?:农历|阴历|节日|佳节|节期)"
)
_MEMORY_PROCESS_SIGNAL_RE = re.compile(
    r"取经|东渡|出使|改革|革新|改进|变法|改制|演变|发展过程|传播过程|"
    r"形成过程|实施过程|步骤|流程|先后|次序"
)
_MEMORY_FIXED_LABEL_RE = re.compile(
    r"别名|又称|尊称|誉为|被称为|合称|简称|对应地|"
    r"空缺处|填入哪一项|可填入|象征(?:什么|何种|何意|[（(])"
)
_MEMORY_ORDERED_LABEL_RE = re.compile(
    r"伯[、，,]仲[、，,]叔[、，,]季|望[、，,]闻[、，,]问[、，,]切"
)
_MEMORY_PERSON_WORK_CONTRAST_RE = re.compile(
    r"作者(?:是|为|：|\?)|哪位(?:人物|诗人|作家|文学家|医家|名医|科学家|"
    r"思想家|法家人物)|出自[^，。；！？]{0,14}之手|代表作品|代表作|"
    r"下列(?:作品|著作|典籍)中[^，。；！？]{0,24}(?:属于|出自|与)"
)
_MEMORY_PERSON_CLAIM_CONTRAST_RE = re.compile(
    r"下列主张中，与[㐀-鿿·]{2,4}关系最密切"
)
_MEMORY_PLACE_CLUE_RE = re.compile(
    r"位于[^，。；！？]{2,20}(?:以|、)[^，。；！？]{2,20}(?:著称|闻名)"
)
_MEMORY_DIAGNOSTIC_OPTION_SETS = (
    frozenset({"望", "闻", "问", "切"}),
)
_ANSWER_ECHO_BRIDGE_RE = re.compile(
    r"(?:^[^，。；;]{1,36}(?:核心对应|思想对应|实际对应|对应(?:的是|为|：|:)?|即为)"
    r"[^，。；;]{1,36}$)|(?:^[^，。；;]{1,80}构成稳定(?:的)?.{0,12}对应$)"
)
_BARE_MAPPING_PHRASE_RE = re.compile(
    r"的典型(?:艺术)?特征是|的(?:创作|生活|出现|成书)时期是|"
    r"这一(?:观点|主张|思想|说法)(?:是|属于)|主要关联(?:的历史)?时期是"
)
_ACTION_PREDICATE_RE = re.compile(
    r"带回|主持|翻译|传播|推动|促进|出使|东渡|西行|求取|改革|变法|创立|"
    r"编纂|撰写|设置|制定|颁布|推行|实行|建立|确立|废除|奖励|统一|强化|增强|规范|吸收|"
    r"(?<!四大)发明|修建|用于|负责|沟通|演示|测报|形成|开创|奠定"
)
_SOURCE_LABEL_RE = re.compile(r"【\s*解析\s*】")
_OCR_SOURCE_SEAM_RE = re.compile(
    r"[”》）](?!(?:是|为|以|由|的|中|内|与|和|及|等|所属|作者|内容|体例|书名|全书|一书|分别|通常|主要|可|用于|记述|记录|分门讨论|正文|把[^，。；]{1,16}(?:列为|归入|视为)))"
    r"[\u3400-\u9fff]{2,8}(?:是|为|指|属于|主张|著有|提出|采用|创作)|"
    r"被称为.{0,16}徐霞客一生|"
    r"(?:思想|理论|作品|著作|时期|时代|人物|内容|成就)(?:他|她|其)"
    r"(?:用|以|主张|提出|认为|强调|倡导|创作|著有|回国|主持|传播|推动|促进|改革)"
)
_LEADING_REFERENCE_RE = re.compile(
    r"^(?:(?:他|她|其人|此人|该人物|该书|此书|这部(?:著作|作品|典籍)|它)"
    r"(?:是|为|在|曾|又|还|由|被|用|以|主张|提出|认为|强调|著有|创作)|"
    r"(?:这|该|此)句(?:诗|话|引文)?)"
)
_INCOMPLETE_CLAUSE_END_RE = re.compile(
    r"(?:名句|著作|代表作|作品|内容|包括|分为|例如|如)?(?:是|(?<!无)为|有|与|和|或|及|包括|分为)[：:]?$|"
    r"(?:不|未|无|并|但|而|又|及|与|和|或|、|，|,|：|:)$|"
    r"御史大$|四大楷书$|与现行公历基$|(?:时代和)?内容范围$|"
    r"前四史.*(?:后汉|三国)$|"
    r"但[^，。；]{0,12}(?:才能|能力|身份|作品)$|"
    r"一部.{0,48}的文$|它使成都平原$"
)
_REVIEW_LANGUAGE_RE = re.compile(
    r"题干已给出|[ABCD]\s*(?:项)?|其余项|事实或类别关系不同|"
    r"属于这一思想传统|主要关联这一时期|高频对应关系|最稳定定位|核心标签"
)
_UNSAFE_OPTION_FACT_RE = re.compile(
    r"不符合[“\"']|不是[“\"']|不属于[“\"']|与题干|未满足题干|无直接对应|故不选|"
    r"^(?:是|为|属于|指)(?=[\u3400-\u9fff《“])|"
    r"^(?:成语|[“\"][^”\"]{1,16}[”\"]一词)(?:最早)?(?:出自|典出)|"
    r"构成稳定(?:的)?.{0,12}对应|的典型(?:艺术)?特征是|"
    r"^[^，；;]{2,18}(?:没有|并非|不属于|不是|无(?:关|直接|明确|实际|任何))(?=[\u3400-\u9fff‘“])"
)
_UNSUPPORTED_OPTION_LIMIT_RE = re.compile(
    r"局限于|仅限于|只限于|范围仅(?:限|在)|只在.{0,16}(?:活动|流行|传播|出现|使用)"
)
_EXPLICIT_OPTION_LIMIT_RE = re.compile(r"仅|只|局限|限于|范围")
_SELF_CONTRADICTION_RE = re.compile(
    r"([\u3400-\u9fff]{2,8}).{0,40}(?:不归于|不属于|不是)\1"
)
_UNSAFE_KNOWLEDGE_RE = re.compile(
    r"记忆对象|做题|答题|先(?=看|圈|分|找|判断|确定|排除|定位|记|抓)|"
    r"再(?=看|分|判断|排除|定位|记|抓)|按.{0,12}(?:分类|区分|辨析|记忆|建立)|"
    r"要区分|需区分|易混|常考|建立时间线|典籍文物需"
)
_SOURCE_FRAGMENT_RE = re.compile(
    r"[（(]\d+[）)]|(?:^|[；;。])\s*\d+\s*[.)．、]|"
    r"^(?:乃(?!(?:[\u3400-\u9fff]{1,6}(?:篇|章)(?:叙述|记载|介绍|讲述)))|且|而|但)(?=[\u3400-\u9fff])"
)
_KNOWLEDGE_FRAGMENT_RE = re.compile(r"^[\u3400-\u9fff]{4,14}(?:、[\u3400-\u9fff]{2,8})*为代表(?:$|[；;])")
_TAUTOLOGY_FACT_RE = re.compile(r"^(.{2,14})(?:归属|属于|指)\1$")
_CHRONOLOGY_QUESTION_RE = re.compile(
    r"先后|顺序|排序|早于|晚于|年代|时期排列|去世后|之后|以前|此前|"
    r"何时|何代|哪(?:个|一)(?:时期|时代|朝代|年代)|什么(?:时期|时代|朝代|年代)|"
    r"(?:历史)?时期(?:是|为|属于|：|:)|"
    r"(?:生活|活动|创作|所处)(?:时间|年代|时代|时期|朝代)最(?:早|晚)|"
    r"(?:生活|活动|成书|创作|出现|建立|设立|创立|实行|使用|产生|完成|问世|形成)于|"
    r"(?:出现|成书|建立|设立|创立|实行|使用|产生|完成|问世|形成)(?:时间)?最早|"
    r"最早(?:出现|成书|建立|设立|创立|实行|使用|产生|完成|问世|形成)"
)
_CHRONOLOGY_FOCUS_RE = re.compile(
    r"(?:对应|关联)的(?:时期|时代|朝代|年代)(?:是|为)[：:]?$"
)
_INVERSE_DIRECTION_RE = re.compile(
    r"不正确|不属于|不包括|不列入|未列入|并非|不是|不符合|错误(?:的是|项)?|有误|不当|"
    r"不同|不相同|不能说明|不应|不宜|排除|不在|例外|逆向|"
    r"与[^，。；！？,;!?]{1,30}无关(?:的是|的(?:一项|著作|作品|人物)|(?=[，。；！？,;!?]|$))"
)
_INVERSE_FALSE_CORRECTION_RE = re.compile(
    r"(?:并不(?:是)?|并非|不是|不算|没有)[^，。；]{0,8}(?:错误|不正确|有误|不当)|"
    r"(?:并非|不是)(?:不|未)"
)
_TIME_VALUE_RE = re.compile(
    r"先秦|夏代|商代|西周|东周|春秋(?:时期)?|战国(?:时期)?|秦(?:朝|代)|"
    r"秦汉(?:时期)?|西汉|东汉|汉(?:朝|代)|三国(?:时期)?|西晋|东晋|"
    r"北魏(?:时期)?|魏晋(?:南北朝)?|南北朝|隋(?:朝|代)|隋唐|"
    r"唐宋(?:时期)?|唐(?:朝|代)|五代十国|北宋|南宋|宋(?:朝|代)|宋元|"
    r"辽代|金代|元末明初|元(?:朝|代)|明(?:朝|代)|明清|清(?:朝|代)|"
    r"民国(?:时期)?|"
    r"近代|现代|当代|[新旧]石器时代|(?:公元前|公元)?\d{1,4}年|"
    r"(?:公元前|公元)?\d{1,2}世纪(?:前期|中期|后期|初|中叶|末)?|"
    r"(?:建安|贞观|开元|天宝|元嘉|开皇|大业|洪武|永乐|嘉靖|万历|康熙|雍正|乾隆)年间"
)
_TIME_EVENT_RE = re.compile(
    r"出现|成书|形成|始建|建于|建立|设立|创立|实行|使用|产生|完成|问世|"
    r"创作|生活|活动|制定|推行|实施|颁布|编纂|编成|流行|成熟|发展|延续|"
    r"兴盛|盛行|始于|终于|生于|卒于"
)
_TIME_IDENTITY_RE = re.compile(
    r"(?:是|为|属于)[^，。；]{0,12}(?:先秦|夏代|商代|西周|东周|春秋|战国|秦朝|秦代|"
    r"秦汉|西汉|东汉|汉朝|汉代|三国|西晋|东晋|北魏|魏晋|南北朝|"
    r"隋朝|隋代|隋唐|唐宋|唐朝|唐代|五代十国|北宋|南宋|宋朝|宋代|宋元|"
    r"辽代|金代|元末明初|元朝|元代|明朝|明代|明清|"
    r"清朝|清代|民国|近代|现代|当代|[新旧]石器时代)[^，。；]{0,10}"
    r"(?:人|诗人|作家|文学家|思想家|书法家|画家|作品|著作|制度|器物)?"
)
_TIME_COMPARISON_QUESTION_RE = re.compile(
    r"先后|顺序|排序|早于|晚于|时期排列|"
    r"(?:生活|活动|创作|所处)(?:时间|年代|时代|时期|朝代)最(?:早|晚)|"
    r"(?:出现|成书|建立|设立|创立|实行|使用|产生|完成|问世|形成)(?:时间)?最早|"
    r"最(?:早|晚)(?:出现|成书|建立|设立|创立|实行|使用|产生|完成|问世|形成)"
)
_TIME_COMPARISON_LINK_RE = re.compile(r"先于|后于|早于|晚于|依次|先后|顺序|最早|最晚|较早|较晚")
_TIME_FACT_SUBJECT_RE = re.compile(
    r"^(?:而|但|同时|随后|其中)?(?P<subject>[\u3400-\u9fffA-Za-z·《》“”]{1,30}?)"
    r"(?:生于|卒于|生活(?:于|在)?|活动(?:于|在)?|创作(?:于|在)?|"
    r"出现于|成书于|形成于|建立于|设立于|创立于|实行于|产生于|完成于|"
    r"是|为|属于)"
)
_TIME_CLAUSE_SPLIT_RE = re.compile(r"[，,;；。！!？?\n]+")
_TIME_CONTINUATION_RE = re.compile(
    r"^(?:其|他|她|该|此|这|并|又|同时|随后|其中|一生|作为|身为|"
    r"生活|活动|创作|出现|成书|建立|设立|创立|实行|使用|产生|完成|问世|形成|"
    r"主要(?:属于|生活|活动|创作|出现|成书|形成|处于|见于))"
)
_YEAR_RANGE_RE = re.compile(
    r"(?P<left_prefix>公元前|公元)?(?P<left>\d{1,4})年?\s*"
    r"(?:至|到|—|–|-)\s*"
    r"(?P<right_prefix>公元前|公元)?(?P<right>\d{1,4})年"
)
_REIGN_YEAR_PREFIX_RE = re.compile(
    r"^(?:建安|贞观|开元|天宝|元嘉|开皇|大业|大德|洪武|永乐|嘉靖|万历|康熙|雍正|乾隆)"
    r"[一二三四五六七八九十百〇零\d]{1,6}年(?:[（(]\d{1,4}[）)])?"
)
_TIME_ALIAS_GROUPS = (
    ("先秦", ("先秦",)),
    ("夏", ("夏代", "夏朝", "夏")),
    ("商", ("商代", "商朝", "商")),
    ("西周", ("西周",)),
    ("东周", ("东周",)),
    ("春秋", ("春秋时期", "春秋")),
    ("战国", ("战国时期", "战国")),
    ("秦汉", ("秦汉时期", "秦汉")),
    ("秦", ("秦代", "秦朝", "秦")),
    ("西汉", ("西汉",)),
    ("东汉", ("东汉",)),
    ("汉", ("汉代", "汉朝", "汉")),
    ("三国", ("三国时期", "三国")),
    ("西晋", ("西晋",)),
    ("东晋", ("东晋",)),
    ("北魏", ("北魏时期", "北魏")),
    ("魏晋南北朝", ("魏晋南北朝",)),
    ("南北朝", ("南北朝",)),
    ("隋", ("隋代", "隋朝", "隋")),
    ("隋唐", ("隋唐",)),
    ("唐宋", ("唐宋时期", "唐宋")),
    ("唐", ("唐代", "唐朝", "唐")),
    ("五代十国", ("五代十国",)),
    ("北宋", ("北宋",)),
    ("南宋", ("南宋",)),
    ("宋", ("宋代", "宋朝", "宋")),
    ("宋元", ("宋元",)),
    ("辽", ("辽代", "辽朝", "辽")),
    ("金", ("金代", "金朝", "金")),
    ("元末明初", ("元末明初",)),
    ("元", ("元代", "元朝", "元")),
    ("明", ("明代", "明朝", "明")),
    ("明清", ("明清",)),
    ("清", ("清代", "清朝", "清")),
    ("民国", ("民国时期", "民国")),
    ("近代", ("近代",)),
    ("现代", ("现代",)),
    ("当代", ("当代",)),
    ("新石器时代", ("新石器时代",)),
    ("旧石器时代", ("旧石器时代",)),
)
_COMPOSITE_TIME_COMPONENTS = {
    "秦汉": {"秦", "汉"},
    "魏晋南北朝": {"魏晋", "南北朝"},
    "隋唐": {"隋", "唐"},
    "唐宋": {"唐", "宋"},
    "宋元": {"宋", "元"},
    "元末明初": {"元", "明"},
    "明清": {"明", "清"},
}
_TIME_PARENT_CHILDREN = {
    "汉": {"西汉", "东汉"},
    "宋": {"北宋", "南宋"},
}
_TIME_DETAIL_VALUE_RE = re.compile(
    r"^(?:(?:公元前|公元)?\d{1,4}年|"
    r"(?:公元前|公元)?\d{1,2}世纪(?:前期|中期|后期|初|中叶|末)?|"
    r"(?:建安|贞观|开元|天宝|元嘉|开皇|大业|洪武|永乐|嘉靖|万历|康熙|雍正|乾隆)年间)$"
)
_BROAD_TIME_ANSWER_RE = re.compile(r"^(?:古代|古时|古时候)$")
_SHORT_CHRONOLOGY_FIT_RE = re.compile(r"^(?:时代|年代|时期|朝代)不同$")
_RELATIVE_TIME_STEM_RE = re.compile(r"去世后|之后|以后|此前|之前|早于|晚于|同时代")
_RELATIVE_TIME_FACT_RE = re.compile(r"生于|卒于|去世|在世|生卒|早于|晚于|同时代|先于|后于")
_TEMPLATE_BRIDGE_RE = re.compile(r"这是.{0,30}的相关思想主张|代表性思想主张[—:：]")
_BRIDGE_FILLER_RE = re.compile(
    r"^(?:和|与|及)?(?:都是|均为|同为|属于)?(?:中国|中华)?(?:重要)?(?:传统)?"
    r"(?:文化|哲学|思想)?(?:常识|知识|内容|观点|主张|概念|范畴)(?:之一)?$"
)
_SCHOOL_BRIDGE_PREDICATE_RE = re.compile(
    r"主张|认为|强调|提出|倡导|反对|解释|阐明|把.{0,24}(?:视为|作为|归于|统一|贯通)|"
    r"以.{0,24}为(?:核心|宗旨|原则|基础)"
)
_SCHOOL_CONTEXT_PREDICATE_RE = re.compile(
    r"(?:以|围绕)[^，。；]{2,24}(?:讨论|辨析)|(?:陈说|游说)[^，。；]{2,24}"
)
_SCHOOL_KNOWLEDGE_FACT_RE = re.compile(
    r"重视|主张|提出|强调|倡导|反对|列为|列入|归入|包括|代表|见于|载于|著有|创立|形成"
)
_FACT_RISK_RE = re.compile(
    r"吴道子是中国山水画的祖师|韩非子等.{0,12}均被称为[“\"]?前期法家|"
    r"世界上最早的天文学著作|古代经验科学出现的标志|由班固于东汉中元元年|"
    r"苏轼也对柳永持贬斥态度|(?:世界|中国|我国)(?:上)?[^，。；]{0,12}最(?:多|大|早|古老)|"
    r"《春秋》.{0,24}(?:三十五卷|十三经.{0,8}最长)|"
    r"经世致用一词由.{0,32}提出|(?:都江堰.{0,32}鳖灵|鳖灵.{0,32}都江堰)|"
    r"十大传世名画|顾炎武.{0,18}《日知录》.{0,18}提出.{0,8}天下兴亡|"
    r"原《洛神赋图》.{0,12}设色绢本|随性而动|存乎一心"
)
_WRONG_FIT_CONNECTOR_RE = re.compile(
    r"不|无关|并非|尚非|而非|属于|对应|混淆|时代|人物|作品|对象|少|多|早|晚|"
    r"提前|推后|遗漏|起点|终点|范围|题干|以前|之后|之前|以后"
)
_RIGHT_FIT_CONNECTOR_RE = re.compile(r"直接|符合|对应|正是|因此|所以|说明|题干|关系最密切")
_GENERIC_ANSWER_RE = re.compile(
    r"^(?:古代|近代|现代|当代|先秦|春秋|战国|秦代|汉代|西汉|东汉|魏晋|南北朝|"
    r"隋代|唐代|宋代|北宋|南宋|元代|明代|清代|儒家|道家|墨家|法家|名家|"
    r"阴阳家|纵横家|杂家|佛教|道教|.+(?:时期|时代|朝代|领域|工程|技术|制度|"
    r"学派|文体|书体|乐器|著作|作品|人物|方法|用途))$"
)
_TOPIC_GENERIC_MODIFIERS = (
    "中国",
    "中华",
    "古代",
    "古典",
    "传统",
    "著名",
    "相关",
    "主要",
    "典型",
)
_PLACE_QUESTION_RE = re.compile(
    r"(?:位于|坐落于|地处)(?:哪里|何处|何地|哪(?:一|个|座)?(?:地区|地方|城市|省份|省|州|县|流域)?)|"
    r"(?:哪|何|什么).{0,8}(?:地区|地点|地方|城市|省份|省|州|县|流域|所在地|地理位置)|"
    r"(?:所在地|发源地|地理位置)(?:是|为|在)?(?:哪里|何处|何地|哪|什么|[：:]?$)"
)
_SCHOOL_QUESTION_RE = re.compile(
    r"哪(?:一|个)?(?:学派|思想传统|思想流派|流派)|"
    r"(?:学派|思想传统|思想流派|流派)(?:归属|所属|是|为)[：:]?$"
)
_UNRELATED_TARGET_RE = re.compile(
    r"与[^，。；！？,;!?]{1,30}无关(?:的是|的(?:一项|著作|作品|人物)|(?=[，。；！？,;!?]|$))"
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _is_string(value: object) -> bool:
    return isinstance(value, str)


def _normalized(value: object) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", _text(value).lower())


def _is_generic_answer(value: object) -> bool:
    """Keep a quoted book title distinct from a same-named era."""

    text = _text(value)
    if re.fullmatch(r"《[^》]{1,40}》", text):
        return False
    return bool(_GENERIC_ANSWER_RE.fullmatch(_normalized(text)))


def _display_normalized(value: object) -> str:
    return re.sub(r"[ \t]+", "", _text(value).replace("\r\n", "\n").replace("\r", "\n"))


def _similar(left: object, right: object) -> float:
    a = _normalized(left)
    b = _normalized(right)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _cjk_bigrams(value: object) -> set[str]:
    text = re.sub(r"[^\u3400-\u9fff]", "", _text(value))
    return {text[index : index + 2] for index in range(max(0, len(text) - 1))}


def _topic_core(value: object) -> str:
    key = _normalized(value)
    for modifier in _TOPIC_GENERIC_MODIFIERS:
        key = key.replace(_normalized(modifier), "")
    return key


def _anchor_residual(value: object, subject: object, answer: object) -> str:
    text = _normalized(value)
    for removable in sorted({_normalized(subject), _normalized(answer)}, key=len, reverse=True):
        if removable:
            text = text.replace(removable, "")
    relations = (
        "的典型艺术特征是",
        "的典型特征是",
        "这一观点是",
        "这一主张是",
        "这一思想是",
        "这一说法是",
        "对应的是",
        "主要关联",
        "创作时期",
        "生活时期",
        "出现时期",
        "成书时期",
        "对应",
        "属于",
        "时期",
        "时代",
        "朝代",
        "学派",
        "观点",
        "主张",
        "思想",
        "特征",
        "典型",
        "指",
        "是",
        "为",
        "的",
    )
    for relation in sorted(relations, key=len, reverse=True):
        text = text.replace(_normalized(relation), "")
    return text


def _fact_names_option(fact: object, option: object) -> bool:
    fact_key = _normalized(fact)
    option_key = _normalized(option)
    if not fact_key or not option_key:
        return False
    if option_key in fact_key:
        return True
    option_bigrams = _cjk_bigrams(option)
    if len(option_bigrams) < 2:
        return False
    return len(option_bigrams & _cjk_bigrams(fact)) / len(option_bigrams) >= 0.45


def _knowledge_is_grounded(
    value: object,
    subject: object,
    answer: object,
    *,
    allow_generic_answer: bool = False,
) -> bool:
    knowledge_key = _normalized(value)
    subject_key = _normalized(subject)
    answer_key = _normalized(answer)
    if not knowledge_key:
        return False
    if subject_key and subject_key in knowledge_key:
        return True
    if subject_key and len(subject_key) <= 8:
        match = SequenceMatcher(None, subject_key, knowledge_key).find_longest_match(
            0,
            len(subject_key),
            0,
            len(knowledge_key),
        )
        if match.size >= 2:
            return True
    if not answer_key or answer_key not in knowledge_key:
        return False
    if not _is_generic_answer(answer):
        return True
    return bool(
        allow_generic_answer
        and len(_anchor_residual(value, subject, answer)) >= 8
        and (
            _SCHOOL_KNOWLEDGE_FACT_RE.search(_text(value))
            or re.search(r"《[^》]{1,40}》", _text(value))
        )
    )


def _school_bridge_has_substantive_claim(
    value: object,
    subject: object,
    answer: object,
) -> bool:
    """Allow context verbs only when they support a grounded school claim."""

    if _SCHOOL_BRIDGE_PREDICATE_RE.search(_text(value)):
        return True
    value_key = _normalized(value)
    answer_key = _normalized(answer)
    return bool(
        _SCHOOL_CONTEXT_PREDICATE_RE.search(_text(value))
        and answer_key
        and answer_key in value_key
        and _weak_topic_overlap(value, subject)
        and len(_anchor_residual(value, subject, answer)) >= 8
    )


def _evidence_is_grounded(value: object, subject: object, answer: object) -> bool:
    evidence_key = _normalized(value)
    subject_key = _normalized(subject)
    answer_key = _normalized(answer)
    if not evidence_key:
        return False
    if subject_key and subject_key in evidence_key:
        return True
    if answer_key and not _is_generic_answer(answer) and answer_key in evidence_key:
        return True
    subject_bigrams = _cjk_bigrams(subject)
    if not subject_bigrams:
        return False
    overlap = len(subject_bigrams & _cjk_bigrams(value))
    return overlap >= max(2, int(len(subject_bigrams) * 0.4 + 0.999))


def _facts_overlap(left: object, right: object) -> bool:
    left_bigrams = _cjk_bigrams(left)
    right_bigrams = _cjk_bigrams(right)
    if not left_bigrams or not right_bigrams:
        return False
    overlap = len(left_bigrams & right_bigrams)
    return overlap >= 3 or (
        overlap >= 2 and overlap / min(len(left_bigrams), len(right_bigrams)) >= 0.35
    )


def _specific_grounding_bigrams(value: object) -> set[str]:
    generic_terms = (
        "中华文化",
        "文化常识",
        "人物作品",
        "作者著作",
        "思想主张",
        "时期时代",
        "朝代年代",
        "诗人作家",
        "画家书法家",
        "学派制度",
        "典籍地点",
        "对应关系",
        "共同特点",
        "错误选项",
        "不属于不包括",
        "作用影响",
    )
    generic_bigrams: set[str] = set()
    for term in generic_terms:
        generic_bigrams.update(_cjk_bigrams(term))
    return _cjk_bigrams(value) - generic_bigrams


def _strong_topic_overlap(value: object, target: object) -> bool:
    text = _text(value)
    value_key = _normalized(text)
    target_text = _text(target)
    target_key = _normalized(target_text)
    if not value_key or not target_key:
        return False

    quoted_entities = [
        _normalized(left or right)
        for left, right in re.findall(r"《([^》]+)》|[“\"]([^”\"]+)[”\"]", target_text)
        if _normalized(left or right)
    ]
    if any(len(entity) >= 2 and entity in value_key for entity in quoted_entities):
        return True

    target_core = _topic_core(target_text)
    value_core = _topic_core(text)
    if len(target_core) >= 4 and target_core in value_core:
        core_bigrams = _specific_grounding_bigrams(target_core)
        if len(core_bigrams & _specific_grounding_bigrams(value_core)) >= 2:
            return True

    generic_short_topics = {
        "四书",
        "六部",
        "古琴",
        "诗歌",
        "文学",
        "艺术",
        "科技",
        "历史",
        "哲学",
        "制度",
        "典籍",
        "书法",
        "绘画",
        "音乐",
        "戏曲",
        "建筑",
        "医学",
        "农学",
        "水利",
        "天文",
        "历法",
        "文化",
    }
    if len(target_key) == 2 and target_key not in generic_short_topics:
        return target_key in value_key

    target_cjk = re.sub(r"[^㐀-鿿]", "", target_text)
    value_cjk = re.sub(r"[^㐀-鿿]", "", text)
    target_trigrams = {
        target_cjk[index : index + 3]
        for index in range(max(0, len(target_cjk) - 2))
    }
    value_trigrams = {
        value_cjk[index : index + 3]
        for index in range(max(0, len(value_cjk) - 2))
    }
    generic_trigrams = {
        "中华文",
        "华文化",
        "文化常",
        "化常识",
        "中国古",
        "国古代",
        "古代文",
        "思想主",
        "想主张",
        "时期时",
        "期时代",
        "朝代年",
        "代年代",
        "唐代诗",
        "代诗人",
        "对应关",
        "应关系",
    }
    return bool((target_trigrams & value_trigrams) - generic_trigrams)


def _weak_topic_overlap(value: object, target: object) -> bool:
    value_key = _normalized(value)
    target_key = _normalized(target)
    if not value_key or not target_key:
        return False
    if len(target_key) >= 2 and target_key in value_key:
        return True
    return bool(_cjk_bigrams(value) & _cjk_bigrams(target))


def _grounding_target_overlap(value: object, target: object) -> bool:
    value_key = _normalized(value)
    target_key = _normalized(target)
    if not value_key or not target_key:
        return False
    if _is_generic_answer(target):
        return False
    if (
        len(target_key) >= 2
        and target_key in value_key
    ):
        return True
    target_bigrams = _specific_grounding_bigrams(target)
    if not target_bigrams:
        return False
    overlap = len(target_bigrams & _specific_grounding_bigrams(value))
    if len(target_bigrams) <= 2:
        return overlap == len(target_bigrams)
    return overlap >= 2 and overlap / len(target_bigrams) >= 0.3


def culture_bridge_is_grounded(
    value: object,
    *,
    subject: object = "",
    clue: object = "",
    correct_option: object = "",
    question_form: object = "",
) -> bool:
    """Require the learner-facing bridge to stay on the actual question fact."""

    topic_targets = [target for target in (subject, clue) if _text(target)]
    strong_topic = any(_strong_topic_overlap(value, target) for target in topic_targets)
    weak_topic = any(_weak_topic_overlap(value, target) for target in topic_targets)
    answer_overlap = _grounding_target_overlap(value, correct_option)
    if _text(question_form) in {"negative_identification", "odd_one_out"}:
        return strong_topic or answer_overlap
    return strong_topic or (weak_topic and answer_overlap)


def _fit_template_family(value: object) -> str:
    text = _text(value)
    if re.search(r"说明的是“[^”]+”，不是“[^”]+”", text):
        return "explains_not_topic"
    if re.search(r"这个时代对应.+，不是.+", text):
        return "era_corresponds_not_topic"
    if re.search(r"其.+与“[^”]+”不同", text):
        return "relation_differs"
    if re.search(r"对象或关系不同|对象不同，不是", text):
        return "generic_object_mismatch"
    return ""


def _enumeration_incomplete(value: object) -> bool:
    text = _text(value)
    match = re.search(r"([二三四五六七八九十两]|\d+)大.{0,12}?分别为(.+)$", text)
    if not match:
        return False
    counts = {"两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    expected = counts.get(match.group(1), int(match.group(1)) if match.group(1).isdigit() else 0)
    actual = len([item for item in re.split(r"[、，,；;和及]", match.group(2)) if _text(item)])
    return bool(expected and actual < expected)


def _sentence(value: object) -> str:
    text = _text(value).rstrip("。！？!?；; ")
    return f"{text}。" if text else ""


def _clause(value: object) -> str:
    return _text(value).rstrip("。！？!?；;，, ")


def _issue(code: str, message: str, severity: str = "high") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def is_culture_v3_metadata(metadata: object) -> bool:
    return isinstance(metadata, Mapping) and _text(metadata.get("version")).startswith("3.")


def _question_focus(value: object) -> str:
    """Return the final semantic clause, where Chinese choice stems ask the target."""

    clauses = [
        _text(clause)
        for clause in re.split(r"[，,；;。]+", _text(value))
        if _text(clause)
    ]
    return clauses[-1] if clauses else _text(value)


def infer_culture_reasoning_mode(question: Mapping[str, object]) -> str:
    """Route common culture questions to a fact-specific reasoning pattern."""

    stem = _text(question.get("stem"))
    focus = _question_focus(stem)
    if is_culture_chronology_question(stem):
        return "chronology"
    if _PLACE_QUESTION_RE.search(focus):
        return "place_object_mapping"
    if re.search(r"著作|作品", stem) and _UNRELATED_TARGET_RE.search(focus):
        return "work_author_era"
    if _SCHOOL_QUESTION_RE.search(focus):
        return "person_school_claim"
    if re.search(r"含义|释义|解释|指的是|概念是|定义|何谓", stem):
        return "concept_definition"
    if re.search(r"诗句|哪句诗|名句|句意|意象|表达了|体现了|描写的是", stem):
        return "quote_meaning"
    if re.search(r"共同点|不同的是|不属于|不包括|不含|没有下列|例外|哪一类|门类|分类|归类|哪一项不同", stem):
        return "category_comparison"
    if re.search(r"制度|选官|科举|职能|功能|作用|用途|用于", stem):
        return "institution_function"
    if re.search(r"作者|曲作者|创作者|撰写|著有|代表作|作品有|作品包括|出自|典籍.*关系|作品.*关系", stem):
        return "work_author_era"
    if re.search(r"取经|东渡|出使|变法|改革|事迹|贡献|影响|推动|促进", stem):
        return "person_event_effect"
    if re.search(r"学派|思想传统|思想家|主张|命题|学说|流派|代表人物", focus):
        return "person_school_claim"
    return "direct_fact"


def is_culture_chronology_question(value: object) -> bool:
    """Return whether the stem truly asks for a time value or time comparison."""

    text = _text(value)
    return bool(
        _CHRONOLOGY_QUESTION_RE.search(text)
        or _CHRONOLOGY_FOCUS_RE.search(_question_focus(text))
    )


def culture_memory_strategy_requirement(
    question: Mapping[str, object],
    metadata: Mapping[str, object],
) -> str | None:
    """Return a high-confidence memory strategy, leaving low-value facts optional.

    This gate intentionally uses only stable question semantics. Difficulty and
    model-authored ``difficulty_features`` must never manufacture a memory card.
    ``None`` means that the model may still add a genuinely useful hook, not that
    every such question should receive one.
    """

    stem = _text(question.get("stem"))
    reasoning_mode = _text(metadata.get("reasoning_mode")) or infer_culture_reasoning_mode(question)
    answer = _text(question.get("answer")).upper()
    correct_option = _text(question.get(OPTION_FIELDS.get(answer, "")))
    option_set = frozenset(
        _normalized(question.get(OPTION_FIELDS[label]))
        for label in OPTION_LABELS
        if _normalized(question.get(OPTION_FIELDS[label]))
    )

    if _MEMORY_FIXED_DATE_QUESTION_RE.search(stem):
        return "keyword"
    if _MEMORY_ORDERED_LABEL_RE.search(stem):
        return "chain"
    if option_set in _MEMORY_DIAGNOSTIC_OPTION_SETS:
        return "contrast"
    if reasoning_mode == "person_event_effect" or _MEMORY_PROCESS_SIGNAL_RE.search(stem):
        return "chain"
    if reasoning_mode == "chronology" and (
        _TIME_COMPARISON_QUESTION_RE.search(stem)
        or _canonical_time_option(correct_option) in _COMPOSITE_TIME_COMPONENTS
    ):
        return "chain"
    if reasoning_mode in {"category_comparison", "work_author_era"}:
        return "contrast"
    if _MEMORY_PERSON_WORK_CONTRAST_RE.search(stem):
        return "contrast"
    if _MEMORY_PERSON_CLAIM_CONTRAST_RE.search(stem):
        return "contrast"
    if reasoning_mode == "place_object_mapping":
        return "keyword"
    if _MEMORY_FIXED_LABEL_RE.search(stem) or _MEMORY_PLACE_CLUE_RE.search(stem):
        return "keyword"
    return None


def _canonical_time_option(value: object) -> str:
    key = _normalized(value)
    for canonical, aliases in _TIME_ALIAS_GROUPS:
        if key in {_normalized(alias) for alias in aliases}:
            return canonical
    if re.fullmatch(
        r"(?:公元前|公元)?\d{1,4}年|"
        r"(?:公元前|公元)?\d{1,2}世纪(?:前期|中期|后期|初|中叶|末)?|"
        r"(?:建安|贞观|开元|天宝|元嘉|开皇|大业|洪武|永乐|嘉靖|万历|康熙|雍正|乾隆)年间",
        key,
    ):
        return key
    return ""


def _explicit_time_values(value: object) -> set[str]:
    text = re.sub(r"《[^》]*》", "", _text(value))
    values: set[str] = set()
    for match in _YEAR_RANGE_RE.finditer(text):
        left_prefix = match.group("left_prefix") or ""
        right_prefix = match.group("right_prefix") or left_prefix
        values.add(f"{left_prefix}{match.group('left')}年")
        values.add(f"{right_prefix}{match.group('right')}年")
    for match in _TIME_VALUE_RE.finditer(text):
        raw = match.group(0)
        values.add(_canonical_time_option(raw) or _normalized(raw))
    return values


def _time_values_cover_expected(
    bridge_values: set[str],
    expected_values: set[str],
) -> bool:
    return all(
        (
            expected in bridge_values
            or all(
                any(
                    _time_values_are_compatible(actual, component)
                    for actual in bridge_values
                )
                for component in _COMPOSITE_TIME_COMPONENTS[expected]
            )
        )
        if expected in _COMPOSITE_TIME_COMPONENTS
        else any(
            _time_values_are_compatible(actual, expected)
            for actual in bridge_values
        )
        for expected in expected_values
    )


def _time_values_are_compatible(actual: str, expected: str) -> bool:
    """Treat a parent dynasty and its named subdivision as one time family."""

    if actual == expected:
        return True
    if actual.startswith("公元") and not actual.startswith("公元前") and actual[2:] == expected:
        return True
    if expected.startswith("公元") and not expected.startswith("公元前") and expected[2:] == actual:
        return True
    for parent, children in _TIME_PARENT_CHILDREN.items():
        if actual == parent and expected in children:
            return True
        if expected == parent and actual in children:
            return True
    return False


def _time_values_overlap(left: str, right: str) -> bool:
    """Return whether two option periods overlap enough to make a choice ambiguous."""

    if _time_values_are_compatible(left, right):
        return True
    if left in _COMPOSITE_TIME_COMPONENTS and any(
        _time_values_are_compatible(right, component)
        for component in _COMPOSITE_TIME_COMPONENTS[left]
    ):
        return True
    if right in _COMPOSITE_TIME_COMPONENTS and any(
        _time_values_are_compatible(left, component)
        for component in _COMPOSITE_TIME_COMPONENTS[right]
    ):
        return True
    return False


def _chronology_options_overlap(
    correct_option: object,
    *,
    answer: str,
    options: Mapping[str, object],
) -> bool:
    expected = _canonical_time_option(correct_option)
    if not expected or _TIME_DETAIL_VALUE_RE.fullmatch(expected):
        return False
    for label, option in options.items():
        if label == answer:
            continue
        actual = _canonical_time_option(option)
        if actual and not _TIME_DETAIL_VALUE_RE.fullmatch(actual) and _time_values_overlap(expected, actual):
            return True
    return False


def _short_chronology_fit_has_date_fact(fact: object, fit: object) -> bool:
    if not _SHORT_CHRONOLOGY_FIT_RE.fullmatch(_text(fit)):
        return False
    return any(
        _TIME_DETAIL_VALUE_RE.fullmatch(value)
        for value in _explicit_time_values(fact)
    )


def _time_binding_state(
    actual_values: set[str],
    expected_values: set[str],
) -> bool | None:
    """Return True/False for a binding, or None for date-only context."""

    if not actual_values:
        return None
    has_expected = any(
        _time_values_are_compatible(actual, expected)
        for actual in actual_values
        for expected in expected_values
    )
    expected_periods = {
        value for value in expected_values if not _TIME_DETAIL_VALUE_RE.fullmatch(value)
    }
    expected_details = expected_values - expected_periods
    if expected_details and not expected_periods:
        competing_details = {
            actual
            for actual in actual_values
            if _TIME_DETAIL_VALUE_RE.fullmatch(actual)
            and not any(
                _time_values_are_compatible(actual, expected)
                for expected in expected_details
            )
        }
        if competing_details:
            return False
        return True if has_expected else None
    competing_periods = {
        actual
        for actual in actual_values
        if not _TIME_DETAIL_VALUE_RE.fullmatch(actual)
        and not any(
            _time_values_are_compatible(actual, expected)
            for expected in expected_periods
        )
    }
    if competing_periods:
        return False
    if has_expected:
        return True
    # Numeric years, centuries and reign periods may qualify a subject without
    # replacing its dynasty.  Let an adjacent continuation supply the dynasty.
    return None


def _expanded_time_values(values: set[str]) -> set[str]:
    expanded = set(values)
    for value in values:
        expanded.update(_COMPOSITE_TIME_COMPONENTS.get(value, set()))
    return expanded


def _time_led_clause_continues_subject(value: object) -> bool:
    # A comma may separate the named subject from a predicate such as
    # “于元代……成书”.  Accept the leading preposition only when the clause then
    # starts with an explicit time value and ends in a time-event predicate;
    # this still rejects loose context such as “在现代文学研究中……”.
    text = re.sub(r"^(?:于|在)", "", _text(value))
    consumed_time = False
    while text:
        match = _TIME_VALUE_RE.match(text)
        if not match:
            break
        consumed_time = True
        text = text[match.end() :].lstrip("时期年间、 的于在")
    text = _REIGN_YEAR_PREFIX_RE.sub("", text)
    text = re.sub(r"^(?:并|又|仍|随后|继续|进一步|逐渐)", "", text)
    return bool(consumed_time and _TIME_EVENT_RE.match(text))


def _time_values_bound_to_subject(
    value: object,
    *,
    subject: object,
) -> set[str]:
    """Collect time values from clauses that form one subject fact window."""

    if not _text(subject):
        return set()
    clauses = [
        _text(clause)
        for clause in _TIME_CLAUSE_SPLIT_RE.split(_text(value))
        if _text(clause)
    ]
    subject_indexes = [
        index
        for index, clause in enumerate(clauses)
        if _strong_topic_overlap(clause, subject)
    ]
    if not subject_indexes:
        return set()

    bound_values: set[str] = set()
    for index in subject_indexes:
        bound_values.update(_explicit_time_values(clauses[index]))

        following_index = index + 1
        while following_index < len(clauses):
            following = clauses[following_index]
            follows_subject = bool(
                _TIME_CONTINUATION_RE.search(following)
                or _time_led_clause_continues_subject(following)
                or (
                    _weak_topic_overlap(following, subject)
                    and (
                        _TIME_EVENT_RE.search(following)
                        or _TIME_IDENTITY_RE.search(following)
                    )
                )
            )
            if not follows_subject:
                break
            bound_values.update(_explicit_time_values(following))
            following_index += 1

        if index > 0:
            preceding = clauses[index - 1]
            preceding_values = _explicit_time_values(preceding)
            preceding_residual = _normalized(_TIME_VALUE_RE.sub("", preceding))
            if preceding_residual in {"", "时期", "时代", "朝代", "年代", "年间"}:
                bound_values.update(preceding_values)
    return bound_values


def _time_value_is_bound_to_subject(
    value: object,
    *,
    subject: object,
    expected_values: set[str],
) -> bool:
    """Bind every required time stage to the subject's semantic window."""

    bound_values = _time_values_bound_to_subject(value, subject=subject)
    return bool(
        bound_values
        and _time_values_cover_expected(bound_values, expected_values)
        and _time_binding_state(
            bound_values,
            _expanded_time_values(expected_values),
        )
        is not False
    )


def _comparison_time_fact_subjects(value: object) -> set[str]:
    subjects: set[str] = set()
    for clause in _TIME_CLAUSE_SPLIT_RE.split(_text(value)):
        if not _explicit_time_values(clause):
            continue
        match = _TIME_FACT_SUBJECT_RE.search(_text(clause))
        if not match:
            continue
        subject = _normalized(match.group("subject"))
        if subject and subject not in {"其", "他", "她", "该", "此", "这", "一生"}:
            subjects.add(subject)
    return subjects


def culture_bridge_has_time_link(
    value: object,
    *,
    stem: object = "",
    correct_option: object = "",
    subject: object = "",
) -> bool:
    """Require the actual answer time, or two dated facts for a comparison."""

    text = _text(value)
    bridge_values = _explicit_time_values(text)
    if _TIME_COMPARISON_QUESTION_RE.search(_text(stem)):
        return bool(
            len(_comparison_time_fact_subjects(text)) >= 2
            and _TIME_COMPARISON_LINK_RE.search(text)
        )

    expected_values = _explicit_time_values(correct_option)
    exact_option = _canonical_time_option(correct_option)
    if exact_option:
        expected_values.add(exact_option)
    if not expected_values:
        expected_values = _explicit_time_values(stem)
    if expected_values and not _time_values_cover_expected(bridge_values, expected_values):
        return False
    if expected_values and _time_binding_state(
        bridge_values,
        _expanded_time_values(expected_values),
    ) is False:
        return False
    if _text(subject) and not _time_value_is_bound_to_subject(
        text,
        subject=subject,
        expected_values=expected_values,
    ):
        return False
    return bool(
        bridge_values
        and (_TIME_EVENT_RE.search(text) or _TIME_IDENTITY_RE.search(text))
    )


def culture_v3_display_budget(question: Mapping[str, object], metadata: Mapping[str, object]) -> int:
    """Return a form-aware upper bound instead of one fixed explanation size."""

    form = _text(metadata.get("question_form"))
    base = {
        "direct_identification": 340,
        "relationship_match": 360,
        "negative_identification": 405,
        "odd_one_out": 420,
    }.get(form, 360)
    try:
        difficulty = int(question.get("difficulty") or 3)
    except (TypeError, ValueError):
        difficulty = 3
    if difficulty >= 4:
        base += 10
    return min(base, 430)


def render_culture_explanation_v3(
    question: Mapping[str, object],
    metadata: Mapping[str, object],
) -> str:
    """Render the current ExplanationPanel labels from a V3 teaching contract."""

    steps = metadata.get("reasoning_steps")
    analyses = metadata.get("option_analysis")
    if not isinstance(steps, Mapping) or not isinstance(analyses, Mapping):
        raise ValueError("culture_v3 缺少 reasoning_steps 或 option_analysis")

    clue = _clause(steps.get("clue"))
    bridge = _clause(steps.get("bridge"))
    conclusion = _clause(steps.get("conclusion"))
    if not all((clue, bridge, conclusion)):
        raise ValueError("culture_v3.reasoning_steps 必须包含 clue、bridge、conclusion")

    answer = _text(question.get("answer")).upper()
    lines = ["解题思路：", f"{clue}→{bridge}→{_sentence(conclusion)}", "", "选项解析："]
    for label in OPTION_LABELS:
        item = analyses.get(label)
        if not isinstance(item, Mapping):
            raise ValueError(f"culture_v3.option_analysis 缺少 {label}")
        fact = _clause(item.get("fact"))
        fit = _clause(item.get("fit"))
        if not fact or not fit:
            raise ValueError(f"culture_v3.option_analysis.{label} 缺少 fact 或 fit")
        option = _text(question.get(OPTION_FIELDS[label]))
        option_prefix = f"{option}：" if option and len(option) <= 22 and _normalized(option) not in _normalized(fact) else ""
        mark = "✓" if label == answer else "×"
        lines.append(f"{label}. {mark} {_sentence(f'{option_prefix}{fact}；{fit}')}")

    lines.extend(["", "知识点：", _sentence(metadata.get("knowledge_extension"))])
    memory_hook = _text(metadata.get("memory_hook"))
    if memory_hook:
        lines.extend(["", "记忆方法：", _sentence(memory_hook)])
    return "\n".join(lines)


def validate_culture_v3_contract(
    question: Mapping[str, object],
    metadata: object,
) -> list[dict[str, str]]:
    """Validate teaching semantics that cannot be guaranteed by display labels."""

    if not isinstance(metadata, Mapping):
        return [_issue("missing_culture_v3_metadata", "中华文化 V3 必须提供 culture_v3 对象", "critical")]

    issues: list[dict[str, str]] = []
    missing = sorted(field for field in CULTURE_V3_REQUIRED_FIELDS if field not in metadata)
    if missing:
        issues.append(
            _issue(
                "incomplete_culture_v3_metadata",
                f"culture_v3 缺少字段：{'、'.join(missing)}",
                "critical",
            )
        )
    extra_metadata_fields = sorted(
        str(field) for field in metadata if field not in CULTURE_V3_REQUIRED_FIELDS
    )
    if extra_metadata_fields:
        issues.append(
            _issue(
                "culture_v3_unknown_fields",
                f"culture_v3 出现契约外字段：{'、'.join(extra_metadata_fields)}",
                "critical",
            )
        )

    scalar_fields = (
        "version",
        "question_form",
        "reasoning_mode",
        "evidence_excerpt",
        "knowledge_extension",
        "memory_strategy",
        "memory_hook",
        "scope_level",
        "controversy_status",
        "verification_status",
    )
    non_string_fields = [
        field
        for field in scalar_fields
        if field in metadata and not _is_string(metadata.get(field))
    ]
    if non_string_fields:
        issues.append(
            _issue(
                "culture_v3_non_string_field",
                f"culture_v3 文本字段必须是字符串：{'、'.join(non_string_fields)}",
                "critical",
            )
        )

    difficulty_features = metadata.get("difficulty_features")
    if not (
        isinstance(difficulty_features, list)
        and difficulty_features
        and all(_is_string(item) and _text(item) for item in difficulty_features)
    ):
        issues.append(
            _issue(
                "invalid_culture_v3_difficulty_features",
                "difficulty_features 必须是至少含一条具体难点的字符串数组",
            )
        )

    if _text(metadata.get("version")) != "3.0":
        issues.append(_issue("invalid_culture_v3_version", "culture_v3.version 必须为 3.0"))

    stem = _text(question.get("stem"))
    answer = _text(question.get("answer")).upper()
    options = {label: _text(question.get(field)) for label, field in OPTION_FIELDS.items()}
    correct_option = options.get(answer, "")
    chronology_question = is_culture_chronology_question(question.get("stem"))

    question_form = _text(metadata.get("question_form"))
    if question_form not in CULTURE_V3_FORMS:
        issues.append(_issue("invalid_culture_v3_question_form", "culture_v3.question_form 不在允许范围内"))
    stem_for_direction = re.sub(
        r"无一不是|没有一个不是|莫不(?:是)?",
        "均是",
        _text(question.get("stem")),
    )
    negative_stem = bool(
        re.search(
            r"不正确|不属于|不包括|并非|不是|错误(?:的是|项)?|有误(?:的是)?|不当(?:的是)?|"
            r"不同的是|不相同|不能说明|不应|不宜|需排除|排除对象|例外|不在(?:该|此|本|名单|范围)|"
            r"与[^，。；！？,;!?]{1,30}无关(?:的是|的(?:一项|著作|作品|人物)|(?=[，。；！？,;!?]|$))",
            stem_for_direction,
        )
    )
    if negative_stem != (question_form in {"negative_identification", "odd_one_out"}):
        issues.append(_issue("culture_v3_question_form_mismatch", "question_form 与题干正向或逆向设问不一致"))
    reasoning_mode = _text(metadata.get("reasoning_mode"))
    if reasoning_mode not in CULTURE_V3_REASONING_MODES:
        issues.append(_issue("invalid_culture_v3_reasoning_mode", "culture_v3.reasoning_mode 不在允许范围内"))
    else:
        expected_mode = infer_culture_reasoning_mode(question)
        if expected_mode != "direct_fact" and reasoning_mode != expected_mode:
            issues.append(
                _issue(
                    "culture_v3_reasoning_mode_mismatch",
                    f"题干应使用 {expected_mode} 推理路径，而不是 {reasoning_mode}",
                )
            )

    if _text(metadata.get("scope_level")) != "core":
        issues.append(_issue("culture_v3_scope_not_core", "只接收核心、稳定的普通文化常识"))
    if _text(metadata.get("controversy_status")) != "stable":
        issues.append(_issue("culture_v3_fact_not_stable", "争议性或考据型事实应进入人工复核"))
    if _text(metadata.get("verification_status")) != "cross_checked":
        issues.append(_issue("culture_v3_not_cross_checked", "culture_v3.verification_status 必须为 cross_checked"))

    anchor = metadata.get("fact_anchor")
    if not isinstance(anchor, Mapping) or any(
        not _is_string(anchor.get(key)) or not _text(anchor.get(key))
        for key in ("subject", "relation", "object")
    ):
        issues.append(_issue("invalid_culture_v3_fact_anchor", "fact_anchor 必须明确对象、关系和值", "critical"))
    else:
        extra_anchor_fields = sorted(
            str(field) for field in anchor if field not in {"subject", "relation", "object"}
        )
        if extra_anchor_fields:
            issues.append(
                _issue(
                    "culture_v3_fact_anchor_unknown_fields",
                    f"fact_anchor 出现契约外字段：{'、'.join(extra_anchor_fields)}",
                    "critical",
                )
            )
        if correct_option and _normalized(correct_option) != _normalized(anchor.get("object")):
            issues.append(_issue("culture_v3_fact_anchor_answer_mismatch", "fact_anchor.object 必须落到正确选项原文"))

    evidence = _text(metadata.get("evidence_excerpt"))
    if len(evidence) < 8 or _GENERIC_FACT_RE.search(evidence):
        issues.append(_issue("weak_culture_v3_evidence", "evidence_excerpt 必须是可核对的具体文化事实"))
    if (
        _LEADING_REFERENCE_RE.search(evidence)
        or _OCR_SOURCE_SEAM_RE.search(evidence)
        or _INCOMPLETE_CLAUSE_END_RE.search(evidence)
        or _FACT_RISK_RE.search(evidence)
        or re.search(r"(?:谁|哪位|哪个|什么|如何|多少).{0,18}[？?]", evidence)
    ):
        issues.append(_issue("culture_v3_evidence_requires_review", "evidence_excerpt 含指代不明、残句或需复核事实"))
    evidence_bridge = ""
    raw_reasoning_steps = metadata.get("reasoning_steps")
    if isinstance(raw_reasoning_steps, Mapping):
        evidence_bridge = raw_reasoning_steps.get("bridge")
    evidence_key = _normalized(evidence)
    answer_key = _normalized(correct_option)
    bridge_rescues_grounding = bool(
        _is_string(evidence_bridge)
        and _facts_overlap(evidence, evidence_bridge)
        and (
            (answer_key and answer_key in evidence_key)
            or _facts_overlap(evidence, correct_option)
        )
    )
    option_bigrams = _cjk_bigrams(correct_option)
    correction_fact_overlap = len(
        (_cjk_bigrams(evidence) - option_bigrams)
        & (_cjk_bigrams(evidence_bridge) - option_bigrams)
    )
    inverse_false_correction = bool(_INVERSE_FALSE_CORRECTION_RE.search(evidence))
    if question_form in {"negative_identification", "odd_one_out"}:
        evidence_is_grounded = bool(
            bridge_rescues_grounding
            and correction_fact_overlap >= 2
            and not inverse_false_correction
        )
        if evidence and not _INVERSE_DIRECTION_RE.search(evidence):
            issues.append(
                _issue(
                    "culture_v3_inverse_evidence_lacks_correction",
                    "逆向题 evidence_excerpt 必须明确写出不属于、不在、并非、不同或例外等纠偏边界",
                )
            )
        if inverse_false_correction:
            issues.append(
                _issue(
                    "culture_v3_inverse_evidence_false_correction",
                    "逆向题 evidence_excerpt 不得用‘并非错误、不是不正确’等双重否定伪装纠偏事实",
                )
            )
    else:
        evidence_is_grounded = bool(
            isinstance(anchor, Mapping)
            and (
                _evidence_is_grounded(evidence, anchor.get("subject"), correct_option)
                or bridge_rescues_grounding
            )
        )
    if isinstance(anchor, Mapping) and not evidence_is_grounded:
        issues.append(_issue("culture_v3_evidence_not_grounded", "evidence_excerpt 必须与题干对象或正确知识直接相关"))

    steps = metadata.get("reasoning_steps")
    if not isinstance(steps, Mapping):
        issues.append(_issue("invalid_culture_v3_reasoning_steps", "reasoning_steps 必须包含 clue、bridge、conclusion", "critical"))
        clue = bridge = conclusion = ""
    else:
        extra_step_fields = sorted(
            str(field) for field in steps if field not in {"clue", "bridge", "conclusion"}
        )
        if extra_step_fields:
            issues.append(
                _issue(
                    "culture_v3_reasoning_steps_unknown_fields",
                    f"reasoning_steps 出现契约外字段：{'、'.join(extra_step_fields)}",
                    "critical",
                )
            )
        if any(not _is_string(steps.get(key)) for key in ("clue", "bridge", "conclusion")):
            issues.append(
                _issue(
                    "culture_v3_reasoning_step_not_string",
                    "reasoning_steps.clue、bridge、conclusion 必须是字符串",
                    "critical",
                )
            )
        clue = _text(steps.get("clue"))
        bridge = _text(steps.get("bridge"))
        conclusion = _text(steps.get("conclusion"))
        event_bridge = bridge
        for removable in (
            _text(anchor.get("subject")) if isinstance(anchor, Mapping) else "",
            correct_option,
        ):
            if removable:
                event_bridge = event_bridge.replace(removable, "")
        bridge_residual = _anchor_residual(
            bridge,
            anchor.get("subject") if isinstance(anchor, Mapping) else "",
            anchor.get("object") if isinstance(anchor, Mapping) else "",
        )
        if len(clue) < 3 or len(bridge) < 8 or len(conclusion) < 6:
            issues.append(_issue("culture_v3_reasoning_steps_too_shallow", "推理必须包含简短线索、具体中间事实和答案结论"))
        if stem and (_normalized(clue) == _normalized(stem) or _similar(clue, stem) >= 0.94):
            issues.append(_issue("culture_v3_clue_repeats_stem", "clue 应提取关键线索，不得整句复述题干"))
        if stem and clue and not (_cjk_bigrams(stem) & _cjk_bigrams(clue)):
            issues.append(_issue("culture_v3_clue_not_grounded", "clue 必须能在题干中找到依据"))
        if bridge and not culture_bridge_is_grounded(
            bridge,
            subject=anchor.get("subject") if isinstance(anchor, Mapping) else "",
            clue=clue,
            correct_option=correct_option,
            question_form=question_form,
        ):
            issues.append(
                _issue(
                    "culture_v3_bridge_not_grounded",
                    "bridge 必须显著命中题干对象、clue 或正确选项，不能用无关人物或同类事实代替",
                )
            )
        if question_form in {"negative_identification", "odd_one_out"} and not _INVERSE_DIRECTION_RE.search(clue):
            issues.append(
                _issue(
                    "culture_v3_inverse_clue_lacks_direction",
                    "逆向题 clue 必须保留不正确、不属于、不同项或例外等设问方向",
                )
            )
        if _SELECTION_RE.search(clue) or _SELECTION_RE.search(bridge):
            issues.append(_issue("culture_v3_answer_leaks_before_conclusion", "选择结论只能出现在 conclusion"))
        if (
            _GENERIC_FACT_RE.search(bridge)
            or _ANSWER_ECHO_BRIDGE_RE.fullmatch(bridge)
            or _TEMPLATE_BRIDGE_RE.search(bridge)
            or _normalized(bridge) in {_normalized(clue), _normalized(correct_option)}
            or (
                isinstance(anchor, Mapping)
                and (
                    len(bridge_residual) < 8
                    or _BRIDGE_FILLER_RE.fullmatch(bridge_residual)
                )
            )
            or (reasoning_mode == "person_event_effect" and len(_ACTION_PREDICATE_RE.findall(event_bridge)) < 2)
            or (
                reasoning_mode == "person_school_claim"
                and not _school_bridge_has_substantive_claim(
                    bridge,
                    anchor.get("subject") if isinstance(anchor, Mapping) else "",
                    correct_option,
                )
            )
        ):
            issues.append(_issue("culture_v3_bridge_is_answer_echo", "bridge 必须补出中间事实，不得只做答案对应"))
        if _BARE_MAPPING_PHRASE_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_uses_bare_mapping", "bridge 使用特征或时期套话改写答案，缺少中间事实"))
        if _LEADING_REFERENCE_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_dangling_reference", "bridge 以他、该书等无指代对象开头"))
        if isinstance(anchor, Mapping):
            topic_key = _normalized(anchor.get("subject"))
            bridge_key = _normalized(bridge)
            topic_position = bridge_key.find(topic_key) if topic_key else -1
            if topic_position > max(12, int(len(bridge_key) * 0.55)):
                issues.append(_issue("culture_v3_bridge_topic_arrives_late", "bridge 先堆叠其他对象，题干对象出现过晚"))
        if _SOURCE_LABEL_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_contains_source_label", "bridge 不得保留资料解析标签"))
        if _OCR_SOURCE_SEAM_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_source_merge", "bridge 疑似拼接了两个未分隔的资料事实"))
        if re.search(r"(?:谁|哪位|哪个|什么|如何|多少).{0,14}[？?]", bridge):
            issues.append(_issue("culture_v3_bridge_is_source_question", "bridge 不得保留资料中的问句"))
        if _FACT_RISK_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_fact_requires_review", "bridge 含有需复核的争议或错配事实"))
        if _INCOMPLETE_CLAUSE_END_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_incomplete", "bridge 句尾残缺，缺少完整文化事实"))
        if _REVIEW_LANGUAGE_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_contains_review_language", "bridge 不得保留选项字母或审核模板语言"))
        if _PROCEDURAL_KNOWLEDGE_RE.search(bridge) or _UNSAFE_KNOWLEDGE_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_contains_procedure", "bridge 不得包含常考、辨析等做题提示"))
        if not negative_stem and re.search(
            r"核对|不是|不在|不属于|不归于|不符合|不正确|错误|有误|未满足题干",
            bridge,
        ):
            issues.append(
                _issue(
                    "culture_v3_positive_bridge_uses_exclusion",
                    "正向题 bridge 应直接证明答案，不得依赖排除型背景",
                )
            )
        if chronology_question and not culture_bridge_has_time_link(
            bridge,
            stem=stem,
            correct_option=correct_option,
            subject=anchor.get("subject") if isinstance(anchor, Mapping) else "",
        ):
            issues.append(_issue("culture_v3_bridge_lacks_time_link", "时代题 bridge 必须说明出现、成书、生活或形成时间"))
        if chronology_question and _BROAD_TIME_ANSWER_RE.fullmatch(_normalized(correct_option)):
            issues.append(_issue("culture_v3_time_answer_too_broad", "时代题答案仅写古代，时间边界过宽，应进入复核"))
        if (
            chronology_question
            and not _BROAD_TIME_ANSWER_RE.fullmatch(_normalized(correct_option))
            and not _explicit_time_values(correct_option)
            and not _canonical_time_option(correct_option)
        ):
            issues.append(
                _issue(
                    "culture_v3_chronology_answer_not_time",
                    "时代题正确项不是可识别的时间值，题目结构需复核",
                )
            )
        if chronology_question and _chronology_options_overlap(
            correct_option,
            answer=answer,
            options=options,
        ):
            issues.append(
                _issue(
                    "culture_v3_time_options_overlap",
                    "时代题正确项与其他选项存在父子时期或包含关系，答案不唯一",
                )
            )
        if reasoning_mode == "chronology" and _RELATIVE_TIME_STEM_RE.search(stem) and not _RELATIVE_TIME_FACT_RE.search(bridge):
            issues.append(_issue("culture_v3_bridge_lacks_relative_time_proof", "先后关系题必须给出生卒或前后关系证据"))
        if bridge and conclusion and _similar(bridge, conclusion) >= 0.88:
            issues.append(_issue("culture_v3_bridge_duplicates_conclusion", "中间事实与答案结论不得重复"))
        names_answer = bool(
            answer
            and (
                re.search(rf"(?:选|选择|应选)\s*{re.escape(answer)}(?=$|[。；，,、:“”‘’（）()\s])", conclusion, re.I)
                or (correct_option and _normalized(correct_option) in _normalized(conclusion))
            )
        )
        if not names_answer:
            issues.append(_issue("culture_v3_conclusion_missing_answer", "conclusion 必须落到正确选项或选项原文"))

    knowledge = _text(metadata.get("knowledge_extension"))
    if len(knowledge) < 10:
        issues.append(_issue("weak_culture_v3_knowledge", "knowledge_extension 必须提供独立、可复习的事实"))
    if (
        _SELECTION_RE.search(knowledge)
        or _PROCEDURAL_KNOWLEDGE_RE.search(knowledge)
        or _REVIEW_LANGUAGE_RE.search(knowledge)
        or _UNSAFE_KNOWLEDGE_RE.search(knowledge)
        or _SOURCE_FRAGMENT_RE.search(knowledge)
        or _KNOWLEDGE_FRAGMENT_RE.search(knowledge)
        or _FACT_RISK_RE.search(knowledge)
    ):
        issues.append(_issue("culture_v3_knowledge_role_mismatch", "知识点只能扩展文化事实，不得写选项结论或通用做题步骤"))
    if _SELF_CONTRADICTION_RE.search(knowledge):
        issues.append(_issue("culture_v3_knowledge_self_contradiction", "知识点内部出现同一对象的自相矛盾表述"))
    if _INCOMPLETE_CLAUSE_END_RE.search(knowledge):
        issues.append(_issue("culture_v3_knowledge_incomplete", "知识点句尾残缺，需补全事实"))
    if _LEADING_REFERENCE_RE.search(knowledge):
        issues.append(_issue("culture_v3_knowledge_dangling_reference", "知识点以无明确对象的代词开头"))
    if _OCR_SOURCE_SEAM_RE.search(knowledge):
        issues.append(_issue("culture_v3_knowledge_source_merge", "知识点疑似粘连了两个资料事实"))
    if re.search(r"(?:谁|哪位|哪个|什么|如何|多少).{0,18}[？?]", knowledge):
        issues.append(_issue("culture_v3_knowledge_is_source_question", "知识点不得保留资料问句"))
    if _enumeration_incomplete(knowledge):
        issues.append(_issue("culture_v3_knowledge_incomplete_enumeration", "知识点列举数量与内容不完整"))
    if knowledge and stem and _similar(knowledge, stem) >= 0.78:
        issues.append(_issue("culture_v3_knowledge_repeats_stem", "知识点不得改写题干或重复本题答案"))
    if isinstance(anchor, Mapping) and bridge and knowledge:
        anchor_subject = anchor.get("subject")
        anchor_answer = anchor.get("object")
        bridge_key = _normalized(bridge)
        knowledge_key = _normalized(knowledge)
        if (
            _normalized(anchor_subject)
            and _normalized(anchor_answer)
            and _normalized(anchor_subject) in bridge_key
            and _normalized(anchor_answer) in bridge_key
            and _normalized(anchor_subject) in knowledge_key
            and _normalized(anchor_answer) in knowledge_key
            and len(_anchor_residual(knowledge, anchor_subject, anchor_answer)) < 8
        ):
            issues.append(_issue("culture_v3_knowledge_repeats_answer_mapping", "知识点不得再次复述题目对象与答案的对应"))
        if not _knowledge_is_grounded(
            knowledge,
            anchor_subject,
            anchor_answer,
            allow_generic_answer=reasoning_mode == "person_school_claim",
        ):
            issues.append(_issue("culture_v3_knowledge_not_grounded", "知识点必须围绕本题对象或正确知识继续扩展"))
    if knowledge and bridge and (
        _normalized(knowledge) in _normalized(bridge)
        or _normalized(bridge) in _normalized(knowledge)
        or _similar(knowledge, bridge) >= 0.82
    ):
        issues.append(_issue("culture_v3_knowledge_duplicates_reasoning", "知识点与中间推理事实重复，应补充独立考试知识"))

    memory_strategy = _text(metadata.get("memory_strategy"))
    memory_hook = _text(metadata.get("memory_hook"))
    required_memory_strategy = culture_memory_strategy_requirement(question, metadata)
    if memory_strategy not in CULTURE_V3_MEMORY_STRATEGIES:
        issues.append(_issue("invalid_culture_v3_memory_strategy", "memory_strategy 只能为 none、keyword、contrast 或 chain"))
    elif memory_strategy == "none":
        if memory_hook:
            issues.append(_issue("culture_v3_memory_none_has_copy", "memory_strategy 为 none 时 memory_hook 应为空"))
        if required_memory_strategy:
            labels = {
                "keyword": "关键词记忆",
                "contrast": "同维度对比记忆",
                "chain": "三节点知识链",
            }
            issues.append(
                _issue(
                    "culture_v3_memory_strategy_required",
                    f"本题存在明确的{labels[required_memory_strategy]}价值，不能省略记忆方法",
                )
            )
    else:
        if len(memory_hook) < 8 or _GENERIC_MEMORY_RE.search(memory_hook):
            issues.append(_issue("weak_culture_v3_memory_hook", "记忆方法必须是可复用的关键词、对比组或知识链"))
        if (
            _INCOMPLETE_CLAUSE_END_RE.search(memory_hook)
            or re.search(r"(?:—|-)[^；;]{0,16}(?:人物|作品|著作|思想)$", memory_hook)
            or _LEADING_REFERENCE_RE.search(memory_hook)
            or _OCR_SOURCE_SEAM_RE.search(memory_hook)
            or _FACT_RISK_RE.search(memory_hook)
        ):
            issues.append(_issue("culture_v3_memory_hook_requires_review", "记忆方法含残句、无指代内容或需复核事实"))
        if memory_hook and knowledge and _similar(memory_hook, knowledge) >= 0.86:
            issues.append(_issue("culture_v3_memory_duplicates_knowledge", "记忆方法不得复述知识点"))

    analyses = metadata.get("option_analysis")
    if not isinstance(analyses, Mapping):
        issues.append(_issue("invalid_culture_v3_option_analysis", "option_analysis 必须逐项覆盖 A-D", "critical"))
    else:
        extra_option_labels = sorted(
            str(label) for label in analyses if label not in OPTION_LABELS
        )
        if extra_option_labels:
            issues.append(
                _issue(
                    "culture_v3_option_analysis_unknown_labels",
                    f"option_analysis 出现 A-D 以外选项：{'、'.join(extra_option_labels)}",
                    "critical",
                )
            )
        missing_options = [label for label in OPTION_LABELS if not isinstance(analyses.get(label), Mapping)]
        if missing_options:
            issues.append(_issue("incomplete_culture_v3_option_analysis", f"option_analysis 缺少：{'、'.join(missing_options)}", "critical"))
        rendered_reasons: list[str] = []
        option_facts: list[str] = []
        wrong_fit_families: list[str] = []
        wrong_fits: list[str] = []
        for label in OPTION_LABELS:
            item = analyses.get(label)
            if not isinstance(item, Mapping):
                continue
            extra_item_fields = sorted(
                str(field) for field in item if field not in {"verdict", "fact", "fit"}
            )
            if extra_item_fields:
                issues.append(
                    _issue(
                        "culture_v3_option_analysis_item_unknown_fields",
                        f"option_analysis.{label} 出现契约外字段：{'、'.join(extra_item_fields)}",
                        "critical",
                    )
                )
            if any(not _is_string(item.get(key)) for key in ("verdict", "fact", "fit")):
                issues.append(
                    _issue(
                        "culture_v3_option_analysis_non_string",
                        f"option_analysis.{label} 的 verdict、fact、fit 必须是字符串",
                        "critical",
                    )
                )
            verdict = _text(item.get("verdict"))
            expected = "correct" if label == answer else "incorrect"
            if verdict != expected:
                issues.append(_issue("culture_v3_option_verdict_mismatch", f"option_analysis.{label}.verdict 应为 {expected}"))
            fact = _text(item.get("fact"))
            fit = _text(item.get("fit"))
            if (
                len(fact) < 7
                or _GENERIC_FACT_RE.search(fact)
                or _UNSAFE_OPTION_FACT_RE.search(fact)
                or _INCOMPLETE_CLAUSE_END_RE.search(fact)
                or _TAUTOLOGY_FACT_RE.fullmatch(fact)
                or _LEADING_REFERENCE_RE.search(fact)
                or _OCR_SOURCE_SEAM_RE.search(fact)
                or _FACT_RISK_RE.search(fact)
                or _REVIEW_LANGUAGE_RE.search(fact)
            ):
                issues.append(_issue("culture_v3_option_fact_weak", f"选项 {label} 必须说明具体知识事实"))
            if options.get(label) and _normalized(fact) == _normalized(options[label]):
                issues.append(_issue("culture_v3_option_fact_repeats_option", f"选项 {label} 的 fact 只是复述选项原文"))
            if (
                _UNSUPPORTED_OPTION_LIMIT_RE.search(fact)
                and not _EXPLICIT_OPTION_LIMIT_RE.search(options.get(label, ""))
            ):
                issues.append(
                    _issue(
                        "culture_v3_option_fact_adds_unsupported_limit",
                        f"选项 {label} 的 fact 擅自增加了原选项未表达的地域、时代或范围限制",
                    )
                )
            if options.get(label) and not _fact_names_option(fact, options[label]):
                code = (
                    "culture_v3_correct_option_fact_missing_answer"
                    if label == answer
                    else "culture_v3_wrong_option_fact_missing_object"
                )
                issues.append(_issue(code, f"选项 {label} 的事实没有保留该选项的知识对象"))
            short_chronology_fit = bool(
                reasoning_mode == "chronology"
                and label != answer
                and _short_chronology_fit_has_date_fact(fact, fit)
            )
            if (len(fit) < 5 and not short_chronology_fit) or _GENERIC_FIT_RE.search(fit):
                issues.append(_issue("culture_v3_option_fit_weak", f"选项 {label} 必须说明该事实为何符合或不符合本题"))
            elif label == answer and not _RIGHT_FIT_CONNECTOR_RE.search(fit):
                issues.append(_issue("culture_v3_correct_option_fit_unclear", f"选项 {label} 未说明与题干的直接关系"))
            elif label != answer and not _WRONG_FIT_CONNECTOR_RE.search(fit):
                issues.append(_issue("culture_v3_wrong_option_mismatch_unclear", f"选项 {label} 未说明错配边界"))
            if len(fact) > 72 or len(fit) > 58:
                issues.append(_issue("culture_v3_option_analysis_too_long", f"选项 {label} 的辨析过长，应保留一个事实和一个错配边界"))
            rendered_reasons.append(f"{_normalized(fact)}|{_normalized(fit)}")
            option_facts.append(fact)
            if label != answer:
                wrong_fits.append(_normalized(fit))
                family = _fit_template_family(fit)
                if family:
                    wrong_fit_families.append(family)
        if len(rendered_reasons) != len(set(rendered_reasons)):
            issues.append(_issue("culture_v3_option_analysis_repeated", "A-D 选项解析不得复制同一句模板"))
        if question_form not in {"negative_identification", "odd_one_out"} and any(
            count >= 3 for count in Counter(wrong_fit_families).values()
        ):
            issues.append(_issue("culture_v3_option_fit_template_repeated", "三个错项不得反复套用同一种判断句式"))
        if any(value and count >= 3 for value, count in Counter(wrong_fits).items()):
            issues.append(_issue("culture_v3_option_fit_repeated", "三个错项不得复用同一句空泛错配说明"))
        if knowledge and any(
            len(_normalized(fact)) >= 7
            and (
                _normalized(fact) in _normalized(knowledge)
                or _normalized(knowledge) in _normalized(fact)
                or _similar(fact, knowledge) >= 0.86
            )
            for fact in option_facts
        ):
            issues.append(_issue("culture_v3_knowledge_duplicates_option_fact", "知识点不得复制选项解析中的事实"))

    try:
        rendered = render_culture_explanation_v3(question, metadata)
    except ValueError as exc:
        issues.append(_issue("culture_v3_render_failed", str(exc), "critical"))
    else:
        explanation = _text(question.get("explanation"))
        if explanation and _display_normalized(explanation) != _display_normalized(rendered):
            issues.append(_issue("culture_v3_explanation_not_canonical", "展示解析必须由 culture_v3 字段统一渲染，不得另写一套内容"))
        budget = culture_v3_display_budget(question, metadata)
        if len(rendered) > budget:
            issues.append(_issue("culture_v3_explanation_over_budget", f"当前题型解析为 {len(rendered)} 字符，超过动态上限 {budget}"))

    return issues
