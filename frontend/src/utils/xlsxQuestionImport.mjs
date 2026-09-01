import { strFromU8, unzipSync } from 'fflate'

const MAX_UPLOAD_BYTES = 20 * 1024 * 1024
const MAX_ZIP_EXPANDED_BYTES = 50 * 1024 * 1024
const MAX_EXCEL_QUESTION_ROWS = 200
const MAX_HEADER_SCAN_ROWS = 10
const PREFERRED_SHEET_NAME = '题目'

const QUESTION_IMPORT_HEADERS = [
  'exam_code',
  'subject',
  'module',
  'submodule',
  'stem',
  'option_a',
  'option_b',
  'option_c',
  'option_d',
  'answer',
  'explanation',
  'difficulty',
  'source_type',
  'source_year',
]

const REQUIRED_HEADERS = new Set([
  'exam_code',
  'subject',
  'module',
  'submodule',
  'stem',
  'option_a',
  'option_b',
  'option_c',
  'option_d',
  'answer',
  'explanation',
])

const HEADER_ALIASES = {
  exam_code: ['exam_code', 'examcode', '考试代码', '试卷代码', '科目代码'],
  subject: ['subject', '科目', '学科'],
  module: ['module', '模块', '题型模块'],
  submodule: ['submodule', '子模块', '考点', '知识点', '细分模块'],
  stem: ['stem', '题干', '问题', '题目', '题干内容'],
  option_a: ['option_a', 'optiona', 'a', '选项a', '选项a项', 'a选项'],
  option_b: ['option_b', 'optionb', 'b', '选项b', '选项b项', 'b选项'],
  option_c: ['option_c', 'optionc', 'c', '选项c', '选项c项', 'c选项'],
  option_d: ['option_d', 'optiond', 'd', '选项d', '选项d项', 'd选项'],
  answer: ['answer', '答案', '正确答案', '答案选项'],
  explanation: ['explanation', '解析', '答案解析', '题目解析'],
  difficulty: ['difficulty', '难度', '难度等级'],
  source_type: ['source_type', 'sourcetype', '来源类型', '来源类别'],
  source_year: ['source_year', 'sourceyear', '来源年份', '年份', '真题年份'],
}

const HEADER_ALIAS_INDEX = new Map(
  Object.entries(HEADER_ALIASES).flatMap(([field, aliases]) =>
    aliases.map((alias) => [normalizeHeader(alias), field]),
  ),
)

const SUBJECT_ALIASES = new Map([
  ['逻辑', '逻辑推理'],
  ['逻辑推理', '逻辑推理'],
  ['英文', '英语运用'],
  ['英语', '英语运用'],
])

const MODULE_ALIASES = new Map([
  ['概念', '概念'],
  ['判断', '判断'],
  ['概念判断', '概念判断'],
  ['推理', '推理'],
  ['推理规则', '推理'],
  ['论证', '论证'],
  ['削弱加强', '论证'],
  ['加强削弱', '论证'],
])

const SUBMODULE_ALIASES = new Map([
  ['概念', '概念种类'],
  ['概念种类', '概念种类'],
  ['概念关系', '概念关系'],
  ['定义', '定义'],
  ['划分', '划分'],
  ['判断', '判断种类'],
  ['判断种类', '判断种类'],
  ['判断关系', '判断关系'],
  ['加强', '加强'],
  ['加强论证', '加强'],
  ['支持', '加强'],
  ['支持论证', '加强'],
  ['削弱', '削弱'],
  ['削弱论证', '削弱'],
  ['质疑', '削弱'],
  ['反驳', '削弱'],
  ['假设', '假设'],
  ['前提', '假设'],
  ['隐含前提', '假设'],
  ['必要假设', '假设'],
  ['解释', '解释'],
  ['推论', '推论'],
  ['结论', '推论'],
  ['论证结构', '论证结构'],
  ['形式相似', '论证结构'],
  ['谬误', '谬误识别'],
  ['谬误识别', '谬误识别'],
  ['演绎', '演绎推理'],
  ['演绎推理', '演绎推理'],
  ['归纳', '归纳推理'],
  ['归纳推理', '归纳推理'],
  ['类比', '类比推理'],
  ['类比推理', '类比推理'],
  ['综合', '综合推理'],
  ['综合推理', '综合推理'],
])

