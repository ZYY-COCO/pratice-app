# AI 题库批量生成规范

本文档用于约束后续 AI 批量生成题目的格式、范围与出题风格，确保生成结果能够直接通过
[scripts/import_questions.py](<C:/Users/1111/Documents/New project/scripts/import_questions.py:1>)
校验，并导入 Supabase `questions` 表。

英语运用 `语言知识` 与 Z002 `数学基础` 的详细硬规则见 [question_bank_generation_rules.md](question_bank_generation_rules.md)。如果两个文档出现冲突，以更具体的专题规则为准。

逻辑推理使用 [logic_question_model_v2.md](logic_question_model_v2.md) 的专用分类、审核元数据、形式化求解和错项反例规则。在线逻辑题缺少 V2 元数据、答案不唯一或形式化规格与声明答案冲突时，不得写入训练题表。

中华文化在线生成使用 [culture_explanation_model_v3.md](culture_explanation_model_v3.md) 的结构化教学契约、统一渲染、答案盲审和解析教学复核；英语运用和数学基础继续使用 [subject_question_models_v2.md](subject_question_models_v2.md) 的分科契约。模型自报“已核验”不作为答案正确证明；数学题还必须通过本地可执行复算规格。

## 1. 权威依据

后续 AI 出题时，默认以以下文件作为约束来源：

- [data/z001_outline.pdf](<C:/Users/1111/Documents/New project/data/z001_outline.pdf>)
- [data/z002_outline.pdf](<C:/Users/1111/Documents/New project/data/z002_outline.pdf>)
- [data/z001_outline_extracted.txt](<C:/Users/1111/Documents/New project/data/z001_outline_extracted.txt>)
- [data/z002_outline_extracted.txt](<C:/Users/1111/Documents/New project/data/z002_outline_extracted.txt>)

同时要与当前项目的知识点树保持一致：

- `中华文化`
- `英语运用`
- `逻辑推理`（仅 `Z001`）
- `数学基础`（仅 `Z002`）

## 2. 当前推荐生成范围

第一阶段建议只生成可直接写入 `questions` 表的单项选择题。

当前推荐：

- `question_type` 固定为 `single_choice`
- 暂不直接批量生成阅读材料型题组
- `passage_id` 默认填 `null`

后续如果做阅读理解批量入库，再单独补“先生成 `passages`，再生成关联 `questions`”流程。

## 3. 标准 JSON 格式

AI 输出必须是一个 JSON 对象，最外层字段固定为 `questions`，值为数组：

```json
{
  "questions": [
    {
      "exam_code": "Z001",
      "subject": "中华文化",
      "module": "中国哲学常识",
      "submodule": "儒家",
      "question_type": "single_choice",
      "stem": "题干",
      "option_a": "选项A",
      "option_b": "选项B",
      "option_c": "选项C",
      "option_d": "选项D",
      "answer": "C",
      "explanation": "解析",
      "difficulty": 2,
      "source_type": "ai_generated",
      "source_year": 2026,
      "passage_id": null
    }
  ]
}
```

## 4. 字段规则

### 4.1 必填字段

- `exam_code`
- `subject`
- `module`
- `submodule`
- `question_type`
- `stem`
- `option_a`
- `option_b`
- `option_c`
- `option_d`
- `answer`
- `explanation`
- `difficulty`

### 4.2 可选字段

- `id`
  - 可不传，由数据库自动生成
- `source_type`
  - 建议固定为 `ai_generated`
- `source_year`
  - 建议填生成年份，如 `2026`
- `passage_id`
  - 非阅读材料题默认 `null`

### 4.3 中华文化解析展示格式

中华文化解析不再用一条长句承载所有信息。在线新题先生成 `culture_v3` 教学字段，再由后端统一渲染 `explanation`；最终存储文本按以下顺序保留真实换行，供客户端分块展示：

解题思路：用一句话说明题干线索与正确项的对应依据。
选项解析：
A. 正确项或错项的具体边界。
B. 正确项或错项的具体边界。
C. 正确项或错项的具体边界。
D. 正确项或错项的具体边界。
知识点：只保留一个可复习的事实锚点。
记忆方法：有真正价值时，给下一次做题一个短记忆抓手；没有时允许省略。

首屏展示“解题思路、知识点”和可选的“记忆方法”；“选项解析”默认折叠，逆向题自动展开。每个区块应短而具体，避免只复述答案、使用“干扰项”套话或堆叠百科背景。历史题可继续读取“为什么、关键知识、易混辨析、记忆提醒”旧标签。

## 5. 字段合法值约束

### 5.1 exam_code

只能是：

- `Z001`
- `Z002`

### 5.2 answer

只能是：

- `A`
- `B`
- `C`
- `D`

### 5.3 difficulty

取值范围：

- `1` 很基础
- `2` 基础
- `3` 中等
- `4` 偏难
- `5` 难

建议 MVP 阶段优先生成 `1-3` 难度题。

### 5.4 subject / module / submodule

必须与当前知识点树完全一致，不能自由创造新字段名。

例如：

- `subject = 中华文化`
- `module = 中国哲学常识`
- `submodule = 儒家`

允许，不要写成：

- `哲学`
- `先秦儒学`
- `儒家思想`

除非未来同步更新知识点树与导入校验。

## 6. 按考试版本的范围约束

### 6.1 Z001

允许科目：

- `中华文化`
- `英语运用`
- `逻辑推理`

不要为 `Z001` 生成 `数学基础` 题。

### 6.2 Z002

允许科目：

- `中华文化`
- `英语运用`
- `数学基础`

不要为 `Z002` 生成 `逻辑推理` 题。

## 7. 出题风格要求

- 题目必须符合考纲范围，不超纲
- 题干表达简洁，接近考试题风格
- 干扰项要看起来合理，不能一眼排除
- 正确答案必须唯一
- 解析要解释“为什么对、为什么错”
- 不要生成明显依赖冷僻专业背景的题
- 不要生成需要图片才能作答的题
- 不要生成含糊不清、答案争议大的题

## 8. AI 输出要求

给模型下发任务时，要明确要求：

- 只输出 JSON
- 不要输出 Markdown
- 不要输出解释性前言
- 不要输出代码块
- 不要附加“以下是题目”之类文本

否则会影响导入脚本读取。

## 9. 推荐工作流

1. 先确定批次参数
   - `exam_code`
   - `subject`
   - `module`
   - `submodule`
   - 数量
   - 难度范围
2. 使用提示词模板让 AI 输出 JSON
3. 保存为 `data/*.json`
4. 先跑 dry run

```powershell
cd "C:\Users\1111\Documents\New project\backend"
.\.venv\Scripts\python.exe ..\scripts\import_questions.py --file "..\data\your_batch.json" --dry-run
```

5. dry-run 确认 `Invalid questions: 0` 且用户明确同意后，正式批量导入

```powershell
cd "C:\Users\1111\Documents\New project\backend"
.\.venv\Scripts\python.exe ..\scripts\import_questions_bulk.py --file "..\data\your_batch.json" --batch-size 100
```

## 10. 当前建议的批次命名

推荐文件名格式：

- `z001_culture_confucianism_batch_001.json`
- `z001_logic_argument_weaken_batch_001.json`
- `z002_math_derivative_batch_001.json`

这样后续追踪来源和复查会更方便。
