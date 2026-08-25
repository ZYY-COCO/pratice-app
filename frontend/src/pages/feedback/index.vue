<template>
  <view class="feedback-record-page" :style="themeInlineStyle">
    <AppPageHeader title="我的反馈" subtitle="处理进度与平台回复" @back="goBack">
      <template #right>
        <button class="feedback-record-refresh" :disabled="loading" aria-label="刷新反馈记录" @tap="loadFeedback">
          <AppRefreshIcon />
        </button>
      </template>
    </AppPageHeader>

    <scroll-view scroll-y class="feedback-record-scroll">
      <view class="feedback-record-content">
        <view class="feedback-record-intro">
          <view class="feedback-record-intro-icon">馈</view>
          <view>
            <strong>每条反馈都可以追踪</strong>
            <text>平台查看、处理完成或给出说明后，会同步到这里和消息中心。</text>
          </view>
        </view>

        <view class="feedback-record-heading">
          <strong>反馈记录</strong>
          <text>{{ recordCountText }}</text>
        </view>

        <view v-if="loading && !items.length" class="feedback-record-state">正在同步反馈记录…</view>
        <view v-else-if="error" class="feedback-record-state error">
          <text>{{ error }}</text>
          <button @tap="loadFeedback">重新加载</button>
        </view>
        <view v-else-if="!items.length" class="feedback-record-state empty">
          <strong>还没有提交过反馈</strong>
          <text>你可以在“关于我们—帮助与反馈”提交题目、功能或体验建议。</text>
          <button @tap="goToFeedbackForm">去提交反馈</button>
        </view>

        <view v-else class="feedback-record-list">
          <view v-for="item in items" :key="item.id" class="feedback-record-card">
            <view class="feedback-record-card-head">
              <view>
                <text>{{ item.feedback_type || '用户反馈' }}</text>
                <strong>{{ formatDateTime(item.created_at) }}</strong>
              </view>
              <view class="feedback-record-status" :class="item.status">{{ statusText(item.status) }}</view>
            </view>
            <view class="feedback-record-body">{{ item.content }}</view>
            <view v-if="item.admin_note" class="feedback-record-result">
              <text>平台处理说明</text>
              <strong>{{ item.admin_note }}</strong>
              <small v-if="item.handled_at">更新于 {{ formatDateTime(item.handled_at) }}</small>
            </view>
            <view v-else class="feedback-record-progress">{{ progressText(item.status) }}</view>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { fetchMyFeedback } from '../../api/feedback'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppRefreshIcon from '../../components/ui/AppRefreshIcon.vue'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const items = ref([])
const loading = ref(false)
const error = ref('')
const themeInlineStyle = computed(() => buildThemeStyle(getStoredThemeKey()))
const recordCountText = computed(() => items.value.length ? `共 ${items.value.length} 条` : '暂无记录')

onShow(() => {
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  void loadFeedback()
})

async function loadFeedback() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const response = await fetchMyFeedback({ limit: 100 })
    items.value = Array.isArray(response?.items) ? response.items : []
  } catch (requestError) {
    error.value = requestError?.detail || '反馈记录读取失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function statusText(status) {
  return ({ open: '待处理', reviewed: '已查看', resolved: '已解决', ignored: '已评估' })[status] || '处理中'
}

function progressText(status) {
  if (status === 'reviewed') return '平台已查看，正在跟进处理。'
  if (status === 'resolved') return '本条反馈已完成处理。'
  if (status === 'ignored') return '本条反馈已完成评估。'
  return '反馈已提交，等待平台查看。'
}

function formatDateTime(value) {
  const date = new Date(value || '')
  if (Number.isNaN(date.getTime())) return '刚刚'
  return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function goToFeedbackForm() {
  uni.redirectTo({ url: '/pages/about/index' })
}

function goLogin() {
  uni.reLaunch({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/feedback/index')}` })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/about/index' })
    }
  })
}
</script>