const SOURCE_TYPE_ALIASES = new Map([
  ['manual', 'manual'],
  ['手工录入', 'manual'],
  ['手工', 'manual'],
  ['人工', 'manual'],
  ['自编', 'manual'],
  ['source_extracted', 'source_extracted'],
  ['sourceextracted', 'source_extracted'],
  ['资料整理', 'source_extracted'],
  ['抽取', 'source_extracted'],
  ['整理', 'source_extracted'],
  ['real_exam', 'real_exam'],
  ['realexam', 'real_exam'],
  ['真题', 'real_exam'],
  ['历年真题', 'real_exam'],
])

export async function recognizeQuestionImportXlsxFile(file, filename = 'upload.xlsx') {
  const resolvedFilename = String(filename || file?.name || 'upload.xlsx')
  if (!resolvedFilename.toLowerCase().endsWith('.xlsx')) {
    throw new Error('仅支持 .xlsx 格式的 Excel 文件。')
  }
  if (!file || typeof file.arrayBuffer !== 'function') {
    throw new Error('未读取到有效的 Excel 文件。')
  }
  if (Number(file.size || 0) > MAX_UPLOAD_BYTES) {
    throw new Error('单个 Excel 文件不能超过 20MB。')
  }

  let archive
  try {
    archive = unzipSync(new Uint8Array(await file.arrayBuffer()))
  } catch (error) {
    throw new Error(`Excel 文件无法读取：${error?.message || '文件可能已损坏'}`)
  }
  const expandedBytes = Object.values(archive).reduce((total, entry) => total + entry.length, 0)
  if (expandedBytes > MAX_ZIP_EXPANDED_BYTES) {
    throw new Error('Excel 解压后的内容过大，请拆分文件后再上传。')
  }

  const sharedStrings = readSharedStrings(archive)
  const selection = discoverImportWorksheet(archive, sharedStrings)
  const questions = []

  selection.rows.slice(selection.header.rowIndex + 1).forEach((row, rowOffset) => {
    const values = readRowValues(row, sharedStrings)
    const rawQuestion = Object.fromEntries(
      QUESTION_IMPORT_HEADERS.map((field) => [field, values[selection.header.columns[field]] || '']),
    )
    if (!Object.values(rawQuestion).some((value) => cleanCell(value))) return

    const excelRow = readAttribute(row.openingTag, 'r') || String(selection.header.rowIndex + rowOffset + 2)
    const question = normalizeQuestion(rawQuestion)
    question.excel_row = Number(excelRow) || excelRow
    question.image_name = resolvedFilename.split(/[\\/]/).pop() || resolvedFilename
    question.image_index = questions.length
    questions.push(question)
    if (questions.length > MAX_EXCEL_QUESTION_ROWS) {
      throw new Error(`单个 Excel 最多导入 ${MAX_EXCEL_QUESTION_ROWS} 题，请拆分后再上传。`)
    }
  })

  const warnings = buildRecognitionWarnings(selection, questions.length)
  return {
    filename: resolvedFilename,
    extension: 'xlsx',
    provider: 'xlsx-local',
    text: '',
    questions,
    warnings,
  }
}

