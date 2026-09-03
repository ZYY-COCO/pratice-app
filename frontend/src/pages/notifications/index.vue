<template>
  <view class="notifications-page" :style="themeInlineStyle">
    <AppPageHeader title="消息中心" @back="goBack">
      <template #right>
        <view class="notifications-header-actions">
          <button
            class="notifications-read-all"
            :disabled="loading || markAllLoading || unreadMessageCount === 0"
            hover-class="none"
            @tap="markAllAsRead"
          >全部已读</button>
          <button class="notifications-refresh" :disabled="loading || markAllLoading" aria-label="刷新消息" @tap="load"><AppRefreshIcon /></button>
        </view>
      </template>
    </AppPageHeader>

    <scroll-view scroll-y class="notifications-scroll">
      <view class="notifications-content">
        <AppPageLoadingState v-if="entryLoading || loading" message="正在整理消息中心..." />
        <view v-else-if="loadError" class="notifications-state error">
          <text>{{ loadError }}</text>
          <button @tap="load">重新加载</button>
        </view>
        <AppEmptyState
          v-else-if="allMessages.length === 0"
          label="暂时没有消息"
          title="暂时没有消息"
          description="咨询动态、研圈互动和平台公告会在这里通知你。"
        />

        <view v-else class="notifications-list">
          <view
            v-for="item in allMessages"
            :key="item.key"
            class="notification-row"
            :class="[{ unread: !item.read }, item.category]"
            @tap="openMessage(item)"
          >
            <view v-if="isOfficialMessage(item)" class="notification-avatar official-avatar">
              <image src="/static/brand/hmtc-community-logo.png" mode="aspectFill" />
            </view>
            <view v-else class="notification-avatar semantic-avatar" :class="item.category">
              {{ categoryMark(item.category) }}
            </view>
            <view class="notification-main">
              <view class="notification-head">
                <view class="notification-sender">{{ senderName(item) }}</view>
              </view>
              <view class="notification-preview">
                <text v-if="item.title" class="notification-title">【{{ messageLabel(item) }}】</text>
                <text class="notification-content">{{ messagePreview(item) }}</text>
              </view>
              <view class="notification-time">{{ formatRelativeTime(item.createdAt) }}</view>
            </view>
            <view v-if="!item.read" class="notification-unread-dot" aria-label="未读消息"></view>
          </view>
        </view>
      </view>
    </scroll-view>

    <view
      v-if="selectedMessage"
      class="message-detail-backdrop"
      @tap="closeMessage"
    >
      <view
        class="message-detail-dialog"
        role="dialog"
        aria-modal="true"
        :aria-label="messageTitle(selectedMessage)"
        @tap.stop
      >
        <view class="message-detail-header">
          <view class="message-detail-heading">
            <view class="message-detail-label">{{ messageLabel(selectedMessage) }}</view>
            <view class="message-detail-title">{{ messageTitle(selectedMessage) }}</view>
            <view class="message-detail-meta">
              {{ senderName(selectedMessage) }} · {{ formatMessageTime(selectedMessage.createdAt) }}
            </view>
          </view>
          <button
            class="message-detail-close"
            aria-label="关闭消息详情"
            hover-class="none"
            @tap.stop="closeMessage"
          ><CloseIcon /></button>
        </view>

        <scroll-view scroll-y class="message-detail-scroll" :show-scrollbar="false">
          <view class="message-detail-content">
            <view v-if="messageSummary(selectedMessage)" class="message-detail-summary">
              {{ messageSummary(selectedMessage) }}
            </view>
            <text v-if="messageBody(selectedMessage)" class="message-detail-body" selectable>
              {{ messageBody(selectedMessage) }}
            </text>
          </view>
        </scroll-view>

        <view v-if="hasMessageRoute(selectedMessage)" class="message-detail-footer">
          <button
            class="message-detail-action"
            :disabled="messageNavigating"
            hover-class="none"
            @tap.stop="navigateFromMessage"
          >{{ messageNavigating ? '正在打开…' : messageActionLabel(selectedMessage) }}<text v-if="!messageNavigating">→</text></button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBackPress, onShow } from '@dcloudio/uni-app'
import {
  fetchUserNotifications,
  markAllUserNotificationsRead,
  markUserNotificationRead
} from '../../api/notifications'
import { fetchOfficialMessages, markOfficialMessageRead } from '../../api/officialMessages'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'
import { resolveLegacyAppRoute } from '../../utils/routeCompat'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import AppRefreshIcon from '../../components/ui/AppRefreshIcon.vue'
import CloseIcon from '../../components/CloseIcon.vue'

