<template>
  <view class="community-appeal-page" :style="themeInlineStyle">
    <AppPageHeader title="提交内容申诉" subtitle="补充事实与上下文供平台复核" @back="goBack" />

    <scroll-view scroll-y class="community-appeal-scroll">
      <view class="community-appeal-content">
        <view class="community-appeal-card target-card">
          <text class="community-appeal-label">申诉对象</text>
          <strong>{{ targetType === 'comment' ? '一条被处理的评论' : '一篇被处理的帖子' }}</strong>
          <view class="community-appeal-target-title">{{ targetTitle || '研圈内容' }}</view>
          <text>平台会结合原内容、此前处置说明和本次申诉重新核实。</text>
        </view>

        <view class="community-appeal-card">
          <view class="community-appeal-heading"><text>申诉说明</text><small>10—500 字</small></view>
          <textarea
            v-model="content"
            maxlength="500"
            placeholder="请说明你认为原处置需要复核的具体事实、补充信息或上下文。"
            placeholder-class="community-appeal-placeholder"
          />
          <view class="community-appeal-count" :class="{ invalid: content.trim().length && content.trim().length < 10 }">{{ content.trim().length }} / 500</view>
        </view>

        <view class="community-appeal-notice">提交后可在“我的举报”的“内容处理”中查看平台处理进度与最终说明。每条被下架内容仅可提交一次申诉。</view>
      </view>
    </scroll-view>

    <view class="community-appeal-footer"><button :disabled="!canSubmit" :loading="submitting" @tap="submit">{{ submitting ? '正在提交' : '提交申诉' }}</button></view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { createCommunityModerationAppeal } from '../../api/community'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const targetType = ref('post')
const targetId = ref('')
const targetTitle = ref('')
const content = ref('')
const submitting = ref(false)
const themeInlineStyle = computed(() => buildThemeStyle(getStoredThemeKey()))
const canSubmit = computed(() => Boolean(targetId.value && content.value.trim().length >= 10 && !submitting.value))

onLoad((options) => {
  const incomingType = String(options?.targetType || 'post')
  targetType.value = incomingType === 'comment' ? 'comment' : 'post'
  targetId.value = String(options?.targetId || '')
  targetTitle.value = decodeOption(options?.title)
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  if (!targetId.value) {
    uni.showToast({ title: '未找到要申诉的内容', icon: 'none' })
  }
})

function decodeOption(value) {
  try {
    return decodeURIComponent(String(value || ''))
  } catch (error) {
    return String(value || '')
  }
}

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    await createCommunityModerationAppeal(targetType.value, targetId.value, { content: content.value.trim() })
    uni.showToast({ title: '申诉已提交', icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/circle/community-reports?tab=content' })
    }, 350)
  } catch (error) {
    uni.showToast({ title: error?.detail || '申诉提交失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  const targetQuery = [
    `targetType=${encodeURIComponent(targetType.value)}`,
    `targetId=${encodeURIComponent(targetId.value)}`,
    `title=${encodeURIComponent(targetTitle.value)}`
  ].join('&')
  uni.reLaunch({
    url: `/pages/login/index?redirect=${encodeURIComponent(`/pages/circle/community-appeal?${targetQuery}`)}`
  })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/circle/community-reports?tab=content' })
    }
  })
}
</script>

<style scoped>
.community-appeal-page{height:100vh;height:100dvh;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f4f8ff);color:#2a3d59}.community-appeal-footer button::after{border:0}.community-appeal-scroll{min-height:0;flex:1}.community-appeal-content{padding:24rpx}.community-appeal-card{margin-bottom:18rpx;padding:26rpx;border:2rpx solid var(--gyt-primary-border,#dbe7fb);border-radius:26rpx;background:var(--gyt-panel-bg,#fff);box-shadow:0 12rpx 30rpx rgba(43,73,112,.05)}.target-card strong,.target-card text{display:block}.community-appeal-label{color:var(--gyt-primary,#3478f6);font-size:19rpx;font-weight:850}.target-card strong{margin-top:10rpx;font-size:27rpx}.community-appeal-target-title{margin-top:10rpx;overflow:hidden;color:#5b6f88;font-size:21rpx;line-height:1.45;text-overflow:ellipsis;white-space:nowrap}.target-card>text:last-child{margin-top:10rpx;color:#8b9aae;font-size:19rpx;line-height:1.5}.community-appeal-heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:14rpx;font-size:24rpx;font-weight:850}.community-appeal-heading small{color:#98a7b8;font-size:18rpx}.community-appeal-card textarea{width:100%;min-height:226rpx;padding:18rpx;box-sizing:border-box;border:2rpx solid #e1e9f8;border-radius:18rpx;background:#fbfdff;color:#334965;font-size:22rpx;line-height:1.55}.community-appeal-placeholder{color:#a3b0c0}.community-appeal-count{margin-top:8rpx;color:#9ba9ba;text-align:right;font-size:18rpx}.community-appeal-count.invalid{color:#d86d5e}.community-appeal-notice{padding:4rpx 8rpx 130rpx;color:#8a99ab;font-size:19rpx;line-height:1.6}.community-appeal-footer{padding:16rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));border-top:2rpx solid var(--gyt-primary-border,#dbe7fb);background:var(--gyt-panel-bg,#fff)}.community-appeal-footer button{width:100%;height:76rpx;margin:0;border:0;border-radius:20rpx;background:var(--gyt-primary-gradient,#3478f6);color:#fff;display:flex;align-items:center;justify-content:center;font-size:24rpx;line-height:1.2;font-weight:900}.community-appeal-footer button[disabled]{background:#b9c6d8}
</style>
