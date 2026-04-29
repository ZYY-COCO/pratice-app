<template>
  <view class="feedback-form">
    <view class="field">
      <view class="label">反馈类型</view>
      <picker :range="typeOptions" :value="typeIndex" @change="onTypeChange">
        <view class="picker-box">{{ form.feedbackType }}</view>
      </picker>
    </view>

    <view class="field">
      <view class="label">反馈内容</view>
      <textarea
        v-model.trim="form.content"
        class="textarea"
        maxlength="1000"
        placeholder="请描述你遇到的问题、建议，或你对 Pro 功能/价格的想法"
      />
    </view>

    <view class="field">
      <view class="label">是否愿意为 Pro 付费</view>
      <view class="pay-row">
        <button
          v-for="item in payOptions"
          :key="item.label"
          class="choice-btn"
          :class="{ active: form.willingToPay === item.value }"
          @tap="form.willingToPay = item.value"
        >
          {{ item.label }}
        </button>
      </view>
    </view>

    <view class="field">
      <view class="label">可接受价格</view>
      <input v-model.trim="form.acceptablePrice" class="input" type="text" placeholder="例如：19元/月、49元/季" />
    </view>

    <view class="field">
      <view class="label">联系方式（可选）</view>
      <input v-model.trim="form.contact" class="input" type="text" placeholder="微信 / 邮箱 / QQ，方便追问问题" />
    </view>

    <button class="primary-button" :disabled="submitting" @tap="submit">
      {{ submitting ? '提交中...' : '提交反馈' }}
    </button>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { submitBetaFeedback } from '../api/feedback'

const props = defineProps({
  sourcePage: {
    type: String,
    default: 'unknown'
  }
})

const typeOptions = ['题目质量', '刷题体验', '错题本', '能力报告', 'Pro付费意愿', 'Bug']
const payOptions = [
  { label: '愿意', value: true },
  { label: '暂不确定', value: null },
  { label: '不愿意', value: false }
]
const submitting = ref(false)
const form = reactive({
  feedbackType: typeOptions[0],
  content: '',
  willingToPay: null,
  acceptablePrice: '',
  contact: ''
})

const typeIndex = computed(() => Math.max(0, typeOptions.indexOf(form.feedbackType)))

function onTypeChange(event) {
  form.feedbackType = typeOptions[Number(event.detail.value)] || typeOptions[0]
}

async function submit() {
  if (!form.content || form.content.length < 5) {
    uni.showToast({ title: '请至少填写 5 个字的反馈内容', icon: 'none' })
    return
  }

  submitting.value = true
  try {
    const response = await submitBetaFeedback({
      feedback_type: form.feedbackType,
      content: form.content,
      willing_to_pay: form.willingToPay,
      acceptable_price: form.acceptablePrice || null,
      contact: form.contact || null,
      source_page: props.sourcePage
    })
    uni.showToast({ title: response.detail || '反馈已提交', icon: 'none' })
    form.content = ''
    form.acceptablePrice = ''
    form.contact = ''
    form.willingToPay = null
  } catch (error) {
    uni.showToast({ title: error?.detail || '反馈提交失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.feedback-form {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.label {
  color: #344054;
  font-size: 24rpx;
  font-weight: 800;
}

.input,
.picker-box,
.textarea {
  margin-top: 14rpx;
  width: 100%;
  border-radius: 28rpx;
  border: 2rpx solid #dbe3f2;
  background: #f8fbff;
  color: #172033;
  font-size: 26rpx;
  box-sizing: border-box;
}

.input,
.picker-box {
  min-height: 96rpx;
  padding: 0 26rpx;
  display: flex;
  align-items: center;
}

.textarea {
  min-height: 200rpx;
  padding: 24rpx;
  line-height: 1.6;
}

.pay-row {
  display: flex;
  gap: 14rpx;
  margin-top: 14rpx;
}

.choice-btn {
  flex: 1;
  min-height: 84rpx;
  border: 2rpx solid #dbe4f5;
  border-radius: 26rpx;
  background: #f8fbff;
  color: #476089;
  font-size: 23rpx;
  font-weight: 800;
}

.choice-btn.active {
  border-color: #2563eb;
  background: #edf3ff;
  color: #2563eb;
  box-shadow: 0 8rpx 18rpx rgba(37, 99, 235, 0.12);
}
</style>
