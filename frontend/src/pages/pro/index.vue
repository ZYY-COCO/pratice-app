<template>
  <view class="page pro-page" :style="themeInlineStyle">
    <template v-if="isProMember">
      <view class="member-hero">
        <view class="member-hero-top">
          <view class="member-hero-copy">
            <view class="hero-tag active">学习权益 · 已开通</view>
            <view class="member-hero-title">{{ memberName }}的学习权益</view>
            <view class="member-hero-subtitle">{{ memberUntilText }}</view>
          </view>
          <view class="member-badge">PRO</view>
        </view>

        <view class="member-meta-grid">
          <view class="member-meta-item">
            <view class="member-meta-label">权益状态</view>
            <view class="member-meta-value">使用中</view>
          </view>
          <view class="member-meta-item">
            <view class="member-meta-label">AI 功能</view>
            <view class="member-meta-value">已解锁</view>
          </view>
        </view>
      </view>

      <SectionCard title="已解锁权益" subtitle="这些能力会随会员状态保持可用。">
        <view class="unlock-list">
          <view v-for="item in unlockedBenefits" :key="item" class="unlock-row">
            <view class="unlock-check">✓</view>
            <view class="unlock-text">{{ item }}</view>
          </view>
        </view>
      </SectionCard>

      <SectionCard title="会员服务" subtitle="当前 App Store 版本暂不开放续费、订单或发票服务。">
        <view class="service-list">
          <view class="service-row" @tap="showComingSoon('服务记录暂未开放')">
            <view>
              <view class="service-title">服务记录</view>
              <view class="service-desc">后续版本会展示权益变化与服务说明</view>
            </view>
            <view class="service-arrow">›</view>
          </view>
          <view class="service-row" @tap="showComingSoon('续期管理暂未开放')">
            <view>
              <view class="service-title">权益说明</view>
              <view class="service-desc">查看当前版本已开放的学习能力</view>
            </view>
            <view class="service-arrow">›</view>
          </view>
        </view>
      </SectionCard>
    </template>

    <template v-else>
      <SectionCard title="学习功能预览" subtitle="当前 App Store 版本专注刷题与学习记录体验。">
        <view class="compare-grid">
          <view class="compare-card free">
            <view class="plan-title">当前开放</view>
            <view v-for="item in freeFeatures" :key="item" class="feature-line">{{ item }}</view>
          </view>
          <view class="compare-card pro">
            <view class="plan-title">后续增强</view>
            <view v-for="item in proFeatures" :key="item" class="feature-line strong">{{ item }}</view>
          </view>
        </view>
      </SectionCard>

      <SectionCard title="版本说明" subtitle="第一版先聚焦刷题、错题和学习记录体验。">
        <view class="service-list">
          <view v-for="item in releaseNotes" :key="item.title" class="service-row">
            <view>
              <view class="service-title">{{ item.title }}</view>
              <view class="service-desc">{{ item.desc }}</view>
            </view>
            <view class="service-arrow">✓</view>
          </view>
        </view>
      </SectionCard>
    </template>

    <!-- #ifdef H5 -->
    <IcpFooter />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import IcpFooter from '../../components/IcpFooter.vue'
import SectionCard from '../../components/SectionCard.vue'
import { fetchMembershipStatus } from '../../api/membership'
import { getAuthUser, updateAuthUser } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'
import { getUserDisplayName } from '../../utils/userDisplay'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const authUser = ref(getAuthUser())

const freeFeatures = [
  '注册登录与基础刷题',
  '专项刷题 / 综合刷题',
  '基础错题本',
  '基础能力统计'
]

const proFeatures = [
  'AI 薄弱诊断',
  '错题同类加练',
  '每日训练计划',
  '每周提分报告'
]

const unlockedBenefits = [
  '收藏、错题和练习记录长期保存',
  '根据薄弱点智能生成题目与解析',
  '查看更详细的正确率与能力分析',
  '自动推荐更适合你的训练内容'
]

const releaseNotes = [
  { title: '无收费入口', desc: '当前版本不展示套餐或收费信息。' },
  { title: '学习数据同步', desc: '登录后可同步刷题记录、收藏和错题本。' },
  { title: '后续功能预览', desc: '增强学习报告和训练建议会在后续版本逐步开放。' }
]

const isProMember = computed(() => getMembershipStatus(authUser.value) === 'active')
const memberName = computed(() => getUserDisplayName(authUser.value, '你'))
const membershipExpiresAt = computed(() => getMembershipExpiresAt(authUser.value))
const memberUntilText = computed(() =>
  membershipExpiresAt.value
    ? `学习权益已开通，有效期至 ${membershipExpiresAt.value}。`
    : '学习权益已开通，可以使用当前版本的增强学习功能。'
)

onShow(() => {
  authUser.value = getAuthUser()
  refreshMembershipStatus()
})

async function refreshMembershipStatus() {
  if (!uni.getStorageSync('accessToken')) return
  try {
    const membership = await fetchMembershipStatus()
    const nextUser = updateAuthUser(membership)
    if (nextUser) {
      authUser.value = nextUser
    }
  } catch (error) {
    // The membership migration may not be applied yet; keep the cached user state.
  }
}

function showComingSoon(title) {
  uni.showToast({ title, icon: 'none' })
}

