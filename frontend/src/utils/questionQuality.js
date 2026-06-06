const PLACEHOLDER_PATTERN = /(undefined|null|\[object Object\])/i
const LATEX_COMMAND_PATTERN = /\\(?:frac|sqrt|lim|int|partial|left|right|to|infty|pi|sin|cos|tan|ln|log|begin|end)/
const MATH_SIGNAL_PATTERN = /(数学|Z002|一元函数|多元函数|微分|积分|极限|导数|偏导|凹凸|渐近线|math)/i

function toText(value) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'number') return String(value)
  return ''
}

function collapseSpaces(value) {
  return toText(value)
    .replace(/\u00a0/g, ' ')
    .replace(/\r?\n/g, ' ')
    .replace(/[ \t]{2,}/g, ' ')
    .replace(/\s+([，。；：？！,.?!)])/g, '$1')
    .replace(/([（(])\s+/g, '$1')
    .trim()
}

function normalizeSqrt(value) {
  let text = value
  text = text.replace(/sqrt\s*\(([^()]+)\)/gi, '\\sqrt{$1}')
  text = text.replace(/√\s*\(([^()]+)\)/g, '\\sqrt{$1}')
  text = text.replace(/√\s*([A-Za-z0-9]+(?:[+\-][A-Za-z0-9]+)+)/g, '\\sqrt{$1}')
  text = text.replace(/\bsqrt\s*([A-Za-z0-9]+(?:[+\-][A-Za-z0-9]+)+)/gi, '\\sqrt{$1}')
  return text
}

function normalizeCommonMathText(value) {
  return normalizeSqrt(collapseSpaces(value))
    .replace(/π/g, '\\pi')
    .replace(/∞/g, '\\infty')
    .replace(/→/g, '\\to')
}

function normalizeOption(option, fallbackKey) {
  if (typeof option === 'string' || typeof option === 'number') {
    return { key: fallbackKey, text: normalizeCommonMathText(option) }
  }
  return {
    key: toText(option?.key || fallbackKey).toUpperCase(),
    text: normalizeCommonMathText(option?.text ?? option?.content ?? option?.value ?? '')
  }
}

function readOptions(question) {
  if (Array.isArray(question?.options)) {
    return question.options.map((option, index) => normalizeOption(option, ['A', 'B', 'C', 'D'][index] || String(index + 1)))
  }

  if (question?.options && typeof question.options === 'object') {
    return ['A', 'B', 'C', 'D'].map((key) => normalizeOption({ key, text: question.options[key] ?? question.options[key.toLowerCase()] }, key))
  }

  return [
    { key: 'A', text: question?.option_a },
    { key: 'B', text: question?.option_b },
    { key: 'C', text: question?.option_c },
    { key: 'D', text: question?.option_d }
  ].map((option) => normalizeOption(option, option.key))
}

export function isMathQuestion(question) {
  const text = [
    question?.exam_code,
    question?.subject,
    question?.module,
    question?.submodule,
    question?.section
  ].filter(Boolean).join(' ')
  if (MATH_SIGNAL_PATTERN.test(text)) return true
  return LATEX_COMMAND_PATTERN.test(toText(question?.stem || question?.stem_latex))
}

export function normalizeQuestion(rawQuestion = {}, context = {}) {
  const question = rawQuestion || {}
  const stemSource = question.stem_latex || question.stem || question.title || question.question || ''
  const normalized = {
    ...question,
    id: question.id || question.questionId || question.question_id || '',
    questionId: question.questionId || question.id || question.question_id || '',
    exam_code: question.exam_code || question.examCode || context.examCode || '',
    subject: question.subject || context.subject || '',
    module: question.module || context.module || '',
    submodule: question.submodule || context.submodule || question.badge || '',
    source_type: question.source_type || question.sourceType || '',
    source_year: question.source_year || question.sourceYear || '',
    stem: normalizeCommonMathText(stemSource),
    options: readOptions(question).slice(0, 4)
  }
  normalized.isMath = isMathQuestion(normalized)
  return normalized
}

function hasBalancedBraces(value) {
  let depth = 0
  for (const char of toText(value)) {
    if (char === '{') depth += 1
    if (char === '}') depth -= 1
    if (depth < 0) return false
  }
  return depth === 0
}

function hasBalancedMathDelimiters(value) {
  const text = toText(value)
  const leftInline = (text.match(/\\\(/g) || []).length
  const rightInline = (text.match(/\\\)/g) || []).length
  const leftDisplay = (text.match(/\\\[/g) || []).length
  const rightDisplay = (text.match(/\\\]/g) || []).length
  return leftInline === rightInline && leftDisplay === rightDisplay
}

function isFragmentStem(stem, isMath) {
  const text = collapseSpaces(stem)
  if (!isMath) return false
  if (/^([设若求则在]|计算|已知|函数|求极限|求导数|求不定积分|求定积分)[，,。.\s]*$/.test(text)) return true
  if (/^设\s*则/.test(text)) return true
  if (/^设\s*(f|y|z)?\s*[，,]?\s*则/.test(text)) return true
  if (/^(设|若|已知)\s*(则|求)\s*[A-Za-z]?'?\s*\([^)]*\)\s*=\s*\?$/.test(text)) return true
  return false
}

function hasMalformedSqrt(value) {
  const text = toText(value)
  return /\bsqrt\s*[A-Za-z0-9]+(?:[+\-][A-Za-z0-9]+)+/i.test(text) || /√\s*[A-Za-z0-9]+(?:[+\-][A-Za-z0-9]+)+/.test(text)
}

export function validateQuestion(rawQuestion = {}) {
  const question = rawQuestion?.stem ? rawQuestion : normalizeQuestion(rawQuestion)
  const reasons = []
  const warnings = []
  const stem = collapseSpaces(question.stem)

  if (!stem) reasons.push('stem 为空')
  if (PLACEHOLDER_PATTERN.test(stem)) reasons.push('stem 包含异常占位符')
  if (isFragmentStem(stem, question.isMath)) reasons.push('stem 疑似残缺')
  if (!hasBalancedBraces(stem) || !hasBalancedMathDelimiters(stem)) reasons.push('stem 公式括号不闭合')
  if (hasMalformedSqrt(stem)) warnings.push('stem 根号写法疑似异常，已尝试兼容显示')
  if (/\s{2,}/.test(toText(question.stem))) warnings.push('stem 存在连续空格，已折叠')

  const options = Array.isArray(question.options) ? question.options : []
  if (options.length < 4) reasons.push('options 不足 4 个')
  options.slice(0, 4).forEach((option) => {
    const text = collapseSpaces(option?.text)
    if (!text) reasons.push(`option_${option?.key || '?'} 为空`)
    if (PLACEHOLDER_PATTERN.test(text)) reasons.push(`option_${option?.key || '?'} 包含异常占位符`)
    if (!hasBalancedBraces(text) || !hasBalancedMathDelimiters(text)) reasons.push(`option_${option?.key || '?'} 公式括号不闭合`)
    if (hasMalformedSqrt(text)) warnings.push(`option_${option?.key || '?'} 根号写法疑似异常，已尝试兼容显示`)
  })

  return {
    valid: reasons.length === 0,
    reasons: Array.from(new Set(reasons)),
    warnings: Array.from(new Set(warnings))
  }
}
