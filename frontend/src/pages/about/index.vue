<template>
  <view class="page about-page" :style="themeInlineStyle">
    <view class="about-hero">
      <view class="app-mark">港</view>
      <view class="hero-copy">
        <view class="hero-eyebrow">关于我们</view>
        <view class="hero-title">港研通</view>
        <view class="hero-subtitle">面向港澳台考研用户的刷题、复盘与学习记录工具</view>
      </view>
    </view>

    <view class="status-card">
      <view class="status-main">
        <view class="status-kicker">当前版本</view>
        <view class="status-title">免费开放学习权益</view>
        <view class="status-desc">
          当前 App Store 版本不提供付费数字内容、订阅、App 内购买或外部付费购买入口。现阶段所有用户均可免费使用学习权益。
        </view>
      </view>
      <view class="status-pill">免费</view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <view class="section-title">我们提供什么</view>
          <view class="section-desc">围绕备考流程，把练习、记录和复盘集中在一个移动端学习闭环中。</view>
        </view>
      </view>
      <view class="feature-grid">
        <view v-for="item in features" :key="item.title" class="feature-item">
          <view class="feature-icon" :class="item.tone">{{ item.icon }}</view>
          <view class="feature-copy">
            <view class="feature-title">{{ item.title }}</view>
            <view class="feature-desc">{{ item.desc }}</view>
          </view>
        </view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-title">帮助与反馈</view>
      <view class="section-desc">
        你可以在这里提交题目质量、刷题体验、账号登录或功能建议。反馈会进入后台处理列表，便于我们持续改进。
      </view>
      <view class="feedback-form-area">
        <BetaFeedbackForm source-page="about" />
      </view>
    </view>

    <view class="section-card">
      <view class="section-title">支持与隐私</view>
      <view class="section-desc">审核、用户支持和隐私说明集中放在这里，方便用户和 App Review 快速找到。</view>
      <view class="action-list">
        <button class="link-row" @tap="openSupportPage">
          <view class="link-icon support">?</view>
          <view class="link-copy">
            <view class="link-title">帮助与支持页面</view>
            <view class="link-subtitle">常见问题、支持邮箱和账号数据说明</view>
          </view>
          <view class="link-arrow">›</view>
        </button>
        <button class="link-row" @tap="openPrivacyPage">
          <view class="link-icon privacy">锁</view>
          <view class="link-copy">
            <view class="link-title">隐私政策</view>
            <view class="link-subtitle">了解账号信息、学习记录和反馈数据的使用方式</view>
          </view>
          <view class="link-arrow">›</view>
        </button>
        <button class="link-row" @tap="copyEmail">
          <view class="link-icon mail">@</view>
          <view class="link-copy">
            <view class="link-title">联系邮箱</view>
            <view class="link-subtitle">{{ supportEmail }}</view>
          </view>
          <view class="link-arrow copy">复制</view>
        </button>
      </view>
    </view>

    <view class="section-card compact">
      <view class="info-row">
        <text class="info-label">应用名称</text>
        <text class="info-value">港研通</text>
      </view>
      <view class="info-row">
        <text class="info-label">版本</text>
        <text class="info-value">1.0</text>
      </view>
      <view class="info-row">
        <text class="info-label">支持网址</text>
        <text class="info-value">gangyantong.com/support.html</text>
      </view>
      <view class="info-row">
        <text class="info-label">隐私政策</text>
        <text class="info-value">gangyantong.com/privacy.html</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import BetaFeedbackForm from '../../components/BetaFeedbackForm.vue'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const supportEmail = '2982326925@qq.com'
const supportUrl = 'https://www.gangyantong.com/support.html'
const privacyUrl = 'https://www.gangyantong.com/privacy.html'

const features = [
  {
    title: '专项刷题',
    desc: '按科目和模块进行练习，帮助用户稳定推进备考。',
    icon: '题',
    tone: 'blue'
  },
  {
    title: '错题复盘',
    desc: '沉淀错题、收藏和练习历史，方便回看薄弱点。',
    icon: '复',
    tone: 'green'
  },
  {
    title: '学习报告',
    desc: '根据练习记录展示能力概览和后续训练方向。',
    icon: '报',
    tone: 'purple'
  }
]

function openExternalUrl(url) {
  // #ifdef APP-PLUS
  if (typeof plus !== 'undefined' && plus?.runtime?.openURL) {
    plus.runtime.openURL(url)
    return
  }
  // #endif

  // #ifdef H5
  if (typeof window !== 'undefined') {
    window.location.href = url
    return
  }
  // #endif

  uni.setClipboardData({
    data: url,
    success() {
      uni.showToast({ title: '链接已复制', icon: 'none' })
    }
  })
}

function openSupportPage() {
  openExternalUrl(supportUrl)
}

function openPrivacyPage() {
  openExternalUrl(privacyUrl)
}

function copyEmail() {
  uni.setClipboardData({
    data: supportEmail,
    success() {
      uni.showToast({ title: '邮箱已复制', icon: 'none' })
    }
  })
}
</script>

