export const THEME_STORAGE_KEY = 'gangyantong_theme_key'

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
    pageBg:
      'radial-gradient(circle at top right, rgba(52, 120, 246, 0.1), transparent 25%), linear-gradient(180deg, #fbfcff 0%, #f4f7fb 100%)',
    panelBg:
      'radial-gradient(circle at 86% 10%, rgba(52, 120, 246, 0.14), transparent 30%), linear-gradient(135deg, #ffffff 0%, #eef6ff 100%)'
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
    pageBg:
      'radial-gradient(circle at top right, rgba(217, 95, 147, 0.1), transparent 25%), linear-gradient(180deg, #fffafa 0%, #fff0f5 100%)',
    panelBg:
      'radial-gradient(circle at 86% 10%, rgba(217, 95, 147, 0.14), transparent 30%), linear-gradient(135deg, #ffffff 0%, #fff1f7 100%)'
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
    pageBg:
      'radial-gradient(circle at top right, rgba(47, 163, 107, 0.1), transparent 25%), linear-gradient(180deg, #fbfffd 0%, #effaf4 100%)',
    panelBg:
      'radial-gradient(circle at 86% 10%, rgba(47, 163, 107, 0.14), transparent 30%), linear-gradient(135deg, #ffffff 0%, #effaf4 100%)'
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
    pageBg:
      'radial-gradient(circle at top right, rgba(118, 104, 223, 0.1), transparent 25%), linear-gradient(180deg, #fbfbff 0%, #f3f1ff 100%)',
    panelBg:
      'radial-gradient(circle at 86% 10%, rgba(118, 104, 223, 0.14), transparent 30%), linear-gradient(135deg, #ffffff 0%, #f2f0ff 100%)'
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

  if (typeof document === 'undefined') {
    return preset
  }

  const root = document.documentElement
  root.style.setProperty('--gyt-primary', preset.primary)
  root.style.setProperty('--gyt-primary-soft', preset.primarySoft)
  root.style.setProperty('--gyt-primary-tint', preset.primaryTint)
  root.style.setProperty('--gyt-primary-border', preset.primaryBorder)
  root.style.setProperty('--gyt-primary-gradient', preset.primaryGradient)
  root.style.setProperty('--gyt-primary-shadow', preset.primaryShadow)
  root.style.setProperty('--gyt-page-bg', preset.pageBg)
  root.style.setProperty('--gyt-panel-bg', preset.panelBg)
  return preset
}
