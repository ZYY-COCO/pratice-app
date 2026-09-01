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
- 正向题使用“核对、不在、不是”等排除型背景代替直接证明
- 从资料中拼接两个未分隔事实，或把“四大发明”中的“发明”误当作事件动作
- `clue` 整句复制题干，或与题干没有依据关系
- 选项 `fact` 只是复制选项原文
- 选项只写“符合 / 不符合题干”“故不选”等空话
- A-D 解析重复同一句模板
- 知识点写成做题建议，或与推理事实重复
- 知识点出现“常考、要区分、按……辨析/串联”等程序性提示
- 记忆方法空洞、强行生成，或重复知识点
- `fact_anchor.object` 与正确选项不一致
- 正反题型和题干不一致
- 地点、年代、人物等推理路径错配
- 展示解析不是由 `culture_v3` 统一渲染
- 解析超过当前题型的动态长度上限

## 7. 兼容与发布边界

- 已发布的 V2 解析继续兼容读取，本次校准不自动重写线上题库。
- 在线新生成中华文化题优先使用 V3；旧 `culture_v2` 在迁移期保留兼容入口。
- 全库优化阶段仍须执行：快照、V3 生成、自动审计、人工复核隔离、importer dry-run、备份、明确发布确认、分批发布、线上回读。
- 仅调整解析不得改变题干、选项、答案、分类、收藏、作答判断、上下题或发布状态。

## 8. 黄金样本

校准入口：

```powershell
$env:PYTHONPATH = "$PWD;$PWD\backend"
& "backend/.venv/Scripts/python.exe" scripts/build_common_culture_explanation_v3_calibration.py
```

产物：

- `data/common_culture_explanation_v3_calibration.json`
- `reports/common_culture_explanation_v3_calibration.md`

该校准只读取快照并生成审核产物，不写数据库、不修改线上题目。
