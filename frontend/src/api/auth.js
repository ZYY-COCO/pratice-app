import { request } from './http'

function buildNoAuthRequest(url, payload, timeout = 12000) {
  return request({
    url,
    method: 'POST',
    timeout,
    authRedirect: false,
    header: {
      Authorization: ''
    },
    data: payload
  })
}

export function checkBackendHealth() {
  return request({
    url: '/health',
    method: 'GET',
    authRedirect: false,
    header: {
      Authorization: ''
    },
    timeout: 3000
  })
}

export function loginWithEmail(payload) {
  return buildNoAuthRequest('/auth/login', payload, 25000)
}

export function sendRegisterCode(payload) {
  return buildNoAuthRequest('/auth/send-register-code', payload, 25000)
}

export function registerWithEmail(payload) {
  return buildNoAuthRequest('/auth/register', payload, 25000)
}

export function sendResetCode(payload) {
  return buildNoAuthRequest('/auth/send-reset-code', payload, 25000)
}

export function resetPasswordWithCode(payload) {
  return buildNoAuthRequest('/auth/reset-password', payload, 25000)
}

export function sendChangeEmailCode(payload) {
  return request({
    url: '/auth/send-change-email-code',
    method: 'POST',
    timeout: 25000,
    data: payload
  })
}

export function changeEmailWithCode(payload) {
  return request({
    url: '/auth/change-email',
    method: 'POST',
    timeout: 25000,
    data: payload
  })
}

export function updateProfile(payload) {
  return request({
    url: '/auth/profile',
    method: 'PATCH',
    data: payload
  })
}
