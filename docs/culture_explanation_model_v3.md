# 中华文化题目解析模型 V3

本文档定义中华文化刷题解析的生成契约、展示职责和质量门。V3 只优化解析内容链路，继续使用现有 Bottom Sheet、正确答案卡、分块卡片、颜色、折叠逻辑和作答业务。

## 1. 目标

解析从“公布答案”升级为“教学型解析”：

```text
提取题干线索
→ 补出可核对的中间文化事实
→ 推导正确选项
→ 说明 A-D 各自的真实知识与题干边界
→ 扩展一个独立复习知识
→ 有价值时提供记忆抓手
```

V3 不接受“X 对应 Y，所以选 Y”作为完整推理，也不接受“该项不符合题干”“属于共同范围”作为选项解析。

## 2. 生成与复核链路

```text
模型生成 culture_v3 结构化教学字段
→ 后端统一渲染 explanation
→ 确定性静态质量门
→ 隐去答案和解析，独立复核唯一答案
→ 展示答案和解析，独立复核教学质量与文化事实
→ 两次复核均通过才接收
→ 拒收原因进入下一轮生成提示词
```

模型不再自由生成一套 `explanation`、同时另写一套审核元数据。学习者看到的解析由 `culture_v3` 统一渲染，避免两套内容相互矛盾。

## 3. 题型路由

`question_form` 表示题目方向：

- `direct_identification`：正向直接识别
- `relationship_match`：关系匹配或共同点
- `negative_identification`：找错误项或例外
- `odd_one_out`：找不同项

`reasoning_mode` 表示中间事实应该怎样组织：

- `person_event_effect`：人物或事件 → 行为 → 影响
- `person_school_claim`：人物或命题 → 学派事实 → 思想归属
- `work_author_era`：作品特征 → 作者及时代 → 答案
- `concept_definition`：概念关键词 → 定义边界 → 答案
- `chronology`：事件年代 → 前后关系 → 答案
- `place_object_mapping`：对象 → 所在地 → 答案
- `category_comparison`：比较维度 → 各项归属 → 共同项或例外
- `quote_meaning`：诗文线索 → 语义或意象 → 答案
- `institution_function`：制度 → 运作方式或功能 → 答案
- `direct_fact`：稳定常识事实的直接识别

后端会根据题干高置信关键词检查路由，防止地点题、年代题和人物题继续套用同一模板。

## 4. `culture_v3` 字段职责

### 4.1 推理字段

`reasoning_steps` 必须包含：

- `clue`：只提取题干中的关键线索，不整句抄题干。
- `bridge`：补出能解释线索和答案关系的具体文化事实。
- `conclusion`：只在这里落到答案字母或正确选项原文。

示例：

```text
clue：玄奘取经
bridge：玄奘西行求法，带回大量佛经并在长安主持译经
conclusion：因此选 B“促进佛典翻译”
```

### 4.2 选项字段

`option_analysis` 必须覆盖 A-D，每项包含：

- `verdict`：`correct` 或 `incorrect`
- `fact`：该选项真正对应的知识
- `fit`：该事实为什么符合题干，或其人物、时代、地点、作品、概念为什么与本题错配

正确项和三个错项使用同一结构，但不能复制同一句模板。

### 4.3 知识点字段

`knowledge_extension` 只保存从本题延伸出的独立考试知识。它不得：

- 重复 `bridge`
- 出现“选 A / 选 B”等结论
- 写“先圈关键词、再排除”等通用做题步骤

### 4.4 记忆字段

`memory_strategy` 只能为：

- `keyword`：关键词记忆
- `contrast`：易混人物、作品、地点等对比
- `chain`：简短知识链
- `none`：当前题没有真正有用的记忆技巧

当策略为 `none` 时，`memory_hook` 必须为空，前端沿用现有能力自动隐藏“记忆方法”卡片。

生成时必须先判断记忆方法是否比解题思路和知识点多提供了一层复习价值：

- 固定日期、称谓、别名或短触发词优先使用 `keyword`。
- 至少两组同维度且容易混淆的人物—作品、人物—主张、概念—归属映射使用 `contrast`。
- 至少三个有真实先后、措施或因果关系的节点使用 `chain`。
- 单跳事实、答案名称已经显露关系、错项跨领域且不构成易混组时使用 `none`。

难度高低本身不是生成记忆方法的理由。禁止牵强谐音、硬凑首字、复述答案或引入未经核准的新事实。后端只对高置信适宜题阻断 `none`，其余题仍允许模型保守选择并由静态质量门检查内容完整性。

### 4.5 事实与审核字段

- `fact_anchor`：对象、关系、正确值
- `evidence_excerpt`：可核对的具体文化事实
- `scope_level = core`
- `controversy_status = stable`
- `verification_status = cross_checked`
- `difficulty_features`：本题真正的辨析难点

## 5. 展示契约

V3 继续输出前端已经支持的标签：

