import { strToU8, zipSync } from 'fflate'

const IMPORT_SHEET_NAME = '题目'
const FEEDBACK_SHEET_NAME = '退回说明'

export const QUESTION_IMPORT_HEADERS = [
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

const FEEDBACK_HEADERS = [
  '题目ID',
  '题干摘要',
  '退回原因',
  '审核老师',
  '审核时间',
  '所属题库',
  '原导入备注'
]

export function downloadReturnedQuestionsWorkbook(questions, meta = {}) {
  const items = Array.isArray(questions) ? questions : []
  if (!items.length) {
    throw new Error('没有可导出的退回题目')
  }

  const filename = buildReturnedQuestionsFilename(meta)
  const workbookBytes = buildReturnedQuestionsWorkbook(items, meta)
  const blob = new Blob([workbookBytes], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  })

  if (typeof document === 'undefined' || typeof URL === 'undefined') {
    throw new Error('当前环境不支持浏览器下载')
  }

  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1500)
}

export function buildReturnedQuestionsWorkbook(questions, meta = {}) {
  const importRows = [
    QUESTION_IMPORT_HEADERS,
    ...questions.map((question) => QUESTION_IMPORT_HEADERS.map((header) => normalizeExportCell(question[header])))
  ]
  const feedbackRows = [
    FEEDBACK_HEADERS,
    ...questions.map((question) => [
      question.question_id || question.id || '',
      summarizeStem(question.stem),
      question.return_reason || question.review_note || '需要修改',
      meta.reviewer || question.reviewer || '题库管理员',
      question.reviewed_at || meta.reviewedAt || formatDateTimeForCell(new Date()),
      meta.bankName || question.question_bank_name || '',
      question.import_note || ''
    ])
  ]

  return zipSync({
    '[Content_Types].xml': xmlBytes(contentTypesXml()),
    '_rels/.rels': xmlBytes(rootRelsXml()),
    'xl/workbook.xml': xmlBytes(workbookXml([IMPORT_SHEET_NAME, FEEDBACK_SHEET_NAME])),
    'xl/_rels/workbook.xml.rels': xmlBytes(workbookRelsXml(2)),
    'xl/styles.xml': xmlBytes(stylesXml()),
    'xl/worksheets/sheet1.xml': xmlBytes(worksheetXml(importRows)),
    'xl/worksheets/sheet2.xml': xmlBytes(worksheetXml(feedbackRows))
  })
}

function buildReturnedQuestionsFilename(meta = {}) {
  const bankName = sanitizeFilename(meta.bankName || '题库')
  const stamp = new Date()
    .toISOString()
    .replace(/[-:]/g, '')
    .replace(/\.\d+Z$/, '')
  return `${bankName}-退回题目-${stamp}.xlsx`
}

function worksheetXml(rows) {
  const rowXml = rows.map((row, rowIndex) => {
    const rowNumber = rowIndex + 1
    const cells = row.map((value, columnIndex) => {
      const cellRef = `${excelColumnName(columnIndex + 1)}${rowNumber}`
      return `<c r="${cellRef}" t="inlineStr"><is><t xml:space="preserve">${escapeXml(value)}</t></is></c>`
    }).join('')
    return `<row r="${rowNumber}">${cells}</row>`
  }).join('')
  const maxColumns = Math.max(...rows.map((row) => row.length), 1)
  const dimension = `A1:${excelColumnName(maxColumns)}${Math.max(rows.length, 1)}`
  return [
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"',
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
    `<dimension ref="${dimension}"/>`,
    '<sheetViews><sheetView workbookViewId="0"/></sheetViews>',
    '<sheetFormatPr defaultRowHeight="18"/>',
    `<sheetData>${rowXml}</sheetData>`,
    '</worksheet>'
  ].join('')
}

function workbookXml(sheetNames) {
  const sheets = sheetNames.map((name, index) => (
    `<sheet name="${escapeXml(name)}" sheetId="${index + 1}" r:id="rId${index + 1}"/>`
  )).join('')
  return [
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"',
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
    `<sheets>${sheets}</sheets>`,
    '</workbook>'
  ].join('')
}

function workbookRelsXml(sheetCount) {
  const sheetRelationships = Array.from({ length: sheetCount }, (_, index) => (
    `<Relationship Id="rId${index + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${index + 1}.xml"/>`
  )).join('')
  return [
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    sheetRelationships,
    `<Relationship Id="rId${sheetCount + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>`,
    '</Relationships>'
  ].join('')
}

function rootRelsXml() {
  return [
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>',
    '</Relationships>'
  ].join('')
}

function contentTypesXml() {
  return [
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
    '<Default Extension="xml" ContentType="application/xml"/>',
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>',
    '<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>',
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
    '</Types>'
  ].join('')
}

function stylesXml() {
  return [
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
    '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>',
    '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>',
    '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>',
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>',
    '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>',
    '</styleSheet>'
  ].join('')
}

function xmlBytes(value) {
  return strToU8(value)
}

function normalizeExportCell(value) {
  if (value === null || value === undefined) return ''
  return String(value)
}

function summarizeStem(value) {
  const text = normalizeExportCell(value).replace(/\s+/g, ' ').trim()
  return text.length > 80 ? `${text.slice(0, 80)}…` : text
}

function formatDateTimeForCell(date) {
  const value = date instanceof Date ? date : new Date(date)
  if (Number.isNaN(value.getTime())) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(value)
}

function sanitizeFilename(value) {
  return normalizeExportCell(value).trim().replace(/[\\/:*?"<>|]/g, '_') || '题库'
}

function excelColumnName(index) {
  let current = Number(index || 1)
  let name = ''
  while (current > 0) {
    const remainder = (current - 1) % 26
    name = String.fromCharCode(65 + remainder) + name
    current = Math.floor((current - 1) / 26)
  }
  return name || 'A'
}

function escapeXml(value) {
  return normalizeExportCell(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}
