<template>
  <view class="page daily-leaderboard-page" :style="pageInlineStyle">
    <AppPageHeader title="今日学习榜" @back="goBack" />

    <view class="daily-leaderboard-shell">
      <view class="daily-ranking-card">
        <view class="daily-ranking-head">
          <view>
            <text class="daily-ranking-title">今日排名</text>
            <text class="daily-ranking-meta">{{ totalUsers }} 人已参与</text>
          </view>
          <text class="daily-ranking-updated">{{ updatedTimeLabel }}</text>
        </view>

        <view v-if="error" class="daily-leaderboard-notice" role="status">
          <text>{{ error }}</text>
          <button hover-class="none" :disabled="loading" @tap="loadLeaderboard({ reset: true })">重试</button>
        </view>

        <view class="daily-ranking-content">
          <AppPageLoadingState
            v-if="loading && !items.length"
            compact
            message="正在同步今日学习排名..."
          />

          <AppEmptyState
            v-else-if="!items.length"
            compact
            title="今天还没有学习记录"
            description="完成一道题后，你的有效刷题时长会进入今日榜单。"
          />

          <scroll-view
            v-else
            class="daily-ranking-scroll"
            scroll-y
            :show-scrollbar="false"
            :refresher-enabled="true"
            :refresher-triggered="refresherTriggered"
            refresher-background="transparent"
            :lower-threshold="120"
            @refresherrefresh="handleRankingRefresh"
            @scrolltolower="handleRankingScrollToLower"
          >
            <view class="daily-ranking-list">
              <view
                v-for="item in items"
                :key="item.userId"
                class="daily-ranking-row"
                :class="{ 'is-top': item.rank <= 3, 'is-current': item.isCurrentUser }"
              >
                <view
                  class="daily-ranking-position"
                  :class="[`rank-${Math.min(item.rank, 4)}`, { 'has-medal': item.rank >= 1 && item.rank <= 3 }]"
                  aria-hidden="true"
                >
                  <image
                    v-if="item.rank >= 1 && item.rank <= 3"
                    class="daily-ranking-medal"
                    :src="getRankMedalIcon(item.rank)"
                    mode="aspectFit"
                  />
                  <text v-else>{{ item.rank }}</text>
                </view>
                <view class="daily-ranking-avatar" aria-hidden="true">
                  <image v-if="item.avatarUrl" :src="item.avatarUrl" mode="aspectFill" />
                  <text v-else>{{ getAvatarText(item.nickname) }}</text>
                </view>
                <view class="daily-ranking-user">
                  <view class="daily-ranking-name-line">
                    <text class="daily-ranking-name">{{ item.nickname }}</text>
                    <text v-if="item.isCurrentUser" class="daily-ranking-me">我</text>
                  </view>
                  <text class="daily-ranking-answer-count">今日 {{ item.answerCount }} 题</text>
                </view>
                <view class="daily-ranking-duration">
                  <text>{{ formatStudyDuration(item.studySeconds) }}</text>
                  <text class="daily-ranking-duration-label">有效时长</text>
                </view>
              </view>
            </view>

            <button
              v-if="hasMore"
              class="daily-ranking-load-more"
              :disabled="loadingMore"
              hover-class="none"
              @tap="loadLeaderboard({ reset: false })"
            >
              {{ loadingMore ? '正在加载...' : '加载更多' }}
            </button>
            <view v-else class="daily-ranking-end">已展示全部今日上榜用户</view>
          </scroll-view>
        </view>
      </view>

      <view class="daily-my-rank-card" :class="{ 'is-empty': !currentUser }">
        <template v-if="currentUser">
          <view class="daily-my-rank-copy">
            <text>我的排名</text>
            <strong>第 {{ currentUser.rank }} 名</strong>
          </view>
          <view class="daily-my-rank-stats">
            <strong>{{ formatStudyDuration(currentUser.studySeconds) }}</strong>
            <text>今日 {{ currentUser.answerCount }} 题</text>
          </view>
        </template>
        <template v-else>
          <view class="daily-my-rank-copy">
            <text>我的排名</text>
            <strong>{{ loading ? '正在同步' : '暂未上榜' }}</strong>
          </view>
          <text class="daily-my-rank-hint">{{ loading ? '正在读取今日排名' : '完成一道题即可参与今日排名' }}</text>
        </template>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { onHide, onShow } from '@dcloudio/uni-app'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import { fetchDailyStudyLeaderboard } from '../../api/reports'
import { isLoggedIn } from '../../utils/auth'
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const DAILY_REFRESH_INTERVAL = 30000
const PAGE_SIZE = 50
const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const mpLayoutStyle = ref(buildMpPageSafeStyle())
const pageInlineStyle = computed(() => [themeInlineStyle, mpLayoutStyle.value].filter(Boolean).join(';'))
const items = ref([])
const currentUser = ref(null)
const totalUsers = ref(0)
const hasMore = ref(false)
const updatedAt = ref('')
const loading = ref(false)
const loadingMore = ref(false)
const refresherTriggered = ref(false)
const error = ref('')
let refreshTimer = null

