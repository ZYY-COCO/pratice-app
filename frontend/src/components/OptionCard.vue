<template>
  <view class="option-card" :class="stateClass" @tap="$emit('select', label)">
    <view class="option-letter">{{ label }}</view>
    <view class="option-content">
      <MathText v-if="isMath" class="option-math" :value="content" />
      <text v-else class="option-text">{{ content }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import MathText from './MathText.vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  content: {
    type: [String, Number],
    default: ''
  },
  isMath: {
    type: Boolean,
    default: false
  },
  selected: {
    type: Boolean,
    default: false
  },
  submitted: {
    type: Boolean,
    default: false
  },
  correct: {
    type: Boolean,
    default: false
  },
  wrong: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select'])

const stateClass = computed(() => ({
  selected: !props.submitted && props.selected,
  correct: props.submitted && props.correct,
  wrong: props.submitted && props.wrong
}))
</script>

<style scoped>
.option-card {
  display: flex;
  align-items: center;
  gap: 22rpx;
  min-height: 112rpx;
  padding: 26rpx 28rpx;
  border-radius: 30rpx;
  border: 2rpx solid #e6ebf5;
  background: #ffffff;
  box-shadow: 0 10rpx 24rpx rgba(20, 31, 66, 0.04);
}

.option-card.selected {
  border-color: var(--gyt-primary);
  background: var(--gyt-primary-tint);
}

.option-card.correct {
  border-color: rgba(22, 163, 74, 0.4);
  background: rgba(22, 163, 74, 0.08);
}

.option-card.wrong {
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.08);
}

.option-letter {
  width: 58rpx;
  height: 58rpx;
  border-radius: 20rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.option-content {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  color: #172033;
  font-size: 31rpx;
  line-height: 1.55;
  font-weight: 800;
  overflow: hidden;
}

.option-math,
.option-text {
  width: 100%;
  min-width: 0;
  color: inherit;
  font-size: inherit;
  line-height: inherit;
  font-weight: inherit;
  word-break: break-word;
  overflow-wrap: anywhere;
}
</style>
