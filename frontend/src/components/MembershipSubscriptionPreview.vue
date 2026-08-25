<template>
  <view class="membership-subscription-preview" :class="{ 'is-admin-preview': preview }">
    <view class="membership-subscription-preview__head">
      <button
        v-if="showClose"
        class="membership-subscription-preview__close"
        type="button"
        aria-label="取消"
        @tap.stop="emit('close')"
        @click.stop
      >
        <CloseIcon />
      </button>
      <view v-else class="membership-subscription-preview__close is-static" aria-hidden="true"><CloseIcon /></view>
      <view class="membership-subscription-preview__title">{{ sheetTitle }}</view>
    </view>

    <view class="membership-subscription-preview__brand">
      <image class="membership-subscription-preview__logo" src="/static/brand/hmtc-community-logo.png" mode="aspectFit" />
      <view class="membership-subscription-preview__brand-name">{{ pageConfig.brand_name }}</view>
    </view>

    <view
      v-if="isActiveMembership"
      class="membership-subscription-preview__member-status"
      :class="{ 'is-expiring': isExpiring }"
    >
      <view class="membership-subscription-preview__member-status-head">
        <view>
          <view class="membership-subscription-preview__member-status-kicker">PLUS 会员 · {{ membershipPlanName }}</view>
          <view class="membership-subscription-preview__member-status-title">
            {{ isExpiring ? 'PLUS 即将到期' : 'PLUS 学习权益已生效' }}
          </view>
        </view>
        <view class="membership-subscription-preview__member-status-badge">{{ isExpiring ? '临期' : '已开通' }}</view>
      </view>
      <view class="membership-subscription-preview__member-status-details">
        <view class="membership-subscription-preview__member-status-item">
          <text class="membership-subscription-preview__member-status-label">有效至</text>
          <text class="membership-subscription-preview__member-status-value">{{ membershipExpiryText }}</text>
        </view>
        <view class="membership-subscription-preview__member-status-divider" />
        <view class="membership-subscription-preview__member-status-item is-days">
          <text class="membership-subscription-preview__member-status-label">剩余</text>
          <text class="membership-subscription-preview__member-status-value">
            <text class="membership-subscription-preview__member-status-days">{{ membershipRemainingDays }}</text> 天
          </text>
        </view>
      </view>
      <view v-if="isExpiring" class="membership-subscription-preview__expiry-alert">
        续订后将从当前到期日顺延，不会损失剩余会员天数。
      </view>
    </view>

    <view class="membership-subscription-preview__benefit-section">
      <view v-if="isActiveMembership" class="membership-subscription-preview__benefit-title">已解锁权益</view>
      <view class="membership-subscription-preview__benefits">
        <view v-for="item in pageConfig.benefits" :key="item" class="membership-subscription-preview__benefit">
          <text class="membership-subscription-preview__check">✓</text>
          <text>{{ item }}</text>
        </view>
      </view>
    </view>

    <view v-if="showPlanSelection" class="membership-subscription-preview__hint">
      {{ isActiveMembership ? '选择要续订的套餐' : pageConfig.plan_hint }}
    </view>
    <view v-if="showPlanSelection" class="membership-subscription-preview__plans" role="radiogroup" aria-label="选择套餐">
      <button
        v-for="plan in plans"
        :key="plan.code"
        class="membership-subscription-preview__plan"
        :class="{ active: selectedPlan === plan.code }"
        type="button"
        :aria-checked="selectedPlan === plan.code"
        role="radio"
        @tap.stop="selectPlan(plan.code)"
      >
        <view class="membership-subscription-preview__plan-name">{{ plan.name }}</view>
        <view class="membership-subscription-preview__plan-price">{{ plan.price }}</view>
      </button>
    </view>

    <view v-if="isExpiredMembership" class="membership-subscription-preview__expired-note">
      你的 PLUS 已到期，选择套餐后即可重新开通。
    </view>

    <button class="membership-subscription-preview__primary" type="button" @tap.stop="handlePrimaryAction">
      {{ primaryButtonText }}
    </button>
    <button
      v-if="isActiveMembership && choosingRenewalPlan"
      class="membership-subscription-preview__secondary"
      type="button"
      @tap.stop="cancelRenewal"
    >
      暂不续订
    </button>
    <button
      v-else-if="!isActiveMembership"
      class="membership-subscription-preview__secondary"
      type="button"
      @tap.stop="emit('restore')"
    >
      {{ pageConfig.secondary_button_text }}
    </button>
    <view class="membership-subscription-preview__copy">{{ descriptionText }}</view>
    <view class="membership-subscription-preview__terms">{{ pageConfig.terms_text }}</view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import CloseIcon from './CloseIcon.vue'