const personalMessages = ref([])
const officialMessages = ref([])
const loading = ref(false)
const markAllLoading = ref(false)
const entryLoading = ref(true)
const loadError = ref('')
const selectedMessage = ref(null)
const messageNavigating = ref(false)
const personalUnreadCount = ref(0)
const officialUnreadCount = ref(0)
const themeKey = ref(getStoredThemeKey())
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))
const allMessages = computed(() => {
  const personal = personalMessages.value.map((item) => ({
    key: `personal:${item.id}`,
    source: 'personal',
    id: item.id,
    category: item.category || 'official',
    notificationType: item.notification_type || '',
    title: item.title || '平台消息',
    summary: item.summary || '',
    content: item.content || '',
    createdAt: item.created_at,
    routePath: resolveLegacyAppRoute(item.route_path || item.delivery_payload?.route_path || ''),
    deliveryPayload: item.delivery_payload || {},
    read: Boolean(item.read)
  }))
  const official = officialMessages.value.map((item) => ({
    key: `official:${item.id}`,
    source: 'official',
    id: item.id,
    category: 'official',
    notificationType: 'official_message',
    title: item.title || '平台公告',
    summary: '',
    content: item.content || '',
    createdAt: item.published_at || item.created_at,
    routePath: '',
    read: Boolean(item.read)
  }))
  return [...personal, ...official].sort((left, right) => (
    String(right.createdAt || '').localeCompare(String(left.createdAt || ''))
  ))
})
const unreadMessageCount = computed(() => {
  const serverCount = personalUnreadCount.value + officialUnreadCount.value
  return serverCount > 0
    ? serverCount
    : allMessages.value.filter((item) => !item.read).length
})
onShow(() => {
  themeKey.value = getStoredThemeKey()
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  void load()
})

onBackPress(() => {
  if (!selectedMessage.value) return false
  closeMessage()
  return true
})

onMounted(() => {
  if (typeof document !== 'undefined') document.addEventListener('keydown', handleMessageKeydown)
})

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') document.removeEventListener('keydown', handleMessageKeydown)
})

async function load() {
  if (loading.value) return
  loading.value = true
  loadError.value = ''
  try {
    const [personalResult, officialResult] = await Promise.allSettled([
      fetchUserNotifications({ limit: 100 }),
      fetchOfficialMessages()
    ])
    const personalLoaded = personalResult.status === 'fulfilled'
    const officialLoaded = officialResult.status === 'fulfilled'
    personalMessages.value = personalLoaded && Array.isArray(personalResult.value?.items)
      ? personalResult.value.items
      : []
    officialMessages.value = officialLoaded && Array.isArray(officialResult.value?.items)
      ? officialResult.value.items
      : []
    personalUnreadCount.value = personalLoaded && Number.isFinite(Number(personalResult.value?.unread_count))
      ? Math.max(0, Number(personalResult.value.unread_count))
      : personalMessages.value.filter((item) => !item.read).length
    officialUnreadCount.value = officialLoaded && Number.isFinite(Number(officialResult.value?.unread_count))
      ? Math.max(0, Number(officialResult.value.unread_count))
      : officialMessages.value.filter((item) => !item.read).length
    if (!personalLoaded && !officialLoaded) {
      loadError.value = personalResult.reason?.detail || officialResult.reason?.detail || '消息读取失败，请稍后重试'
    }
  } catch (error) {
    loadError.value = error?.detail || '消息读取失败，请稍后重试'
  } finally {
    loading.value = false
    entryLoading.value = false
  }
}

async function markAllAsRead() {
  if (loading.value || markAllLoading.value || unreadMessageCount.value === 0) return
  markAllLoading.value = true
  loadError.value = ''
  // Give the interface immediate feedback while the server mutation settles.
  personalMessages.value = personalMessages.value.map((item) => ({ ...item, read: true }))
  officialMessages.value = officialMessages.value.map((item) => ({ ...item, read: true }))
  personalUnreadCount.value = 0
  officialUnreadCount.value = 0
  try {
    await markAllUserNotificationsRead()
    uni.showToast({ title: '已全部标记为已读', icon: 'success' })
    await load()
  } catch (error) {
    await load()
    uni.showToast({ title: error?.detail || '全部已读失败，请稍后重试', icon: 'none' })
  } finally {
    markAllLoading.value = false
  }
}

