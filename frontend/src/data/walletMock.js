import { getAuthUser } from '../utils/auth'

export const WALLET_ROLES = ['user', 'mentor']
export const WALLET_TRANSACTION_TYPES = [
  'consult_pay',
  'refund',
  'recharge',
  'consult_income',
  'settlement_transfer',
  'withdraw',
  'withdraw_fail',
  'adjustment'
]
export const WALLET_TRANSACTION_STATUSES = [
  'pending',
  'success',
  'failed',
  'settling',
  'withdrawable',
  'processing',
  'completed',
  'refunded'
]

export const WALLET_ROLE_STORAGE_KEY = 'gangyantong_wallet_mock_role_v1'
const WALLET_WITHDRAWAL_STORAGE_KEY = 'gangyantong_wallet_mock_withdrawals_v1'

export const userWalletMock = {
  role: 'user',
  balance: 268.5,
  withdrawableBalance: 0,
  pendingSettlement: 0,
  monthlyExpense: 96,
  monthlyRefund: 12,
  monthlyIncome: 0,
  totalIncome: 0,
  totalPaid: 368,
  transactions: [
    {
      id: 'tx_user_001',
      type: 'consult_pay',
      title: '钟*宏 · 咨询支付',
      description: '暨南大学应用经济学咨询',
      amount: -39,
      status: 'completed',
      monthKey: '2026-08',
      createdAt: '2026-08-19 15:09',
      completedAt: '2026-08-19 15:09',
      paymentMethod: '钱包余额',
      counterparty: '港研通咨询服务',
      mentor: '钟*宏',
      orderId: 'CO202608190001',
      transactionId: 'TX202608190001',
      note: '60 分钟院校与备考规划咨询',
      iconLabel: '咨',
      iconTone: 'blue'
    },
    {
      id: 'tx_user_002',
      type: 'refund',
      title: '咨询订单退款',
      description: '前辈未能按时接单，费用已退回',
      amount: 39,
      status: 'refunded',
      monthKey: '2026-08',
      createdAt: '2026-08-18 11:20',
      completedAt: '2026-08-18 11:21',
      paymentMethod: '退回钱包余额',
      counterparty: '港研通咨询服务',
      mentor: '王*曦',
      orderId: 'CO202608180006',
      transactionId: 'TX202608180006',
      note: '咨询订单自动退款',
      iconLabel: '退',
      iconTone: 'mint'
    },
    {
      id: 'tx_user_003',
      type: 'recharge',
      title: '钱包充值',
      description: '演示充值记录',
      amount: 100,
      status: 'success',
      monthKey: '2026-08',
      createdAt: '2026-08-16 19:00',
      completedAt: '2026-08-16 19:00',
      paymentMethod: '微信支付（演示）',
      counterparty: '港研通钱包',
      mentor: '',
      orderId: 'RC202608160002',
      transactionId: 'TX202608160002',
      note: '第一版仅用于展示充值信息层级',
      iconLabel: '充',
      iconTone: 'cyan'
    },
    {
      id: 'tx_user_004',
      type: 'consult_pay',
      title: '林* · 咨询支付',
      description: 'Z002 复习规划咨询',
      amount: -57,
      status: 'completed',
      monthKey: '2026-08',
      createdAt: '2026-08-08 20:15',
      completedAt: '2026-08-08 20:15',
      paymentMethod: '钱包余额',
      counterparty: '港研通咨询服务',
      mentor: '林*',
      orderId: 'CO202608080003',
      transactionId: 'TX202608080003',
      note: '60 分钟在线咨询',
      iconLabel: '咨',
      iconTone: 'blue'
    },
    {
      id: 'tx_user_005',
      type: 'consult_pay',
      title: '陈*程 · 咨询支付',
      description: '复试经验咨询',
      amount: -100,
      status: 'completed',
      monthKey: '2026-07',
      createdAt: '2026-07-27 10:40',
      completedAt: '2026-07-27 10:40',
      paymentMethod: '钱包余额',
      counterparty: '港研通咨询服务',
      mentor: '陈*程',
      orderId: 'CO202607270004',
      transactionId: 'TX202607270004',
      note: '复试案例表达与准备建议',
      iconLabel: '咨',
      iconTone: 'blue'
    }
  ]
}