function getMembershipStatus(user) {
  const status = String(
    user?.membership_status ||
    user?.pro_status ||
    user?.subscription_status ||
    user?.vip_status ||
    uni.getStorageSync('proMembershipStatus') ||
    ''
  ).toLowerCase()
  if (user?.membership_active || user?.is_pro || user?.isPro || user?.pro_member || status === 'active' || status === 'paid') {
    return 'active'
  }
  return 'inactive'
}

function getMembershipExpiresAt(user) {
  const rawValue = user?.membership_expires_at || user?.pro_expires_at || user?.vip_expires_at || ''
  if (!rawValue) return ''
  const date = new Date(rawValue)
  if (Number.isNaN(date.getTime())) {
    return String(rawValue).slice(0, 10)
  }
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.pro-page {
  padding-bottom: calc(env(safe-area-inset-bottom) + 48rpx);
}

.member-hero {
  padding: 34rpx 30rpx 28rpx;
  border-radius: 36rpx;
  background:
    radial-gradient(circle at 82% 14%, rgba(52, 211, 153, 0.28), transparent 30%),
    linear-gradient(135deg, #0f172a 0%, #14532d 100%);
  color: #ffffff;
  box-shadow: 0 18rpx 42rpx rgba(15, 23, 42, 0.18);
}

.member-hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.member-hero-copy {
  flex: 1;
  min-width: 0;
}

.hero-tag {
  display: inline-flex;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 800;
}

.hero-tag.active {
  background: rgba(255, 255, 255, 0.18);
}

.member-hero-title {
  margin-top: 22rpx;
  font-size: 42rpx;
  line-height: 1.25;
  font-weight: 950;
}

.member-hero-subtitle {
  margin-top: 14rpx;
  color: rgba(255, 255, 255, 0.84);
  font-size: 24rpx;
  line-height: 1.65;
  font-weight: 650;
}

.member-badge {
  width: 104rpx;
  height: 104rpx;
  flex: 0 0 104rpx;
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.16);
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 950;
}

.member-meta-grid {
  margin-top: 28rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.member-meta-item {
  padding: 18rpx 10rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.12);
  text-align: center;
}

.member-meta-label {
  color: rgba(255, 255, 255, 0.68);
  font-size: 20rpx;
  line-height: 1.3;
  font-weight: 700;
}

.member-meta-value {
  margin-top: 8rpx;
  color: #ffffff;
  font-size: 25rpx;
  line-height: 1.25;
  font-weight: 950;
}

.unlock-list,
.service-list,
.price-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.unlock-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  color: #475467;
  font-size: 24rpx;
  line-height: 1.5;
  font-weight: 750;
}

.unlock-check {
  width: 32rpx;
  height: 32rpx;
  flex: 0 0 32rpx;
  border-radius: 50%;
  background: #10b981;
  color: #ffffff;
  text-align: center;
  font-size: 20rpx;
  line-height: 32rpx;
  font-weight: 950;
}

.unlock-text {
  flex: 1;
  min-width: 0;
}

.service-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 20rpx 0;
  border-bottom: 2rpx solid #edf1f7;
}

.service-row:last-child {
  border-bottom: 0;
}

.service-title {
  color: #172033;
  font-size: 26rpx;
  line-height: 1.35;
  font-weight: 900;
}

.service-desc {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.45;
}

.service-arrow {
  color: #98a2b3;
  font-size: 42rpx;
  font-weight: 800;
}

.compare-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
}

.compare-card,
.price-card {
  padding: 22rpx;
  border-radius: 26rpx;
  border: 2rpx solid #e6ebf5;
  background: #fbfcff;
}

.compare-card.pro {
  border-color: var(--gyt-primary-shadow);
  background: var(--gyt-primary-tint);
}

.plan-title,
.price-name {
  color: #172033;
  font-size: 27rpx;
  font-weight: 900;
}

.feature-line {
  margin-top: 14rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.5;
}

.feature-line.strong {
  color: var(--gyt-primary);
  font-weight: 800;
}

.price-desc {
  margin-top: 8rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.7;
}

.price-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22rpx;
  background: #ffffff;
}

.price-card.hot {
  border-color: var(--gyt-primary);
  background: linear-gradient(135deg, #ffffff, var(--gyt-primary-soft));
}

.price-content {
  flex: 1;
  min-width: 0;
}

.price-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.price-badge {
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary);
  color: #ffffff;
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 900;
}

.price-value {
  color: #172033;
  font-size: 34rpx;
  font-weight: 900;
  white-space: nowrap;
}

.price-note {
  margin-top: 8rpx;
  color: #98a2b3;
  font-size: 21rpx;
  line-height: 1.5;
  font-weight: 700;
}

.price-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12rpx;
  flex: 0 0 auto;
}

.price-action-btn {
  min-width: 148rpx;
  min-height: 58rpx;
  margin: 0;
  padding: 0 18rpx;
  border: 0;
  border-radius: 16rpx;
  background: linear-gradient(135deg, var(--gyt-primary), var(--gyt-primary));
  color: #ffffff;
  font-size: 23rpx;
  line-height: 58rpx;
  font-weight: 900;
  box-shadow: 0 10rpx 22rpx var(--gyt-primary-shadow);
}

.price-action-btn:disabled {
  background: #e8edf7;
  color: #98a2b3;
  box-shadow: none;
}

@media (max-width: 380px) {
  .compare-grid,
  .member-meta-grid {
    grid-template-columns: 1fr;
  }

  .price-card {
    align-items: stretch;
    flex-direction: column;
  }

  .price-side {
    align-items: stretch;
  }
}
</style>
