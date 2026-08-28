const PUBLIC_API_BASE_URL = 'https://www.gangyantong.com/api'
const appDevelopmentApiBaseUrl = String(import.meta.env.VITE_APP_DEV_API_BASE_URL || '').trim()
const hasAbsoluteAppDevelopmentApiBaseUrl = /^https?:\/\//i.test(appDevelopmentApiBaseUrl)

let DEFAULT_API_BASE_URL = '/api'

// #ifdef MP-WEIXIN
DEFAULT_API_BASE_URL = PUBLIC_API_BASE_URL
// #endif

// #ifdef APP-PLUS
// HBuilderX 真机运行读取显式配置的局域网后端；正式构建始终回到公网 HTTPS。
DEFAULT_API_BASE_URL = import.meta.env.DEV && hasAbsoluteAppDevelopmentApiBaseUrl
  ? appDevelopmentApiBaseUrl
  : PUBLIC_API_BASE_URL
// #endif

let configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL

let isH5Development = false
// #ifdef H5
isH5Development = Boolean(import.meta.env.DEV)
// #endif

const isLoopbackApiUrl = /^https?:\/\/(?:127\.0\.0\.1|localhost)(?::\d+)?(?:\/|$)/i.test(configuredBaseUrl)

// H5 development always goes through Vite's /api proxy.  This lets the LAN
// preview and localhost use the same local consultation flow without URL flags.
if (isH5Development && isLoopbackApiUrl) {
  configuredBaseUrl = '/api'
}

// #ifdef MP-WEIXIN
configuredBaseUrl = DEFAULT_API_BASE_URL
// #endif

// #ifdef APP-PLUS
configuredBaseUrl = DEFAULT_API_BASE_URL
// #endif

export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '')
