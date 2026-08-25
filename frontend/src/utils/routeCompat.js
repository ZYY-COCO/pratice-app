const LEGACY_ROUTE_MAP = Object.freeze({
  '/pages/circle/mentor-detail': '/pages-sub-consultation/consultation/mentor-detail',
  '/pages/circle/mentor-booking': '/pages-sub-consultation/consultation/mentor-booking',
  '/pages/circle/mentor-schedule': '/pages-sub-consultation/consultation/mentor-schedule',
  '/pages/circle/mentor-info': '/pages-sub-consultation/consultation/mentor-info',
  '/pages/circle/mentor-consult-form': '/pages-sub-consultation/consultation/mentor-consult-form',
  '/pages/circle/mentor-waiting': '/pages-sub-consultation/consultation/mentor-waiting',
  '/pages/circle/mentor-chat': '/pages-sub-consultation/consultation/mentor-chat',
  '/pages/circle/my-consultations': '/pages-sub-consultation/consultation/my-consultations',
  '/pages/circle/mentor-report': '/pages-sub-consultation/consultation/mentor-report',
  '/pages/circle/mentor-support': '/pages-sub-consultation/consultation/mentor-support',
  '/pages/circle/mentor-response': '/pages-sub-consultation/consultation/mentor-response',
  '/pages/circle/mentor-appeal': '/pages-sub-consultation/consultation/mentor-appeal',
  '/pages/circle/mentor-apply': '/pages-sub-consultation/consultation/mentor-apply',
  '/pages/wallet/index': '/pages-sub-wallet/wallet/index',
  '/pages/wallet/transaction-detail': '/pages-sub-wallet/wallet/transaction-detail',
  '/pages/wallet/withdraw': '/pages-sub-wallet/wallet/withdraw',
  '/pages/wallet/withdrawal-records': '/pages-sub-wallet/wallet/withdrawal-records',
  '/pages/admin/index': '/pages-sub-admin/admin/index',
  '/pages/admin/question-login': '/pages-sub-admin/admin/question-login',
  '/pages/admin/question-desktop': '/pages-sub-admin/admin/question-desktop',
  '/pages/admin/question-image-import': '/pages-sub-admin/admin/question-image-import',
  '/pages/major-catalog/index': '/pages-sub-data/major-catalog/index',
  '/pages/school-announcements/index': '/pages-sub-data/school-announcements/index'
})

export function resolveLegacyAppRoute(routePath = '') {
  const normalized = String(routePath || '').trim()
  if (!normalized.startsWith('/')) return normalized

  const suffixIndex = normalized.search(/[?#]/)
  const pathname = suffixIndex >= 0 ? normalized.slice(0, suffixIndex) : normalized
  const suffix = suffixIndex >= 0 ? normalized.slice(suffixIndex) : ''
  const resolvedPath = LEGACY_ROUTE_MAP[pathname] || pathname
  return `${resolvedPath}${suffix}`
}
