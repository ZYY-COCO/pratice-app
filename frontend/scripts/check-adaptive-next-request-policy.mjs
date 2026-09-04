import assert from 'node:assert/strict'
import fs from 'node:fs'

const httpPath = new URL('../src/api/http.js', import.meta.url)
const adaptivePath = new URL('../src/api/adaptivePractice.js', import.meta.url)

globalThis.__adaptiveHttpAuthMocks = {
  clearAuthSession() {},
  getAccessToken() { return '' },
  getAuthUser() { return null },
  getRefreshToken() { return '' },
  isAccessTokenExpiring() { return false },
  isUsableRefreshToken() { return false },
  saveAuthSession() {}
}

let requestCalls = []
let pendingResponses = []
globalThis.uni = {
  request(options) {
    requestCalls.push(options)
    const respond = pendingResponses.shift()
    if (!respond) throw new Error(`unexpected request: ${options.url}`)
    queueMicrotask(() => respond(options))
    return {}
  },
  showToast() {},
  reLaunch() {}
}
globalThis.getCurrentPages = () => []

let httpSource = fs.readFileSync(httpPath, 'utf8')
httpSource = httpSource
  .replace(
    /import \{ API_BASE_URL \} from '\.\/config'\r?\n/,
    "const API_BASE_URL = 'https://api.test'\n"
  )
  .replace(
    /import \{\r?\n[\s\S]*?\r?\n\} from '\.\.\/utils\/auth'\r?\n/,
    `const {
  clearAuthSession,
  getAccessToken,
  getAuthUser,
  getRefreshToken,
  isAccessTokenExpiring,
  isUsableRefreshToken,
  saveAuthSession
} = globalThis.__adaptiveHttpAuthMocks
`
  )

const httpModule = await import(
  `data:text/javascript;base64,${Buffer.from(httpSource).toString('base64')}`
)
globalThis.__adaptiveNextRequestMocks = { request: httpModule.request }

const adaptiveSource = fs.readFileSync(adaptivePath, 'utf8').replace(
  "import { request } from './http'",
  'const { request } = globalThis.__adaptiveNextRequestMocks'
)
const adaptiveModule = await import(
  `data:text/javascript;base64,${Buffer.from(adaptiveSource).toString('base64')}`
)

const nativeSetTimeout = globalThis.setTimeout
globalThis.setTimeout = (callback) => {
  queueMicrotask(callback)
  return 1
}

function resetRequests(...responses) {
  requestCalls = []
  pendingResponses = responses
}

try {
  resetRequests(({ fail }) => fail({ errMsg: 'request:fail timeout' }))
  await assert.rejects(
    adaptiveModule.fetchNextAdaptivePracticeItem('session/timeout'),
    (error) => error?.code === 'NETWORK_TIMEOUT'
  )
  assert.equal(requestCalls.length, 1, '/next timeout must not trigger a hidden GET retry')
  assert.equal(requestCalls[0].timeout, 8000)

  resetRequests(({ success }) => success({
    statusCode: 503,
    data: { detail: { code: 'ADAPTIVE_SAFE_POOL_UNAVAILABLE' } }
  }))
  await assert.rejects(
    adaptiveModule.fetchNextAdaptivePracticeItem('session-503'),
    (error) => error?.statusCode === 503
  )
  assert.equal(requestCalls.length, 1, '/next 503 must reach the page after one request')

  resetRequests(
    ({ success }) => success({ statusCode: 503, data: { detail: 'busy' } }),
    ({ success }) => success({ statusCode: 200, data: { ok: true } })
  )
  const ordinaryResult = await httpModule.request({ url: '/ordinary-read', timeout: 8000 })
  assert.deepEqual(ordinaryResult, { ok: true })
  assert.equal(requestCalls.length, 2, 'ordinary retryable GET requests must keep one automatic retry')

  console.log('adaptive next request policy: ok')
} finally {
  globalThis.setTimeout = nativeSetTimeout
  delete globalThis.__adaptiveHttpAuthMocks
  delete globalThis.__adaptiveNextRequestMocks
  delete globalThis.uni
  delete globalThis.getCurrentPages
}
