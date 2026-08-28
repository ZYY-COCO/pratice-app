import { applyRootCssVariables } from '../platform/runtime'

export const THEME_STORAGE_KEY = 'gangyantong_theme_key'
export const UNIFIED_PAGE_BACKGROUND = '#f5f3f7'
export const UNIFIED_PANEL_BACKGROUND = 'rgba(255,255,255,.94)'

export const THEME_PRESETS = [
  {
    key: 'blue',
    name: '清爽蓝',
    desc: '默认浅蓝，适合长时间刷题。',
    primary: '#3478f6',
    primarySoft: '#edf4ff',
    primaryTint: '#f4f8ff',
    primaryBorder: '#d7e5ff',
    primaryGradient: 'linear-gradient(135deg, #3478f6, #68a0ff)',
    primaryShadow: 'rgba(52, 120, 246, 0.2)',
    pageBg: UNIFIED_PAGE_BACKGROUND,
    panelBg: UNIFIED_PANEL_BACKGROUND
  }
]

export function getThemePreset(key) {
  return THEME_PRESETS.find((item) => item.key === key) || THEME_PRESETS[0]
}

export function getStoredThemeKey() {
  try {
    const stored = uni.getStorageSync(THEME_STORAGE_KEY)
    return getThemePreset(stored).key
  } catch (error) {
    return THEME_PRESETS[0].key
  }
}

export function buildThemeStyle(key) {
  const preset = getThemePreset(key)
  return [
    `--gyt-primary:${preset.primary}`,
    `--gyt-primary-soft:${preset.primarySoft}`,
    `--gyt-primary-tint:${preset.primaryTint}`,
    `--gyt-primary-border:${preset.primaryBorder}`,
    `--gyt-primary-gradient:${preset.primaryGradient}`,
    `--gyt-primary-shadow:${preset.primaryShadow}`,
    `--gyt-page-bg:${preset.pageBg}`,
    `--gyt-panel-bg:${preset.panelBg}`
  ].join(';')
}

export function applyThemeByKey(key) {
  const preset = getThemePreset(key)
  try {
    uni.setStorageSync(THEME_STORAGE_KEY, preset.key)
  } catch (error) {
    // Storage can fail in private browsing; theme still applies for this session on H5.
  }

  applyRootCssVariables({
    '--gyt-primary': preset.primary,
    '--gyt-primary-soft': preset.primarySoft,
    '--gyt-primary-tint': preset.primaryTint,
    '--gyt-primary-border': preset.primaryBorder,
    '--gyt-primary-gradient': preset.primaryGradient,
    '--gyt-primary-shadow': preset.primaryShadow,
    '--gyt-page-bg': preset.pageBg,
    '--gyt-panel-bg': preset.panelBg
  })

  if (typeof document !== 'undefined') {
    document.documentElement.classList.toggle('gyt-circle-glass-theme', preset.circleGlass === true)
  }
  return preset
}
