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
  return String(value)
    .replace(/\\\((.*?)\\\)/g, '$1')
    .replace(/\\\[(.*?)\\\]/g, '$1')
    .replace(/\$(.*?)\$/g, '$1')
}

function normalizeStructuralLatexSource(value) {
  return String(value || '')
    .replace(/\\(?:displaystyle|textstyle|scriptstyle|scriptscriptstyle)\s*/g, '')
    .replace(/\\(?:limits|nolimits)/g, '')
    .replace(/\\[dt]frac/g, '\\frac')
}

function normalizeLatexCommands(value) {
  return String(value)
    .replace(/\\(?:displaystyle|textstyle|scriptstyle|scriptscriptstyle)\s*/g, '')
    .replace(/\\(?:limits|nolimits)/g, '')
    .replace(/\\[dt]frac/g, '\\frac')
    .replace(/\\mathrm\{([^{}]*)\}/g, '$1')
    .replace(/\\left\./g, '')
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
    .replace(/\\ne(?![A-Za-z])/g, '≠')
    .replace(/\\begin\{cases\}/g, '')
    .replace(/\\end\{cases\}/g, '')
    .replace(/\\\\/g, '；')
    .replace(/&/g, '，')
    .replace(/\\partial/g, '∂')
    .replace(/\\int/g, '∫')
    .replace(/\\(arcsin|arccos|arctan|sin|cos|tan|ln|log|sec|max|min)\b/g, '$1')
    .replace(/\b(arcsin|arccos|arctan|sin|cos|tan|ln|log|sec|max|min)(?=[0-9A-Za-z])/g, '$1 ')
}

function replacePowers(value) {
  return String(value)
    .replace(/\^\{(-?[0-9xyn+\-]+)\}/g, (_, power) => toSuperscript(power))
    .replace(/\^\((-?\d+)\)/g, (_, power) => toSuperscript(power))
    .replace(/\^(-?[0-9xyn])/g, (_, power) => toSuperscript(power))
}

function replaceSubscripts(value) {
  return String(value)
    .replace(/_\{([0-9xyena+\-]+)\}/g, (_, subscript) => toSubscript(subscript))
    .replace(/_([0-9xyena+\-])/g, (_, subscript) => toSubscript(subscript))
}

function tidyMathTextBase(value) {
  return String(value)
    .replace(/\s+/g, ' ')
    .replace(/\s*→\s*/g, '→')
    .replace(/∂\s+(?=[A-Za-z])/g, '∂')
    .replace(/(∂[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ˣʸⁿ]*)\s+(?=[A-Za-z])/g, '$1')
    .replace(/\bd\s+(?=[A-Za-z])/g, 'd')
    .replace(/\s+([，。；：？！、)])/g, '$1')
    .replace(/([(])\s+/g, '$1')
    .replace(/\s+([)])/g, '$1')
}

function tidyMathText(value) {
  return tidyMathTextBase(value).trim()
}

function parseBraceGroup(value, start) {
  let cursor = start
  while (value[cursor] === ' ') cursor += 1
  if (value[cursor] !== '{') return null

  let depth = 0
  for (let index = cursor; index < value.length; index += 1) {
    const char = value[index]
    if (char === '{') {
      depth += 1
    } else if (char === '}') {
      depth -= 1
      if (depth === 0) {
        return {
          content: value.slice(cursor + 1, index),
          end: index + 1
        }
      }
    }
  }

  return null
}

function parseBracketGroup(value, start) {
  let cursor = start
  while (value[cursor] === ' ') cursor += 1
  if (value[cursor] !== '[') return null

  let depth = 0
  for (let index = cursor; index < value.length; index += 1) {
    const char = value[index]
    if (char === '[') {
      depth += 1
    } else if (char === ']') {
      depth -= 1
      if (depth === 0) {
        return { content: value.slice(cursor + 1, index), end: index + 1 }
      }
    }
  }

  return null
}

