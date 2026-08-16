<template>
  <view class="option-card" :class="[stateClass, { compact }, compactContentClass]" @tap="$emit('select', label)">
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
  compact: {
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

const compactContentClass = computed(() => {
  if (!props.compact) return ''
  const length = String(props.content || '').replace(/\s+/g, '').length
  if (length >= 28) return 'compact-content-long'
  if (length >= 16) return 'compact-content-medium'
  return ''
})
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
  transition: border-color 180ms ease, background 180ms ease, box-shadow 180ms ease;
}

.option-card.selected {
  border-color: var(--gyt-primary);
  background: var(--gyt-primary-tint);
}

.option-card.compact {
  min-height: 112rpx;
  height: 100%;
  box-sizing: border-box;
  gap: 18rpx;
  padding: 18rpx 24rpx;
  border-radius: 26rpx;
}

.option-card.compact .option-letter {
  width: 60rpx;
  height: 60rpx;
  border-radius: 20rpx;
  font-size: 28rpx;
}

.option-card.compact .option-content {
  font-size: 29rpx;
  line-height: 1.38;
}

.option-card.compact.compact-content-medium .option-content {
  font-size: 26rpx;
  line-height: 1.36;
}

.option-card.compact.compact-content-long .option-content {
  font-size: 23rpx;
  line-height: 1.32;
}

.option-card.correct {
  border-color: #67b58a;
  background: #eaf8ef;
}

.option-card.wrong {
  border-color: #e7a0a0;
  background: #fff0f0;
}

.option-card.correct .option-letter {
  background: #258957;
  color: #ffffff;
}

.option-card.wrong .option-letter {
  background: #d65b5b;
  color: #ffffff;
}

/* 方案一使用背景图，结果态必须保持实色，避免底图透入选项卡。 */
:global(.gyt-circle-glass-theme) .option-card.selected {
  border-color: #2b9488;
  background: #e7f5f1;
  box-shadow: 0 12rpx 28rpx rgba(18, 88, 80, 0.14);
}

:global(.gyt-circle-glass-theme) .option-card.selected .option-letter {
  background: #16786f;
  color: #ffffff;
}

.option-letter {
  width: 64rpx;
  height: 64rpx;
  border-radius: 22rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
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
