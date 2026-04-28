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
            <view class="member-meta-label">今日建议</view>
            <view class="member-meta-value">10 题</view>
          </view>
          <view class="member-meta-item">
            <view class="member-meta-label">AI 功能</view>
            <view class="member-meta-value">已解锁</view>
          </view>
        </view>
      </view>

      <view class="member-action-grid">
        <view
          v-for="item in memberFeatureCards"
          :key="item.title"
          class="member-action-card"
          @tap="handleMemberFeature(item)"
        >
          <view class="member-action-icon" :class="item.tone">{{ item.icon }}</view>
          <view class="member-action-title">{{ item.title }}</view>
          <view class="member-action-desc">{{ item.desc }}</view>
        </view>
      </view>

      <SectionCard title="专属训练建议" subtitle="根据近期错题与正确率，优先安排更值得做的一组。">
        <view class="training-plan-card">
          <view class="plan-main">
            <view class="plan-kicker">今日推荐</view>
            <view class="member-plan-title">逻辑推理 · 判断关系</view>
            <view class="plan-desc">当前正确率偏低，建议完成一组 10 题标准提升训练，再回看错题解析。</view>
          </view>
          <button class="primary-button plan-btn" @tap="startMemberTraining">开始训练</button>
        </view>
      </SectionCard>

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
      <PageHeader
        eyebrow="Pro 功能预览"
        title="会员中心"
        subtitle="内测阶段先展示权益和定价，不接真实支付。你可以把它当作后续商业化验证页面。"
      />

      <view class="hero-card">
        <view class="hero-tag">支付准备中 · 订单骨架已接入</view>
        <view class="hero-title">把刷题结果变成下一步行动</view>
        <view class="hero-sub">
          Pro 版本计划围绕 AI 薄弱诊断、错题同类加练、每日训练计划和每周提分报告展开，帮助用户从“做题”走到“知道怎么提分”。
        </view>
        <button class="hero-btn" @tap="showPaymentClosed">查看开通方式</button>
      </view>

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

      <SectionCard title="计划开放的 Pro 能力" subtitle="先做展示，不调用真实 AI。">
        <view class="feature-list">
          <view v-for="item in previewFeatures" :key="item.title" class="preview-item">
            <view class="preview-icon">{{ item.icon }}</view>
            <view>
              <view class="preview-title">{{ item.title }}</view>
              <view class="preview-desc">{{ item.desc }}</view>
            </view>
          </view>
        </view>
      </SectionCard>

      <SectionCard title="会员套餐" subtitle="当前先创建待支付订单，正式支付渠道接入后会打开收银台。">
        <view class="price-list">
          <view v-for="item in pricePlans" :key="item.name" class="price-card" :class="{ hot: item.hot }">
            <view>
              <view class="price-name">{{ item.name }}</view>
              <view class="price-desc">{{ item.desc }}</view>
            </view>
            <view class="price-side">
              <view class="price-value">{{ item.price }}</view>
              <button
                class="price-action-btn"
                :disabled="creatingOrderCode === item.code"
                @tap.stop="handleCreateOrder(item)"
              >
                {{ creatingOrderCode === item.code ? '创建中' : '立即开通' }}
              </button>
            </view>
          </view>
        </view>
      </SectionCard>

      <SectionCard title="内测反馈" subtitle="如果你愿意付费，欢迎把原因和可接受价格反馈给开发者。">
        <view class="feedback-text">
          反馈模板：我是否愿意为 Pro 付费？最想要哪个功能？能接受的价格是多少？当前页面哪里让我不清楚？
        </view>
        <BetaFeedbackForm source-page="pro" />
        <button class="ghost-button" @tap="copyFeedbackTemplate">复制反馈模板</button>
      </SectionCard>
    </template>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import PageHeader from '../../components/PageHeader.vue'
import SectionCard from '../../components/SectionCard.vue'
import BetaFeedbackForm from '../../components/BetaFeedbackForm.vue'
import { createMembershipOrder, fetchMembershipPlans, fetchMembershipStatus } from '../../api/membership'
import { getAuthUser, updateAuthUser } from '../../utils/auth'

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

const previewFeatures = [
  {
    icon: '诊',
    title: 'AI 薄弱诊断',
    desc: '根据正确率、错题标签和近期训练记录，生成更像老师点评的薄弱项总结。'
  },
  {
    icon: '练',
    title: '错题同类加练',
    desc: '围绕错题的 module / submodule 自动推荐同类题，减少“看懂解析但下次还错”。'
  },
  {
    icon: '日',
    title: '每日训练计划',
    desc: '每天给出 10-20 题的小任务，优先覆盖最低正确率知识点。'
  },
  {
    icon: '周',
    title: '每周提分报告',
    desc: '按周总结刷题量、正确率变化、薄弱项变化和下周训练重点。'
  }
]

const pricePlans = ref([
  { code: 'pro_monthly', name: '月卡', price: '9.9元/月', desc: '适合短期试用 Pro 功能', hot: false },
  { code: 'pro_quarterly', name: '季卡', price: '24.9元/季', desc: '适合一轮系统复习', hot: true }
])

const memberFeatureCards = [
  { icon: 'AI', title: 'AI 生题', desc: '按薄弱点生成专项题', tone: 'green', action: 'ai' },
  { icon: '析', title: '完整报告', desc: '查看更细能力分析', tone: 'blue', action: 'report' },
  { icon: '练', title: '专属训练', desc: '自动匹配训练内容', tone: 'purple', action: 'training' },
  { icon: '∞', title: '长期保存', desc: '收藏与记录更安心', tone: 'orange', action: 'storage' }
]