function discoverImportWorksheet(archive, sharedStrings) {
  const candidates = []
  for (const sheet of worksheetEntries(archive)) {
    const xml = readArchiveText(archive, sheet.path)
    const rows = findElementBlocks(xml, 'row')
    const header = findHeaderRow(rows, sharedStrings)
    if (header) {
      candidates.push({ ...sheet, rows, header })
    }
  }

  if (!candidates.length) {
    throw new Error('未找到可识别的题目表头。请保留题干、A-D 选项、答案和解析等字段。')
  }

  candidates.sort((left, right) => {
    const leftPreferred = left.name === PREFERRED_SHEET_NAME ? 0 : 1
    const rightPreferred = right.name === PREFERRED_SHEET_NAME ? 0 : 1
    return leftPreferred - rightPreferred || left.name.localeCompare(right.name, 'zh-CN')
  })

  if (candidates.length > 1 && candidates[0].name !== PREFERRED_SHEET_NAME) {
    throw new Error(`发现 ${candidates.length} 个可识别的题目工作表，请仅保留一个，或将目标工作表命名为“${PREFERRED_SHEET_NAME}”。`)
  }

  return candidates[0]
}

function findHeaderRow(rows, sharedStrings) {
  for (let rowIndex = 0; rowIndex < Math.min(rows.length, MAX_HEADER_SCAN_ROWS); rowIndex += 1) {
    const values = readRowValues(rows[rowIndex], sharedStrings)
    const mapped = mapHeaders(values)
    if (mapped.missingRequired.length === 0) {
      return {
        rowIndex,
        columns: mapped.columns,
        aliases: mapped.aliases,
        ignoredHeaders: mapped.ignoredHeaders,
      }
    }
  }
  return null
}

function mapHeaders(values) {
  const columns = {}
  const aliases = []
  const ignoredHeaders = []
  const duplicateFields = []

  values.forEach((value, index) => {
    const label = cleanCell(value)
    if (!label) return
    const field = HEADER_ALIAS_INDEX.get(normalizeHeader(label))
    if (!field) {
      ignoredHeaders.push(label)
      return
    }
    if (Object.hasOwn(columns, field)) {
      duplicateFields.push(field)
      return
    }
    columns[field] = index
    if (normalizeHeader(label) !== normalizeHeader(field)) aliases.push(label)
  })

  const missingRequired = [...REQUIRED_HEADERS].filter((field) => !Object.hasOwn(columns, field))
  if (!missingRequired.length && duplicateFields.length) {
    throw new Error(`表头中存在重复字段：${[...new Set(duplicateFields)].join('、')}。请保留其中一列。`)
  }
  return { columns, aliases, ignoredHeaders, missingRequired }
}

function normalizeQuestion(rawQuestion) {
  const answer = normalizeAnswer(rawQuestion.answer)
  const subject = normalizeCatalogValue(rawQuestion.subject, SUBJECT_ALIASES)
  let module = normalizeCatalogValue(rawQuestion.module, MODULE_ALIASES)
  const submodule = normalizeCatalogValue(rawQuestion.submodule, SUBMODULE_ALIASES)
  if (subject === '逻辑推理' && module === '概念判断') {
    module = ['判断种类', '判断关系'].includes(submodule) ? '判断' : '概念'
  }
  const question = {
    exam_code: cleanCell(rawQuestion.exam_code).toUpperCase(),
    subject,
    module,
    submodule,
    stem: cleanCell(rawQuestion.stem),
    option_a: normalizeOption(rawQuestion.option_a, 'A'),
    option_b: normalizeOption(rawQuestion.option_b, 'B'),
    option_c: normalizeOption(rawQuestion.option_c, 'C'),
    option_d: normalizeOption(rawQuestion.option_d, 'D'),
    answer,
    explanation: cleanCell(rawQuestion.explanation),
    difficulty: normalizeDifficulty(rawQuestion.difficulty),
    source_type: normalizeSourceType(rawQuestion.source_type),
    source_year: cleanCell(rawQuestion.source_year) || null,
  }
  return question
}

function normalizeCatalogValue(value, aliases) {
  const cleaned = cleanCell(value)
  return aliases.get(normalizeHeader(cleaned)) || cleaned
}

