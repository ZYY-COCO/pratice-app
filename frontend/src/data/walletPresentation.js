export const WALLET_ROLES = ['user', 'mentor']
export const WALLET_ROLE_STORAGE_KEY = 'gangyantong_wallet_role_v2'

export const walletFilterOptions = {
  user: [
    { value: 'all', label: '全部' },
    { value: 'expense', label: '支出' },
    { value: 'refund', label: '退款' }
  ],
  mentor: [
    { value: 'all', label: '全部' },
    { value: 'income', label: '收入' },
    { value: 'settling', label: '待结算' },
    { value: 'withdraw', label: '提现' },
    { value: 'adjustment', label: '退款调整' }
  ]
}

export const walletStatusLabels = {
  pending: '待处理',
  success: '成功',
  failed: '处理失败',
  settling: '待结算',
  withdrawable: '已结算',
  processing: '处理中',
  completed: '已完成',
  refunded: '已退款'
}

export const walletTypeLabels = {
  consultation_payment: '咨询支付',
  consultation_refund: '退款到账',
  consultation_income_pending: '咨询收入',
  consultation_income_settled: '结算转入',
  consultation_income_reversed: '退款调整',
  withdraw: '提现',
  withdraw_fail: '提现'
}

export function getStoredWalletRole() {
  try {
    const stored = String(uni.getStorageSync(WALLET_ROLE_STORAGE_KEY) || 'user')
    return WALLET_ROLES.includes(stored) ? stored : 'user'
  } catch (error) {
    return 'user'
  }
}

export function setStoredWalletRole(role) {
  const next = WALLET_ROLES.includes(role) ? role : 'user'
  try {
    uni.setStorageSync(WALLET_ROLE_STORAGE_KEY, next)
  } catch (error) {
    // 页面仍可使用当前内存角色。
  }
  return next
}

export function matchesWalletFilter(transaction, filter, role) {
  if (!transaction || !filter || filter === 'all') return true
  if (role === 'user') {
    if (filter === 'expense') return transaction.type === 'consultation_payment'
    if (filter === 'refund') return ['consultation_refund', 'consultation_income_reversed'].includes(transaction.type)
    return true
  }
  if (filter === 'income') return ['consultation_income_pending', 'consultation_income_settled'].includes(transaction.type)
  if (filter === 'settling') return transaction.status === 'settling'
  if (filter === 'withdraw') return ['withdraw', 'withdraw_fail'].includes(transaction.type)
  if (filter === 'adjustment') return transaction.type === 'consultation_income_reversed'
  return true
}

export function formatWalletAmount(amount, withSign = false) {
  const value = Number(amount || 0)
  const absolute = Math.abs(value).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
  if (!withSign) return `¥${absolute}`
  if (value > 0) return `+${absolute}`
  if (value < 0) return `-${absolute}`
  return '0.00'
}
