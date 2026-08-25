import { request } from './http'
import { getAuthUser } from '../utils/auth'

const WALLET_CACHE_PREFIX = 'gangyantong_wallet_ledger_cache_v1'

export function fetchWalletSummary({ role = 'user', mode, limit = 100 } = {}) {
  return request({
    url: '/wallet',
    method: 'GET',
    data: {
      role: role === 'mentor' ? 'mentor' : 'user',
      ...(mode ? { mode } : {}),
      limit
    }
  }).then((payload) => {
    const summary = normalizeWalletSummary(payload)
    writeWalletCache(summary)
    return summary
  })
}

export function fetchWalletTransaction(transactionId, { role = 'user', mode } = {}) {
  return request({
    url: `/wallet/transactions/${encodeURIComponent(transactionId)}`,
    method: 'GET',
    data: {
      role: role === 'mentor' ? 'mentor' : 'user',
      ...(mode ? { mode } : {})
    }
  }).then((item) => normalizeWalletTransaction(item, mode || 'real'))
}

export function getCachedWalletTransactionById(id, role = 'user') {
  const normalizedId = String(id || '')
  if (!normalizedId) return null
  try {
    const cache = uni.getStorageSync(getWalletCacheKey(role))
    const items = Array.isArray(cache?.transactions) ? cache.transactions : []
    return items.find((item) => String(item?.id || '') === normalizedId) || null
  } catch (error) {
    return null
  }
}

function writeWalletCache(summary) {
  try {
    uni.setStorageSync(getWalletCacheKey(summary.role), summary)
  } catch (error) {
    // 缓存失败不影响当前页面使用服务端账本。
  }
}

function getWalletCacheKey(role = 'user') {
  const user = getAuthUser() || {}
  const userId = String(user.id || user.user_id || user.userId || '').trim()
  return `${WALLET_CACHE_PREFIX}:${userId || 'guest'}:${role === 'mentor' ? 'mentor' : 'user'}`
}

function normalizeWalletSummary(payload = {}) {
  return {
    role: payload.role === 'mentor' ? 'mentor' : 'user',
    fundMode: String(payload.fund_mode || 'real'),
    balance: Number(payload.balance || 0),
    withdrawableBalance: Number(payload.withdrawable_balance || 0),
    pendingSettlement: Number(payload.pending_settlement || 0),
    monthlyExpense: Number(payload.monthly_expense || 0),
    monthlyRefund: Number(payload.monthly_refund || 0),
    monthlyIncome: Number(payload.monthly_income || 0),
    totalIncome: Number(payload.total_income || 0),
    totalPaid: Number(payload.total_paid || 0),
    withdrawalEnabled: Boolean(payload.withdrawal_enabled),
    paymentEnabled: Boolean(payload.payment_enabled),
    message: String(payload.message || ''),
    transactions: Array.isArray(payload.transactions)
      ? payload.transactions.map((item) => normalizeWalletTransaction(item, payload.fund_mode || 'real'))
      : []
  }
}

function normalizeWalletTransaction(item = {}, fundMode = 'real') {
  return {
    ...item,
    fundMode: String(item.fund_mode || fundMode || 'real'),
    id: String(item.id || ''),
    transactionId: String(item.transaction_no || item.transactionId || ''),
    monthKey: String(item.month_key || item.monthKey || ''),
    createdAt: String(item.created_at || item.createdAt || ''),
    completedAt: String(item.completed_at || item.completedAt || ''),
    orderId: String(item.order_id || item.orderId || ''),
    settlementStatus: String(item.settlement_status || item.settlementStatus || ''),
    availableAt: String(item.available_at || item.availableAt || ''),
    paymentMethod: String(item.payment_method || item.paymentMethod || ''),
    iconLabel: String(item.icon_label || item.iconLabel || '账'),
    iconTone: String(item.icon_tone || item.iconTone || 'blue'),
    amount: Number(item.amount || 0)
  }
}