```text
解题思路：
选项解析：
知识点：
记忆方法：    # 仅在 memory_strategy 不是 none 时出现
```

长度按题型动态控制：直接常识题更短，逆向题和同类比较题可适当展开。A-D 每项只保留一个真实事实和一个判断边界，避免重新形成长篇文字墙。

## 6. 确定性质量门

V3 会拦截：

- `bridge` 只是答案复述或“X 对应 Y”
- `bridge` 使用“典型特征是”“创作时期是”“这一观点属于”等句式改写答案
- `bridge` 以“他、该书、这句诗”等无指代内容开头，或先堆叠其他对象再补题干对象
- `bridge` 没有显著命中事实锚点、clue 或正确选项，而是用无关人物或同类背景替代当前题目的中间事实
- 正向题使用“核对、不在、不是”等排除型背景代替直接证明
- 从资料中拼接两个未分隔事实，或把“四大发明”中的“发明”误当作事件动作
- 资料问句、章节编号、OCR 粘连句、残缺句和宣传性绝对表述
- `clue` 整句复制题干，或与题干没有依据关系
- 选项 `fact` 只是复制选项原文
- 选项 `fact` 没有保留该选项对象，或拿同一人物的无关轶事充当排除依据
- 选项只写“符合 / 不符合题干”“故不选”等空话
- A-D 解析重复同一句模板
- 知识点写成做题建议，或与推理事实重复
- 知识点出现“常考、要区分、按……辨析/串联”等程序性提示
- 知识点脱离本题对象，或直接复制任一选项解析事实
- 记忆方法空洞、强行生成，或重复知识点
- 记忆方法因长度压缩形成残句
- `fact_anchor.object` 与正确选项不一致
- 逆向题证据只与主题词或推理动作词重合，却没有同时支撑推理桥并点名被纠正的选项事实
- 逆向题把错误选项原句当成 `evidence_excerpt`，却没有写出“不在、不属于、并非、不同、例外”等纠偏边界
- 逆向题用“并非错误、不是不正确”等双重否定伪装纠偏，或纠偏证据没有提供至少两个超出错误选项原文的共同事实片段
- 逆向题的 `clue` 丢失“不正确、不属于、不同项、例外”等方向词，导致客户端不能可靠自动展开选项解析
- 正反题型和题干不一致
- 地点、年代、人物等推理路径错配
- 裸“最早”不得自动触发年代路由；简单朝代题必须让桥接事实出现正确时间值，先后比较题必须至少给出两个不同时间值和明确先后关系
- 展示解析不是由 `culture_v3` 统一渲染
- 解析超过当前题型的动态长度上限

## 7. 现有题解析重生成边界

现有题库优化与在线新题生成使用不同的信任边界：

- 输入只提供固定 `id`、题干、A-D、答案、分类和难度，不把旧 `explanation` 送回模型。
- 模型每题只能返回一次 `id + culture_v3`；改题、增加字段、未知 ID、漏 ID或重复 ID均整题拒收。
- `culture_v3` 及其 `fact_anchor`、`reasoning_steps`、`option_analysis` 采用精确字段白名单；任何嵌套未知字段也整题拒收。
- 每批最多 6 题，静态门拒收原因可清洗后反馈到下一轮；反馈不得混入本批之外的 ID。
- 后端根据原题重新渲染 `explanation`，再运行同一套 V3 静态门；模型不能直接提交展示文本。
- 解析候选必须继续与原题不可变字段绑定，后续批处理不得通过替换 ID 或重排题目绕过审核。

实现入口：

- `backend/app/services/culture_explanation_regeneration.py`
- `backend/tests/test_culture_explanation_regeneration.py`
- `scripts/regenerate_common_culture_explanation_v3.py`
- `backend/tests/test_regenerate_common_culture_explanation_v3.py`

全库编排器固定使用活动快照作为不可变基线，每批最多 6 题，并为每题分别记录尝试次数、静态门反馈和基线 SHA-256。checkpoint、候选和审核报告始终保留 `database_writes=0`、`ready_for_publish=false`；模型调用失败、响应协议失败和内容静态门失败必须分别统计，不能把基础设施问题误报成内容质量问题。

离线重生成支持两种 provider：

- `deepseek`：保留既有服务通道，需要对应的开发环境配置。
- `codex-cli`：复用本机已经登录的 Codex，只在开发期预生成候选；App 与生产后端不调用 Codex，也不需要 DeepSeek 密钥。

provider、Codex CLI 版本和三条产物路径都会写入 checkpoint；续跑时必须完全一致。CLI 在空临时目录和只读沙箱中运行，Prompt 只包含固定题目字段，不包含旧解析。基础设施故障会暂停整场任务，且不会回灌为解析修改意见；只有确定性内容质量门的拒收原因会进入下一轮 Prompt。

小批验证必须使用独立产物路径，避免占用正式全库 checkpoint：