function parseParenGroup(value, start) {
  let cursor = start
  while (value[cursor] === ' ') cursor += 1
  if (value[cursor] !== '(') return null

  let depth = 0
  for (let index = cursor; index < value.length; index += 1) {
    const char = value[index]
    if (char === '(') {
      depth += 1
    } else if (char === ')') {
      depth -= 1
      if (depth === 0) {
        return { content: value.slice(cursor + 1, index), end: index + 1 }
      }
    }
  }

  return null
}

function parseLatexScript(value, start) {
  let cursor = start
  while (value[cursor] === ' ') cursor += 1
  if (value[cursor] !== '_' && value[cursor] !== '^') return null

  const marker = value[cursor]
  cursor += 1
  while (value[cursor] === ' ') cursor += 1

  const group = parseBraceGroup(value, cursor)
  if (group) {
    return {
      marker,
      content: group.content,
      end: group.end
    }
  }

  if (cursor < value.length) {
    return {
      marker,
      content: value[cursor],
      end: cursor + 1
    }
  }

  return null
}

function parseLatexScripts(value, start) {
  let cursor = start
  let lower = ''
  let upper = ''

  for (let index = 0; index < 2; index += 1) {
    const script = parseLatexScript(value, cursor)
    if (!script) break
    if (script.marker === '_') {
      lower = script.content
    } else {
      upper = script.content
    }
    cursor = script.end
  }

  if (!lower && !upper) return null
  return { lower, upper, end: cursor }
}

function parseStructuredLatex(value) {
  const raw = normalizeStructuralLatexSource(value)
  const tokens = []
  let cursor = 0
  let index = 0

  function pushText(end) {
    if (end > cursor) {
      tokens.push({ type: 'rawText', text: raw.slice(cursor, end) })
    }
  }

  while (index < raw.length) {
    if (raw.startsWith('\\begin{cases}', index)) {
      const contentStart = index + '\\begin{cases}'.length
      const contentEnd = raw.indexOf('\\end{cases}', contentStart)
      if (contentEnd >= 0) {
        pushText(index)
        tokens.push({ type: 'cases', rows: parseCasesRows(raw.slice(contentStart, contentEnd)) })
        index = contentEnd + '\\end{cases}'.length
        cursor = index
        continue
      }
    }

    if (raw.startsWith('\\frac', index)) {
      const numerator = parseBraceGroup(raw, index + 5)
      const denominator = numerator ? parseBraceGroup(raw, numerator.end) : null
      if (numerator && denominator) {
        pushText(index)
        tokens.push({ type: 'fraction', numerator: numerator.content, denominator: denominator.content })
        index = denominator.end
        cursor = index
        continue
      }
    }

    if (raw.startsWith('\\left.', index)) {
      pushText(index)
      index += 6
      cursor = index
      continue
    }

    if (raw.startsWith('\\right|', index)) {
      pushText(index)
      const scripts = parseLatexScripts(raw, index + 7)
      tokens.push({ type: 'evalBar', condition: scripts?.lower || '' })
      index = scripts?.end || index + 7
      cursor = index
      continue
    }

    if (raw[index] === '|') {
      const scripts = parseLatexScripts(raw, index + 1)
      if (scripts?.lower) {
        pushText(index)
        tokens.push({ type: 'evalBar', condition: scripts.lower })
        index = scripts.end
        cursor = index
        continue
      }
    }

    if (raw.startsWith('\\int', index)) {
      pushText(index)
      const scripts = parseLatexScripts(raw, index + 4)
      tokens.push({ type: 'integral', lower: scripts?.lower || '', upper: scripts?.upper || '' })
      index = scripts?.end || index + 4
      cursor = index
      continue
    }

    if (raw.startsWith('\\sqrt', index)) {
      let groupStart = index + 5
      const optionalRoot = parseBracketGroup(raw, groupStart)
      if (optionalRoot) {
        groupStart = optionalRoot.end
      }
      const radicand = parseBraceGroup(raw, groupStart)
      if (radicand) {
        pushText(index)
        tokens.push({ type: 'sqrt', radicand: radicand.content })
        index = radicand.end
        cursor = index
        continue
      }
    }

    if (raw[index] === '√') {
      const radicand = parseParenGroup(raw, index + 1)
      if (radicand) {
        pushText(index)
        tokens.push({ type: 'sqrt', radicand: radicand.content })
        index = radicand.end
        cursor = index
        continue
      }
    }

    if (raw.startsWith('\\lim_', index)) {
      const condition = parseBraceGroup(raw, index + 5)
      if (condition) {
        pushText(index)
        tokens.push({ type: 'limit', condition: condition.content })
        index = condition.end
        cursor = index
        continue
      }
    }

    if (raw.startsWith('lim', index)) {
      const condition = parseParenGroup(raw, index + 3)
      if (condition) {
        pushText(index)
        tokens.push({ type: 'limit', condition: condition.content })
        index = condition.end
        cursor = index
        continue
      }
    }

    index += 1
  }

  pushText(raw.length)
  return tokens
}

