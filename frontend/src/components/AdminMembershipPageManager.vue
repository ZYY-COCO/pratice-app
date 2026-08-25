<template>
  <view class="membership-page-manager-backdrop" role="presentation" @tap="close">
    <view class="membership-page-manager" role="dialog" aria-modal="true" aria-label="会员管理" @tap.stop>
      <view class="membership-page-manager__head">
        <view>
          <view class="membership-page-manager__kicker">MEMBERSHIP MANAGEMENT</view>
          <view class="membership-page-manager__title">会员管理</view>
          <view class="membership-page-manager__subtitle">保存后会同步更新用户端“我的 → 订阅”中的 PLUS 页面与套餐定价。</view>
        </view>
        <button class="membership-page-manager__close" type="button" aria-label="关闭" :disabled="saving" @tap="close">×</button>
      </view>

      <view v-if="loading" class="membership-page-manager__state">正在读取当前会员配置…</view>
      <view v-else class="membership-page-manager__body">
        <view class="membership-page-manager__preview-column">
          <view class="membership-page-manager__preview-heading">
            <view>
              <view class="membership-page-manager__section-kicker">USER PREVIEW</view>
              <view class="membership-page-manager__section-title">用户端实时预览</view>
            </view>
            <view class="membership-page-manager__preview-actions">
              <view class="membership-page-manager__sync-badge">实时联动</view>
              <view class="membership-page-manager__state-switch" role="group" aria-label="会员状态预览">
                <button
                  v-for="item in previewMembershipStates"
                  :key="item.value"
                  class="membership-page-manager__state-switch-item"
                  :class="{ active: previewMembershipState === item.value }"
                  type="button"
                  :aria-pressed="previewMembershipState === item.value"
                  @tap="previewMembershipState = item.value"
                >
                  {{ item.label }}
                </button>
              </view>
            </view>
          </view>
          <view class="membership-page-manager__phone">
            <scroll-view scroll-y class="membership-page-manager__phone-scroll">
              <view class="membership-page-manager__phone-content">
                <MembershipSubscriptionPreview
                  :config="previewConfig"
                  :membership="previewMembership"
                  :show-close="false"
                  preview
                />
              </view>
            </scroll-view>
          </view>
        </view>

        <scroll-view scroll-y class="membership-page-manager__editor">
          <view class="membership-page-manager__editor-content">
            <view v-if="loadError" class="membership-page-manager__warning">{{ loadError }} 当前正在使用默认配置，保存前请确认数据库迁移已执行。</view>

            <view class="membership-page-manager__form-section">
              <view class="membership-page-manager__section-title">页面文案</view>
              <view class="membership-page-manager__field-grid">
                <view class="membership-page-manager__field">
                  <view class="membership-page-manager__label">主标题</view>
                  <input v-model.trim="form.title" class="membership-page-manager__input" maxlength="30" placeholder="例如：开通 PLUS" />
                </view>
                <view class="membership-page-manager__field">
                  <view class="membership-page-manager__label">品牌名称</view>
                  <input v-model.trim="form.brand_name" class="membership-page-manager__input" maxlength="50" placeholder="例如：HMTC 升学交流圈" />
                </view>
                <view class="membership-page-manager__field full">
                  <view class="membership-page-manager__label">套餐提示</view>
                  <input v-model.trim="form.plan_hint" class="membership-page-manager__input" maxlength="80" placeholder="例如：选择适合你的学习计划" />
                </view>
                <view class="membership-page-manager__field">
                  <view class="membership-page-manager__label">主按钮文案</view>
                  <input v-model.trim="form.primary_button_text" class="membership-page-manager__input" maxlength="30" placeholder="例如：订阅 PLUS" />
                </view>
                <view class="membership-page-manager__field">
                  <view class="membership-page-manager__label">辅助按钮文案</view>
                  <input v-model.trim="form.secondary_button_text" class="membership-page-manager__input" maxlength="30" placeholder="例如：恢复购买" />
                </view>
                <view class="membership-page-manager__field full">
                  <view class="membership-page-manager__label">页面说明</view>
                  <textarea v-model.trim="form.description_text" class="membership-page-manager__textarea" maxlength="180" placeholder="填写订阅说明" />
                </view>
                <view class="membership-page-manager__field full">
                  <view class="membership-page-manager__label">页底条款文案</view>
                  <input v-model.trim="form.terms_text" class="membership-page-manager__input" maxlength="60" placeholder="例如：服务条款 · 隐私政策" />
                </view>
              </view>
            </view>

            <view class="membership-page-manager__form-section">
              <view class="membership-page-manager__section-row">
                <view>
                  <view class="membership-page-manager__section-title">套餐定价</view>
                  <view class="membership-page-manager__section-note">金额单位为人民币元，保存时会按分写入订单配置。</view>
                </view>
              </view>
              <view class="membership-page-manager__price-grid">
                <view class="membership-page-manager__price-field">
                  <view class="membership-page-manager__price-label">月卡</view>
                  <view class="membership-page-manager__price-input-wrap"><text>¥</text><input v-model="priceInput.monthly" class="membership-page-manager__price-input" type="digit" maxlength="10" placeholder="88" /><text>/月</text></view>
                </view>
                <view class="membership-page-manager__price-field">
                  <view class="membership-page-manager__price-label">季卡</view>
                  <view class="membership-page-manager__price-input-wrap"><text>¥</text><input v-model="priceInput.quarterly" class="membership-page-manager__price-input" type="digit" maxlength="10" placeholder="228" /><text>/季</text></view>
                </view>
              </view>
            </view>

            <view class="membership-page-manager__form-section">
              <view class="membership-page-manager__section-row">
                <view>
                  <view class="membership-page-manager__section-title">PLUS 权益</view>
                  <view class="membership-page-manager__section-note">支持增加、删除和调整顺序，最多 8 条。</view>
                </view>
                <button class="membership-page-manager__add-benefit" type="button" :disabled="form.benefits.length >= 8" @tap="addBenefit">+ 添加权益</button>
              </view>
              <view class="membership-page-manager__benefit-list">
                <view v-for="(benefit, index) in form.benefits" :key="`${index}-${benefit}`" class="membership-page-manager__benefit-row">
                  <view class="membership-page-manager__benefit-index">{{ index + 1 }}</view>
                  <input v-model.trim="form.benefits[index]" class="membership-page-manager__benefit-input" maxlength="80" placeholder="填写权益文案" />
                  <view class="membership-page-manager__benefit-actions">
                    <button type="button" aria-label="上移" :disabled="index === 0" @tap="moveBenefit(index, -1)">↑</button>
                    <button type="button" aria-label="下移" :disabled="index === form.benefits.length - 1" @tap="moveBenefit(index, 1)">↓</button>
                    <button type="button" aria-label="删除" :disabled="form.benefits.length <= 1" @tap="removeBenefit(index)">×</button>
                  </view>
                </view>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>

      <view class="membership-page-manager__footer">
        <button class="membership-page-manager__reset" type="button" :disabled="saving" @tap="resetForm">恢复默认</button>
        <view class="membership-page-manager__footer-actions">
          <button class="membership-page-manager__cancel" type="button" :disabled="saving" @tap="close">取消</button>
          <button class="membership-page-manager__save" type="button" :disabled="saving" @tap="save">{{ saving ? '同步中…' : '保存并同步用户端' }}</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { fetchAdminSubscriptionPageConfig, updateAdminSubscriptionPageConfig } from '../api/membership'
