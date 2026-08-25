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
  },
  {
    key: 'sakura',
    name: '樱花粉',
    desc: '柔和浅粉，页面更温暖。',
    primary: '#d95f93',
    primarySoft: '#fff0f6',
    primaryTint: '#fff7fa',
    primaryBorder: '#ffd6e8',
    primaryGradient: 'linear-gradient(135deg, #e65f9a, #ff9ac2)',
    primaryShadow: 'rgba(217, 95, 147, 0.18)',
    pageBg: UNIFIED_PAGE_BACKGROUND,
    panelBg: UNIFIED_PANEL_BACKGROUND
  },
  {
    key: 'mint',
    name: '薄荷绿',
    desc: '清淡绿色，视觉更放松。',
    primary: '#2fa36b',
    primarySoft: '#ecfdf5',
    primaryTint: '#f4fff9',
    primaryBorder: '#ccefdc',
    primaryGradient: 'linear-gradient(135deg, #2fa36b, #72d69c)',
    primaryShadow: 'rgba(47, 163, 107, 0.18)',
    pageBg: UNIFIED_PAGE_BACKGROUND,
    panelBg: UNIFIED_PANEL_BACKGROUND
  },
  {
    key: 'lavender',
    name: '浅紫蓝',
    desc: '轻盈紫蓝，适合低亮度环境。',
    primary: '#7668df',
    primarySoft: '#f1efff',
    primaryTint: '#f8f7ff',
    primaryBorder: '#ddd8ff',
    primaryGradient: 'linear-gradient(135deg, #7668df, #9f96ff)',
    primaryShadow: 'rgba(118, 104, 223, 0.18)',
    pageBg: UNIFIED_PAGE_BACKGROUND,
    panelBg: UNIFIED_PANEL_BACKGROUND
  },
  {
    key: 'circle-glass',
    name: '方案一（研圈玻璃）',
    desc: '研圈背景与磨砂卡片，适合全局预览。',
    primary: '#16786f',
    primarySoft: 'rgba(225, 242, 237, 0.62)',
    primaryTint: 'rgba(241, 249, 246, 0.74)',
    primaryBorder: 'rgba(255, 255, 255, 0.68)',
    primaryGradient: 'linear-gradient(135deg, #16786f, #57a99b)',
    primaryShadow: 'rgba(30, 55, 56, 0.16)',
    pageBg: UNIFIED_PAGE_BACKGROUND,
    panelBg: UNIFIED_PANEL_BACKGROUND,
    circleGlass: true,
    iconThemeKey: 'blue'
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
