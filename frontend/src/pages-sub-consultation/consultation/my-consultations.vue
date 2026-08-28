<template>
  <view class="my-consultations-page" :style="themeInlineStyle">
    <MentorPageHeader title="我的咨询" @back="goBack">
      <template #right>
        <button
          class="my-consultations-refresh"
          :class="{ spinning: loading }"
          aria-label="刷新咨询记录"
          :disabled="loading"
          @tap="loadOrders"
        >
          <view class="my-consultations-refresh-glyph" aria-hidden="true"><AppRefreshIcon /></view>
        </button>
      </template>
    </MentorPageHeader>

    <scroll-view scroll-y class="my-consultations-scroll" @scrolltolower="loadMoreOrders">
      <view class="my-consultations-content">
        <view class="my-consultations-list-head">
          <text>{{ recordCountText }}</text>
        </view>

        <AppPageLoadingState v-if="entryLoading || (loading && !orders.length)" message="正在整理我的咨询..." />
        <view v-else-if="error" class="my-consultations-state error">
          <text>{{ error }}</text>
          <button @tap="loadOrders">重新加载</button>
        </view>
        <AppEmptyState
          v-else-if="!orders.length"
          label="还没有咨询记录"
          title="还没有咨询记录"
          description="完成一次前辈咨询后，聊天记录会自动保存在这里。"
        >
          <button @tap="goToMentors">去找前辈咨询</button>
        </AppEmptyState>

        <view v-else class="my-consultations-list">
          <view
            v-for="order in orders"
            :key="order.id"
            class="my-consultation-card"
            :class="{ 'is-openable': canOpenChat(order), 'has-unread-update': isOrderUnread(order) }"
            @tap="openOrder(order)"
          >
            <view class="my-consultation-card-head">
              <view class="my-consultation-avatar" :class="`tone-${getMentor(order)?.avatarTone || 'blue'}`">
                <image v-if="getMentorAvatarUrl(order)" :src="getMentorAvatarUrl(order)" mode="aspectFill" />
                <text v-else>{{ getMentor(order)?.avatar || '前' }}</text>
              </view>
              <view class="my-consultation-target">
                <strong>{{ getMentorName(order) }}</strong>
                <text>{{ getMentorMeta(order) }}</text>
              </view>
              <view class="my-consultation-head-badges">
                <view v-if="isOrderUnread(order)" class="my-consultation-unread-badge">新动态</view>
                <view class="my-consultation-status" :class="order.orderStatus">{{ getOrderStatusLabel(order.orderStatus) }}</view>
              </view>
            </view>

            <view v-if="order.questionnaire?.question" class="my-consultation-question">
              <text>咨询问题</text>
              <view>“{{ order.questionnaire.question }}”</view>
            </view>

            <view class="my-consultation-meta">
              <text>{{ order.consultationType === 'booking' ? '预约咨询' : '即时咨询' }}</text>
              <text>{{ formatOrderTime(order.createdAt) }}</text>
            </view>

            <view v-if="canOpenChat(order)" class="my-consultation-record-link">
              <text>{{ order.orderStatus === 'completed' ? '查看完整聊天记录' : '进入本次咨询' }}</text><text>›</text>
            </view>
            <view v-else class="my-consultation-pending-copy">{{ getOrderStateHint(order) }}</view>
          </view>
          <view v-if="orders.length" class="my-consultations-load-state" @tap="loadMoreOrders">
            {{ loadingMore ? '正在加载更多…' : hasMore ? '继续下滑加载更多' : '已加载全部咨询记录' }}
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import AppRefreshIcon from '../../components/ui/AppRefreshIcon.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import { fetchMentorProfile, fetchMyMentorConsultationOrders } from '../../api/mentorConsultation'
import {
  fetchUserNotificationUnreadSummary,
  markUserNotificationReadTarget
} from '../../api/notifications'
import {
  cacheMentors,
  getMentorById,
  normalizeMentorConsultationOrder,
  normalizeMentorDetailResponse
} from '../../data/mentorConsultation'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const CHAT_RECORD_STATUSES = new Set(['in_progress', 'completed'])

const orders = ref([])
const mentorProfilesById = ref({})
const loading = ref(false)
const entryLoading = ref(true)
const loadingMore = ref(false)
const nextCursor = ref('')
const hasMore = ref(false)
const error = ref('')
const unreadOrderTargets = ref({})
const themeKey = ref(getStoredThemeKey())
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))
const recordCountText = computed(() => orders.value.length ? `共 ${orders.value.length} 条` : '暂无记录')
let latestLoadToken = 0