import {
  DEFAULT_SUBSCRIPTION_PAGE_CONFIG,
  createSubscriptionPageConfig,
  formatSubscriptionPriceInput,
  parseSubscriptionPriceInput
} from '../data/membershipSubscription'
import MembershipSubscriptionPreview from './MembershipSubscriptionPreview.vue'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'saved'])
const loading = ref(true)
const saving = ref(false)
const loadError = ref('')
const form = reactive(createSubscriptionPageConfig())
const priceInput = reactive({
  monthly: formatSubscriptionPriceInput(DEFAULT_SUBSCRIPTION_PAGE_CONFIG.monthly_price_cents),
  quarterly: formatSubscriptionPriceInput(DEFAULT_SUBSCRIPTION_PAGE_CONFIG.quarterly_price_cents)
})
const previewMembershipState = ref('inactive')
const previewMembershipStates = Object.freeze([
  { value: 'inactive', label: '未开通' },
  { value: 'active', label: '已开通' },
  { value: 'expiring', label: '临近到期' },
  { value: 'expired', label: '已到期' }
])

const previewConfig = computed(() => createSubscriptionPageConfig({
  ...form,
  benefits: [...form.benefits],
  monthly_price_cents: parseSubscriptionPriceInput(priceInput.monthly, form.monthly_price_cents),
  quarterly_price_cents: parseSubscriptionPriceInput(priceInput.quarterly, form.quarterly_price_cents)
}))
const previewMembership = computed(() => {
  if (previewMembershipState.value === 'inactive') return {}
  const now = new Date()
  const expiresAt = new Date(now)
  const isExpired = previewMembershipState.value === 'expired'
  expiresAt.setDate(now.getDate() + (isExpired ? -1 : previewMembershipState.value === 'expiring' ? 5 : 68))
  const startedAt = new Date(now)
  startedAt.setDate(now.getDate() - 25)
  return {
    membership_status: isExpired ? 'expired' : 'active',
    membership_plan: 'pro_quarterly',
    membership_started_at: startedAt.toISOString(),
    membership_expires_at: expiresAt.toISOString(),
    membership_updated_at: now.toISOString(),
    membership_active: !isExpired
  }
})

