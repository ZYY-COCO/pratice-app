<template>
  <view class="page access-page" :style="themeInlineStyle">
    <view class="access-hero">
      <view class="hero-tag">免费开放</view>
      <view class="hero-title">学习功能说明</view>
      <view class="hero-subtitle">
        当前 App Store 版本不提供付费数字内容、订阅、App 内购买或外部支付入口。登录后可免费使用当前已开放的刷题、复盘和学习记录功能。
      </view>
    </view>

    <SectionCard title="当前可用功能" subtitle="以下学习工具均为当前版本免费开放内容。">
      <view class="feature-list">
        <view v-for="item in freeFeatures" :key="item.title" class="feature-row">
          <view class="feature-icon" :class="item.tone">{{ item.icon }}</view>
          <view class="feature-copy">
            <view class="feature-title">{{ item.title }}</view>
            <view class="feature-desc">{{ item.desc }}</view>
          </view>
        </view>
      </view>
    </SectionCard>

    <SectionCard title="支持与反馈" subtitle="遇到账号、刷题记录、错题本或学习报告问题时，可通过以下方式联系我们。">
      <view class="support-list">
        <button class="support-row" @tap="openSupportPage">
          <view>
            <view class="support-title">帮助与支持页面</view>
            <view class="support-desc">查看常见问题、联系方式和账号数据说明</view>
          </view>
          <view class="support-arrow">›</view>
        </button>
        <button class="support-row" @tap="openPrivacyPage">
          <view>
            <view class="support-title">隐私政策</view>
            <view class="support-desc">了解账号信息、学习记录和反馈数据的使用方式</view>
          </view>
          <view class="support-arrow">›</view>
        </button>
        <button class="support-row" @tap="copyEmail">
          <view>
            <view class="support-title">联系邮箱</view>
            <view class="support-desc">{{ supportEmail }}</view>
          </view>
          <view class="support-copy">复制</view>
        </button>
      </view>
    </SectionCard>

    <!-- #ifdef H5 -->
    <IcpFooter />
    <!-- #endif -->
  </view>
</template>

<script setup>
import IcpFooter from '../../components/IcpFooter.vue'
import SectionCard from '../../components/SectionCard.vue'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const supportEmail = '2982326925@qq.com'
const supportUrl = 'https://www.gangyantong.com/support.html'
const privacyUrl = 'https://www.gangyantong.com/privacy.html'

const freeFeatures = [
  {
    title: '专项刷题',
    desc: '按科目、模块和考点进行练习，帮助用户持续推进备考。',
    icon: '题',
    tone: 'blue'
  },
  {
    title: '错题复盘',
    desc: '记录错题、收藏和练习历史，便于回看薄弱点。',
    icon: '复',
    tone: 'green'
  },
  {
    title: '学习报告',
    desc: '根据练习记录展示正确率、薄弱模块和训练建议。',
    icon: '报',
    tone: 'purple'
  },
  {
    title: 'AI 专项练习',
    desc: '登录后可按知识点生成专项练习内容，用于巩固学习。',
    icon: 'AI',
    tone: 'orange'
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
.access-page {
  padding-bottom: calc(env(safe-area-inset-bottom) + 48rpx);
}

.access-hero {
  padding: 34rpx 30rpx 32rpx;
  border-radius: 32rpx;
  background:
    radial-gradient(circle at 88% 10%, rgba(52, 120, 246, 0.24), transparent 30%),
    linear-gradient(135deg, #ffffff 0%, #f4f8ff 100%);
  border: 2rpx solid #dbe8ff;
  box-shadow: 0 18rpx 42rpx rgba(25, 48, 89, 0.08);
}

.hero-tag {
  display: inline-flex;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: #eafbf1;
  color: #16a34a;
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 900;
}

.hero-title {
  margin-top: 20rpx;
  color: #101828;
  font-size: 42rpx;
  line-height: 1.2;
  font-weight: 950;
}

.hero-subtitle {
  margin-top: 14rpx;
  color: #5f6b7d;
  font-size: 24rpx;
  line-height: 1.65;
  font-weight: 650;
}

.feature-list,
.support-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.feature-row {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: #f8fbff;
  border: 2rpx solid #edf2fb;
}

.feature-icon {
  width: 54rpx;
  height: 54rpx;
  flex: 0 0 54rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 23rpx;
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

.feature-icon.orange {
  background: #fff4e5;
  color: #f59e0b;
}

.feature-copy {
  flex: 1;
  min-width: 0;
}

.feature-title {
  color: #101828;
  font-size: 25rpx;
  line-height: 1.35;
  font-weight: 900;
}

.feature-desc {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.5;
}

.support-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  min-height: 104rpx;
  margin: 0;
  padding: 20rpx 0;
  border: 0;
  border-bottom: 2rpx solid #edf1f7;
  border-radius: 0;
  background: transparent;
  text-align: left;
}

.support-row:last-child {
  border-bottom: 0;
}

.support-title {
  color: #172033;
  font-size: 25rpx;
  line-height: 1.35;
  font-weight: 900;
}

.support-desc {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.45;
}

.support-arrow {
  color: #98a2b3;
  font-size: 42rpx;
  font-weight: 800;
}

.support-copy {
  color: var(--gyt-primary, #3478f6);
  font-size: 22rpx;
  font-weight: 900;
}
</style>