onShow(() => {
  themeKey.value = getStoredThemeKey()
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  void loadUnreadOrderTargets()
  void loadOrders()
})

async function loadUnreadOrderTargets() {
  try {
    const summary = await fetchUserNotificationUnreadSummary()
    const targets = summary?.consultation_order_targets?.applicant
    unreadOrderTargets.value = targets && typeof targets === 'object' && !Array.isArray(targets)
      ? Object.fromEntries(
          Object.entries(targets)
            .map(([id, count]) => [String(id || '').trim(), Math.max(0, Number(count) || 0)])
            .filter(([id, count]) => id && count > 0)
        )
      : {}
  } catch (error) {
    // 未读提示同步失败不应妨碍用户查看咨询记录。
  }
}

function isOrderUnread(order = {}) {
  return Number(unreadOrderTargets.value[String(order.id || '')] || 0) > 0
}

function markOrderNotificationsRead(order = {}) {
  const orderId = String(order.id || '').trim()
  if (!orderId) return
  const nextTargets = { ...unreadOrderTargets.value }
  delete nextTargets[orderId]
  unreadOrderTargets.value = nextTargets
  void markUserNotificationReadTarget('consultation_order', orderId)
    .then(() => loadUnreadOrderTargets())
    .catch(() => loadUnreadOrderTargets())
}

async function loadOrders() {
  if (loading.value || loadingMore.value) return
  const loadToken = ++latestLoadToken
  loading.value = true
  nextCursor.value = ''
  hasMore.value = false
  error.value = ''
  try {
    const payload = await fetchMyMentorConsultationOrders({ limit: 20 })
    if (loadToken !== latestLoadToken) return
    const nextOrders = (Array.isArray(payload?.items) ? payload.items : [])
      .map((item) => normalizeMentorConsultationOrder(item))
      .sort((left, right) => toTimestamp(right.updatedAt || right.createdAt) - toTimestamp(left.updatedAt || left.createdAt))
    orders.value = nextOrders
    nextCursor.value = String(payload?.next_cursor || '')
    hasMore.value = payload?.has_more === true
    void hydrateMentorProfiles(nextOrders, loadToken)
  } catch (requestError) {
    if (loadToken === latestLoadToken) error.value = requestError?.detail || '咨询记录读取失败，请稍后重试'
  } finally {
    if (loadToken === latestLoadToken) {
      loading.value = false
      entryLoading.value = false
    }
  }
}

async function loadMoreOrders() {
  if (loading.value || loadingMore.value || !hasMore.value || !nextCursor.value) return
  loadingMore.value = true
  try {
    const payload = await fetchMyMentorConsultationOrders({ limit: 20, cursor: nextCursor.value })
    const nextOrders = (Array.isArray(payload?.items) ? payload.items : [])
      .map((item) => normalizeMentorConsultationOrder(item))
    orders.value = [...orders.value, ...nextOrders.filter((item) => !orders.value.some((existing) => existing.id === item.id))]
    nextCursor.value = String(payload?.next_cursor || '')
    hasMore.value = payload?.has_more === true
    void hydrateMentorProfiles(nextOrders, latestLoadToken)
  } catch (requestError) {
    uni.showToast({ title: requestError?.detail || '更多咨询记录读取失败', icon: 'none' })
  } finally {
    loadingMore.value = false
  }
}

async function hydrateMentorProfiles(items, loadToken) {
  const nextProfiles = { ...mentorProfilesById.value }
  const missingIds = []
  for (const item of items) {
    const mentorId = String(item?.mentorId || '')
    if (!mentorId || nextProfiles[mentorId]) continue
    const cached = getMentorById(mentorId)
    if (cached) {
      nextProfiles[mentorId] = cached
    } else {
      missingIds.push(mentorId)
    }
  }
  if (loadToken !== latestLoadToken) return
  mentorProfilesById.value = nextProfiles
  if (!missingIds.length) return

  const profiles = (await Promise.all([...new Set(missingIds)].map(async (mentorId) => {
    try {
      return normalizeMentorDetailResponse(await fetchMentorProfile(mentorId))
    } catch (requestError) {
      return null
    }
  }))).filter(Boolean)
  if (loadToken !== latestLoadToken || !profiles.length) return

  cacheMentors(profiles)
  mentorProfilesById.value = profiles.reduce((result, profile) => ({ ...result, [profile.id]: profile }), {
    ...mentorProfilesById.value
  })
}

