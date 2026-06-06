<template>
  <view class="question-stem">
    <view v-if="!quality.valid" class="question-stem-error">
      <view class="error-title">题目数据异常，请检查题库</view>
      <view v-if="quality.reasons.length" class="error-detail">{{ quality.reasons.join('；') }}</view>
    </view>
    <MathText v-else-if="normalized.isMath" class="question-stem-text" :value="normalized.stem" />
    <text v-else class="question-stem-text">{{ normalized.stem }}</text>
  </view>
</template>

<script setup>
import { computed, watch } from 'vue'
import MathText from './MathText.vue'
import { normalizeQuestion, validateQuestion } from '../utils/questionQuality'

const props = defineProps({
  question: {
    type: Object,
    required: true
  }
})

const normalized = computed(() => normalizeQuestion(props.question))
const quality = computed(() => validateQuestion(normalized.value))

watch(
  () => [normalized.value.id, normalized.value.stem, quality.value.valid],
  () => {
    if (quality.value.valid && !quality.value.warnings.length) return
    const id = normalized.value.id || normalized.value.questionId || '(no-id)'
    // eslint-disable-next-line no-console
    console.warn('[question-quality]', id, [...quality.value.reasons, ...quality.value.warnings])
  },
  { immediate: true }
)
</script>

<style scoped>
.question-stem {
  width: 100%;
  min-width: 0;
}

.question-stem-text {
  display: block;
  width: 100%;
  color: #172033;
  font-size: inherit;
  font-weight: inherit;
  line-height: inherit;
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.question-stem-error {
  padding: 22rpx;
  border-radius: 22rpx;
  border: 2rpx dashed #fda4af;
  background: #fff1f2;
  color: #be123c;
  font-size: 25rpx;
  line-height: 1.55;
  font-weight: 800;
}

.error-detail {
  margin-top: 8rpx;
  color: #9f1239;
  font-size: 22rpx;
  font-weight: 600;
}
</style>
