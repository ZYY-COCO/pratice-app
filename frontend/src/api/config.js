const DEFAULT_API_BASE_URL = 'https://pratice-app.onrender.com'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL

export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '')
