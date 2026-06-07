const AI_QUESTION_SOURCE_TYPE = 'ai_deepseek'

export function isAiGeneratedQuestion(question = {}) {
  const sourceType = String(question?.source_type || question?.sourceType || '').toLowerCase()
  return sourceType === AI_QUESTION_SOURCE_TYPE
}

export function getQuestionSourceLabel(question = {}) {
  return isAiGeneratedQuestion(question) ? 'AI专项出题' : ''
}