function cleanCasesCell(value) {
  return String(value || '')
    .trim()
    .replace(/^[,，;；]+/, '')
    .replace(/[,，;；.。]+$/, '')
    .trim()
}

function parseCasesRows(value) {
  const rows = String(value || '')
    .split(/\\\\/)
    .map((row) => row.trim())
    .filter(Boolean)
    .map((row) => {
      const cells = row.split('&')
      return {
        expression: cleanCasesCell(cells[0]),
        condition: cleanCasesCell(cells.slice(1).join(' '))
      }
    })
    .filter((row) => row.expression || row.condition)

  return rows.length ? rows : [{ expression: formatRawText(value), condition: '' }]
}

function formatRawText(value) {
  let result = String(value || '')
  result = normalizeLatexCommands(result)
  result = replacePowers(result)
  result = replaceSubscripts(result)
  return tidyMathTextBase(result)
}

function wrapFractionPart(value) {
  if (!value) return ''
  if (/^\(.+\)$/.test(value)) return value
  return /[\s+\-*/]/.test(value) ? `(${value})` : value
}

function formatForPlain(value) {
  const raw = stripMathDelimiters(value || '')
  const parts = parseStructuredLatex(raw)
  const text = parts
    .map((part) => {
      if (part.type === 'rawText') {
        return formatRawText(part.text)
      }
      if (part.type === 'fraction') {
        return `${wrapFractionPart(formatForPlain(part.numerator))}/${wrapFractionPart(formatForPlain(part.denominator))}`
      }
      if (part.type === 'sqrt') {
        return `√(${formatForPlain(part.radicand)})`
      }
      if (part.type === 'limit') {
        return `lim(${formatForPlain(part.condition)})`
      }
      if (part.type === 'integral') {
        const lower = part.lower ? `_${formatForPlain(part.lower)}` : ''
        const upper = part.upper ? `^${formatForPlain(part.upper)}` : ''
        return `∫${lower}${upper}`
      }
      if (part.type === 'evalBar') {
        return `|_${formatForPlain(part.condition)}`
      }
      if (part.type === 'cases') {
        return part.rows
          .map((row) => `${formatForPlain(row.expression)}${row.condition ? `, ${formatForPlain(row.condition)}` : ''}`)
          .join('; ')
      }
      return ''
    })
    .join('')
  return tidyMathText(text)
}

export function formatMathText(value) {
  if (value === null || value === undefined) {
    return ''
  }
  return formatForPlain(value)
}

