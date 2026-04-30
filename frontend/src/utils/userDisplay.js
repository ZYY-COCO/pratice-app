const PHONE_SHADOW_EMAIL_DOMAIN = '@phone.gangyantong.local'

export function isPhoneShadowEmail(email) {
  return typeof email === 'string' && email.endsWith(PHONE_SHADOW_EMAIL_DOMAIN)
}

export function getPublicEmail(user) {
  const email = user?.email || ''
  return isPhoneShadowEmail(email) ? '' : email
}

export function maskPhone(phone) {
  const value = String(phone || '').trim()
  if (!value) return ''
  const prefixLength = value.startsWith('+') ? 4 : 3
  if (value.length <= prefixLength + 4) return value
  return `${value.slice(0, prefixLength)}****${value.slice(-4)}`
}

export function getUserDisplayName(user, fallback = '用户') {
  const nickname = user?.nickname
  if (typeof nickname === 'string' && nickname.trim()) {
    return nickname.trim()
  }
  const phone = maskPhone(user?.phone)
  if (phone) return phone
  const email = getPublicEmail(user)
  if (email) return email.split('@')[0] || fallback
  return fallback
}

export function getUserContactLabel(user, fallback = '未绑定账号') {
  const phone = maskPhone(user?.phone)
  if (phone) return phone
  return getPublicEmail(user) || fallback
}
