<template>
  <view class="page pro-page">
    <PageHeader
      eyebrow="Pro 功能预览"
      title="会员中心"
      subtitle="内测阶段先展示权益和定价，不接真实支付。你可以把它当作后续商业化验证页面。"
    />

    <view class="hero-card">
      <view class="hero-tag">内测版 · 暂未开放支付</view>
      <view class="hero-title">把刷题结果变成下一步行动</view>
      <view class="hero-sub">
        Pro 版本计划围绕 AI 薄弱诊断、错题同类加练、每日训练计划和每周提分报告展开，帮助用户从“做题”走到“知道怎么提分”。
      </view>
      <button class="hero-btn" @tap="showPaymentClosed">内测阶段暂未开放支付</button>
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

    <SectionCard title="内测定价 Mock" subtitle="价格仅用于验证意愿，后续上线前会重新确认。">
      <view class="price-list">
        <view v-for="item in pricePlans" :key="item.name" class="price-card" :class="{ hot: item.hot }">
          <view>
            <view class="price-name">{{ item.name }}</view>
            <view class="price-desc">{{ item.desc }}</view>
          </view>
          <view class="price-value">{{ item.price }}</view>
        </view>
      </view>
      <button class="primary-button pay-btn" @tap="showPaymentClosed">内测阶段暂未开放支付</button>
    </SectionCard>

    <SectionCard title="内测反馈" subtitle="如果你愿意付费，欢迎把原因和可接受价格反馈给开发者。">
      <view class="feedback-text">
        反馈模板：我是否愿意为 Pro 付费？最想要哪个功能？能接受的价格是多少？当前页面哪里让我不清楚？
      </view>
      <BetaFeedbackForm source-page="pro" />
      <button class="ghost-button" @tap="copyFeedbackTemplate">复制反馈模板</button>
    </SectionCard>
  </view>
</template>

<script setup>
import PageHeader from '../../components/PageHeader.vue'
import SectionCard from '../../components/SectionCard.vue'
import BetaFeedbackForm from '../../components/BetaFeedbackForm.vue'

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

const pricePlans = [
  { name: '月卡', price: '19元', desc: '适合短期试用 Pro 功能', hot: false },
  { name: '季卡', price: '49元', desc: '适合一轮系统复习', hot: true },
  { name: '半年卡', price: '89元', desc: '适合完整备考周期', hot: false }
]

function showPaymentClosed() {
  uni.showToast({ title: '内测阶段暂未开放支付', icon: 'none' })
}

function copyFeedbackTemplate() {
  const text = 'Pro反馈：我是否愿意付费？最想要哪个功能？能接受的价格是多少？当前页面哪里让我不清楚？'
  uni.setClipboardData({
    data: text,
    success() {
      uni.showToast({ title: '反馈模板已复制', icon: 'none' })
    }
  })
}
</script>

<style scoped>
.pro-page {
  padding-bottom: calc(env(safe-area-inset-bottom) + 48rpx);
}

.hero-card {
  padding: 34rpx;
  border-radius: 36rpx;
  background: linear-gradient(135deg, #111827, #305bd8 58%, #5b8cff);
  color: #ffffff;
  box-shadow: 0 18rpx 38rpx rgba(37, 99, 235, 0.2);
}

.hero-tag {
  display: inline-flex;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 22rpx;
  font-weight: 800;
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

.feature-list,
.price-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
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

@media (max-width: 380px) {
  .compare-grid {
    grid-template-columns: 1fr;
  }
}
</style>
