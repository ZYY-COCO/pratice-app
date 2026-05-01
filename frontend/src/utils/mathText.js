const SUPERSCRIPT_MAP = {
  0: '⁰',
  1: '¹',
  2: '²',
  3: '³',
  4: '⁴',
  5: '⁵',
  6: '⁶',
  7: '⁷',
  8: '⁸',
  9: '⁹',
  '+': '⁺',
  '-': '⁻',
  x: 'ˣ',
  y: 'ʸ',
  n: 'ⁿ'
}

const SUBSCRIPT_MAP = {
  0: '₀',
  1: '₁',
  2: '₂',
  3: '₃',
  4: '₄',
  5: '₅',
  6: '₆',
  7: '₇',
  8: '₈',
  9: '₉',
  '+': '₊',
  '-': '₋',
  x: 'ₓ',
  y: 'ᵧ',
  a: 'ₐ',
  e: 'ₑ',
  n: 'ₙ'
}

function toSuperscript(value) {
  return String(value)
    .split('')
    .map((char) => SUPERSCRIPT_MAP[char] || char)
    .join('')
}

function toSubscript(value) {
  return String(value)
    .split('')
    .map((char) => SUBSCRIPT_MAP[char] || char)
    .join('')
}

function stripMathDelimiters(value) {
  return value
    .replace(/\\\((.*?)\\\)/g, '$1')
    .replace(/\\\[(.*?)\\\]/g, '$1')
    .replace(/\$(.*?)\$/g, '$1')
}

function normalizeLatexCommands(value) {
  return value
    .replace(/\\left/g, '')
    .replace(/\\right/g, '')
    .replace(/\\,/g, ' ')
    .replace(/\\;/g, ' ')
    .replace(/\\!/g, '')
    .replace(/\\to/g, '→')
    .replace(/->/g, '→')
    .replace(/\\infty/g, '∞')
    .replace(/\\pi/g, 'π')
    .replace(/\\cdot/g, '·')
    .replace(/\\times/g, '×')
    .replace(/\\leq?/g, '≤')
    .replace(/\\geq?/g, '≥')
    .replace(/\\neq/g, '≠')
    .replace(/\\partial/g, '∂')
    .replace(/\\sqrt\{([^{}]+)\}/g, '√($1)')
    .replace(/\\(sin|cos|tan|ln|log|sec)\b/g, '$1')
    .replace(/\b(sin|cos|tan|ln|log|sec)(?=[0-9])/g, '$1 ')
}

function wrapFractionPart(value) {
  if (!value) return ''
  if (/^\(.+\)$/.test(value)) return value
  return /[\s+\-*/]/.test(value) ? `(${value})` : value
}

function replaceFractions(value) {
  let result = value
  const fractionPattern = /\\frac\{([^{}]+)\}\{([^{}]+)\}/g
  let previous = ''

  while (previous !== result) {
    previous = result
    result = result.replace(fractionPattern, (_, numerator, denominator) => {
      return `(${wrapFractionPart(formatMathText(numerator))} / ${wrapFractionPart(formatMathText(denominator))})`
    })
  }

  return result
}

function replaceLimits(value) {
  return value.replace(/\\lim_\{([^{}]+)\}/g, (_, condition) => {
    return `lim(${formatMathText(condition)})`
  })
}

function replacePowers(value) {
  return value
    .replace(/\^\{?(-?[0-9xyn])\}?/g, (_, power) => toSuperscript(power))
    .replace(/\^\((-?\d+)\)/g, (_, power) => toSuperscript(power))
}

function replaceSubscripts(value) {
  return value.replace(/_\{?([0-9xyen+\-])\}?/g, (_, subscript) => toSubscript(subscript))
}

function tidyMathTextBase(value) {
  return value
    .replace(/\s+/g, ' ')
    .replace(/\s*→\s*/g, '→')
    .replace(/\s+([，。；：？！、])/g, '$1')
    .replace(/([(])\s+/g, '$1')
    .replace(/\s+([)])/g, '$1')
    .replace(/lim\s*\(([^)]+)\)/g, 'lim($1)')
}