import { createSubscriptionPageConfig, formatSubscriptionPrice } from '../data/membershipSubscription'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({})
  },
  showClose: {
    type: Boolean,
    default: true
  },
  preview: {
    type: Boolean,
    default: false
  },
  membership: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close', 'subscribe', 'restore'])
const selectedPlan = ref('monthly')
const choosingRenewalPlan = ref(false)
const pageConfig = computed(() => createSubscriptionPageConfig(props.config))
const plans = computed(() => ([
  {
    code: 'monthly',
    name: '月卡',
    price: formatSubscriptionPrice(pageConfig.value.monthly_price_cents, '/月')
  },
  {
    code: 'quarterly',
    name: '季卡',
    price: formatSubscriptionPrice(pageConfig.value.quarterly_price_cents, '/季')
  }
]))
const membershipStatus = computed(() => String(props.membership?.membership_status || 'inactive').toLowerCase())
const membershipExpiry = computed(() => parseMembershipDate(props.membership?.membership_expires_at))
const isActiveMembership = computed(() => {
  if (membershipStatus.value !== 'active' && props.membership?.membership_active !== true) return false
  return !membershipExpiry.value || membershipExpiry.value.getTime() > Date.now()
})
const isExpiredMembership = computed(() => (
  membershipStatus.value === 'expired'
  || (!isActiveMembership.value && membershipStatus.value === 'active' && Boolean(membershipExpiry.value))
))
const membershipPlanName = computed(() => (
  String(props.membership?.membership_plan || '').includes('quarter') ? '季卡' : '月卡'
))
const membershipRemainingDays = computed(() => {
  if (!membershipExpiry.value) return '—'
  const remaining = membershipExpiry.value.getTime() - Date.now()
  return Math.max(0, Math.ceil(remaining / (24 * 60 * 60 * 1000)))
})
const membershipExpiryText = computed(() => formatMembershipDate(membershipExpiry.value))
const isExpiring = computed(() => (
  isActiveMembership.value
  && typeof membershipRemainingDays.value === 'number'
  && membershipRemainingDays.value <= 7
))
const showPlanSelection = computed(() => !isActiveMembership.value || choosingRenewalPlan.value)
const sheetTitle = computed(() => {
  if (!isActiveMembership.value) return pageConfig.value.title
  return choosingRenewalPlan.value ? '续订 PLUS' : '我的 PLUS'
})
const primaryButtonText = computed(() => {
  if (!isActiveMembership.value) return pageConfig.value.primary_button_text
  return choosingRenewalPlan.value ? '确认续订' : '续订 PLUS'
})
const descriptionText = computed(() => {
  if (isActiveMembership.value) {
    return choosingRenewalPlan.value
      ? '续订成功后，新的会员有效期将从当前到期日开始顺延。'
      : '你的 PLUS 会员正在生效中，可随时续订以延长有效期。'
  }
  return pageConfig.value.description_text
})

watch(
  () => [
    props.membership?.membership_status,
    props.membership?.membership_plan,
    props.membership?.membership_expires_at,
    props.membership?.membership_active
  ],
  () => {
    choosingRenewalPlan.value = false
    selectedPlan.value = String(props.membership?.membership_plan || '').includes('quarter') ? 'quarterly' : 'monthly'
  },
  { immediate: true }
)