function getMentor(order = {}) {
  const mentorId = String(order?.mentorId || '')
  return mentorProfilesById.value[mentorId] || getMentorById(mentorId) || null
}

function getMentorAvatarUrl(order) {
  const avatarUrl = String(getMentor(order)?.avatarUrl || '')
  return /^(https?:\/\/|data:image\/)/i.test(avatarUrl) ? avatarUrl : ''
}

function getMentorName(order) {
  return getMentor(order)?.maskedName || '认证前辈'
}

function getMentorMeta(order) {
  const mentor = getMentor(order)
  const profileMeta = [mentor?.school, mentor?.major].filter(Boolean).join(' · ')
  return profileMeta || '前辈咨询记录'
}

function canOpenChat(order = {}) {
  return CHAT_RECORD_STATUSES.has(String(order?.orderStatus || ''))
}

function openOrder(order) {
  markOrderNotificationsRead(order)
  if (!canOpenChat(order) || !order?.id || !order?.mentorId) return
  uni.navigateTo({
    url: `/pages-sub-consultation/consultation/mentor-chat?mentorId=${encodeURIComponent(order.mentorId)}&orderId=${encodeURIComponent(order.id)}&role=applicant&from=my-consultations`
  })
}

function getOrderStatusLabel(status) {
  if (status === 'pending_payment' && import.meta.env.DEV) return '待确认'
  return ({
    pending_payment: '待支付',
    pending_accept: '待接单',
    accepted: '已接单',
    booked: '已预约',
    in_progress: '咨询中',
    completed: '已完成',
    rejected: '未接单',
    timeout: '已超时',
    refunded: '已退款',
    cancelled: '已取消'
  })[status] || '处理中'
}

function getOrderStateHint(order = {}) {
  const status = String(order.orderStatus || '')
  if (status === 'pending_payment') return import.meta.env.DEV ? '请在订单页确认后发送给前辈。' : '完成支付后会生成本次咨询记录。'
  if (status === 'pending_accept') return '前辈确认接单后即可进入咨询。'
  if (status === 'rejected') return order.rejectionReason ? `前辈说明：${order.rejectionReason}` : '本次咨询未进入聊天阶段。'
  if (status === 'timeout') return '本次咨询已超时，未生成可查看的聊天记录。'
  if (status === 'refunded') return '本次订单已退款，未生成可查看的聊天记录。'
  if (status === 'cancelled') return '本次咨询已取消，未生成可查看的聊天记录。'
  return '本次咨询暂未生成可查看的聊天记录。'
}

function formatOrderTime(value) {
  const date = new Date(value || '')
  if (Number.isNaN(date.getTime())) return '刚刚'
  const now = new Date()
  if (now.toDateString() === date.toDateString()) {
    return `今天 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
  return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`
}

function toTimestamp(value) {
  const timestamp = Date.parse(String(value || ''))
  return Number.isFinite(timestamp) ? timestamp : 0
}

function goToMentors() {
  uni.navigateTo({ url: '/pages/home/index?tab=circle&section=community&communityTab=mentor' })
}

function goLogin() {
  uni.reLaunch({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages-sub-consultation/consultation/my-consultations')}` })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=profile' })
    }
  })
}
</script>