function categoryMark(category) {
  return { community: '研', consultation: '咨', official: '官' }[category] || '信'
}

function isOfficialMessage(item) {
  return item?.source === 'official' || item?.category === 'official'
}

function senderName(item) {
  if (isOfficialMessage(item)) return 'HMTC升学交流圈'
  return item?.category === 'consultation' ? '咨询动态' : '研圈互动'
}

function messageLabel(item) {
  if (isOfficialMessage(item)) return item?.source === 'official' ? '官方通知' : '系统通知'
  return item?.category === 'consultation' ? '咨询通知' : '互动通知'
}

function messagePreview(item) {
  const title = String(item?.title || '').trim()
  const summary = String(item?.summary || '').trim()
  const content = String(item?.content || '').trim()
  const parts = [title, summary, content].filter((part, index, values) => (
    part && values.indexOf(part) === index
  ))
  return parts.join(' ') || '平台已更新一条消息。'
}

function messageTitle(item) {
  return String(item?.title || '').trim() || '消息详情'
}

function messageSummary(item) {
  const title = messageTitle(item)
  const summary = String(item?.summary || '').trim()
  const content = String(item?.content || '').trim()
  return summary && summary !== title && summary !== content ? summary : ''
}

function messageBody(item) {
  const title = messageTitle(item)
  const content = String(item?.content || '').trim()
  const summary = String(item?.summary || '').trim()
  if (content && content !== title) return content
  if (!messageSummary(item) && summary && summary !== title) return summary
  if (!content && !summary) return '平台已更新一条消息。'
  return ''
}

function hasMessageRoute(item) {
  return Boolean(String(item?.routePath || '').trim())
}

function messageActionLabel(item) {
  const notificationType = String(item?.notificationType || '').trim()
  if (notificationType === 'community_experience_review_rejected') return '查看处理详情'
  if (/^community_(post|experience)/.test(notificationType)) return '查看相关帖子'
  if (/^mentor_(verification|qualification|profile)/.test(notificationType)) return '查看认证详情'
  if (/(feedback|report|appeal|moderation|review)/.test(notificationType)) return '查看处理详情'
  if (item?.category === 'consultation') return '查看咨询详情'
  return '前往查看'
}

function openMessage(item) {
  if (!item) return
  selectedMessage.value = { ...item, read: true }
  messageNavigating.value = false
  if (!item.read) {
    updateLocalReadState(item)
    void persistMessageRead(item)
  }
}

async function persistMessageRead(item) {
  try {
    if (item.source === 'official') {
      await markOfficialMessageRead(item.id)
    } else {
      await markUserNotificationRead(item.id)
    }
  } catch (error) {
    // 已在页面本地更新状态；下次刷新会以服务端实际状态为准。
  }
}

function closeMessage() {
  selectedMessage.value = null
  messageNavigating.value = false
}

function navigateFromMessage() {
  const item = selectedMessage.value
  const routePath = String(item?.routePath || '').trim()
  if (!routePath || messageNavigating.value) return
  messageNavigating.value = true
  uni.navigateTo({
    url: routePath,
    success() {
      closeMessage()
    },
    fail() {
      messageNavigating.value = false
      uni.showToast({ title: '页面暂时不可访问，请稍后再试', icon: 'none' })
    }
  })
}

function handleMessageKeydown(event) {
  if (event?.key !== 'Escape' || !selectedMessage.value) return
  event.preventDefault?.()
  closeMessage()
}

function updateLocalReadState(item) {
  if (item.source === 'official') {
    officialMessages.value = officialMessages.value.map((message) => (
      message.id === item.id ? { ...message, read: true } : message
    ))
    officialUnreadCount.value = Math.max(0, officialUnreadCount.value - 1)
    return
  }
  personalMessages.value = personalMessages.value.map((message) => (
    message.id === item.id ? { ...message, read: true } : message
  ))
  personalUnreadCount.value = Math.max(0, personalUnreadCount.value - 1)
}

function formatRelativeTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '刚刚'
  const diffMs = Math.max(0, Date.now() - date.getTime())
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  if (diffMs < minute) return '刚刚'
  if (diffMs < hour) return `${Math.floor(diffMs / minute)} 分钟前`
  if (diffMs < day) return `${Math.floor(diffMs / hour)} 小时前`
  if (diffMs < 7 * day) return `${Math.floor(diffMs / day)} 天前`
  const now = new Date()
  return date.getFullYear() === now.getFullYear()
    ? `${date.getMonth() + 1}月${date.getDate()}日`
    : `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
}

function formatMessageTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '刚刚'
  const pad = (part) => String(part).padStart(2, '0')
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function goLogin() {
  uni.reLaunch({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/notifications/index')}` })
}