export const mentorWalletMock = {
  role: 'mentor',
  balance: 0,
  withdrawableBalance: 1286,
  pendingSettlement: 328,
  monthlyExpense: 0,
  monthlyRefund: 0,
  monthlyIncome: 2460,
  totalIncome: 5880,
  totalPaid: 0,
  transactions: [
    {
      id: 'tx_mentor_001',
      type: 'consult_income',
      title: '张同学 · 院校选择咨询',
      description: '咨询收入已进入 3 天结算期',
      amount: 39,
      status: 'settling',
      monthKey: '2026-08',
      createdAt: '2026-08-19 15:09',
      completedAt: '2026-08-19 16:09',
      sourceUser: '张同学',
      orderId: 'CO202608190018',
      transactionId: 'TX202608190018',
      settlementStatus: '待结算',
      availableAt: '2026-08-22 15:09',
      note: '咨询完成后自动进入待结算',
      iconLabel: '入',
      iconTone: 'mint'
    },
    {
      id: 'tx_mentor_002',
      type: 'settlement_transfer',
      title: '待结算转入余额',
      description: '王同学 · Z001 备考咨询',
      amount: 49,
      status: 'withdrawable',
      monthKey: '2026-08',
      createdAt: '2026-08-15 09:30',
      completedAt: '2026-08-18 09:30',
      sourceUser: '王同学',
      orderId: 'CO202608150011',
      transactionId: 'TX202608180011',
      settlementStatus: '已结算，可提现',
      availableAt: '2026-08-18 09:30',
      note: '满 3 天后自动转入可提现余额',
      iconLabel: '结',
      iconTone: 'cyan'
    },
    {
      id: 'tx_mentor_003',
      type: 'withdraw',
      title: '提现到微信',
      description: '尾号 0826 的微信账户',
      amount: -200,
      status: 'success',
      monthKey: '2026-08',
      createdAt: '2026-08-12 10:30',
      completedAt: '2026-08-13 16:20',
      sourceUser: '',
      orderId: '',
      transactionId: 'WD202608120001',
      settlementStatus: '提现成功',
      availableAt: '',
      withdrawalMethod: '微信',
      note: '演示提现记录，未发生真实打款',
      iconLabel: '提',
      iconTone: 'blue'
    },
    {
      id: 'tx_mentor_004',
      type: 'adjustment',
      title: '咨询退款扣回',
      description: '李同学 · 复试经验咨询',
      amount: -39,
      status: 'refunded',
      monthKey: '2026-08',
      createdAt: '2026-08-10 16:00',
      completedAt: '2026-08-10 16:00',
      sourceUser: '李同学',
      orderId: 'CO202608090007',
      transactionId: 'TX202608100007',
      settlementStatus: '已扣回',
      availableAt: '',
      note: '关联咨询退款后进行收入调整',
      iconLabel: '调',
      iconTone: 'warm'
    },
    {
      id: 'tx_mentor_005',
      type: 'consult_income',
      title: '陈同学 · 学习规划咨询',
      description: '咨询收入已结算',
      amount: 300,
      status: 'completed',
      monthKey: '2026-08',
      createdAt: '2026-08-03 13:20',
      completedAt: '2026-08-06 13:20',
      sourceUser: '陈同学',
      orderId: 'CO202608030003',
      transactionId: 'TX202608030003',
      settlementStatus: '已结算，可提现',
      availableAt: '2026-08-06 13:20',
      note: '咨询收入结算完成',
      iconLabel: '入',
      iconTone: 'mint'
    },
    {
      id: 'tx_mentor_006',
      type: 'withdraw_fail',
      title: '提现到支付宝',
      description: '账户信息待完善',
      amount: -100,
      status: 'failed',
      monthKey: '2026-07',
      createdAt: '2026-07-28 09:20',
      completedAt: '2026-07-28 09:35',
      sourceUser: '',
      orderId: '',
      transactionId: 'WD202607280002',
      settlementStatus: '提现失败，金额已退回余额',
      availableAt: '',
      withdrawalMethod: '支付宝',
      note: '请完善到账账户后重新提交',
      iconLabel: '提',
      iconTone: 'warm'
    },
    {
      id: 'tx_mentor_007',
      type: 'consult_income',
      title: '林同学 · Z002 备考咨询',
      description: '咨询收入已结算',
      amount: 610,
      status: 'completed',
      monthKey: '2026-07',
      createdAt: '2026-07-18 18:20',
      completedAt: '2026-07-21 18:20',
      sourceUser: '林同学',
      orderId: 'CO202607180009',
      transactionId: 'TX202607180009',
      settlementStatus: '已结算，可提现',
      availableAt: '2026-07-21 18:20',
      note: '咨询收入结算完成',
      iconLabel: '入',
      iconTone: 'mint'
    }
  ]
}