function cleanFractionPart(value) {
  const text = formatForPlain(value).trim()
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

function createSqrtToken(radicand) {
  return {
    type: 'sqrt',
    radicand: formatForPlain(radicand)
  }
}

function createLimitToken(condition) {
  return {
    type: 'limit',
    condition: formatForPlain(condition)
  }
}

function createIntegralToken(lower, upper) {
  return {
    type: 'integral',
    lower: formatForPlain(lower),
    upper: formatForPlain(upper)
  }
}

function createEvalBarToken(condition) {
  return {
    type: 'evalBar',
    condition: formatForPlain(condition)
  }
}

function createCasesToken(rows) {
  return {
    type: 'cases',
    rows: (rows || [])
      .map((row) => ({
        expression: formatForPlain(row.expression),
        condition: formatForPlain(row.condition)
      }))
      .filter((row) => row.expression || row.condition)
  }
}

const SUPERSCRIPT_CHARS = '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ˣʸⁿ'
const SUBSCRIPT_CHARS = '₀₁₂₃₄₅₆₇₈₉₊₋ₓᵧₐₑₙ'
const SIMPLE_MATH_PART = `[A-Za-z0-9π∞∂√${SUPERSCRIPT_CHARS}${SUBSCRIPT_CHARS}]+`
const GROUPED_MATH_PART = `\\[[^\\]]+\\]|\\([^)]+\\)|${SIMPLE_MATH_PART}`
const PLAIN_FRACTION_PATTERN = new RegExp(`(${GROUPED_MATH_PART})\\s*\\/\\s*(${GROUPED_MATH_PART})`, 'g')

function pushTextToken(tokens, text) {
  if (!text) return
  tokens.push({ type: 'text', text })
}

function pushPlainMathTokens(tokens, value) {
  const text = formatRawText(value)
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

  const raw = stripMathDelimiters(value)
  const parsed = parseStructuredLatex(raw)
  const tokens = []

  parsed.forEach((part) => {
    if (part.type === 'rawText') {
      pushPlainMathTokens(tokens, part.text)
      return
    }
    if (part.type === 'fraction') {
      tokens.push(createFractionToken(part.numerator, part.denominator))
      return
    }
    if (part.type === 'sqrt') {
      tokens.push(createSqrtToken(part.radicand))
      return
    }
    if (part.type === 'limit') {
      tokens.push(createLimitToken(part.condition))
      return
    }
    if (part.type === 'integral') {
      tokens.push(createIntegralToken(part.lower, part.upper))
      return
    }
    if (part.type === 'evalBar') {
      tokens.push(createEvalBarToken(part.condition))
      return
    }
    if (part.type === 'cases') {
      tokens.push(createCasesToken(part.rows))
    }
  })

  return tokens.filter((token) => token.type !== 'text' || token.text)
}

const KATEX_COMMAND_PATTERN =
  /\\(?:begin|end|frac|dfrac|tfrac|sqrt|lim|int|partial|left|right|sum|prod|arcsin|arccos|arctan|sin|cos|tan|ln|log|sec|max|min|pm|cdot|times|leq|le|geq|ge|ne|neq|infty|pi|to|mathrm|displaystyle|textstyle|scriptstyle|scriptscriptstyle|limits|nolimits)(?=[^A-Za-z]|$)/g

const CJK_PATTERN = /[\u3400-\u9fff]/
const CJK_OR_STOP_PUNCT_PATTERN = /[\u3400-\u9fff\u3002\uff0c\uff1b\uff1a\uff1f\uff01\uff0e]/
const WHOLE_NUMBER_FRACTION_PATTERN = /^[-+]?\d+(?:\.\d+)?\s*\/\s*[-+]?\d+(?:\.\d+)?$/

function normalizeMathSource(value) {
  return String(value ?? '').replace(/\r?\n/g, ' ').trim()
}

function normalizeKatexLatex(value) {
  return String(value ?? '')
    .replace(/\u221a\s*\(([^()]*)\)/g, '\\sqrt{$1}')
    .replace(/\u221e/g, '\\infty')
    .replace(/\u2192/g, '\\to')
    .replace(/\\[dt]frac/g, '\\frac')
    .replace(/\\(?:displaystyle|textstyle|scriptstyle|scriptscriptstyle)\s*/g, '')
    .replace(/\\(?:limits|nolimits)/g, '')
    .replace(/\u00b9/g, '^1')
    .replace(/\u00b2/g, '^2')
    .replace(/\u00b3/g, '^3')
    .trim()
}

export function escapeMathTextHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function pushKatexPart(parts, math, content) {
  if (!content) return
  parts.push({
    math,
    content: math ? normalizeKatexLatex(content) : content
  })
}

function findNextDelimiter(text, start) {
  const candidates = [
    { open: '\\(', close: '\\)', display: false },
    { open: '\\[', close: '\\]', display: true },
    { open: '$', close: '$', display: false }
  ]
    .map((delimiter) => ({ ...delimiter, index: text.indexOf(delimiter.open, start) }))
    .filter((delimiter) => delimiter.index >= 0)
    .sort((left, right) => left.index - right.index)

  return candidates[0] || null
}

function splitExplicitMath(text) {
  const parts = []
  let cursor = 0
  let foundMath = false

  while (cursor < text.length) {
    const delimiter = findNextDelimiter(text, cursor)
    if (!delimiter) break

    if (delimiter.open === '$' && delimiter.index > 0 && text[delimiter.index - 1] === '\\') {
      cursor = delimiter.index + 1
      continue
    }

    const contentStart = delimiter.index + delimiter.open.length
    const closeIndex = text.indexOf(delimiter.close, contentStart)
    if (closeIndex < 0) break

    pushTextWithImplicitMath(parts, text.slice(cursor, delimiter.index))
    pushKatexPart(parts, true, text.slice(contentStart, closeIndex))
    foundMath = true
    cursor = closeIndex + delimiter.close.length
  }

  pushTextWithImplicitMath(parts, text.slice(cursor))
  return foundMath ? parts : null
}

function findNextCommandStart(text, start) {
  KATEX_COMMAND_PATTERN.lastIndex = start
  const match = KATEX_COMMAND_PATTERN.exec(text)
  return match ? match.index : -1
}

function readCommandMathRun(text, start) {
  let cursor = start
  let braceDepth = 0
  let parenDepth = 0
  let bracketDepth = 0

  while (cursor < text.length) {
    const char = text[cursor]

    if (char === '\\') {
      cursor += 1
      continue
    }

    if (char === '{') braceDepth += 1
    if (char === '}') braceDepth = Math.max(0, braceDepth - 1)
    if (char === '(') parenDepth += 1
    if (char === ')') parenDepth = Math.max(0, parenDepth - 1)
    if (char === '[') bracketDepth += 1
    if (char === ']') bracketDepth = Math.max(0, bracketDepth - 1)

    const depth = braceDepth + parenDepth + bracketDepth
    if (cursor > start && depth === 0 && (CJK_OR_STOP_PUNCT_PATTERN.test(char) || char === '?' || char === '!')) {
      break
    }

    cursor += 1
  }

  return cursor
}

function hasUsefulPlainMathSignal(value) {
  const text = value.trim()
  if (!text) return false
  if (WHOLE_NUMBER_FRACTION_PATTERN.test(text)) return true
  if (!/[A-Za-z0-9]/.test(text)) return false
  const words = text.match(/[A-Za-z]{3,}/g) || []
  const allowedMathWords = new Set(['sin', 'cos', 'tan', 'log', 'lim', 'max', 'min'])
  if (words.some((word) => !allowedMathWords.has(word))) return false
  if (/[=^_]/.test(text)) return true
  return /^[([-]?\d+(?:\.\d+)?\s*\/\s*[-+]?\d+(?:\.\d+)?[\])]?$/.test(text)
}

function readPlainMathRun(text, start) {
  let cursor = start
  let braceDepth = 0
  let parenDepth = 0
  let bracketDepth = 0

  while (cursor < text.length) {
    const char = text[cursor]
    if (char === '{') braceDepth += 1
    if (char === '}') braceDepth = Math.max(0, braceDepth - 1)
    if (char === '(') parenDepth += 1
    if (char === ')') parenDepth = Math.max(0, parenDepth - 1)
    if (char === '[') bracketDepth += 1
    if (char === ']') bracketDepth = Math.max(0, bracketDepth - 1)

    const depth = braceDepth + parenDepth + bracketDepth
    if (cursor > start && depth === 0 && CJK_OR_STOP_PUNCT_PATTERN.test(char)) {
      break
    }

    cursor += 1
  }

  return cursor
}

function pushTextWithImplicitMath(parts, value) {
  const text = String(value || '')
  let plainCursor = 0
  let searchCursor = 0

  while (searchCursor < text.length) {
    let start = -1
    for (let index = searchCursor; index < text.length; index += 1) {
      const char = text[index]
      const previous = index > 0 ? text[index - 1] : ''
      if (/[A-Za-z0-9]/.test(previous)) continue
      if (/[A-Za-z0-9([]/.test(char)) {
        start = index
        break
      }
    }

    if (start < 0) {
      pushKatexPart(parts, false, text.slice(plainCursor))
      return
    }

    const end = readPlainMathRun(text, start)
    const candidate = text.slice(start, end).trim()

    if (hasUsefulPlainMathSignal(candidate) && !CJK_PATTERN.test(candidate)) {
      pushKatexPart(parts, false, text.slice(plainCursor, start))
      pushKatexPart(parts, true, candidate)
      plainCursor = end
      searchCursor = end
    } else {
      searchCursor = start + 1
    }
  }

  pushKatexPart(parts, false, text.slice(plainCursor))
}

function splitImplicitCommandMath(text) {
  const parts = []
  let cursor = 0

  while (cursor < text.length) {
    const start = findNextCommandStart(text, cursor)
    if (start < 0) break

    pushTextWithImplicitMath(parts, text.slice(cursor, start))
    const end = readCommandMathRun(text, start)
    pushKatexPart(parts, true, text.slice(start, end))
    cursor = end
  }

  pushTextWithImplicitMath(parts, text.slice(cursor))
  return parts
}

function isWholeMathText(text) {
  if (!text || CJK_PATTERN.test(text)) return false
  KATEX_COMMAND_PATTERN.lastIndex = 0
  if (KATEX_COMMAND_PATTERN.test(text)) {
    KATEX_COMMAND_PATTERN.lastIndex = 0
    return true
  }
  KATEX_COMMAND_PATTERN.lastIndex = 0
  return hasUsefulPlainMathSignal(text)
}

export function splitMathTextForKatex(value) {
  const text = normalizeMathSource(value)
  if (!text) return []

  const explicitParts = splitExplicitMath(text)
  if (explicitParts) return explicitParts

  if (isWholeMathText(text)) {
    return [{ math: true, content: normalizeKatexLatex(text) }]
  }

  return splitImplicitCommandMath(text)
}

const FORMULA_IMAGE_SIGNAL_PATTERN =
  /\\(?:begin\{cases\}|end\{cases\}|frac|dfrac|tfrac|sqrt|lim|int|partial|left|right|to|infty|pi|sin|cos|tan|ln|log)|\^|_|√|∫|∂|∞|→|π|lim\s*[\(_]|[A-Za-z0-9)\]\u00b9\u00b2\u00b3]\s*\/\s*[A-Za-z0-9([]/

export function shouldUseMathImage(value) {
  const text = normalizeMathSource(value)
  if (!text) return false
  return FORMULA_IMAGE_SIGNAL_PATTERN.test(text)
}

export function estimateMathImageDisplayRpx(value) {
  const text = formatMathText(value)
  if (!text) return 120

  let width = 36
  for (const char of text) {
    if (/[\u3400-\u9fff]/.test(char)) {
      width += 32
    } else if (char === '/') {
      width += 26
    } else if (/[=+\-×·()[\]{}]/.test(char)) {
      width += 20
    } else if (char.trim() === '') {
      width += 12
    } else {
      width += 18
    }
  }

  if (/\\frac|\/|√|\\sqrt/.test(String(value || ''))) {
    width += 24
  }
  return Math.max(92, Math.min(680, Math.round(width)))
}
