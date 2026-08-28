<template>
  <view class="notifications-page" :style="themeInlineStyle">
    <AppPageHeader title="消息中心" @back="goBack">
      <template #right><button class="notifications-refresh" :disabled="loading" aria-label="刷新消息" @tap="load"><AppRefreshIcon /></button></template>
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
            :class="[{ unread: !item.read, expanded: expandedMessageKey === item.key }, item.category]"
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
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { fetchUserNotifications, markUserNotificationRead } from '../../api/notifications'
import { fetchOfficialMessages, markOfficialMessageRead } from '../../api/officialMessages'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'
import { resolveLegacyAppRoute } from '../../utils/routeCompat'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import AppRefreshIcon from '../../components/ui/AppRefreshIcon.vue'

const personalMessages = ref([])
const officialMessages = ref([])
const loading = ref(false)
const entryLoading = ref(true)
const loadError = ref('')
const expandedMessageKey = ref('')
const themeKey = ref(getStoredThemeKey())
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))
const allMessages = computed(() => {
  const personal = personalMessages.value.map((item) => ({
    key: `personal:${item.id}`,
    source: 'personal',
    id: item.id,
    category: item.category || 'official',
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
onShow(() => {
  themeKey.value = getStoredThemeKey()
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  void load()
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

async function openMessage(item) {
  if (!item) return
  if (!item.read) {
    updateLocalReadState(item)
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

  if (item.routePath) {
    uni.navigateTo({ url: item.routePath })
    return
  }
  expandedMessageKey.value = expandedMessageKey.value === item.key ? '' : item.key
}

function updateLocalReadState(item) {
  if (item.source === 'official') {
    officialMessages.value = officialMessages.value.map((message) => (
      message.id === item.id ? { ...message, read: true } : message
    ))
    return
  }
  personalMessages.value = personalMessages.value.map((message) => (
    message.id === item.id ? { ...message, read: true } : message
  ))
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

function goLogin() {
  uni.reLaunch({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/notifications/index')}` })
}

function goBack() {
  uni.navigateBack({ fail() { uni.reLaunch({ url: '/pages/home/index?tab=profile' }) } })
}
</script>

<style scoped>
.notifications-page{height:100vh;height:100dvh;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f8faff);color:#111827}
.notifications-refresh{width:72rpx;height:72rpx;margin:0;padding:0;border:0;border-radius:50%;background:rgba(255,255,255,.82);color:var(--gyt-primary,#3478f6);display:flex;align-items:center;justify-content:center;box-shadow:0 8rpx 22rpx rgba(29,45,86,.055)}
.notifications-refresh::after,.notifications-state button::after{border:0}
.notifications-refresh:active{background:var(--gyt-primary-soft,#edf4ff);transform:scale(.97)}
.notifications-scroll{min-height:0;flex:1}.notifications-content{width:100%;max-width:760rpx;margin:0 auto;padding:30rpx 30rpx calc(48rpx + env(safe-area-inset-bottom));box-sizing:border-box}
.notifications-state{padding:48rpx 28rpx;color:#8a94a5;text-align:center;font-size:22rpx;line-height:1.65}.notifications-state strong,.notifications-state text{display:block}.notifications-state strong{color:#576579;font-size:26rpx}.notifications-state text{margin-top:8rpx}.notifications-state button{margin-top:18rpx;border:0;border-radius:18rpx;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-size:21rpx}.notifications-state.error{color:#bd655c}
.notifications-list{width:100%}.notification-row{position:relative;display:flex;align-items:flex-start;gap:30rpx;min-height:132rpx;padding:22rpx 4rpx 30rpx;box-sizing:border-box}.notification-row+.notification-row{margin-top:8rpx}
.notification-avatar{width:104rpx;height:104rpx;flex:none;box-sizing:border-box}.official-avatar{overflow:hidden;border:2rpx solid #e4e8ef;border-radius:50%;background:#fff}.official-avatar image{display:block;width:100%;height:100%}.semantic-avatar{display:flex;align-items:center;justify-content:center;border-radius:50%;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-size:32rpx;font-weight:var(--gyt-font-weight-bold,700)}.semantic-avatar.consultation{background:#eaf8f4;color:#289278}.semantic-avatar.community{background:#edf4ff;color:#397bc8}
.notification-main{min-width:0;flex:1;padding-top:2rpx}.notification-head{display:flex;align-items:center;min-height:36rpx}.notification-sender{min-width:0;overflow:hidden;color:#111827;font-size:28rpx;font-weight:var(--gyt-font-weight-bold,700);line-height:1.3;text-overflow:ellipsis;white-space:nowrap}
.notification-preview{display:-webkit-box;margin-top:10rpx;overflow:hidden;color:#222a37;font-size:23rpx;line-height:1.55;-webkit-box-orient:vertical;-webkit-line-clamp:2}.notification-row.expanded .notification-preview{-webkit-line-clamp:unset}.notification-title{font-weight:var(--gyt-font-weight-bold,700)}.notification-content{font-weight:var(--gyt-font-weight-regular,400)}.notification-time{margin-top:10rpx;color:#9ca3af;font-size:21rpx;line-height:1.35}
.notification-unread-dot{width:18rpx;height:18rpx;flex:none;margin:14rpx 2rpx 0 6rpx;border-radius:50%;background:#ff1738;box-shadow:0 0 0 4rpx rgba(255,23,56,.08)}
@media (min-width:760px){.notifications-content{padding-right:42rpx;padding-left:42rpx}.notification-row{padding-top:26rpx;padding-bottom:32rpx}}
</style>
