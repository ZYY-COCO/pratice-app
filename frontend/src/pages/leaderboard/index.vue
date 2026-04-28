<template>
  <view class="page leaderboard-page">
    <view class="leaderboard-head">
      <button class="back-btn" @tap="goBack">‹</button>
      <view class="head-copy">
        <view class="head-eyebrow">港研通</view>
        <view class="head-title">学习排行榜</view>
      </view>
      <button class="refresh-btn" :disabled="loading" @tap="loadLeaderboard">↻</button>
    </view>

    <view class="rank-hero">
      <view>
        <view class="hero-kicker">总正确率优先</view>
        <view class="hero-title">看看谁刷题又稳又勤</view>
        <view class="hero-subtitle">同正确率时，按本周刷题数继续排序。</view>
      </view>
      <view class="hero-badge">
        <text class="hero-badge-main">{{ topCount }}</text>
        <text class="hero-badge-label">上榜</text>
      </view>
    </view>

    <view class="summary-strip">
      <view>
        <view class="summary-value">{{ totalUsers }}</view>
        <view class="summary-label">注册用户</view>
      </view>
      <view class="summary-divider"></view>
      <view>
        <view class="summary-value">{{ bestAccuracy }}</view>
        <view class="summary-label">最高正确率</view>
      </view>
      <view class="summary-divider"></view>
      <view>
        <view class="summary-value">{{ bestWeekly }}</view>
        <view class="summary-label">本周最高刷题</view>
      </view>
    </view>

    <view v-if="loading" class="state-card">正在加载排行榜...</view>
    <view v-else-if="error" class="state-card warning">
      <view>{{ error }}</view>
      <button class="retry-btn" @tap="loadLeaderboard">重新加载</button>
    </view>
    <view v-else-if="leaderboard.length === 0" class="state-card">
      暂无排行榜数据，完成第一组练习后会自动出现。
    </view>

    <view v-else class="leaderboard-list">
      <view
        v-for="item in leaderboard"
        :key="item.user_id"
        class="leaderboard-row"
        :class="{ podium: item.rank <= 3, current: isCurrentUser(item) }"
      >
        <view class="rank-index" :class="`rank-${item.rank}`">{{ item.rank }}</view>
        <image
          v-if="isImageAvatar(item.avatar_url)"
          class="user-avatar image-avatar"
          :src="item.avatar_url"
          mode="aspectFill"
        />
        <view v-else class="user-avatar">{{ getAvatarText(item) }}</view>
        <view class="user-info">
          <view class="user-line">
            <text class="user-name">{{ item.nickname }}</text>
            <text v-if="isCurrentUser(item)" class="me-badge">我</text>
          </view>
          <view class="user-meta">本周 {{ item.weekly_answers || 0 }} 题</view>
        </view>
        <view class="score-box">
          <view class="accuracy">{{ formatAccuracy(item.accuracy) }}</view>
          <view class="answer-count">{{ item.total_answers || 0 }} 题</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { fetchLeaderboard } from '../../api/reports'
import { getAuthUser, isLoggedIn } from '../../utils/auth'

const leaderboard = ref([])
const totalUsers = ref(0)
const loading = ref(false)
const error = ref('')
const authUser = ref(getAuthUser())

const topCount = computed(() => leaderboard.value.length)
const bestAccuracy = computed(() => {
  const first = leaderboard.value[0]
  return first ? formatAccuracy(first.accuracy) : '--'
})
const bestWeekly = computed(() => {
  const maxValue = leaderboard.value.reduce((max, item) => Math.max(max, Number(item.weekly_answers || 0)), 0)
  return `${maxValue}题`
})

onShow(() => {
  authUser.value = getAuthUser()
  if (!isLoggedIn()) {
    uni.navigateTo({
      url: `/pages/login/index?redirect=${encodeURIComponent('/pages/leaderboard/index')}`
    })
    return
  }
  loadLeaderboard()
})

async function loadLeaderboard() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const response = await fetchLeaderboard({ limit: 50 })
    leaderboard.value = response.items || []
    totalUsers.value = response.total_users || leaderboard.value.length
  } catch (err) {
    error.value = err?.detail || '排行榜加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
    return
  }
  uni.reLaunch({ url: '/pages/home/index' })
}

function isCurrentUser(item) {
  return Boolean(authUser.value?.id && item.user_id === authUser.value.id)
}

function getAvatarText(item) {
  return (item.avatar_url || item.nickname || '学').slice(0, 1)
}

function isImageAvatar(value) {
  const avatar = String(value || '')
  return avatar.startsWith('http://') || avatar.startsWith('https://') || avatar.startsWith('data:image')
}

function formatAccuracy(value) {
  const numeric = Number(value || 0)
  return numeric ? `${Math.round(numeric)}%` : '0%'
}
</script>