<style scoped>
.my-consultations-page{height:100vh;height:100dvh;overflow:hidden;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f4f8ff);color:#2a3b57}.my-consultations-scroll{min-height:0;flex:1}.my-consultations-content{padding:24rpx 24rpx calc(env(safe-area-inset-bottom) + 42rpx)}.my-consultations-refresh{width:88rpx;height:88rpx;min-width:88rpx;min-height:88rpx;margin:0;padding:0;border:0;border-radius:50%;background:transparent;color:#9b9795;display:flex;align-items:center;justify-content:center;line-height:1;box-shadow:none}.my-consultations-refresh-glyph{display:flex;align-items:center;justify-content:center}.my-consultations-refresh::after,.my-consultations-state button::after,.my-consultations-empty button::after{border:0}.my-consultations-refresh:active{transform:scale(.96)}.my-consultations-refresh.spinning .my-consultations-refresh-glyph{animation:consultation-refresh-spin 900ms linear infinite}.my-consultations-refresh[disabled]{opacity:.55}.my-consultations-empty-icon{display:flex;align-items:center;justify-content:center;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-weight:900;flex-shrink:0}.my-consultations-list-head{margin:0 4rpx 18rpx;display:flex;align-items:baseline;justify-content:space-between;gap:16rpx}.my-consultations-list-head strong{color:#273953;font-size:29rpx;font-weight:900}.my-consultations-list-head text{color:#93a0b1;font-size:20rpx;font-weight:700}.my-consultations-state,.my-consultations-empty{padding:42rpx 30rpx;border:2rpx solid var(--gyt-primary-border,#dce8fa);border-radius:28rpx;background:var(--gyt-panel-bg,#fff);color:#8191a6;font-size:22rpx;line-height:1.55;text-align:center}.my-consultations-state.error{color:#bd655c}.my-consultations-state text,.my-consultations-empty strong,.my-consultations-empty text{display:block}.my-consultations-state button{margin-top:16rpx;border:0;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-size:21rpx;font-weight:800}.my-consultations-empty{padding-top:50rpx}.my-consultations-empty-icon{width:88rpx;height:88rpx;margin:0 auto 20rpx;border-radius:29rpx;font-size:35rpx}.my-consultations-empty strong{color:#2d405d;font-size:27rpx;font-weight:900}.my-consultations-empty text{margin:11rpx auto 0;max-width:480rpx;color:#8493a8;font-size:21rpx;line-height:1.6}.my-consultations-empty button{height:70rpx;margin-top:26rpx;padding:0 30rpx;border:0;border-radius:21rpx;background:var(--gyt-primary,#3478f6);color:#fff;font-size:23rpx;font-weight:900;box-shadow:0 10rpx 22rpx var(--gyt-primary-shadow,rgba(52,120,246,.18))}.my-consultations-list{display:flex;flex-direction:column;gap:18rpx}.my-consultations-load-state{padding:22rpx 0 8rpx;color:#8a9ab0;font-size:19rpx;line-height:1.4;font-weight:750;text-align:center}.my-consultation-card{padding:25rpx;border:2rpx solid #e0e9f7;border-radius:28rpx;background:var(--gyt-panel-bg,#fff);box-shadow:0 12rpx 30rpx rgba(43,73,112,.05);box-sizing:border-box}.my-consultation-card.is-openable{cursor:pointer;transition:transform 160ms ease,border-color 160ms ease}.my-consultation-card.is-openable:active{border-color:var(--gyt-primary-border,#cfe0fc);transform:scale(.992)}.my-consultation-card-head{display:flex;align-items:center;gap:14rpx}.my-consultation-avatar{width:64rpx;height:64rpx;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;background:#e6efff;color:#3478f6;font-size:25rpx;font-weight:900;flex-shrink:0}.my-consultation-avatar image{width:100%;height:100%}.my-consultation-avatar.tone-mint{background:#e2f4ef;color:#198777}.my-consultation-avatar.tone-violet{background:#eeeafe;color:#7162bd}.my-consultation-avatar.tone-warm{background:#f9eee1;color:#b66c32}.my-consultation-target{min-width:0;flex:1}.my-consultation-target strong,.my-consultation-target text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.my-consultation-target strong{color:#2d405d;font-size:25rpx;line-height:1.3;font-weight:900}.my-consultation-target text{margin-top:6rpx;color:#8b99ac;font-size:19rpx;line-height:1.25;font-weight:650}.my-consultation-status{padding:7rpx 10rpx;border-radius:999rpx;background:#edf4ff;color:#5276aa;font-size:18rpx;line-height:1.2;font-weight:850;white-space:nowrap}.my-consultation-status.in_progress{background:#e5f2ff;color:#3478f6}.my-consultation-status.completed{background:#e6f7f1;color:#248b75}.my-consultation-status.rejected,.my-consultation-status.timeout,.my-consultation-status.refunded,.my-consultation-status.cancelled{background:#f0eef2;color:#807987}.my-consultation-status.pending_payment,.my-consultation-status.pending_accept{background:#fff4dd;color:#aa792e}.my-consultation-question{margin-top:19rpx;padding-top:17rpx;border-top:2rpx solid #edf2f8}.my-consultation-question text{display:block;color:#8b99ac;font-size:19rpx;font-weight:750}.my-consultation-question view{margin-top:7rpx;overflow:hidden;color:#566a86;font-size:21rpx;line-height:1.55;font-weight:650;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}.my-consultation-meta{margin-top:17rpx;display:flex;align-items:center;justify-content:space-between;gap:16rpx;color:#93a0b1;font-size:18rpx;font-weight:650}.my-consultation-record-link{margin-top:18rpx;padding-top:17rpx;border-top:2rpx solid #edf2f8;display:flex;align-items:center;justify-content:space-between;color:var(--gyt-primary,#3478f6);font-size:21rpx;font-weight:850}.my-consultation-record-link text:last-child{font-size:34rpx;line-height:.7;font-weight:500}.my-consultation-pending-copy{margin-top:18rpx;padding-top:17rpx;border-top:2rpx solid #edf2f8;color:#91a0b2;font-size:19rpx;line-height:1.45;font-weight:650}