<style scoped>
.feedback-record-page{height:100vh;height:100dvh;overflow:hidden;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f4f8ff);color:#2a3b57}.feedback-record-scroll{min-height:0;flex:1}.feedback-record-content{padding:24rpx 24rpx calc(env(safe-area-inset-bottom) + 42rpx)}.feedback-record-refresh{width:64rpx;height:64rpx;min-width:64rpx;min-height:64rpx;margin:0;padding:0;border:0;border-radius:50%;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);display:flex;align-items:center;justify-content:center}.feedback-record-refresh::after,.feedback-record-state button::after{border:0}.feedback-record-refresh[disabled]{opacity:.55}.feedback-record-intro{padding:24rpx;display:flex;align-items:center;gap:18rpx;border:2rpx solid var(--gyt-primary-border,#d8e7fb);border-radius:24rpx;background:var(--gyt-panel-bg,#fff);box-shadow:var(--gyt-content-surface-shadow,none)}.feedback-record-intro-icon{width:68rpx;height:68rpx;border-radius:20rpx;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);display:flex;align-items:center;justify-content:center;font-size:25rpx;font-weight:900;flex:none}.feedback-record-intro strong,.feedback-record-intro text{display:block}.feedback-record-intro strong{color:#2e405d;font-size:25rpx;line-height:1.35;font-weight:900}.feedback-record-intro text{margin-top:6rpx;color:#8495aa;font-size:20rpx;line-height:1.5;font-weight:650}.feedback-record-heading{margin:30rpx 4rpx 18rpx;display:flex;align-items:baseline;justify-content:space-between;gap:16rpx}.feedback-record-heading strong{color:#273953;font-size:29rpx;font-weight:900}.feedback-record-heading text{color:#93a0b1;font-size:20rpx;font-weight:700}.feedback-record-state{padding:42rpx 30rpx;border:2rpx solid var(--gyt-primary-border,#dce8fa);border-radius:24rpx;background:var(--gyt-panel-bg,#fff);color:#8191a6;font-size:21rpx;line-height:1.55;text-align:center}.feedback-record-state.error{color:#bd655c}.feedback-record-state strong,.feedback-record-state text{display:block}.feedback-record-state button{height:70rpx;margin-top:22rpx;padding:0 28rpx;border:0;border-radius:18rpx;background:var(--gyt-primary,#3478f6);color:#fff;font-size:21rpx;line-height:1;font-weight:850}.feedback-record-list{display:flex;flex-direction:column;gap:16rpx}.feedback-record-card{padding:24rpx;border:2rpx solid var(--gyt-primary-border,#e0e9f7);border-radius:22rpx;background:var(--gyt-panel-bg,#fff);box-shadow:var(--gyt-content-surface-shadow,none)}.feedback-record-card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16rpx}.feedback-record-card-head text,.feedback-record-card-head strong{display:block}.feedback-record-card-head text{color:#334760;font-size:23rpx;font-weight:900}.feedback-record-card-head strong{margin-top:5rpx;color:#94a1b2;font-size:17rpx;font-weight:650}.feedback-record-status{padding:7rpx 11rpx;border-radius:999rpx;background:#fff4dd;color:#a9792e;font-size:18rpx;line-height:1.2;font-weight:850;white-space:nowrap}.feedback-record-status.reviewed{background:#eaf2ff;color:#3478f6}.feedback-record-status.resolved{background:#e7f7f0;color:#248b75}.feedback-record-status.ignored{background:#f0f2f5;color:#778496}.feedback-record-body{margin-top:18rpx;padding-top:17rpx;border-top:2rpx solid #edf2f8;color:#536882;font-size:21rpx;line-height:1.6;font-weight:650;white-space:pre-wrap}.feedback-record-result{margin-top:18rpx;padding:18rpx;border-radius:18rpx;background:var(--gyt-primary-tint,#f7faff)}.feedback-record-result text,.feedback-record-result strong,.feedback-record-result small{display:block}.feedback-record-result text{color:var(--gyt-primary,#3478f6);font-size:18rpx;font-weight:850}.feedback-record-result strong{margin-top:8rpx;color:#425773;font-size:21rpx;line-height:1.55;font-weight:750}.feedback-record-result small{margin-top:9rpx;color:#8b99ab;font-size:17rpx}.feedback-record-progress{margin-top:16rpx;color:#8b99ab;font-size:18rpx;line-height:1.45;font-weight:650}
</style>