function tidyMathText(value) {
  return tidyMathTextBase(value)
    .trim()
}

export function formatMathText(value) {
  if (value === null || value === undefined) {
    return ''
  }

  let result = String(value)
  result = stripMathDelimiters(result)
  result = replaceLimits(result)
  result = replaceFractions(result)
  result = normalizeLatexCommands(result)
  result = replacePowers(result)
  result = replaceSubscripts(result)
  return tidyMathText(result)
}

function formatMathSegment(value) {
  let result = String(value || '')
  result = normalizeLatexCommands(result)
  result = replacePowers(result)
  result = replaceSubscripts(result)
  return tidyMathTextBase(result)
}

function cleanFractionPart(value) {
  const text = formatMathSegment(value).trim()
  if ((text.startsWith('(') && text.endsWith(')')) || (text.startsWith('[') && text.endsWith(']'))) {
    return text.slice(1, -1).trim()
  }
  return text
}

function createFractionToken(numerator, denominator) {
  return {
    type: 'fraction',
    numerator: cleanFractionPart(numerator),
    denominator: cleanFractionPart(denominator)
  }
}

function extractLatexFractionTokens(value) {
  let result = value
  const fractions = []
  const fractionPattern = /\\frac\{([^{}]+)\}\{([^{}]+)\}/g
  let previous = ''

  while (previous !== result) {
    previous = result
    result = result.replace(fractionPattern, (_, numerator, denominator) => {
      const marker = `@@MATHFRAC${fractions.length}@@`
      fractions.push(createFractionToken(numerator, denominator))
      return marker
    })
  }

  return { result, fractions }
}

const SUPERSCRIPT_CHARS = '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ˣʸⁿ'
const SUBSCRIPT_CHARS = '₀₁₂₃₄₅₆₇₈₉₊₋ₓᵧₐₑₙ'
const SIMPLE_MATH_PART = `[A-Za-z0-9π∞∂]+[A-Za-z0-9π∞∂${SUPERSCRIPT_CHARS}${SUBSCRIPT_CHARS}]*`
const GROUPED_MATH_PART = `\\[[^\\]]+\\]|\\([^)]+\\)|${SIMPLE_MATH_PART}`
const PLAIN_FRACTION_PATTERN = new RegExp(`(${GROUPED_MATH_PART})\\s*\\/\\s*(${GROUPED_MATH_PART})`, 'g')

function pushTextToken(tokens, text) {
  if (!text) return
  tokens.push({ type: 'text', text })
}

function pushPlainMathTokens(tokens, value) {
  const text = formatMathSegment(value)
  let cursor = 0
  let match

  PLAIN_FRACTION_PATTERN.lastIndex = 0
  while ((match = PLAIN_FRACTION_PATTERN.exec(text)) !== null) {
    pushTextToken(tokens, text.slice(cursor, match.index))
    tokens.push(createFractionToken(match[1], match[2]))
    cursor = match.index + match[0].length
  }

  pushTextToken(tokens, text.slice(cursor))
}

export function tokenizeMathText(value) {
  if (value === null || value === undefined) {
    return []
  }

  let result = String(value)
  result = stripMathDelimiters(result)
  result = replaceLimits(result)

  const extracted = extractLatexFractionTokens(result)
  result = formatMathSegment(extracted.result)

  const tokens = []
  const markerPattern = /@@MATHFRAC(\d+)@@/g
  let cursor = 0
  let match

  while ((match = markerPattern.exec(result)) !== null) {
    pushPlainMathTokens(tokens, result.slice(cursor, match.index))
    const fraction = extracted.fractions[Number(match[1])]
    if (fraction) {
      tokens.push(fraction)
    }
    cursor = match.index + match[0].length
  }

  pushPlainMathTokens(tokens, result.slice(cursor))
  return tokens.filter((token) => token.type === 'fraction' || token.text)
}