/* 延续“历年分数线”的分组卡语言：暖灰底、白色容器、浅灰分隔。
   品牌色与状态色仅承担操作及业务状态提示。 */
.my-consultations-page {
  --consultation-surface: rgba(255, 255, 255, 0.96);
  --consultation-soft: #f7f6f8;
  --consultation-ink: #243343;
  --consultation-muted: #85808a;
  --consultation-line: rgba(42, 38, 48, 0.065);
  background: #f5f3f7;
  color: var(--consultation-ink);
}

.my-consultations-page :deep(.app-page-header) {
  border-bottom-color: transparent;
  background: #f5f3f7;
  box-shadow: none;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.my-consultations-page :deep(.app-page-header-title) {
  color: var(--consultation-ink);
}

.my-consultations-page :deep(.app-page-header-back:active) {
  background: #ebe8ed;
}

.my-consultations-content {
  padding: 24rpx 34rpx calc(env(safe-area-inset-bottom) + 42rpx);
}

.my-consultations-refresh {
  background: transparent;
  color: #9b9795;
  box-shadow: none;
}

.my-consultations-list-head {
  align-items: center;
  justify-content: flex-end;
}

.my-consultations-list-head text,
.my-consultations-load-state {
  color: #8f8a93;
}

.my-consultations-state,
.my-consultations-empty {
  border: 0;
  border-radius: 36rpx;
  background: var(--consultation-surface);
  color: var(--consultation-muted);
  box-shadow: 0 14rpx 36rpx rgba(56, 49, 64, 0.04);
}

.my-consultations-empty-icon {
  background: #f0eef2;
  color: #68636c;
}

.my-consultations-empty strong {
  color: var(--consultation-ink);
}

.my-consultations-empty text {
  color: var(--consultation-muted);
}

.my-consultations-list {
  gap: 0;
  padding: 0 28rpx;
  overflow: hidden;
  border-radius: 36rpx;
  background: var(--consultation-surface);
  box-shadow: 0 14rpx 36rpx rgba(56, 49, 64, 0.04);
}

.my-consultation-card {
  padding: 26rpx 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.my-consultation-card + .my-consultation-card {
  border-top: 2rpx solid var(--consultation-line);
}

.my-consultation-card.is-openable {
  transition: background-color 160ms ease;
}

.my-consultation-card.is-openable:active {
  border-color: transparent;
  background: rgba(247, 246, 248, 0.72);
  transform: none;
}

.my-consultation-target strong {
  color: var(--consultation-ink);
}

.my-consultation-target text,
.my-consultation-question text,
.my-consultation-meta,
.my-consultation-pending-copy {
  color: var(--consultation-muted);
}

.my-consultation-status {
  background: #f0eef2;
  color: #68636c;
}

.my-consultation-head-badges {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.my-consultation-unread-badge {
  padding: 7rpx 10rpx;
  border-radius: 999rpx;
  background: rgba(242, 85, 85, 0.1);
  color: #d94b4b;
  font-size: 17rpx;
  line-height: 1;
  font-weight: 900;
  white-space: nowrap;
}

.my-consultation-card.has-unread-update {
  background: rgba(255, 252, 252, 0.78);
}

.my-consultation-question {
  border-top-color: var(--consultation-line);
}

.my-consultation-record-link,
.my-consultation-pending-copy {
  border-top: 0;
}

.my-consultation-question view {
  color: #4b4750;
}

.my-consultations-load-state {
  margin: 0;
  padding: 22rpx 0;
  border-top: 2rpx solid var(--consultation-line);
}

@keyframes consultation-refresh-spin {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .my-consultations-refresh.spinning .my-consultations-refresh-glyph {
    animation: none;
  }
}

@media(max-width:350px) {
  .my-consultations-content {
    padding-right: 26rpx;
    padding-left: 26rpx;
  }

  .my-consultations-list {
    padding-right: 24rpx;
    padding-left: 24rpx;
  }
}
</style>
