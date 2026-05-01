<template>
  <view class="math-text">
    <template v-for="(token, index) in tokens" :key="`${token.type}-${index}`">
      <text v-if="token.type === 'text'" class="math-segment">{{ token.text }}</text>
      <text v-else class="math-fraction">
        <text class="fraction-part numerator">{{ token.numerator }}</text>
        <text class="fraction-line"></text>
        <text class="fraction-part denominator">{{ token.denominator }}</text>
      </text>
    </template>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { tokenizeMathText } from '../utils/mathText'

const props = defineProps({
  value: {
    type: [String, Number],
    default: ''
  }
})

const tokens = computed(() => tokenizeMathText(props.value))
</script>

<style scoped>
.math-text {
  display: block;
  color: inherit;
  font-size: inherit;
  font-weight: inherit;
  line-height: inherit;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.math-segment {
  display: inline;
  color: inherit;
  font-size: inherit;
  font-weight: inherit;
  line-height: inherit;
  white-space: pre-wrap;
}

.math-fraction {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 26rpx;
  margin: 0 4rpx;
  color: inherit;
  line-height: 1;
  vertical-align: middle;
}

.fraction-part {
  display: block;
  padding: 0 6rpx;
  color: inherit;
  font-size: 0.78em;
  font-weight: inherit;
  line-height: 1.05;
  white-space: nowrap;
}

.fraction-line {
  display: block;
  width: 100%;
  min-width: 24rpx;
  height: 2rpx;
  margin: 3rpx 0;
  border-radius: 999rpx;
  background: currentColor;
}
</style>
