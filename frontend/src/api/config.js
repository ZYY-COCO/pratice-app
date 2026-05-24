let DEFAULT_API_BASE_URL = '/api'

// #ifdef MP-WEIXIN
DEFAULT_API_BASE_URL = 'https://www.gangyantong.com/api'
// #endif

let configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL

// #ifdef MP-WEIXIN
configuredBaseUrl = DEFAULT_API_BASE_URL
// #endif

export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '')