function selectPlan(plan) {
  selectedPlan.value = plan === 'quarterly' ? 'quarterly' : 'monthly'
}

function handlePrimaryAction() {
  if (isActiveMembership.value && !choosingRenewalPlan.value) {
    choosingRenewalPlan.value = true
    return
  }
  emit('subscribe', selectedPlan.value)
}

function cancelRenewal() {
  choosingRenewalPlan.value = false
}

function parseMembershipDate(value) {
  if (!value) return null
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function formatMembershipDate(value) {
  if (!value) return '有效期信息同步中'
  return `${value.getFullYear()}年${value.getMonth() + 1}月${value.getDate()}日`
}
</script>

<style scoped>
.membership-subscription-preview {
  color: #111214;
}

.membership-subscription-preview__head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.membership-subscription-preview__close {
  width: 38px;
  min-width: 38px;
  height: 38px;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #f4f4f3;
  color: #111214;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.membership-subscription-preview__close::after,
.membership-subscription-preview__plan::after,
.membership-subscription-preview__primary::after,
.membership-subscription-preview__secondary::after {
  border: 0;
}

.membership-subscription-preview__close.is-static {
  pointer-events: none;
}

.membership-subscription-preview__close :deep(svg) {
  width: 19px;
  height: 19px;
}

.membership-subscription-preview__title {
  min-width: 0;
  color: #111214;
  font-size: 21px;
  line-height: 1.2;
  font-weight: 900;
  letter-spacing: 0.02em;
}

.membership-subscription-preview__brand {
  margin: 28px auto 25px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.membership-subscription-preview__logo {
  width: 95px;
  height: 95px;
  display: block;
  border-radius: 24px;
  transform: scale(1.32);
}

.membership-subscription-preview__brand-name {
  margin-top: 12px;
  color: #111214;
  font-size: 20px;
  line-height: 1.25;
  font-weight: 900;
  letter-spacing: 0.01em;
  text-align: center;
}

.membership-subscription-preview__member-status {
  margin: 0 0 15px;
  padding: 16px;
  border: 1px solid rgba(33, 34, 36, 0.08);
  border-radius: 19px;
  background: #f7f7f6;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.84);
}

.membership-subscription-preview__member-status.is-expiring {
  border-color: rgba(202, 126, 46, 0.18);
  background: #fff9f0;
}

.membership-subscription-preview__member-status-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.membership-subscription-preview__member-status-kicker {
  color: #70706c;
  font-size: 12px;
  line-height: 1.25;
  font-weight: 800;
}

.membership-subscription-preview__member-status-title {
  margin-top: 5px;
  color: #171816;
  font-size: 16px;
  line-height: 1.35;
  font-weight: 900;
}

.membership-subscription-preview__member-status-badge {
  flex: 0 0 auto;
  padding: 5px 9px;
  border-radius: 999px;
  color: #167657;
  background: #e7f6ed;
  font-size: 11px;
  line-height: 1.2;
  font-weight: 900;
}

.is-expiring .membership-subscription-preview__member-status-badge {
  color: #ae681d;
  background: #ffecd2;
}

.membership-subscription-preview__member-status-details {
  margin-top: 15px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 1px minmax(72px, auto);
  align-items: center;
  gap: 13px;
}

.membership-subscription-preview__member-status-item {
  min-width: 0;
}

.membership-subscription-preview__member-status-item.is-days {
  text-align: right;
}

.membership-subscription-preview__member-status-label {
  display: block;
  color: #8a8a86;
  font-size: 11px;
  line-height: 1.2;
  font-weight: 700;
}

.membership-subscription-preview__member-status-value {
  display: block;
  margin-top: 5px;
  overflow: hidden;
  color: #20211f;
  font-size: 14px;
  line-height: 1.25;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.membership-subscription-preview__member-status-days {
  font-size: 20px;
}

.membership-subscription-preview__member-status-divider {
  width: 1px;
  height: 30px;
  background: rgba(33, 34, 36, 0.1);
}

.membership-subscription-preview__expiry-alert,
.membership-subscription-preview__expired-note {
  margin-top: 13px;
  padding: 10px 11px;
  border-radius: 12px;
  color: #9c5d1b;
  background: rgba(255, 229, 193, 0.58);
  font-size: 12px;
  line-height: 1.5;
  font-weight: 700;
}

.membership-subscription-preview__benefit-section {
  margin: 0;
}

.membership-subscription-preview__benefit-title {
  margin: 0 0 8px;
  color: #646460;
  font-size: 12px;
  line-height: 1.25;
  font-weight: 900;
}

.membership-subscription-preview__benefits {
  padding: 17px;
  border-radius: 19px;
  background: #f7f7f6;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.membership-subscription-preview__benefit {
  min-height: 35px;
  display: flex;
  align-items: center;
  gap: 11px;
  color: #202124;
  font-size: 14px;
  line-height: 1.5;
  font-weight: 700;
}

.membership-subscription-preview__benefit + .membership-subscription-preview__benefit {
  margin-top: 9px;
}

.membership-subscription-preview__check {
  width: 17px;
  flex: 0 0 17px;
  color: #18a66a;
  font-family: var(--gyt-app-font);
  font-size: 23px;
  line-height: 1;
  font-weight: 400;
  text-align: center;
}

.membership-subscription-preview__hint {
  margin: 15px 0 10px;
  color: #777774;
  font-size: 13px;
  line-height: 1.45;
  font-weight: 700;
  text-align: center;
}

.membership-subscription-preview__expired-note {
  margin: 15px 0 0;
  color: #85613d;
  background: #f7f2eb;
  text-align: center;
}

.membership-subscription-preview__plans {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}

.membership-subscription-preview__plan {
  min-height: 67px;
  margin: 0;
  padding: 10px 8px;
  border: 1px solid #ebeae8;
  border-radius: 15px;
  background: #ffffff;
  color: #30312f;
  box-sizing: border-box;
  text-align: left;
  transition: border-color 160ms ease, background-color 160ms ease, box-shadow 160ms ease;
}

.membership-subscription-preview__plan.active {
  border-color: #151618;
  background: #fbfbfa;
  box-shadow: 0 7px 15px rgba(17, 18, 20, 0.09);
}

.membership-subscription-preview__plan-name {
  color: #686864;
  font-size: 12px;
  line-height: 1.2;
  font-weight: 700;
}

.membership-subscription-preview__plan-price {
  margin-top: 5px;
  color: #111214;
  font-size: 17px;
  line-height: 1.2;
  font-weight: 900;
}

.membership-subscription-preview__primary,
.membership-subscription-preview__secondary {
  width: 100%;
  margin: 0;
  padding: 0 14px;
  border: 0;
  box-sizing: border-box;
  font-weight: 900;
}

.membership-subscription-preview__primary {
  min-height: 48px;
  margin-top: 15px;
  border-radius: 999px;
  background: #111214;
  color: #ffffff;
  font-size: 16px;
  line-height: 48px;
  box-shadow: 0 7px 13px rgba(17, 18, 20, 0.16);
}

.membership-subscription-preview__secondary {
  min-height: 39px;
  background: transparent;
  color: #535350;
  font-size: 14px;
  line-height: 39px;
}

.membership-subscription-preview__copy {
  margin: 1px auto 0;
  max-width: 300px;
  color: #91918d;
  font-size: 11px;
  line-height: 1.65;
  font-weight: 600;
  text-align: center;
}

.membership-subscription-preview__terms {
  margin-top: 13px;
  color: #3f403e;
  font-size: 12px;
  line-height: 1.45;
  font-weight: 700;
  text-align: center;
}

@media (max-width: 360px) {
  .membership-subscription-preview__benefit {
    font-size: 13px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .membership-subscription-preview__plan {
    transition-duration: 1ms;
  }
}
</style>
