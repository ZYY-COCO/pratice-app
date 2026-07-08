<template>
  <view class="page about-page" :style="themeInlineStyle">
    <view class="about-hero">
      <view class="app-mark">港</view>
      <view class="hero-copy">
        <view class="hero-eyebrow">关于我们</view>
        <view class="hero-title">港研通</view>
        <view class="hero-subtitle">面向港澳台考研用户的刷题与学习记录工具</view>
      </view>
    </view>

    <view class="notice-card">
      <view class="notice-title">当前 App Store 版本说明</view>
      <view class="notice-text">
        当前版本不提供付费数字内容、订阅、App 内购买或外部付费购买入口。若未来上线付费数字内容，将按 Apple 规则接入 App 内购买。
      </view>
    </view>

    <view class="section-card">
      <view class="section-title">帮助与支持</view>
      <view class="section-desc">遇到登录、刷题记录、错题本、收藏夹或学习报告问题时，可以通过支持页面或邮箱联系我们。</view>
      <view class="action-list">
        <button class="link-row" @tap="openSupportPage">
          <view class="link-icon support">?</view>
          <view class="link-copy">
            <view class="link-title">帮助与支持</view>
            <view class="link-subtitle">打开线上支持页面</view>
          </view>
          <view class="link-arrow">›</view>
        </button>
        <button class="link-row" @tap="copyEmail">
          <view class="link-icon mail">@</view>
          <view class="link-copy">
            <view class="link-title">联系邮箱</view>
            <view class="link-subtitle">{{ supportEmail }}</view>
          </view>
          <view class="link-arrow">复制</view>
        </button>
      </view>
    </view>

    <view class="section-card">
      <view class="section-title">隐私与数据</view>
      <view class="section-desc">你可以查看隐私政策，了解账号信息、学习记录和反馈数据的使用方式。</view>
      <view class="action-list">
        <button class="link-row" @tap="openPrivacyPage">
          <view class="link-icon privacy">锁</view>
          <view class="link-copy">
            <view class="link-title">隐私政策</view>
            <view class="link-subtitle">查看线上隐私政策</view>
          </view>
          <view class="link-arrow">›</view>
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
    </view>
  </view>
</template>

<script setup>
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const supportEmail = '2982326925@qq.com'
const supportUrl = 'https://www.gangyantong.com/support.html'
const privacyUrl = 'https://www.gangyantong.com/privacy.html'

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

.notice-card,
.section-card {
  margin-top: 22rpx;
  padding: 28rpx;
  border-radius: 26rpx;
  border: 2rpx solid #e7edf7;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 38rpx rgba(25, 48, 89, 0.07);
}

.notice-card {
  border-color: #d7e5ff;
  background: #f4f8ff;
}

.notice-title,
.section-title {
  color: #101828;
  font-size: 30rpx;
  line-height: 1.3;
  font-weight: 950;
}

.notice-text,
.section-desc {
  margin-top: 12rpx;
  color: #5f6b7d;
  font-size: 25rpx;
  line-height: 1.7;
  font-weight: 650;
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