function goBack() {
  uni.navigateBack({ fail() { uni.reLaunch({ url: '/pages/home/index?tab=profile' }) } })
}
</script>

<style scoped>
.notifications-page{height:100vh;height:100dvh;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f8faff);color:#111827}
.notifications-header-actions{position:absolute;top:calc(var(--status-bar-height, env(safe-area-inset-top)) + 14rpx);right:28rpx;width:184rpx;height:82rpx;display:flex;align-items:center;justify-content:flex-end;gap:10rpx;white-space:nowrap}
.notifications-read-all{box-sizing:border-box;width:96rpx;min-width:96rpx;height:64rpx;flex:0 0 96rpx;margin:0;padding:0;border:0;border-radius:18rpx;background:transparent;color:var(--gyt-primary,#3478f6);font-size:21rpx;line-height:1;font-weight:750;display:flex;align-items:center;justify-content:center;white-space:nowrap}
.notifications-read-all::after{border:0}
.notifications-read-all:active{background:var(--gyt-primary-soft,#edf4ff)}
.notifications-read-all[disabled]{color:#aeb8c7;opacity:.72}
.notifications-refresh{width:72rpx;height:72rpx;flex:0 0 72rpx;margin:0;padding:0;border:0;border-radius:50%;background:rgba(255,255,255,.82);color:var(--gyt-primary,#3478f6);display:flex;align-items:center;justify-content:center;box-shadow:0 8rpx 22rpx rgba(29,45,86,.055)}
.notifications-refresh::after,.notifications-state button::after{border:0}
.notifications-refresh:active{background:var(--gyt-primary-soft,#edf4ff);transform:scale(.97)}
.notifications-scroll{min-height:0;flex:1}.notifications-content{width:100%;max-width:760rpx;margin:0 auto;padding:30rpx 30rpx calc(48rpx + env(safe-area-inset-bottom));box-sizing:border-box}
.notifications-state{padding:48rpx 28rpx;color:#8a94a5;text-align:center;font-size:22rpx;line-height:1.65}.notifications-state strong,.notifications-state text{display:block}.notifications-state strong{color:#576579;font-size:26rpx}.notifications-state text{margin-top:8rpx}.notifications-state button{margin-top:18rpx;border:0;border-radius:18rpx;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-size:21rpx}.notifications-state.error{color:#bd655c}
.notifications-list{width:100%}.notification-row{position:relative;display:flex;align-items:flex-start;gap:30rpx;min-height:132rpx;padding:22rpx 4rpx 30rpx;box-sizing:border-box}.notification-row+.notification-row{margin-top:8rpx}
.notification-avatar{width:104rpx;height:104rpx;flex:none;box-sizing:border-box}.official-avatar{overflow:hidden;border:2rpx solid #e4e8ef;border-radius:50%;background:#fff}.official-avatar image{display:block;width:100%;height:100%}.semantic-avatar{display:flex;align-items:center;justify-content:center;border-radius:50%;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-size:32rpx;font-weight:var(--gyt-font-weight-bold,700)}.semantic-avatar.consultation{background:#eaf8f4;color:#289278}.semantic-avatar.community{background:#edf4ff;color:#397bc8}
.notification-main{min-width:0;flex:1;padding-top:2rpx}.notification-head{display:flex;align-items:center;min-height:36rpx}.notification-sender{min-width:0;overflow:hidden;color:#111827;font-size:28rpx;font-weight:var(--gyt-font-weight-bold,700);line-height:1.3;text-overflow:ellipsis;white-space:nowrap}
.notification-preview{display:-webkit-box;margin-top:10rpx;overflow:hidden;color:#222a37;font-size:23rpx;line-height:1.55;-webkit-box-orient:vertical;-webkit-line-clamp:2}.notification-title{font-weight:var(--gyt-font-weight-bold,700)}.notification-content{font-weight:var(--gyt-font-weight-regular,400)}.notification-time{margin-top:10rpx;color:#9ca3af;font-size:21rpx;line-height:1.35}
.notification-unread-dot{width:18rpx;height:18rpx;flex:none;margin:14rpx 2rpx 0 6rpx;border-radius:50%;background:#ff1738;box-shadow:0 0 0 4rpx rgba(255,23,56,.08)}
.message-detail-backdrop{position:fixed;z-index:300;inset:0;padding:calc(32rpx + env(safe-area-inset-top)) 32rpx calc(32rpx + env(safe-area-inset-bottom));box-sizing:border-box;display:flex;align-items:center;justify-content:center;background:rgba(20,31,47,.42);-webkit-backdrop-filter:blur(6rpx);backdrop-filter:blur(6rpx);animation:message-backdrop-in .18s ease-out both}
.message-detail-dialog{width:min(650rpx,calc(100vw - 64rpx));max-height:min(980rpx,72vh);max-height:min(980rpx,72dvh);overflow:hidden;border:2rpx solid rgba(226,231,239,.9);border-radius:32rpx;background:#fff;box-shadow:0 34rpx 96rpx rgba(15,29,48,.24);display:flex;flex-direction:column;animation:message-dialog-in .2s cubic-bezier(.2,.8,.2,1) both}
.message-detail-header{padding:30rpx 24rpx 24rpx 30rpx;display:flex;align-items:flex-start;justify-content:space-between;gap:18rpx;border-bottom:2rpx solid #eef1f5}.message-detail-heading{min-width:0;flex:1}.message-detail-label{display:inline-flex;align-items:center;min-height:38rpx;padding:0 14rpx;border-radius:19rpx;color:var(--gyt-primary,#3478f6);background:var(--gyt-primary-soft,#edf4ff);font-size:19rpx;font-weight:850;line-height:1}.message-detail-title{margin-top:16rpx;color:#172033;font-size:32rpx;font-weight:var(--gyt-font-weight-bold,700);line-height:1.42;word-break:break-word}.message-detail-meta{margin-top:10rpx;color:#97a1b1;font-size:20rpx;line-height:1.45}.message-detail-close{width:88rpx;height:88rpx;flex:0 0 88rpx;margin:-12rpx -8rpx 0 0;padding:0;border:0;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#6f7a8a;background:transparent}.message-detail-close::after,.message-detail-action::after{border:0}.message-detail-close:active{background:#f1f4f8}.message-detail-close :deep(.close-icon-image){width:30rpx;height:30rpx}
.message-detail-scroll{min-height:0;max-height:54vh;max-height:54dvh;flex:1;overscroll-behavior:contain}.message-detail-content{padding:28rpx 30rpx 34rpx}.message-detail-summary{padding:18rpx 20rpx;border-radius:18rpx;color:#34425a;background:#f6f8fb;font-size:25rpx;font-weight:700;line-height:1.62;word-break:break-word}.message-detail-body{display:block;color:#3c4658;font-size:27rpx;line-height:1.78;white-space:pre-wrap;word-break:break-word}.message-detail-summary+.message-detail-body{margin-top:22rpx}
.message-detail-footer{padding:20rpx 30rpx 28rpx;border-top:2rpx solid #eef1f5;background:#fff}.message-detail-action{width:100%;height:88rpx;margin:0;padding:0 24rpx;border:0;border-radius:22rpx;display:flex;align-items:center;justify-content:center;gap:12rpx;color:#fff;background:var(--gyt-primary,#3478f6);font-size:26rpx;font-weight:800;line-height:1;box-shadow:0 12rpx 28rpx rgba(52,120,246,.2)}.message-detail-action text{font-size:28rpx;line-height:1}.message-detail-action:active{transform:scale(.985);opacity:.94}.message-detail-action[disabled]{opacity:.68;box-shadow:none}
@keyframes message-backdrop-in{from{opacity:0}to{opacity:1}}@keyframes message-dialog-in{from{opacity:0;transform:translateY(18rpx) scale(.975)}to{opacity:1;transform:translateY(0) scale(1)}}
@media (min-width:760px){.notifications-content{padding-right:42rpx;padding-left:42rpx}.notification-row{padding-top:26rpx;padding-bottom:32rpx}}
@media (max-width:350px){.notifications-header-actions{width:170rpx;gap:4rpx}.notifications-read-all{width:92rpx;min-width:92rpx;flex-basis:92rpx;font-size:20rpx}.notifications-refresh{width:66rpx;height:66rpx;flex-basis:66rpx}}
@media (prefers-reduced-motion:reduce){.message-detail-backdrop,.message-detail-dialog{animation:none}.message-detail-action:active{transform:none}}
/* #ifdef MP-WEIXIN */
.notifications-header-actions{top:var(--mp-page-content-top,96px)}
/* #endif */
</style>