```powershell
$env:PYTHONPATH = "$PWD;$PWD\backend"
& "backend/.venv/Scripts/python.exe" scripts/regenerate_common_culture_explanation_v3.py `
  --provider codex-cli `
  --ids <已确认的6个固定题目ID> `
  --checkpoint data/common_culture_explanation_v3_regeneration_smoke_checkpoint.json `
  --output data/common_culture_explanation_v3_regeneration_smoke_candidates.json `
  --report reports/common_culture_explanation_v3_regeneration_smoke_review.json
```

正式全库运行和断点续跑分别使用默认路径：

```powershell
& "backend/.venv/Scripts/python.exe" scripts/regenerate_common_culture_explanation_v3.py --provider codex-cli
& "backend/.venv/Scripts/python.exe" scripts/regenerate_common_culture_explanation_v3.py --provider codex-cli --resume
```

`--ids` 或 `--limit` 的小范围任务必须同时指定独立的 checkpoint、候选和报告路径，避免占用正式全库断点。

如果某次运行已经因旧版确定性静态门耗尽重试，而保存的
`last_rejected_culture_v3` 在静态门修正后应重新判断，使用显式本地复审模式：

```powershell
& "backend/.venv/Scripts/python.exe" scripts/regenerate_common_culture_explanation_v3.py `
  --provider codex-cli `
  --resume `
  --reaudit-rejected `
  --checkpoint data/<checkpoint>.json `
  --output data/<candidates>.json `
  --report reports/<review>.json
```

该模式只复审 `terminal_category=static_gate_failed` 且保留了结构化候选的题目，
不执行 provider preflight、不调用模型、不增加题目尝试次数，也不处理 provider、协议或中断类失败。
原失败次数和拒收原因继续保存在 checkpoint，晋升动作另写 `static_reaudit_events` 审计记录。

确定性静态门新增规则后，还应把 `--reaudit-rejected` 换成 `--reaudit-all`，同时复审
checkpoint 中已经接收的候选。旧候选若不再通过，会从 candidate 中移除并记录为
`static_gate_failed`，但不会新增模型调用或题目尝试次数；这可避免旧 checkpoint 继续把过期的
静态门结论显示为通过。

如果新增的是“高置信题缺少有价值记忆方法”规则，使用专用迁移模式：

```powershell
& "backend/.venv/Scripts/python.exe" scripts/regenerate_common_culture_explanation_v3.py `
  --provider codex-cli `
  --resume `
  --migrate-memory-gate
```

该模式先本地复审全部保存候选，只把当前唯一阻断码为
`culture_v3_memory_strategy_required` 的题重新排队，不调用模型。原尝试次数和失败历史保持不变；
已经到达普通三次上限的题最多获得一次单题迁移机会，并单独写入
`memory_gate_migration_events`，不会提高全局重试上限。

全库候选仍只是解析审核输入；不得直接交给数据库导入器。

## 8. 30 题试点与审核隔离

大规模重生成前，先固定五个板块各 6 题的 30 题试点：

- 人工覆盖解析保存题干、A-D、答案、分类、难度等基线字段的 SHA-256；快照漂移时立即阻断。
- 盲审输入只包含题目索引、ID、题干和 A-D，不得包含答案、解析、`culture_v3` 或学科/模块/子模块；分类名称可能与选项同名，也视为答案泄漏。
- 静态门通过只表示格式、字段职责和确定性教学规则合格，不代表答案或文化事实已经复核。
- 答案盲审、教学事实复核和用户确认均通过前，所有产物保持 `ready_for_publish=false`。
- importer 形状的预览固定为 `archived + pending`，只允许改变 `explanation`、`status`、`review_status`，并且不连接数据库。

试点入口：

- `scripts/build_common_culture_explanation_v3_pilot.py`
- `data/common_culture_explanation_v3_pilot_blind_answer_review.json`
- `reports/common_culture_explanation_v3_pilot.md`

## 9. 兼容与发布边界

- 已发布的 V2 解析继续兼容读取，本次校准不自动重写线上题库。
- 在线新生成中华文化题优先使用 V3；旧 `culture_v2` 在迁移期保留兼容入口。
- 在线新题的第二阶段教学复核同时读取统一渲染文本和内部 `culture_v3` 事实字段；内部复核字段在写库前剥离，不能进入 questions 表。
- 全库优化阶段仍须执行：快照、V3 生成、自动审计、人工复核隔离、importer dry-run、备份、明确发布确认、分批发布、线上回读。
- 仅调整解析不得改变题干、选项、答案、分类、收藏、作答判断、上下题或发布状态。

## 10. 黄金样本

校准入口：

```powershell
$env:PYTHONPATH = "$PWD;$PWD\backend"
& "backend/.venv/Scripts/python.exe" scripts/build_common_culture_explanation_v3_calibration.py
```

产物：

- `data/common_culture_explanation_v3_calibration.json`
- `reports/common_culture_explanation_v3_calibration.md`

该校准只读取快照并生成审核产物，不写数据库、不修改线上题目。
