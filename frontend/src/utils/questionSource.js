const AI_QUESTION_SOURCE_TYPE = 'ai_deepseek'

export function isAiGeneratedQuestion(question = {}) {
  const sourceType = String(question?.source_type || question?.sourceType || '').toLowerCase()
  return sourceType === AI_QUESTION_SOURCE_TYPE
}

export function getQuestionSourceLabel(question = {}) {
  if (!isAiGeneratedQuestion(question)) return ''
  // #ifdef MP-WEIXIN
  return ''
  // #endif
  // #ifndef MP-WEIXIN
  return 'AI专项出题'
  // #endif
}
