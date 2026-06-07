export function isAiGeneratedQuestion(question = {}) {
  const sourceType = String(question?.source_type || question?.sourceType || '').toLowerCase()
  return sourceType.startsWith('ai')
}

export function getQuestionSourceLabel(question = {}) {
  return isAiGeneratedQuestion(question) ? 'AI专项出题' : ''
}
