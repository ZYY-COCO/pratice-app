<template>
  <view class="community-report-page" :style="themeInlineStyle">
    <AppPageHeader title="内容举报" subtitle="平台将核实原内容与处理记录" @back="goBack" />

    <scroll-view scroll-y class="community-report-scroll">
      <view class="community-report-content">
        <view class="community-report-card target-card">
          <text class="community-report-label">举报对象</text>
          <strong>{{ targetType === 'comment' ? '一条评论' : '一篇帖子' }}</strong>
          <view class="community-report-target-title">{{ targetTitle || '研圈内容' }}</view>
          <text>平台会关联原内容与处理记录进行核实。</text>
        </view>

        <view class="community-report-card">
          <view class="community-report-heading"><text>举报原因</text><small>必填</small></view>
          <picker mode="selector" :range="reasonOptions" :value="reasonIndex" @change="selectReason">
            <view class="community-report-picker" :class="{ placeholder: !reason }">
              <text>{{ reason || '请选择举报原因' }}</text><view class="community-report-picker-arrow" aria-hidden="true"></view>
            </view>
          </picker>
        </view>

        <view class="community-report-card">
          <view class="community-report-heading"><text>补充说明</text><small>10—500 字</small></view>
          <textarea
            v-model="content"
            maxlength="500"
            placeholder="请说明具体问题、出现位置和经过，便于平台核实。"
            placeholder-class="community-report-placeholder"
          />
          <view class="community-report-count" :class="{ invalid: content.trim().length && content.trim().length < 10 }">{{ content.trim().length }} / 500</view>
        </view>

        <view class="community-report-notice">提交后可在“我的举报”查看处理状态和平台结论。请勿提交无关内容或他人隐私。</view>
      </view>
    </scroll-view>

    <view class="community-report-footer"><button :disabled="!canSubmit" :loading="submitting" @tap="submit">{{ submitting ? '正在提交' : '提交举报' }}</button></view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { createCommunityCommentReport, createCommunityPostReport } from '../../api/community'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const postId = ref('')
const commentId = ref('')
const targetTitle = ref('')
const targetType = computed(() => commentId.value ? 'comment' : 'post')
const reason = ref('')
const content = ref('')
const submitting = ref(false)
const themeInlineStyle = buildThemeStyle(getStoredThemeKey())

const postReasons = ['虚假或误导信息', '广告或引流', '骚扰、辱骂或不当言行', '泄露隐私', '违规交易或收费', '其他问题']
const commentReasons = ['骚扰、辱骂或不当言行', '广告或引流', '虚假或误导信息', '泄露隐私', '其他问题']
const reasonOptions = computed(() => targetType.value === 'comment' ? commentReasons : postReasons)
const reasonIndex = computed(() => Math.max(0, reasonOptions.value.indexOf(reason.value)))
const canSubmit = computed(() => Boolean(postId.value && reason.value && content.value.trim().length >= 10 && !submitting.value))

onLoad((options) => {
  postId.value = String(options?.postId || '')
  commentId.value = String(options?.commentId || '')
  targetTitle.value = decodeOption(options?.title)
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  if (!postId.value) {
    uni.showToast({ title: '未找到要举报的内容', icon: 'none' })
  }
})

function decodeOption(value) {
  try { return decodeURIComponent(String(value || '')) } catch (error) { return String(value || '') }
}

function selectReason(event) {
  reason.value = reasonOptions.value[Number(event?.detail?.value || 0)] || ''
}

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    const payload = { reason: reason.value, content: content.value.trim() }
    if (commentId.value) {
      await createCommunityCommentReport(postId.value, commentId.value, payload)
    } else {
      await createCommunityPostReport(postId.value, payload)
    }
    uni.showToast({ title: '举报已提交', icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/circle/community-reports' })
    }, 350)
  } catch (error) {
    uni.showToast({ title: error?.detail || '举报提交失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  const reportQuery = [
    `postId=${encodeURIComponent(postId.value)}`,
    commentId.value ? `commentId=${encodeURIComponent(commentId.value)}` : '',
    `title=${encodeURIComponent(targetTitle.value)}`
  ].filter(Boolean).join('&')
  uni.reLaunch({
    url: `/pages/login/index?redirect=${encodeURIComponent(`/pages/circle/community-report?${reportQuery}`)}`
  })
}

function goBack() {
  uni.navigateBack({ fail() { uni.reLaunch({ url: '/pages/home/index?tab=circle&section=community&communityTab=chat' }) } })
}
</script>

<style scoped>
.community-report-page{height:100vh;height:100dvh;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f4f8ff);color:#2a3d59}.community-report-footer button::after{border:0}.community-report-scroll{min-height:0;flex:1}.community-report-content{padding:24rpx}.community-report-card{margin-bottom:18rpx;padding:26rpx;border:2rpx solid var(--gyt-primary-border,#dbe7fb);border-radius:26rpx;background:var(--gyt-panel-bg,#fff);box-shadow:0 12rpx 30rpx rgba(43,73,112,.05)}.target-card strong,.target-card text{display:block}.community-report-label{color:var(--gyt-primary,#3478f6);font-size:19rpx;font-weight:850}.target-card strong{margin-top:10rpx;font-size:27rpx}.community-report-target-title{margin-top:10rpx;overflow:hidden;color:#5b6f88;font-size:21rpx;line-height:1.45;text-overflow:ellipsis;white-space:nowrap}.target-card>text:last-child{margin-top:10rpx;color:#8b9aae;font-size:19rpx;line-height:1.5}.community-report-heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:14rpx;font-size:24rpx;font-weight:850}.community-report-heading small{color:#98a7b8;font-size:18rpx}.community-report-picker{height:76rpx;padding:0 18rpx;display:flex;align-items:center;justify-content:space-between;border:2rpx solid var(--gyt-primary-border,#e1e9f8);border-radius:18rpx;background:var(--gyt-primary-tint,#fbfdff);color:#334965;font-size:22rpx}.community-report-picker.placeholder{color:#a3b0c0}.community-report-picker-arrow{width:14rpx;height:14rpx;margin:0 4rpx 7rpx 12rpx;border-right:3rpx solid currentColor;border-bottom:3rpx solid currentColor;color:#8293aa;transform:rotate(45deg);flex:none}.community-report-card textarea{width:100%;min-height:226rpx;padding:18rpx;box-sizing:border-box;border:2rpx solid var(--gyt-primary-border,#e1e9f8);border-radius:18rpx;background:var(--gyt-primary-tint,#fbfdff);color:#334965;font-size:22rpx;line-height:1.55}.community-report-placeholder{color:#a3b0c0}.community-report-count{margin-top:8rpx;color:#9ba9ba;text-align:right;font-size:18rpx}.community-report-count.invalid{color:#d86d5e}.community-report-notice{padding:4rpx 8rpx 130rpx;color:#8a99ab;font-size:19rpx;line-height:1.6}.community-report-footer{padding:16rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));border-top:2rpx solid var(--gyt-primary-border,#dbe7fb);background:var(--gyt-panel-bg,#fff)}.community-report-footer button{width:100%;height:76rpx;margin:0;border:0;border-radius:20rpx;background:var(--gyt-primary-gradient,#3478f6);color:#fff;display:flex;align-items:center;justify-content:center;font-size:24rpx;line-height:1.2;font-weight:900}.community-report-footer button[disabled]{background:#b9c6d8}
</style>
