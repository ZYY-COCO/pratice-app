export const DEFAULT_SUBSCRIPTION_PAGE_CONFIG = Object.freeze({
  title: '开通 PLUS',
  brand_name: 'HMTC 升学交流圈',
  benefits: Object.freeze([
    '完整访问港澳台考研题库',
    '获得 AI 专项训练与学习建议',
    '查看学习报告与错题复盘',
    '优先体验后续 PLUS 学习权益'
  ]),
  monthly_price_cents: 8800,
  quarterly_price_cents: 22800,
  plan_hint: '选择适合你的学习计划',
  primary_button_text: '订阅 PLUS',
  secondary_button_text: '恢复购买',
  description_text: '订阅服务开通后，将按所选套餐为你提供 PLUS 学习权益。',
  terms_text: '服务条款 · 隐私政策'
})

function cleanText(value, fallback) {
  const normalized = typeof value === 'string' ? value.trim() : ''
  return normalized || fallback
}

function cleanPrice(value, fallback) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed < 1) return fallback
  return Math.round(parsed)
}

export function createSubscriptionPageConfig(source = {}) {
  const raw = source && typeof source === 'object' ? source : {}
  const benefits = Array.isArray(raw.benefits)
    ? raw.benefits.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 8)
    : []

  return {
    title: cleanText(raw.title, DEFAULT_SUBSCRIPTION_PAGE_CONFIG.title),
    brand_name: cleanText(raw.brand_name, DEFAULT_SUBSCRIPTION_PAGE_CONFIG.brand_name),
    benefits: benefits.length ? benefits : [...DEFAULT_SUBSCRIPTION_PAGE_CONFIG.benefits],
    monthly_price_cents: cleanPrice(raw.monthly_price_cents, DEFAULT_SUBSCRIPTION_PAGE_CONFIG.monthly_price_cents),
    quarterly_price_cents: cleanPrice(raw.quarterly_price_cents, DEFAULT_SUBSCRIPTION_PAGE_CONFIG.quarterly_price_cents),
    plan_hint: cleanText(raw.plan_hint, DEFAULT_SUBSCRIPTION_PAGE_CONFIG.plan_hint),
    primary_button_text: cleanText(raw.primary_button_text, DEFAULT_SUBSCRIPTION_PAGE_CONFIG.primary_button_text),
    secondary_button_text: cleanText(raw.secondary_button_text, DEFAULT_SUBSCRIPTION_PAGE_CONFIG.secondary_button_text),
    description_text: cleanText(raw.description_text, DEFAULT_SUBSCRIPTION_PAGE_CONFIG.description_text),
    terms_text: cleanText(raw.terms_text, DEFAULT_SUBSCRIPTION_PAGE_CONFIG.terms_text),
    updated_at: raw.updated_at || null
  }
}

export function formatSubscriptionPrice(priceCents, suffix) {
  const cents = cleanPrice(priceCents, 0)
  const yuan = cents / 100
  const amount = Number.isInteger(yuan)
    ? String(yuan)
    : yuan.toFixed(2).replace(/\.00$/, '').replace(/(\.\d)0$/, '$1')
  return `¥${amount}${suffix}`
}

export function formatSubscriptionPriceInput(priceCents) {
  const cents = cleanPrice(priceCents, 0)
  const yuan = cents / 100
  return Number.isInteger(yuan)
    ? String(yuan)
    : yuan.toFixed(2).replace(/\.00$/, '').replace(/(\.\d)0$/, '$1')
}

export function parseSubscriptionPriceInput(value, fallbackCents) {
  const normalized = String(value ?? '').trim()
  if (!normalized) return fallbackCents
  const amount = Number(normalized)
  if (!Number.isFinite(amount) || amount <= 0) return fallbackCents
  return Math.round(amount * 100)
}