onMounted(() => {
  void loadConfig()
})

function applyConfig(source) {
  const normalized = createSubscriptionPageConfig(source)
  Object.assign(form, normalized, { benefits: [...normalized.benefits] })
  priceInput.monthly = formatSubscriptionPriceInput(normalized.monthly_price_cents)
  priceInput.quarterly = formatSubscriptionPriceInput(normalized.quarterly_price_cents)
}

async function loadConfig() {
  loading.value = true
  loadError.value = ''
  try {
    const response = props.preview ? DEFAULT_SUBSCRIPTION_PAGE_CONFIG : await fetchAdminSubscriptionPageConfig()
    applyConfig(response)
  } catch (error) {
    applyConfig(DEFAULT_SUBSCRIPTION_PAGE_CONFIG)
    loadError.value = error?.detail || '会员配置读取失败。'
  } finally {
    loading.value = false
  }
}

function addBenefit() {
  if (form.benefits.length >= 8) return
  form.benefits.push('新增 PLUS 学习权益')
}

function removeBenefit(index) {
  if (form.benefits.length <= 1) return
  form.benefits.splice(index, 1)
}

function moveBenefit(index, direction) {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= form.benefits.length) return
  const [benefit] = form.benefits.splice(index, 1)
  form.benefits.splice(targetIndex, 0, benefit)
}

function resetForm() {
  applyConfig(DEFAULT_SUBSCRIPTION_PAGE_CONFIG)
}

function buildPayload() {
  const monthlyAmount = Number(String(priceInput.monthly || '').trim())
  const quarterlyAmount = Number(String(priceInput.quarterly || '').trim())
  const textFields = [
    ['主标题', form.title],
    ['品牌名称', form.brand_name],
    ['套餐提示', form.plan_hint],
    ['主按钮文案', form.primary_button_text],
    ['辅助按钮文案', form.secondary_button_text],
    ['页面说明', form.description_text],
    ['页底条款文案', form.terms_text]
  ]
  const emptyField = textFields.find(([, value]) => !String(value || '').trim())
  if (emptyField) {
    uni.showToast({ title: `请填写${emptyField[0]}`, icon: 'none' })
    return null
  }
  if (!Number.isFinite(monthlyAmount) || monthlyAmount <= 0 || !Number.isFinite(quarterlyAmount) || quarterlyAmount <= 0) {
    uni.showToast({ title: '请填写正确的月卡和季卡价格', icon: 'none' })
    return null
  }
  const benefits = form.benefits.map((item) => String(item || '').trim()).filter(Boolean)
  if (!benefits.length || benefits.length !== form.benefits.length) {
    uni.showToast({ title: '请完整填写每一条 PLUS 权益', icon: 'none' })
    return null
  }
  return {
    title: String(form.title).trim(),
    brand_name: String(form.brand_name).trim(),
    benefits,
    monthly_price_cents: Math.round(monthlyAmount * 100),
    quarterly_price_cents: Math.round(quarterlyAmount * 100),
    plan_hint: String(form.plan_hint).trim(),
    primary_button_text: String(form.primary_button_text).trim(),
    secondary_button_text: String(form.secondary_button_text).trim(),
    description_text: String(form.description_text).trim(),
    terms_text: String(form.terms_text).trim()
  }
}

