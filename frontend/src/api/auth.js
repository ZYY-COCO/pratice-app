import { request, uploadFileRequest } from './http'

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

export function sendPhoneCode(payload) {
  return buildNoAuthRequest('/auth/send-phone-code', payload, 25000)
}

export function registerWithPhone(payload) {
  return buildNoAuthRequest('/auth/phone-register', payload, 25000)
}

export function loginWithPhone(payload) {
  return buildNoAuthRequest('/auth/phone-login', payload, 25000)
}

export function loginWithWechat(payload = {}) {
  return buildNoAuthRequest('/auth/wechat-login', payload, 25000)
}

export function fetchWechatAuthUrl(payload = {}) {
  return request({
    url: '/auth/wechat-auth-url',
    method: 'GET',
    timeout: 12000,
    authRedirect: false,
    header: {
      Authorization: ''
    },
    data: payload
  })
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

export function sendBindEmailCode(payload) {
  return request({
    url: '/auth/send-bind-email-code',
    method: 'POST',
    timeout: 25000,
    data: payload
  })
}

export function bindWechatEmail(payload) {
  return request({
    url: '/auth/bind-wechat-email',
    method: 'POST',
    timeout: 30000,
    data: payload
  })
}

export function sendUnbindWechatCode() {
  return request({
    url: '/auth/send-unbind-wechat-code',
    method: 'POST',
    timeout: 25000,
    data: {}
  })
}

export function unbindWechat(payload) {
  return request({
    url: '/auth/unbind-wechat',
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

export function uploadAvatar({ filePath, file, fileName }) {
  return uploadFileRequest({
    url: '/auth/avatar',
    filePath,
    file,
    fileName,
    name: 'file',
    timeout: 60000
  })
}

export function deleteAccount() {
  return request({
    url: '/auth/account',
    method: 'DELETE',
    timeout: 25000
  })
}