<style scoped>
.about-page {
  min-height: 100vh;
  padding-bottom: calc(env(safe-area-inset-bottom) + 44rpx);
  background:
    radial-gradient(circle at 92% 0%, rgba(52, 120, 246, 0.12), transparent 30%),
    linear-gradient(180deg, #f7faff 0%, #f4f7fb 100%);
}

.about-hero {
  display: flex;
  align-items: center;
  gap: 22rpx;
  padding: 28rpx 4rpx 22rpx;
}

.app-mark {
  width: 96rpx;
  height: 96rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 96rpx;
  background: var(--gyt-primary-gradient, linear-gradient(135deg, #3478f6, #68a0ff));
  color: #ffffff;
  font-size: 44rpx;
  line-height: 1;
  font-weight: 950;
  box-shadow: 0 18rpx 38rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.22));
}

.hero-copy {
  flex: 1;
  min-width: 0;
}

.hero-eyebrow {
  color: var(--gyt-primary, #3478f6);
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 900;
}

.hero-title {
  margin-top: 6rpx;
  color: #101828;
  font-size: 42rpx;
  line-height: 1.2;
  font-weight: 950;
}

.hero-subtitle {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.45;
  font-weight: 650;
}

.status-card,
.section-card {
  margin-top: 22rpx;
  border: 2rpx solid #e7edf7;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 38rpx rgba(25, 48, 89, 0.07);
}

.status-card {
  display: flex;
  gap: 22rpx;
  align-items: flex-start;
  padding: 30rpx;
  border-radius: 30rpx;
  border-color: #d7e5ff;
  background: linear-gradient(135deg, #f4f8ff 0%, #ffffff 100%);
}

.status-main {
  flex: 1;
  min-width: 0;
}

.status-kicker {
  color: var(--gyt-primary, #3478f6);
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 900;
}

.status-title {
  margin-top: 8rpx;
  color: #101828;
  font-size: 32rpx;
  line-height: 1.3;
  font-weight: 950;
}

.status-desc {
  margin-top: 10rpx;
  color: #5f6b7d;
  font-size: 24rpx;
  line-height: 1.65;
  font-weight: 650;
}

.status-pill {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: #eafbf1;
  color: #16a34a;
  font-size: 23rpx;
  line-height: 1;
  font-weight: 950;
}

.section-card {
  padding: 28rpx;
  border-radius: 26rpx;
}

.section-title {
  color: #101828;
  font-size: 30rpx;
  line-height: 1.3;
  font-weight: 950;
}

.section-desc {
  margin-top: 12rpx;
  color: #5f6b7d;
  font-size: 25rpx;
  line-height: 1.7;
  font-weight: 650;
}

.feature-grid {
  margin-top: 22rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
  min-width: 0;
  padding: 20rpx;
  border-radius: 22rpx;
  background: #f8fbff;
  border: 2rpx solid #edf2fb;
}

.feature-icon {
  width: 54rpx;
  height: 54rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 54rpx;
  font-size: 24rpx;
  line-height: 1;
  font-weight: 950;
}

.feature-icon.blue {
  background: #edf4ff;
  color: #3478f6;
}

.feature-icon.green {
  background: #eafbf1;
  color: #16a34a;
}

.feature-icon.purple {
  background: #f0edff;
  color: #6d5dfc;
}

.feature-copy {
  flex: 1;
  min-width: 0;
}

.feature-title {
  color: #101828;
  font-size: 24rpx;
  line-height: 1.3;
  font-weight: 900;
}

.feature-desc {
  margin-top: 8rpx;
  color: #667085;
  font-size: 21rpx;
  line-height: 1.5;
  font-weight: 650;
}

.feedback-form-area {
  margin-top: 22rpx;
}

.action-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
}

.link-row {
  min-height: 94rpx;
  margin: 0;
  padding: 18rpx 0;
  border: 0;
  border-bottom: 2rpx solid #edf2fb;
  border-radius: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 18rpx;
  text-align: left;
}

.link-row::after {
  border: 0;
}

.link-row:last-child {
  border-bottom: 0;
}

.link-icon {
  width: 58rpx;
  height: 58rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 58rpx;
  font-size: 27rpx;
  line-height: 1;
  font-weight: 950;
}

.link-icon.support {
  background: #fff3e8;
  color: #f97316;
}

.link-icon.mail {
  background: #eafbf1;
  color: #16a34a;
}

.link-icon.privacy {
  background: #edf4ff;
  color: #3478f6;
}

.link-copy {
  flex: 1;
  min-width: 0;
}

.link-title {
  color: #101828;
  font-size: 27rpx;
  line-height: 1.3;
  font-weight: 900;
}

.link-subtitle {
  margin-top: 6rpx;
  color: #8a95a8;
  font-size: 22rpx;
  line-height: 1.35;
  font-weight: 650;
  word-break: break-all;
}

.link-arrow {
  flex: 0 0 auto;
  color: #98a2b3;
  font-size: 25rpx;
  line-height: 1;
  font-weight: 900;
}

.link-arrow.copy {
  font-size: 22rpx;
}

.section-card.compact {
  padding-top: 18rpx;
  padding-bottom: 18rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 24rpx;
  padding: 16rpx 0;
  border-bottom: 2rpx solid #edf2fb;
}

.info-row:last-child {
  border-bottom: 0;
}

.info-label {
  color: #667085;
  font-size: 24rpx;
  line-height: 1.4;
  font-weight: 700;
}

.info-value {
  min-width: 0;
  color: #101828;
  font-size: 24rpx;
  line-height: 1.4;
  font-weight: 850;
  text-align: right;
  word-break: break-all;
}
</style>