function normalizeAnswer(value) {
  const cleaned = cleanCell(value)
  const match = cleaned.match(/^(?:(?:正确)?答案|answer|选项)?\s*[:：]?\s*([A-D])(?:\s*项)?[.、。)）]?\s*$/i)
  return match ? match[1].toUpperCase() : cleaned.toUpperCase()
}

function normalizeOption(value, optionLetter) {
  const cleaned = cleanCell(value)
  const prefix = new RegExp(`^(?:选项\\s*)?${optionLetter}\\s*(?:[.、。:：）)])\\s*`, 'i')
  return cleaned.replace(prefix, '')
}

function normalizeDifficulty(value) {
  const cleaned = cleanCell(value)
  if (!cleaned) return 2
  if (/^(简单|易|easy)$/i.test(cleaned)) return 1
  if (/^(中等|适中|medium)$/i.test(cleaned)) return 2
  if (/^(困难|难|hard)$/i.test(cleaned)) return 3
  const number = Number(cleaned)
  return Number.isFinite(number) ? number : cleaned
}

function normalizeSourceType(value) {
  const cleaned = cleanCell(value)
  return SOURCE_TYPE_ALIASES.get(normalizeHeader(cleaned)) || cleaned || 'manual'
}

function buildRecognitionWarnings(selection, questionCount) {
  const warnings = []
  if (selection.name !== PREFERRED_SHEET_NAME) {
    warnings.push(`已从工作表“${selection.name}”识别题目。建议后续统一命名为“${PREFERRED_SHEET_NAME}”。`)
  }
  if (selection.header.rowIndex > 0) {
    warnings.push(`已自动跳过前 ${selection.header.rowIndex} 行说明文字，从第 ${selection.header.rowIndex + 1} 行识别表头。`)
  }
  if (selection.header.aliases.length) {
    warnings.push('已兼容中文或别名表头，并自动转换为系统字段。')
  }
  if (selection.header.ignoredHeaders.length) {
    warnings.push(`已忽略 ${selection.header.ignoredHeaders.length} 个备注/辅助列。`)
  }
  if (!questionCount) {
    warnings.push('已识别表头，但没有可导入的数据行。请从表头下一行开始填写题目。')
  }
  return warnings
}

function worksheetEntries(archive) {
  const workbookXml = readArchiveText(archive, 'xl/workbook.xml')
  const relationshipsXml = readArchiveText(archive, 'xl/_rels/workbook.xml.rels')
  const relationTargets = new Map(
    findOpeningTags(relationshipsXml, 'Relationship').map((tag) => [
      readAttribute(tag, 'Id'),
      readAttribute(tag, 'Target'),
    ]),
  )

  return findOpeningTags(workbookXml, 'sheet').map((tag) => {
    const name = cleanCell(readAttribute(tag, 'name'))
    const relationId = readAttribute(tag, 'r:id') || readAttribute(tag, 'id')
    const target = relationTargets.get(relationId)
    const path = resolveArchivePath('xl', target)
    if (!name || !path || !archive[path]) {
      throw new Error('Excel 工作表结构不完整，请重新另存为 .xlsx 后再上传。')
    }
    return { name, path }
  })
}

function readSharedStrings(archive) {
  if (!archive['xl/sharedStrings.xml']) return []
  const xml = readArchiveText(archive, 'xl/sharedStrings.xml')
  return findElementBlocks(xml, 'si').map((item) => collectTagTexts(item.innerXml, 't').join(''))
}

function readRowValues(row, sharedStrings) {
  const cells = findElementBlocks(row.innerXml, 'c')
  const values = []
  let nextIndex = 0
  cells.forEach((cell) => {
    const reference = readAttribute(cell.openingTag, 'r')
    const columnIndex = columnIndexFromReference(reference)
    const index = Number.isInteger(columnIndex) ? columnIndex : nextIndex
    values[index] = readCellValue(cell, sharedStrings)
    nextIndex = index + 1
  })
  return values
}