export const walletFilterOptions = {
  user: [
    { value: 'all', label: '全部' },
    { value: 'expense', label: '支出' },
    { value: 'refund', label: '退款' },
    { value: 'recharge', label: '充值' }
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
  failed: '提现失败',
  settling: '待结算',
  withdrawable: '已结算',
  processing: '处理中',
  completed: '已完成',
  refunded: '已退款'
}

export const walletTypeLabels = {
  consult_pay: '咨询支付',
  refund: '退款到账',
  recharge: '钱包充值',
  consult_income: '咨询收入',
  settlement_transfer: '结算转入',
  withdraw: '提现',
  withdraw_fail: '提现',
  adjustment: '退款调整'
}

export function getStoredWalletRole() {
  const stored = String(readStorage(WALLET_ROLE_STORAGE_KEY, 'user') || 'user')
  return WALLET_ROLES.includes(stored) ? stored : 'user'
}

export function setStoredWalletRole(role) {
  const next = WALLET_ROLES.includes(role) ? role : 'user'
  writeStorage(WALLET_ROLE_STORAGE_KEY, next)
  return next
}

export function getWalletMockByRole(role = getStoredWalletRole()) {
  const normalizedRole = WALLET_ROLES.includes(role) ? role : 'user'
  const source = normalizedRole === 'mentor' ? mentorWalletMock : userWalletMock
  const wallet = clone(source)
  const addedWithdrawals = getStoredWithdrawalRecords(normalizedRole)

  if (addedWithdrawals.length) {
    const deducted = addedWithdrawals.reduce((sum, item) => sum + Math.abs(Number(item.amount || 0)), 0)
    wallet.transactions = [...addedWithdrawals, ...wallet.transactions]
    if (normalizedRole === 'mentor') {
      wallet.withdrawableBalance = Math.max(0, wallet.withdrawableBalance - deducted)
    } else {
      wallet.balance = Math.max(0, wallet.balance - deducted)
    }
  }

  return wallet
}

export function getWalletTransactionById(id, role) {
  const normalizedId = String(id || '')
  if (!normalizedId) return null
  const roleOrder = role && WALLET_ROLES.includes(role) ? [role] : WALLET_ROLES
  for (const walletRole of roleOrder) {
    const transaction = getWalletMockByRole(walletRole).transactions.find((item) => item.id === normalizedId)
    if (transaction) return { ...clone(transaction), role: walletRole }
  }
  return null
}

export function getWithdrawalRecords(role = getStoredWalletRole()) {
  const normalizedRole = WALLET_ROLES.includes(role) ? role : 'user'
  return getWalletMockByRole(normalizedRole).transactions.filter((item) => (
    item.type === 'withdraw' || item.type === 'withdraw_fail'
  ))
}

export function submitMockWithdrawal({ amount, channel, role = 'user' }) {
  const numericAmount = Number(amount)
  const safeChannel = channel === 'alipay' ? '支付宝' : '微信'
  const normalizedRole = WALLET_ROLES.includes(role) ? role : 'user'
  const now = new Date()
  const record = {
    id: `tx_withdraw_demo_${now.getTime()}`,
    role: normalizedRole,
    type: 'withdraw',
    title: `提现到${safeChannel}`,
    description: '提现申请已提交，等待审核',
    amount: -numericAmount,
    status: 'processing',
    monthKey: formatMonthKey(now),
    createdAt: formatDateTime(now),
    completedAt: '',
    sourceUser: '',
    orderId: '',
    paymentMethod: `提现至${safeChannel}（演示）`,
    counterparty: `${safeChannel}账户（演示）`,
    mentor: '',
    transactionId: `WD${formatCompactDate(now)}${String(now.getTime()).slice(-6)}`,
    settlementStatus: '处理中',
    availableAt: '',
    withdrawalMethod: safeChannel,
    note: '第一版仅保存本地演示状态，不发起真实打款',
    iconLabel: '提',
    iconTone: 'blue'
  }
  const records = getStoredWithdrawalRecords()
  writeStorage(getWithdrawalStorageKey(), [record, ...records])
  return clone(record)
}

export function matchesWalletFilter(transaction, filter, role) {
  if (!transaction || !filter || filter === 'all') return true
  if (role === 'user') {
    if (filter === 'expense') return transaction.type === 'consult_pay'
    if (filter === 'refund') return transaction.type === 'refund'
    if (filter === 'recharge') return transaction.type === 'recharge'
    return true
  }
  if (filter === 'income') return ['consult_income', 'settlement_transfer'].includes(transaction.type)
  if (filter === 'settling') return transaction.status === 'settling'
  if (filter === 'withdraw') return ['withdraw', 'withdraw_fail'].includes(transaction.type)
  if (filter === 'adjustment') return transaction.type === 'adjustment'
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

function getStoredWithdrawalRecords(role) {
  const records = readStorage(getWithdrawalStorageKey(), [])
  if (!Array.isArray(records)) return []
  if (!role) return clone(records)
  const normalizedRole = WALLET_ROLES.includes(role) ? role : 'user'
  return clone(records).filter((item) => String(item?.role || 'mentor') === normalizedRole)
}

function formatMonthKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

function formatCompactDate(date) {
  return `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`
}

function formatDateTime(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function getWithdrawalStorageKey() {
  const user = getAuthUser() || {}
  const userId = String(user.id || user.user_id || user.userId || '').trim()
  return `${WALLET_WITHDRAWAL_STORAGE_KEY}:${userId || 'guest'}`
}

function readStorage(key, fallback) {
  try {
    if (typeof uni === 'undefined' || typeof uni.getStorageSync !== 'function') return fallback
    const value = uni.getStorageSync(key)
    return value === undefined || value === '' || value === null ? fallback : value
  } catch (error) {
    return fallback
  }
}

function writeStorage(key, value) {
  try {
    if (typeof uni !== 'undefined' && typeof uni.setStorageSync === 'function') {
      uni.setStorageSync(key, value)
    }
  } catch (error) {
    // 本地缓存不可用时，钱包仍可使用当前页面内的 Mock 状态。
  }
}
