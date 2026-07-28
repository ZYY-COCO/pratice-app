import { strFromU8, unzipSync } from 'fflate'

const TEMPLATE_SHEET_NAME = '题目'
const TEMPLATE_HEADERS = [
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
  'source_year'
]

const MAX_EXCEL_QUESTION_ROWS = 100
const MAX_ZIP_EXPANDED_BYTES = 50 * 1024 * 1024

export async function recognizeQuestionImportXlsxFile(file, filename = 'upload.xlsx') {
  if (!file || typeof file.arrayBuffer !== 'function') {
    throw new Error('无法读取浏览器中的 Excel 文件，请重新选择文件')
  }

  const normalizedFilename = String(filename || file.name || 'upload.xlsx')
  if (!normalizedFilename.toLowerCase().endsWith('.xlsx')) {
    throw new Error('仅支持 .xlsx Excel 题库模板文件')
  }

  const content = new Uint8Array(await file.arrayBuffer())
  if (!content.length) {
    throw new Error('上传的 Excel 文件为空')
  }

  let archive
  try {
    archive = unzipSync(content)
  } catch (error) {
    throw new Error('Excel 文件结构无效，请使用“下载模板”创建文件')
  }

  const expandedBytes = Object.values(archive).reduce((total, entry) => total + entry.length, 0)
  if (expandedBytes > MAX_ZIP_EXPANDED_BYTES) {
    throw new Error('Excel 解压后的内容过大，请拆分文件后重新上传')
  }

  const sharedStrings = readSharedStrings(archive)
  const sheetPath = findWorksheetPath(archive, TEMPLATE_SHEET_NAME)
  const rows = findElements(readArchiveText(archive, sheetPath), 'row')
  if (!rows.length) {
    throw new Error('Excel 模板缺少表头。请使用“下载模板”获取标准文件。')
  }

  const headers = readRowValues(rows[0], sharedStrings)
    .map((value) => value.replace(/\ufeff/g, '').trim())
  if (!sameStringArray(headers, TEMPLATE_HEADERS)) {
    const expected = TEMPLATE_HEADERS.join('、')
    const actual = headers.join('、') || '（空）'
    throw new Error(`Excel 首行字段与模板不一致。请保持字段顺序不变。期望：${expected}；当前：${actual}`)
  }

  const questions = []
  rows.slice(1).forEach((row, rowOffset) => {
    const excelRow = parsePositiveInteger(readAttribute(row.attributes, 'r')) || rowOffset + 2
    const values = readRowValues(row, sharedStrings)
    if (values.length > TEMPLATE_HEADERS.length && values.slice(TEMPLATE_HEADERS.length).some((value) => value.trim())) {
      throw new Error(`Excel 第 ${excelRow} 行包含模板以外的内容，请删除多余列后重新上传。`)
    }

    const paddedValues = [...values, ...Array(TEMPLATE_HEADERS.length).fill('')]
      .slice(0, TEMPLATE_HEADERS.length)
    if (!paddedValues.some((value) => value.trim())) return

    const question = Object.fromEntries(TEMPLATE_HEADERS.map((header, index) => [header, paddedValues[index]]))
    question.answer = question.answer.trim().toUpperCase()
    question.source_type = question.source_type.trim() || 'manual'
    question.source_year = question.source_year.trim() || null
    question.excel_row = excelRow
    question.image_name = normalizedFilename.split(/[\\/]/).pop() || normalizedFilename
    question.image_index = questions.length
    questions.push(question)

    if (questions.length > MAX_EXCEL_QUESTION_ROWS) {
      throw new Error(`单次 Excel 最多导入 ${MAX_EXCEL_QUESTION_ROWS} 道题，请拆分文件后重新上传。`)
    }
  })

  return {
    filename: normalizedFilename,
    extension: 'xlsx',
    provider: 'xlsx-local',
    text: `已读取 ${questions.length} 道题目`,
    questions,
    warnings: questions.length
      ? []
      : ['题目工作表中没有可导入的数据行。请从 Excel 第 2 行开始填写题目。']
  }
}

function readSharedStrings(archive) {
  const entry = archive['xl/sharedStrings.xml']
  if (!entry) return []
  return findElements(strFromU8(entry), 'si').map((item) => (
    findElements(item.content, 't').map((node) => decodeXmlText(stripXmlTags(node.content))).join('')
  ))
}