const unlockedBenefits = [
  '收藏、错题和练习记录长期保存',
  '根据薄弱点智能生成题目与解析',
  '查看更详细的正确率与能力分析',
  '自动推荐更适合你的训练内容'
]

const isProMember = computed(() => getMembershipStatus(authUser.value) === 'active')
const memberName = computed(() => authUser.value?.nickname || authUser.value?.email || '你')
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

function showPaymentClosed() {
  uni.showToast({ title: '已支持创建订单，正式支付渠道接入中', icon: 'none' })
}

async function loadMembershipPlans() {
  try {
    const plans = await fetchMembershipPlans()
    if (!Array.isArray(plans) || !plans.length) return
    pricePlans.value = plans.map((item) => ({
      code: item.code,
      name: item.name,
      price: item.price_label,
      desc: item.description,
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
      title: '订单已创建',
      content: `套餐：${plan.name}\n金额：${plan.price}\n订单号：${order.provider_order_id}\n\n正式支付渠道接入后，这里会继续打开收银台。`,
      confirmText: '知道了',
      showCancel: false
    })
  } catch (error) {
    uni.showToast({ title: error?.detail || '创建订单失败，请稍后重试', icon: 'none' })
  } finally {
    creatingOrderCode.value = ''
  }
}

function handleMemberFeature(item) {
  if (!item) return
  const messageMap = {
    ai: 'AI 生题入口将在下一步接入',
    report: '完整报告会复用能力报告并增加 Pro 指标',
    training: '专属训练已具备推荐训练入口雏形',
    storage: '长期保存能力会随会员状态开放'
  }
  showComingSoon(messageMap[item.action] || '功能准备中')
}

function startMemberTraining() {
  uni.setStorageSync('recommendedTrainingConfig', {
    trainingMode: 'member',
    subject: '逻辑推理',
    module: '判断',
    submodule: '判断关系',
    difficulty: '标准提升',
    questionCount: 10
  })
  uni.navigateTo({
    url: `/pages/practice/index?subject=${encodeURIComponent('逻辑推理')}&module=${encodeURIComponent('判断')}&submodule=${encodeURIComponent('判断关系')}&count=10&trainingMode=member`
  })
}

function copyFeedbackTemplate() {
  const text = 'Pro反馈：我是否愿意为 Pro 付费？最想要哪个功能？能接受的价格是多少？当前页面哪里让我不清楚？'
  uni.setClipboardData({
    data: text,
    success() {
      uni.showToast({ title: '反馈模板已复制', icon: 'none' })
    }
  })
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
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

.member-action-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.member-action-card {
  padding: 24rpx;
  border-radius: 26rpx;
  border: 2rpx solid #e8eef7;
  background: #ffffff;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.06);
}

.member-action-icon {
  width: 58rpx;
  height: 58rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 25rpx;
  line-height: 1;
  font-weight: 950;
}

.member-action-icon.green {
  color: #10b981;
  background: #edfdf6;
}

.member-action-icon.blue {
  color: #2563eb;
  background: #edf3ff;
}

.member-action-icon.purple {
  color: #7c3aed;
  background: #f2edff;
}

.member-action-icon.orange {
  color: #f59e0b;
  background: #fff7e8;
}

.member-action-title {
  margin-top: 18rpx;
  color: #172033;
  font-size: 27rpx;
  line-height: 1.35;
  font-weight: 950;
}

.member-action-desc {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.5;
  font-weight: 650;
}

.training-plan-card {
  display: flex;
  align-items: flex-end;
  gap: 18rpx;
}

.plan-main {
  flex: 1;
  min-width: 0;
}

.plan-kicker {
  color: #10b981;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 900;
}

.member-plan-title {
  margin-top: 8rpx;
  color: #172033;
  font-size: 31rpx;
  line-height: 1.35;
  font-weight: 950;
}

.plan-desc {
  margin-top: 10rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.65;
  font-weight: 650;
}

.plan-btn {
  width: 176rpx;
  flex: 0 0 176rpx;
  margin: 0;
}

.unlock-list,
.service-list,
.feature-list,
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

.hero-card {
  padding: 34rpx;
  border-radius: 36rpx;
  background: linear-gradient(135deg, #111827, #305bd8 58%, #5b8cff);
  color: #ffffff;
  box-shadow: 0 18rpx 38rpx rgba(37, 99, 235, 0.2);
}

.hero-title {
  margin-top: 22rpx;
  font-size: 44rpx;
  font-weight: 900;
  line-height: 1.25;
}

.hero-sub {
  margin-top: 16rpx;
  color: rgba(255, 255, 255, 0.9);
  font-size: 25rpx;
  line-height: 1.8;
}

.hero-btn,
.pay-btn {
  margin-top: 24rpx;
}

.compare-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
}

.compare-card,
.price-card,
.preview-item {
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
.price-name,
.preview-title {
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

.preview-item {
  display: flex;
  gap: 18rpx;
  align-items: flex-start;
}

.preview-icon {
  width: 58rpx;
  height: 58rpx;
  border-radius: 20rpx;
  background: #edf3ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
}

.preview-desc,
.price-desc,
.feedback-text {
  margin-top: 8rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.7;
}

.price-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.price-card.hot {
  border-color: #2563eb;
  background: #edf3ff;
}

.price-value {
  color: #172033;
  font-size: 34rpx;
  font-weight: 900;
  white-space: nowrap;
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
  .member-action-grid,
  .member-meta-grid {
    grid-template-columns: 1fr;
  }

  .training-plan-card {
    align-items: stretch;
    flex-direction: column;
  }

  .plan-btn {
    width: 100%;
    flex-basis: auto;
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
