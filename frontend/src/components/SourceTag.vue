<template>
  <view class="source-tag">
    <text class="source-tag-text">{{ label }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { normalizeQuestion } from '../utils/questionQuality'

const props = defineProps({
  question: {
    type: Object,
    required: true
  },
  practiceMode: {
    type: String,
    default: ''
  },
  reviewMode: {
    type: Boolean,
    default: false
  },
  mockExamMode: {
    type: Boolean,
    default: false
  }
})

const normalized = computed(() => normalizeQuestion(props.question))

const label = computed(() => {
  if (props.mockExamMode) {
    return props.reviewMode ? '来源：模拟测试 · 解析回顾' : '来源：模拟测试'
  }
  if (props.practiceMode === 'comprehensive') {
    return props.reviewMode ? '来源：综合刷题 · 解析回顾' : '来源：综合刷题 · 隐藏知识点'
  }

  const question = normalized.value
  const sourceType = String(question.source_type || '')
  const submodule = question.submodule || question.module || question.subject || '题库练习'
  if (/ai/i.test(sourceType)) {
    return `来源：AI专项出题 · ${submodule}`
  }
  if (question.source_year) {
    return `来源：${question.source_year}年真题 · ${question.subject || '题库'} · ${submodule}`
  }
  return `来源：题库练习 · ${submodule}`
})
</script>

<style scoped>
.source-tag {
  margin-top: 22rpx;
  padding: 20rpx 22rpx;
  border-radius: 24rpx;
  border: 2rpx dashed var(--gyt-primary-border);
  background: var(--gyt-primary-tint);
  color: #476089;
  font-size: 23rpx;
  line-height: 1.45;
}

.source-tag-text {
  display: block;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
}
</style>