const updatedTimeLabel = computed(() => {
  if (!updatedAt.value) return '等待同步'
  const date = new Date(updatedAt.value)
  if (Number.isNaN(date.getTime())) return '刚刚更新'
  return `更新于 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
})

onShow(() => {
  mpLayoutStyle.value = buildMpPageSafeStyle()
  if (!isLoggedIn()) {
    uni.navigateTo({
      url: `/pages/login/index?redirect=${encodeURIComponent('/pages/daily-leaderboard/index')}`
    })
    return
  }
  void loadLeaderboard({ reset: true })
  startRefreshTimer()
})

onHide(stopRefreshTimer)
onBeforeUnmount(stopRefreshTimer)

function normalizeLeaderboardItem(item = {}) {
  return {
    rank: Math.max(0, Number(item.rank || 0)),
    userId: String(item.user_id || item.userId || ''),
    nickname: String(item.nickname || '学习用户'),
    avatarUrl: String(item.avatar_url || item.avatarUrl || '').trim(),
    studySeconds: Math.max(0, Number(item.study_seconds ?? item.studySeconds ?? 0)),
    answerCount: Math.max(0, Number(item.answer_count ?? item.answerCount ?? 0)),
    correctCount: Math.max(0, Number(item.correct_count ?? item.correctCount ?? 0)),
    accuracy: Math.max(0, Number(item.accuracy || 0)),
    isCurrentUser: item.is_current_user === true || item.isCurrentUser === true
  }
}

async function loadLeaderboard({ reset = true } = {}) {
  if (reset ? loading.value : loadingMore.value) return
  if (!reset && !hasMore.value) return
  if (reset) loading.value = true
  else loadingMore.value = true
  error.value = ''
  try {
    const response = await fetchDailyStudyLeaderboard({
      limit: PAGE_SIZE,
      offset: reset ? 0 : items.value.length
    })
    const nextItems = Array.isArray(response?.items)
      ? response.items.map(normalizeLeaderboardItem).filter((item) => item.userId)
      : []
    items.value = reset
      ? nextItems
      : [...items.value, ...nextItems.filter((item) => !items.value.some((existing) => existing.userId === item.userId))]
    currentUser.value = response?.current_user ? normalizeLeaderboardItem(response.current_user) : null
    totalUsers.value = Math.max(0, Number(response?.total_users ?? items.value.length))
    hasMore.value = response?.has_more === true
    updatedAt.value = String(response?.updated_at || '')
  } catch (requestError) {
    error.value = requestError?.detail || '今日学习榜同步失败，请稍后重试'
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function handleRankingRefresh() {
  if (refresherTriggered.value) return
  refresherTriggered.value = true
  try {
    await loadLeaderboard({ reset: true })
  } finally {
    refresherTriggered.value = false
  }
}

function handleRankingScrollToLower() {
  if (hasMore.value && !loadingMore.value) void loadLeaderboard({ reset: false })
}

function startRefreshTimer() {
  stopRefreshTimer()
  refreshTimer = setInterval(() => {
    if (!loading.value && !loadingMore.value) void loadLeaderboard({ reset: true })
  }, DAILY_REFRESH_INTERVAL)
}

function stopRefreshTimer() {
  if (!refreshTimer) return
  clearInterval(refreshTimer)
  refreshTimer = null
}

function formatStudyDuration(value) {
  const seconds = Math.max(0, Math.floor(Number(value || 0)))
  if (seconds > 0 && seconds < 60) return '<1分钟'
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const remaining = minutes % 60
  if (hours && remaining) return `${hours}小时${remaining}分`
  if (hours) return `${hours}小时`
  return `${minutes}分钟`
}

function getAvatarText(value) {
  return String(value || '学').trim().slice(0, 1) || '学'
}

function getRankMedalIcon(rank) {
  const normalizedRank = Math.floor(Number(rank || 0))
  if (normalizedRank < 1 || normalizedRank > 3) return ''
  return `/static/ui-icons/png/original/rank-medal-${normalizedRank}.png`
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
    return
  }
  uni.reLaunch({ url: '/pages/home/index?tab=home' })
}
</script>

<style scoped>
.daily-leaderboard-page {
  width: 100%;
  height: 100vh;
  min-height: 0;
  box-sizing: border-box;
  background: var(--gyt-page-bg, #f7f6f8);
  color: #172033;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.daily-leaderboard-shell {
  width: min(100%, 760rpx);
  min-height: 0;
  flex: 1;
  margin: 0 auto;
  box-sizing: border-box;
  padding: 18rpx 30rpx calc(env(safe-area-inset-bottom) + 24rpx);
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  overflow: hidden;
}

.daily-ranking-card,
.daily-my-rank-card {
  border: 2rpx solid var(--gyt-border, #e5edf8);
  background: rgba(255, 255, 255, 0.97);
  box-shadow: none;
}

.daily-leaderboard-notice {
  flex: 0 0 auto;
  margin: 0 6rpx 16rpx;
  padding: 20rpx 24rpx;
  border-radius: 24rpx;
  background: #fff3f1;
  color: #a74c45;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  font-size: 22rpx;
}

.daily-leaderboard-notice button {
  min-width: 104rpx;
  margin: 0;
  padding: 0 18rpx;
  border: 0;
  background: transparent;
  color: #a74c45;
  font-size: 22rpx;
  font-weight: 750;
}

.daily-leaderboard-notice button::after,
.daily-ranking-load-more::after {
  border: 0;
}

.daily-ranking-card {
  min-height: 0;
  flex: 1;
  padding: 30rpx 26rpx 22rpx;
  border-radius: 44rpx;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.daily-ranking-head {
  flex: 0 0 auto;
  padding: 0 6rpx 22rpx;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.daily-ranking-title,
.daily-ranking-meta {
  display: block;
}

.daily-ranking-title {
  font-size: 32rpx;
  line-height: 1.2;
  font-weight: 820;
}

.daily-ranking-meta,
.daily-ranking-updated {
  margin-top: 7rpx;
  color: #8b94a4;
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 550;
}

.daily-ranking-content {
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.daily-ranking-content :deep(.app-page-loading-state),
.daily-ranking-content :deep(.app-empty-state) {
  min-height: 0;
  flex: 1;
}

.daily-ranking-scroll {
  width: 100%;
  height: 0;
  min-height: 0;
  flex: 1;
}

.daily-ranking-list {
  padding-bottom: 4rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.daily-ranking-row {
  min-height: 106rpx;
  padding: 12rpx 16rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.daily-ranking-row.is-top {
  background: var(--gyt-primary-tint, #f6f9ff);
}

.daily-ranking-row.is-current {
  box-shadow: inset 0 0 0 2rpx var(--gyt-primary-soft, #dbe9ff);
}

.daily-ranking-position {
  width: 54rpx;
  height: 62rpx;
  flex: 0 0 54rpx;
  border-radius: 15rpx;
  background: #f1f3f6;
  color: #778195;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  line-height: 1;
  font-weight: 800;
}

.daily-ranking-position.rank-1,
.daily-ranking-position.rank-2,
.daily-ranking-position.rank-3 {
  background: var(--gyt-primary-soft, #e8f1ff);
  color: var(--gyt-primary, #3478f6);
}

.daily-ranking-position.has-medal {
  border-radius: 0;
  background: transparent;
}

.daily-ranking-medal {
  display: block;
  width: 54rpx;
  height: 62rpx;
}

.daily-ranking-avatar {
  width: 72rpx;
  height: 72rpx;
  flex: 0 0 72rpx;
  overflow: hidden;
  border-radius: 50%;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;
}

.daily-ranking-avatar image {
  width: 100%;
  height: 100%;
}

.daily-ranking-user {
  min-width: 0;
  flex: 1;
}

.daily-ranking-name-line {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.daily-ranking-name {
  overflow: hidden;
  font-size: 27rpx;
  line-height: 1.25;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.daily-ranking-me {
  padding: 3rpx 9rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary, #3478f6);
  color: #ffffff;
  font-size: 17rpx;
  font-weight: 750;
}

.daily-ranking-answer-count {
  display: block;
  margin-top: 6rpx;
  color: #8b94a4;
  font-size: 20rpx;
  line-height: 1.2;
}

.daily-ranking-duration {
  flex: 0 0 auto;
  text-align: right;
}

.daily-ranking-duration text {
  display: block;
}

.daily-ranking-duration text {
  font-size: 25rpx;
  line-height: 1.2;
  font-weight: 820;
}

.daily-ranking-duration .daily-ranking-duration-label {
  margin-top: 6rpx;
  color: #8b94a4;
  font-size: 18rpx;
}

.daily-ranking-load-more {
  height: 76rpx;
  margin: 18rpx 0 0;
  border: 0;
  border-radius: 24rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 23rpx;
  font-weight: 750;
}

.daily-ranking-end {
  padding: 24rpx 0 4rpx;
  color: #a0a7b3;
  text-align: center;
  font-size: 20rpx;
}

.daily-my-rank-card {
  position: relative;
  flex: 0 0 auto;
  min-height: 106rpx;
  margin-top: 0;
  padding: 22rpx 28rpx;
  border-radius: 34rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.daily-my-rank-copy text,
.daily-my-rank-copy strong,
.daily-my-rank-stats strong,
.daily-my-rank-stats text {
  display: block;
}

.daily-my-rank-copy text,
.daily-my-rank-stats text,
.daily-my-rank-hint {
  color: #7e889c;
  font-size: 20rpx;
  line-height: 1.3;
}

.daily-my-rank-copy strong {
  margin-top: 5rpx;
  font-size: 29rpx;
  line-height: 1.2;
}

.daily-my-rank-stats {
  text-align: right;
}

.daily-my-rank-stats strong {
  color: var(--gyt-primary, #3478f6);
  font-size: 27rpx;
  line-height: 1.2;
}

.daily-my-rank-stats text {
  margin-top: 5rpx;
}

.daily-my-rank-card.is-empty {
  background: rgba(255, 255, 255, 0.94);
}

@media (max-width: 360px) {
  .daily-leaderboard-shell {
    padding-right: 24rpx;
    padding-left: 24rpx;
  }

  .daily-ranking-duration text {
    font-size: 23rpx;
  }
}
</style>