function findWorksheetPath(archive, sheetName) {
  const workbook = readArchiveText(archive, 'xl/workbook.xml', 'Excel 文件结构不完整。请使用“下载模板”创建文件。')
  const relationships = readArchiveText(
    archive,
    'xl/_rels/workbook.xml.rels',
    'Excel 文件结构不完整。请使用“下载模板”创建文件。'
  )

  const targetById = new Map(
    findElements(relationships, 'Relationship').map((relationship) => [
      readAttribute(relationship.attributes, 'Id'),
      readAttribute(relationship.attributes, 'Target')
    ])
  )
  const sheet = findElements(workbook, 'sheet').find((item) => (
    decodeXmlText(readAttribute(item.attributes, 'name')) === sheetName
  ))
  const relationshipId = sheet
    ? readAttribute(sheet.attributes, 'r:id') || readAttribute(sheet.attributes, 'id')
    : ''
  const target = targetById.get(relationshipId)
  if (!target) {
    throw new Error('Excel 模板缺少“题目”工作表。请使用“下载模板”获取标准文件。')
  }

  const normalizedPath = normalizeArchivePath(target)
  if (!archive[normalizedPath]) {
    throw new Error('Excel 模板缺少“题目”工作表。请使用“下载模板”获取标准文件。')
  }
  return normalizedPath
}

function normalizeArchivePath(target) {
  const rawPath = String(target || '').replace(/\\/g, '/').replace(/^\/+/, '')
  const candidate = rawPath.startsWith('xl/') ? rawPath : `xl/${rawPath}`
  const parts = []
  candidate.split('/').forEach((part) => {
    if (!part || part === '.') return
    if (part === '..') {
      parts.pop()
      return
    }
    parts.push(part)
  })
  return parts.join('/')
}

function readArchiveText(archive, path, errorMessage = 'Excel 文件结构不完整') {
  const entry = archive[path]
  if (!entry) throw new Error(errorMessage)
  return strFromU8(entry)
}

function readRowValues(row, sharedStrings) {
  const cells = new Map()
  findElements(row.content, 'c').forEach((cell, fallbackIndex) => {
    const reference = readAttribute(cell.attributes, 'r')
    const columnIndex = reference ? excelColumnIndex(reference) : fallbackIndex
    cells.set(columnIndex, readCellValue(cell, sharedStrings))
  })
  if (!cells.size) return []
  const lastColumn = Math.max(...cells.keys())
  return Array.from({ length: lastColumn + 1 }, (_, index) => cells.get(index) || '')
}

function readCellValue(cell, sharedStrings) {
  const type = readAttribute(cell.attributes, 't')
  const inlineText = findElements(cell.content, 't')
    .map((node) => decodeXmlText(stripXmlTags(node.content)))
    .join('')
  if (inlineText) return inlineText.trim()

  const valueNode = findElements(cell.content, 'v')[0]
  let value = valueNode ? decodeXmlText(stripXmlTags(valueNode.content)).trim() : ''
  if (type === 's' && value) {
    const sharedValue = sharedStrings[Number(value)]
    if (sharedValue !== undefined) value = sharedValue
  }
  return String(value).trim()
}

function findElements(xml, localName) {
  const escapedName = String(localName).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const namespace = '(?:[A-Za-z_][\\w.-]*:)?'
  const pattern = new RegExp(
    `<${namespace}${escapedName}\\b([^>]*?)(?:\\/\\s*>|>([\\s\\S]*?)<\\/${namespace}${escapedName}\\s*>)`,
    'gi'
  )
  const elements = []
  let match
  while ((match = pattern.exec(String(xml || ''))) !== null) {
    elements.push({ attributes: match[1] || '', content: match[2] || '' })
  }
  return elements
}

function readAttribute(attributes, name) {
  const escapedName = String(name).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = String(attributes || '').match(new RegExp(`(?:^|\\s)${escapedName}\\s*=\\s*("([^"]*)"|'([^']*)')`, 'i'))
  return decodeXmlText(match?.[2] ?? match?.[3] ?? '')
}

function stripXmlTags(value) {
  return String(value || '').replace(/<[^>]*>/g, '')
}

function decodeXmlText(value) {
  return String(value || '')
    .replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCodePoint(Number.parseInt(code, 16)))
    .replace(/&#([0-9]+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&amp;/g, '&')
}

function excelColumnIndex(reference) {
  const letters = String(reference || '').toUpperCase().replace(/[^A-Z]/g, '')
  if (!letters) return 0
  return [...letters].reduce((index, letter) => index * 26 + letter.charCodeAt(0) - 64, 0) - 1
}

function parsePositiveInteger(value) {
  const parsed = Number.parseInt(String(value || ''), 10)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
}

function sameStringArray(left, right) {
  return left.length === right.length && left.every((value, index) => value === right[index])
}
