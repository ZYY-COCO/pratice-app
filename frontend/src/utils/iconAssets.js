const ICON_SOURCE_ROOT = '/static/ui-icons/'
const ICON_RUNTIME_ROOT = '/static/ui-icons/png'

const SUBJECT_ICON_SOURCES = {
  中华文化: `${ICON_RUNTIME_ROOT}/original/subject-culture-logo.png`,
  英语运用: `${ICON_RUNTIME_ROOT}/original/subject-english-logo.png`,
  逻辑推理: `${ICON_RUNTIME_ROOT}/original/subject-logic-logo.png`,
  数学基础: `${ICON_RUNTIME_ROOT}/original/subject-math-logo.png`
}

const THEME_ICON_KEYS = new Set(['blue'])
const TONE_ICON_KEYS = new Set([
  'neutral',
  'dark',
  'white',
  'gold',
  'danger',
  'success',
  'orange',
  'violet',
  'circle-community',
  'circle-scores',
  'circle-materials',
  'circle-courses'
])

function iconFilename(source) {
  const value = String(source || '').trim()
  const filename = value.split('/').pop()?.split('?')[0] || ''
  return filename.replace(/\.svg$/i, '.png')
}

export function getOriginalIconSrc(source) {
  const filename = iconFilename(source)
  return filename ? `${ICON_RUNTIME_ROOT}/original/${filename}` : ''
}

export function normalizeThemeIconKey(themeKey) {
  const key = String(themeKey || '').trim()
  return THEME_ICON_KEYS.has(key) ? key : 'blue'
}

export function getThemeIconSrc(source, themeKey = 'blue') {
  const filename = iconFilename(source)
  return filename
    ? `${ICON_RUNTIME_ROOT}/${normalizeThemeIconKey(themeKey)}/${filename}`
    : ''
}

export function getToneIconSrc(source, tone = 'dark') {
  const filename = iconFilename(source)
  const normalizedTone = TONE_ICON_KEYS.has(tone) ? tone : 'dark'
  return filename ? `${ICON_RUNTIME_ROOT}/${normalizedTone}/${filename}` : ''
}

export function getSubjectIconSrc(subject, themeKey = 'blue') {
  const normalizedSubject = String(subject || '').trim()
  const source = SUBJECT_ICON_SOURCES[normalizedSubject]
  if (!source) return getThemeIconSrc(`${ICON_RUNTIME_ROOT}/original/report.png`, themeKey)
  return getThemeIconSrc(source, themeKey)
}

export function isVectorIconSource(source) {
  return String(source || '').startsWith(ICON_SOURCE_ROOT) && /\.svg(?:\?|$)/i.test(String(source || ''))
}