async function save() {
  const payload = buildPayload()
  if (!payload) return
  saving.value = true
  try {
    const response = props.preview ? payload : await updateAdminSubscriptionPageConfig(payload)
    applyConfig(response)
    emit('saved', response)
    uni.showToast({ title: props.preview ? '预览已更新' : '已同步到用户端', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '会员配置保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

function close() {
  if (saving.value) return
  emit('close')
}
</script>

<style scoped>
.membership-page-manager-backdrop {
  position: fixed;
  inset: 0;
  z-index: 900;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  background: rgba(16, 24, 40, 0.46);
  backdrop-filter: blur(7px);
  -webkit-backdrop-filter: blur(7px);
}

.membership-page-manager {
  width: min(1240px, 100%);
  max-height: min(860px, calc(100dvh - 48px));
  border: 1px solid rgba(226, 231, 239, 0.9);
  border-radius: 28px;
  background: #ffffff;
  box-shadow: 0 28px 80px rgba(15, 23, 42, 0.28);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.membership-page-manager__head {
  padding: 24px 28px 20px;
  border-bottom: 1px solid #edf0f4;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.membership-page-manager__kicker,
.membership-page-manager__section-kicker {
  color: #8c9aab;
  font-size: 11px;
  line-height: 1.2;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.membership-page-manager__title {
  margin-top: 5px;
  color: #172033;
  font-size: 26px;
  line-height: 1.2;
  font-weight: 900;
}

.membership-page-manager__subtitle {
  margin-top: 7px;
  color: #75849a;
  font-size: 13px;
  line-height: 1.55;
}

.membership-page-manager__close {
  width: 38px;
  min-width: 38px;
  height: 38px;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #f3f5f7;
  color: #64748b;
  font-size: 25px;
  line-height: 38px;
}

.membership-page-manager__close::after,
.membership-page-manager button::after {
  border: 0;
}

.membership-page-manager__state {
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #738299;
  font-size: 14px;
}

.membership-page-manager__body {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(330px, 0.84fr) minmax(0, 1.16fr);
}

.membership-page-manager__preview-column {
  min-height: 0;
  padding: 23px 24px 24px;
  border-right: 1px solid #edf0f4;
  background: #f7f7f6;
  display: flex;
  flex-direction: column;
}

.membership-page-manager__preview-heading,
.membership-page-manager__section-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.membership-page-manager__preview-actions {
  display: flex;
  align-items: flex-end;
  flex-direction: column;
  gap: 8px;
}

.membership-page-manager__section-title {
  color: #26364d;
  font-size: 16px;
  line-height: 1.35;
  font-weight: 900;
}

.membership-page-manager__sync-badge {
  padding: 5px 9px;
  border-radius: 999px;
  background: #e8f7f1;
  color: #23836e;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}

.membership-page-manager__state-switch {
  display: inline-flex;
  padding: 3px;
  border: 1px solid #e4e6ea;
  border-radius: 10px;
  background: #ffffff;
}

.membership-page-manager__state-switch-item {
  min-height: 25px;
  margin: 0;
  padding: 0 7px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #8490a0;
  font-size: 10px;
  line-height: 25px;
  font-weight: 800;
}

.membership-page-manager__state-switch-item::after {
  border: 0;
}

.membership-page-manager__state-switch-item.active {
  background: #26364d;
  color: #ffffff;
}

.membership-page-manager__phone {
  min-height: 0;
  flex: 1;
  width: min(100%, 366px);
  margin: 18px auto 0;
  padding: 10px;
  border: 7px solid #252b34;
  border-radius: 35px;
  background: #252b34;
  box-shadow: 0 22px 38px rgba(44, 48, 57, 0.18);
  box-sizing: border-box;
}

.membership-page-manager__phone-scroll {
  height: 100%;
  border-radius: 24px;
  background: #ffffff;
}

.membership-page-manager__phone-content {
  padding: 20px 17px 24px;
}

.membership-page-manager__editor {
  min-height: 0;
  height: 100%;
  background: #ffffff;
}

.membership-page-manager__editor-content {
  padding: 23px 27px 32px;
}

.membership-page-manager__warning {
  margin-bottom: 16px;
  padding: 11px 13px;
  border: 1px solid #f1deb8;
  border-radius: 12px;
  background: #fffaf0;
  color: #9b6c25;
  font-size: 12px;
  line-height: 1.55;
}

.membership-page-manager__form-section + .membership-page-manager__form-section {
  margin-top: 25px;
  padding-top: 24px;
  border-top: 1px solid #eef1f4;
}

.membership-page-manager__section-note {
  margin-top: 5px;
  color: #8a98aa;
  font-size: 12px;
  line-height: 1.45;
}

.membership-page-manager__field-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.membership-page-manager__field.full {
  grid-column: 1 / -1;
}

.membership-page-manager__label,
.membership-page-manager__price-label {
  margin-bottom: 7px;
  color: #65768b;
  font-size: 12px;
  line-height: 1.3;
  font-weight: 800;
}

.membership-page-manager__input,
.membership-page-manager__textarea,
.membership-page-manager__benefit-input {
  width: 100%;
  border: 1px solid #e1e7ee;
  border-radius: 10px;
  background: #fbfcfd;
  color: #26364d;
  box-sizing: border-box;
  font-size: 13px;
  line-height: 1.45;
}

.membership-page-manager__input,
.membership-page-manager__benefit-input {
  min-height: 38px;
  padding: 0 11px;
}

.membership-page-manager__textarea {
  min-height: 68px;
  padding: 9px 11px;
}

.membership-page-manager__input:focus,
.membership-page-manager__textarea:focus,
.membership-page-manager__benefit-input:focus {
  border-color: #6b9df2;
  background: #ffffff;
}

.membership-page-manager__price-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.membership-page-manager__price-field {
  padding: 14px;
  border: 1px solid #e6ebf1;
  border-radius: 14px;
  background: #fbfcfd;
}

.membership-page-manager__price-input-wrap {
  min-height: 40px;
  padding: 0 11px;
  border: 1px solid #dfe6ee;
  border-radius: 10px;
  background: #ffffff;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #617187;
  font-size: 13px;
}

.membership-page-manager__price-input {
  min-width: 0;
  flex: 1;
  height: 38px;
  border: 0;
  background: transparent;
  color: #20324a;
  font-size: 19px;
  font-weight: 900;
}

.membership-page-manager__add-benefit {
  min-height: 31px;
  margin: 0;
  padding: 0 10px;
  border: 1px solid #cfe0fa;
  border-radius: 9px;
  background: #f3f8ff;
  color: #3d7ad1;
  font-size: 12px;
  line-height: 29px;
  font-weight: 800;
  white-space: nowrap;
}

.membership-page-manager__benefit-list {
  margin-top: 13px;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.membership-page-manager__benefit-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.membership-page-manager__benefit-index {
  width: 25px;
  height: 25px;
  flex: 0 0 25px;
  border-radius: 8px;
  background: #eef7f4;
  color: #348d77;
  font-size: 12px;
  line-height: 25px;
  font-weight: 900;
  text-align: center;
}

.membership-page-manager__benefit-input {
  min-width: 0;
  flex: 1;
}

.membership-page-manager__benefit-actions {
  display: flex;
  gap: 3px;
}

.membership-page-manager__benefit-actions button {
  width: 28px;
  min-width: 28px;
  height: 28px;
  margin: 0;
  padding: 0;
  border: 1px solid #e0e6ed;
  border-radius: 8px;
  background: #ffffff;
  color: #66778d;
  font-size: 15px;
  line-height: 26px;
}

.membership-page-manager__benefit-actions button:disabled,
.membership-page-manager__add-benefit:disabled,
.membership-page-manager__footer button:disabled,
.membership-page-manager__close:disabled {
  opacity: 0.48;
}

.membership-page-manager__footer {
  min-height: 76px;
  padding: 14px 28px;
  border-top: 1px solid #edf0f4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  box-sizing: border-box;
}

.membership-page-manager__footer-actions {
  display: flex;
  align-items: center;
  gap: 9px;
}

.membership-page-manager__footer button {
  min-height: 38px;
  margin: 0;
  padding: 0 15px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 36px;
  font-weight: 850;
}

.membership-page-manager__reset,
.membership-page-manager__cancel {
  border: 1px solid #e0e6ed;
  background: #ffffff;
  color: #66778d;
}

.membership-page-manager__save {
  border: 1px solid #1e2a3a;
  background: #1f2937;
  color: #ffffff;
  box-shadow: 0 8px 16px rgba(31, 41, 55, 0.16);
}

@media (max-width: 980px) {
  .membership-page-manager-backdrop {
    padding: 14px;
  }

  .membership-page-manager {
    max-height: calc(100dvh - 28px);
  }

  .membership-page-manager__body {
    grid-template-columns: 1fr;
    overflow-y: auto;
  }

  .membership-page-manager__preview-column {
    min-height: 520px;
    border-right: 0;
    border-bottom: 1px solid #edf0f4;
  }

  .membership-page-manager__editor {
    height: auto;
  }
}

@media (max-width: 620px) {
  .membership-page-manager__head,
  .membership-page-manager__editor-content,
  .membership-page-manager__footer {
    padding-left: 18px;
    padding-right: 18px;
  }

  .membership-page-manager__subtitle {
    display: none;
  }

  .membership-page-manager__field-grid,
  .membership-page-manager__price-grid {
    grid-template-columns: 1fr;
  }

  .membership-page-manager__field.full {
    grid-column: auto;
  }

  .membership-page-manager__footer {
    align-items: flex-end;
    flex-direction: column;
  }

  .membership-page-manager__footer-actions {
    width: 100%;
  }

  .membership-page-manager__footer-actions button {
    flex: 1;
  }
}
</style>
