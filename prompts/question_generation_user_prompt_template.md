请根据以下参数批量生成题目，并严格按 JSON 返回。

【批次参数】
- exam_code: {{exam_code}}
- subject: {{subject}}
- module: {{module}}
- submodule: {{submodule}}
- count: {{count}}
- difficulty_range: {{difficulty_range}}
- source_year: {{source_year}}

【生成要求】
1. 只生成属于以上知识点的题目。
2. 所有题目都必须是单项选择题，`question_type` 固定为 `single_choice`。
3. 每题必须有 4 个选项，且只有 1 个正确答案。
4. `answer` 只能是 `A/B/C/D`。
5. `difficulty` 必须落在 `{{difficulty_range}}` 范围内。
6. `source_type` 固定为 `ai_generated`。
7. `source_year` 固定为 `{{source_year}}`。
8. `passage_id` 固定为 `null`。
9. 解析需要简洁明确，指出正确项依据。
10. 不要生成重复题。
11. 不要输出 Markdown，不要输出解释文字，只输出 JSON。

【输出格式】
{
  "questions": [
    {
      "exam_code": "{{exam_code}}",
      "subject": "{{subject}}",
      "module": "{{module}}",
      "submodule": "{{submodule}}",
      "question_type": "single_choice",
      "stem": "题干",
      "option_a": "选项A",
      "option_b": "选项B",
      "option_c": "选项C",
      "option_d": "选项D",
      "answer": "A",
      "explanation": "解析",
      "difficulty": 2,
      "source_type": "ai_generated",
      "source_year": {{source_year}},
      "passage_id": null
    }
  ]
}

【本次特别提醒】
- 如果是 `Z001`，不要生成数学基础题。
- 如果是 `Z002`，不要生成逻辑推理题。
- 如果指定的是中华文化，请尽量贴近考纲中的“文化常识”型命题风格。
- 如果指定的是逻辑推理或数学基础，请保持基础概念清晰、干扰项合理。