<style scoped>
.leaderboard-page {
  min-height: 100vh;
  padding: calc(28rpx + env(safe-area-inset-top)) 28rpx calc(52rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  background:
    linear-gradient(180deg, rgba(229, 239, 255, 0.78), rgba(246, 248, 252, 0.94) 36%, #f6f8fc 100%);
}

.leaderboard-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 28rpx;
}

.back-btn,
.refresh-btn {
  width: 76rpx;
  height: 76rpx;
  border-radius: 38rpx;
  padding: 0;
  border: 0;
  background: rgba(255, 255, 255, 0.86);
  color: #172033;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
  font-weight: 900;
  box-shadow: 0 10rpx 26rpx rgba(30, 52, 91, 0.08);
}

.refresh-btn {
  color: #2f7cf6;
  font-size: 34rpx;
}

.head-copy {
  flex: 1;
  min-width: 0;
  text-align: center;
}

.head-eyebrow {
  color: #2f7cf6;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 800;
}

.head-title {
  margin-top: 6rpx;
  color: #101828;
  font-size: 36rpx;
  line-height: 1.2;
  font-weight: 900;
}

.rank-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  padding: 34rpx 30rpx;
  border-radius: 34rpx;
  background: linear-gradient(135deg, #1b2a52 0%, #2563eb 54%, #4f8cff 100%);
  color: #ffffff;
  box-shadow: 0 22rpx 48rpx rgba(37, 99, 235, 0.2);
}

.hero-kicker {
  display: inline-flex;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 22rpx;
  font-weight: 800;
}

.hero-title {
  margin-top: 18rpx;
  font-size: 38rpx;
  line-height: 1.25;
  font-weight: 900;
}

.hero-subtitle {
  margin-top: 12rpx;
  color: rgba(255, 255, 255, 0.78);
  font-size: 24rpx;
  line-height: 1.5;
}

.hero-badge {
  width: 128rpx;
  height: 128rpx;
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2rpx solid rgba(255, 255, 255, 0.18);
}

.hero-badge-main {
  font-size: 38rpx;
  line-height: 1.1;
  font-weight: 900;
}

.hero-badge-label {
  margin-top: 4rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.76);
}

.summary-strip {
  margin: 22rpx 0;
  padding: 24rpx 18rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 2rpx solid #e8effc;
  box-shadow: 0 14rpx 34rpx rgba(25, 48, 89, 0.06);
  display: grid;
  grid-template-columns: 1fr 2rpx 1fr 2rpx 1fr;
  align-items: center;
  text-align: center;
}

.summary-value {
  color: #2f7cf6;
  font-size: 32rpx;
  line-height: 1.2;
  font-weight: 900;
}

.summary-label {
  margin-top: 8rpx;
  color: #8a95a8;
  font-size: 22rpx;
  font-weight: 700;
}

.summary-divider {
  width: 2rpx;
  height: 48rpx;
  background: #e8edf7;
}

.state-card {
  padding: 34rpx 28rpx;
  border-radius: 28rpx;
  background: #ffffff;
  border: 2rpx solid #e8effc;
  color: #667085;
  font-size: 26rpx;
  line-height: 1.6;
  text-align: center;
  box-shadow: 0 14rpx 34rpx rgba(25, 48, 89, 0.06);
}

.state-card.warning {
  color: #b42318;
}

.retry-btn {
  margin-top: 18rpx;
  width: 220rpx;
  height: 72rpx;
  border-radius: 22rpx;
  background: #eef4ff;
  color: #2f7cf6;
  font-size: 24rpx;
  font-weight: 800;
}

.leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.leaderboard-row {
  min-height: 120rpx;
  padding: 22rpx 22rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid #e8effc;
  box-shadow: 0 14rpx 34rpx rgba(25, 48, 89, 0.06);
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.leaderboard-row.podium {
  border-color: rgba(47, 124, 246, 0.28);
  background: linear-gradient(180deg, #ffffff, #f4f8ff);
}

.leaderboard-row.current {
  border-color: rgba(47, 124, 246, 0.58);
  box-shadow: 0 16rpx 38rpx rgba(47, 124, 246, 0.14);
}

.rank-index {
  width: 54rpx;
  height: 54rpx;
  border-radius: 18rpx;
  background: #eef2f8;
  color: #667085;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 24rpx;
  font-weight: 900;
}

.rank-index.rank-1 {
  background: #fff5d9;
  color: #c57900;
}

.rank-index.rank-2 {
  background: #eef3ff;
  color: #4c6fb8;
}

.rank-index.rank-3 {
  background: #fff0e6;
  color: #b65c16;
}

.user-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 24rpx;
  background: linear-gradient(145deg, #edf4ff, #dce8ff);
  color: #2f7cf6;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 30rpx;
  font-weight: 900;
}

.image-avatar {
  display: block;
  background: #eef4ff;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-line {
  display: flex;
  align-items: center;
  gap: 10rpx;
  min-width: 0;
}

.user-name {
  max-width: 320rpx;
  color: #172033;
  font-size: 28rpx;
  line-height: 1.35;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.me-badge {
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  background: #eef4ff;
  color: #2f7cf6;
  font-size: 20rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.user-meta {
  margin-top: 8rpx;
  color: #8a95a8;
  font-size: 22rpx;
  font-weight: 700;
}

.score-box {
  min-width: 104rpx;
  text-align: right;
  flex-shrink: 0;
}

.accuracy {
  color: #2f7cf6;
  font-size: 32rpx;
  line-height: 1.2;
  font-weight: 900;
}

.answer-count {
  margin-top: 8rpx;
  color: #8a95a8;
  font-size: 22rpx;
  font-weight: 700;
}
</style>
