<template>
  <view class="page pro-page">
    <template v-if="isProMember">
      <view class="member-hero">
        <view class="member-hero-top">
          <view class="member-hero-copy">
            <view class="hero-tag active">Pro 会员 · 已开通</view>
            <view class="member-hero-title">{{ memberName }}的会员中心</view>
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

      <SectionCard title="会员服务" subtitle="支付接入后，这里会显示订单、续费和发票等服务入口。">
        <view class="service-list">
          <view class="service-row" @tap="showComingSoon('开通记录将在支付接入后开放')">
            <view>
              <view class="service-title">开通记录</view>
              <view class="service-desc">查看会员订单与有效期变化</view>
            </view>
            <view class="service-arrow">›</view>
          </view>
          <view class="service-row" @tap="showComingSoon('续费管理将在支付接入后开放')">
            <view>
              <view class="service-title">续费管理</view>
              <view class="service-desc">管理会员续费、升级与到期提醒</view>
            </view>
            <view class="service-arrow">›</view>
          </view>
        </view>
      </SectionCard>
    </template>

    <template v-else>
      <SectionCard title="免费版 / Pro 版差异" subtitle="当前不限制功能，只用于验证用户是否认可会员价值。">
        <view class="compare-grid">
          <view class="compare-card free">
            <view class="plan-title">免费版</view>
            <view v-for="item in freeFeatures" :key="item" class="feature-line">{{ item }}</view>
          </view>
          <view class="compare-card pro">
            <view class="plan-title">Pro 会员</view>
            <view v-for="item in proFeatures" :key="item" class="feature-line strong">{{ item }}</view>
          </view>
        </view>
      </SectionCard>

      <SectionCard title="会员套餐" subtitle="真实支付暂未开放，现在只记录内测开通意向。">
        <view class="price-list">
          <view v-for="item in pricePlans" :key="item.name" class="price-card" :class="{ hot: item.hot }">
            <view class="price-content">
              <view class="price-name-row">
                <view class="price-name">{{ item.name }}</view>
                <view v-if="item.hot" class="price-badge">推荐</view>
              </view>
              <view class="price-desc">{{ item.desc }}</view>
              <view class="price-note">{{ item.note }}</view>
            </view>
            <view class="price-side">
              <view class="price-value">{{ item.price }}</view>
              <button
                class="price-action-btn"
                :disabled="creatingOrderCode === item.code"
                @tap.stop="handleCreateOrder(item)"
              >
                {{ creatingOrderCode === item.code ? '记录中' : '内测登记' }}
              </button>
            </view>
          </view>
        </view>
      </SectionCard>
    </template>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import SectionCard from '../../components/SectionCard.vue'
import { createMembershipOrder, fetchMembershipPlans, fetchMembershipStatus } from '../../api/membership'
import { getAuthUser, updateAuthUser } from '../../utils/auth'
import { getUserDisplayName } from '../../utils/userDisplay'

const authUser = ref(getAuthUser())
const creatingOrderCode = ref('')

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

const pricePlans = ref([
  { code: 'pro_monthly', name: '月卡', price: '9.9元/月', desc: '适合短期试用 Pro 功能', note: '先体验学习报告和推荐训练', hot: false },
  { code: 'pro_quarterly', name: '季卡', price: '24.9元/季', desc: '适合一轮系统复习', note: '覆盖阶段复习和持续错题复盘', hot: true }
])

const unlockedBenefits = [
  '收藏、错题和练习记录长期保存',
  '根据薄弱点智能生成题目与解析',
  '查看更详细的正确率与能力分析',
  '自动推荐更适合你的训练内容'
]

const isProMember = computed(() => getMembershipStatus(authUser.value) === 'active')
const memberName = computed(() => getUserDisplayName(authUser.value, '你'))
const membershipExpiresAt = computed(() => getMembershipExpiresAt(authUser.value))
const memberUntilText = computed(() =>
  membershipExpiresAt.value
    ? `会员权益已开通，有效期至 ${membershipExpiresAt.value}。`
    : '会员权益已开通，可以使用 Pro 专属学习功能。'
)

onShow(() => {
  authUser.value = getAuthUser()
  loadMembershipPlans()
  refreshMembershipStatus()
})

async function loadMembershipPlans() {
  try {
    const plans = await fetchMembershipPlans()
    if (!Array.isArray(plans) || !plans.length) return
    pricePlans.value = plans.map((item) => ({
      code: item.code,
      name: item.name,
      price: item.price_label,
      desc: item.description,
      note: item.code === 'pro_quarterly' ? '覆盖阶段复习和持续错题复盘' : '先体验学习报告和推荐训练',
      hot: item.code === 'pro_quarterly'
    }))
  } catch (error) {
    // Keep local fallback plan display when the backend is unavailable.
  }
}

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

async function handleCreateOrder(plan) {
  if (!uni.getStorageSync('accessToken')) {
    uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/pro/index')}` })
    return
  }
  if (!plan?.code || creatingOrderCode.value) return

  creatingOrderCode.value = plan.code
  try {
    const order = await createMembershipOrder({ plan_code: plan.code })
    uni.showModal({
      title: '内测登记已记录',
      content: `套餐：${plan.name}\n价格：${plan.price}\n登记号：${order.provider_order_id}\n\n当前不会跳转真实支付，后续接入支付渠道后再开放开通。`,
      confirmText: '知道了',
      showCancel: false
    })
  } catch (error) {
    uni.showToast({ title: error?.detail || '创建订单失败，请稍后重试', icon: 'none' })
  } finally {
    creatingOrderCode.value = ''
  }
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
  border-color: rgba(37, 99, 235, 0.35);
  background: #f4f8ff;
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
  color: #2563eb;
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
  border-color: #2563eb;
  background: linear-gradient(135deg, #ffffff, #edf4ff);
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
  background: #2563eb;
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
  background: linear-gradient(135deg, #2563eb, #4f86ff);
  color: #ffffff;
  font-size: 23rpx;
  line-height: 58rpx;
  font-weight: 900;
  box-shadow: 0 10rpx 22rpx rgba(37, 99, 235, 0.18);
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