function readCellValue(cell, sharedStrings) {
  const type = readAttribute(cell.openingTag, 't')
  if (type === 'inlineStr') return collectTagTexts(cell.innerXml, 't').join('')
  const value = extractTagText(cell.innerXml, 'v')
  if (type === 's') return sharedStrings[Number(value)] || ''
  if (type === 'str') return value || collectTagTexts(cell.innerXml, 't').join('')
  return value || collectTagTexts(cell.innerXml, 't').join('')
}

function findOpeningTags(xml, tagName) {
  const expression = new RegExp(`<(?:(?:[A-Za-z_][\\w.-]*):)?${tagName}\\b[^>]*\\/?>`, 'gi')
  return [...String(xml || '').matchAll(expression)].map((match) => match[0])
}

function findElementBlocks(xml, tagName) {
  const expression = new RegExp(
    `<(?:(?:[A-Za-z_][\\w.-]*):)?${tagName}\\b([^>]*)>([\\s\\S]*?)<\\/(?:[A-Za-z_][\\w.-]*:)?${tagName}\\s*>`,
    'gi',
  )
  return [...String(xml || '').matchAll(expression)].map((match) => ({
    openingTag: match[0].slice(0, match[0].indexOf('>') + 1),
    innerXml: match[2],
  }))
}

function collectTagTexts(xml, tagName) {
  const expression = new RegExp(
    `<(?:(?:[A-Za-z_][\\w.-]*):)?${tagName}\\b[^>]*>([\\s\\S]*?)<\\/(?:[A-Za-z_][\\w.-]*:)?${tagName}\\s*>`,
    'gi',
  )
  return [...String(xml || '').matchAll(expression)].map((match) => decodeXmlText(stripXml(match[1])))
}

function extractTagText(xml, tagName) {
  return collectTagTexts(xml, tagName)[0] || ''
}

function readAttribute(tag, attributeName) {
  const expression = new RegExp(`\\s${escapeRegExp(attributeName)}\\s*=\\s*(?:"([^"]*)"|'([^']*)')`, 'i')
  const match = String(tag || '').match(expression)
  return match ? decodeXmlText(match[1] ?? match[2] ?? '') : ''
}

function columnIndexFromReference(reference) {
  const letters = String(reference || '').match(/[A-Za-z]+/)?.[0]
  if (!letters) return null
  return [...letters.toUpperCase()].reduce((total, letter) => total * 26 + letter.charCodeAt(0) - 64, 0) - 1
}

function readArchiveText(archive, path) {
  const entry = archive[path]
  if (!entry) throw new Error(`Excel 缺少必要文件：${path}`)
  return strFromU8(entry)
}

function resolveArchivePath(basePath, target) {
  const raw = String(target || '').replace(/\\/g, '/')
  if (!raw) return ''
  const segments = raw.startsWith('/') ? raw.slice(1).split('/') : [...basePath.split('/'), ...raw.split('/')]
  const normalized = []
  for (const segment of segments) {
    if (!segment || segment === '.') continue
    if (segment === '..') {
      if (!normalized.length) return ''
      normalized.pop()
      continue
    }
    normalized.push(segment)
  }
  return normalized.join('/')
}

function normalizeHeader(value) {
  return cleanCell(value)
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[\s_—–\-:：()（）\[\]【】.。]/g, '')
}

function cleanCell(value) {
  return String(value ?? '')
    .replace(/^\uFEFF/, '')
    .replace(/\r\n/g, '\n')
    .trim()
}

function stripXml(value) {
  return String(value || '').replace(/<[^>]+>/g, '')
}

function decodeXmlText(value) {
  return String(value || '')
    .replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCodePoint(Number.parseInt(code, 16)))
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number.parseInt(code, 10)))
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export { MAX_EXCEL_QUESTION_ROWS, QUESTION_IMPORT_HEADERS }
