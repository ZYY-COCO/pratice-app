let DEFAULT_API_BASE_URL = '/api'

// #ifdef MP-WEIXIN
DEFAULT_API_BASE_URL = 'https://www.gangyantong.com/api'
// #endif

// #ifdef APP-PLUS
DEFAULT_API_BASE_URL = 'https://www.gangyantong.com/api'
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
