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
}

function replaceFractions(value) {
  let result = value
  const fractionPattern = /\\frac\{([^{}]+)\}\{([^{}]+)\}/g
  let previous = ''

  while (previous !== result) {
    previous = result
    result = result.replace(fractionPattern, (_, numerator, denominator) => {
      return `${formatMathText(numerator)} / ${formatMathText(denominator)}`
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

function tidyMathText(value) {
  return value
    .replace(/\s+/g, ' ')
    .replace(/\s*→\s*/g, '→')
    .replace(/\s+([，。；：？！、])/g, '$1')
    .replace(/([(])\s+/g, '$1')
    .replace(/\s+([)])/g, '$1')
    .replace(/lim\s*\(([^)]+)\)/g, 'lim($1)')
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
