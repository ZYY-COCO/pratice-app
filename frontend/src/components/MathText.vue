<template>
  <!-- #ifdef H5 -->
  <view class="math-text katex-math-text" v-html="renderedHtml"></view>
  <!-- #endif -->

  <!-- #ifndef H5 -->
  <view class="math-text">
    <template v-for="(token, index) in tokens" :key="`${token.type}-${index}`">
      <text v-if="token.type === 'text'" class="math-segment">{{ token.text }}</text>
      <text v-else-if="token.type === 'fraction'" class="math-fraction">
        <text class="fraction-part numerator">{{ token.numerator }}</text>
        <text class="fraction-line"></text>
        <text class="fraction-part denominator">{{ token.denominator }}</text>
      </text>
      <text v-else-if="token.type === 'sqrt'" class="math-root">
        <text class="sqrt-symbol">√</text>
        <text class="sqrt-radicand">{{ token.radicand }}</text>
      </text>
      <text v-else-if="token.type === 'limit'" class="math-limit">
        <text class="limit-base">lim</text>
        <text class="limit-condition">{{ token.condition }}</text>
      </text>
      <text v-else-if="token.type === 'integral'" class="math-integral">
        <text class="integral-symbol">∫</text>
        <text v-if="token.upper || token.lower" class="integral-limits">
          <text class="integral-upper">{{ token.upper }}</text>
          <text class="integral-lower">{{ token.lower }}</text>
        </text>
      </text>
      <text v-else-if="token.type === 'evalBar'" class="math-eval">
        <text class="eval-bar">|</text>
        <text class="eval-condition">{{ token.condition }}</text>
      </text>
    </template>
  </view>
  <!-- #endif -->
</template>

<script setup>
import { computed } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { escapeMathTextHtml, splitMathTextForKatex, tokenizeMathText } from '../utils/mathText'

const props = defineProps({
  value: {
    type: [String, Number],
    default: ''
  }
})

function renderKatex(latex) {
  try {
    return katex.renderToString(latex, {
      displayMode: false,
      throwOnError: false,
      strict: 'ignore',
      trust: false,
      output: 'html'
    })
  } catch (error) {
    return escapeMathTextHtml(latex)
  }
}

const renderedHtml = computed(() =>
  splitMathTextForKatex(props.value)
    .map((part) => (part.math ? renderKatex(part.content) : escapeMathTextHtml(part.content)))
    .join('')
)

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

.katex-math-text {
  white-space: normal;
}

.katex-math-text :deep(.katex) {
  color: inherit;
  font-size: 1em;
  font-weight: inherit;
  line-height: 1.25;
  white-space: nowrap;
}

.katex-math-text :deep(.katex-html) {
  white-space: nowrap;
}

.katex-math-text :deep(.base) {
  max-width: 100%;
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
  min-width: 32rpx;
  margin: 0 7rpx;
  color: inherit;
  line-height: 1;
  vertical-align: middle;
  white-space: nowrap;
}

.fraction-part {
  display: block;
  min-width: 100%;
  padding: 0 9rpx;
  color: inherit;
  font-size: 0.9em;
  font-weight: inherit;
  line-height: 1.08;
  text-align: center;
  white-space: nowrap;
}

.numerator {
  padding-bottom: 1rpx;
}

.denominator {
  padding-top: 1rpx;
}

.fraction-line {
  display: block;
  width: 100%;
  min-width: 34rpx;
  height: 2rpx;
  margin: 2rpx 0;
  border-radius: 999rpx;
  background: currentColor;
}

.math-root {
  display: inline-flex;
  align-items: flex-start;
  margin: 0 3rpx;
  color: inherit;
  line-height: 1.1;
  vertical-align: middle;
  white-space: nowrap;
}

.sqrt-symbol {
  display: inline-block;
  margin-right: 1rpx;
  color: inherit;
  font-size: 1.08em;
  font-weight: inherit;
  line-height: 1.15;
  transform: translateY(0.02em);
}

.sqrt-radicand {
  display: inline-block;
  padding: 1rpx 4rpx 0 3rpx;
  border-top: 2rpx solid currentColor;
  color: inherit;
  line-height: 1.08;
  white-space: nowrap;
}

.math-limit {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0 5rpx;
  color: inherit;
  line-height: 1;
  vertical-align: middle;
  white-space: nowrap;
}

.limit-base {
  display: block;
  color: inherit;
  font-size: 0.95em;
  line-height: 0.95;
}

.limit-condition {
  display: block;
  margin-top: -1rpx;
  color: inherit;
  font-size: 0.52em;
  font-weight: 700;
  line-height: 1;
}

.math-integral {
  display: inline-flex;
  align-items: center;
  margin: 0 4rpx;
  color: inherit;
  line-height: 1;
  vertical-align: middle;
  white-space: nowrap;
}

.integral-symbol {
  display: inline-block;
  color: inherit;
  font-family: 'Times New Roman', 'STIX Two Math', serif;
  font-size: 1.42em;
  font-weight: 500;
  line-height: 1;
  transform: translateY(0.02em);
}

.integral-limits {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  margin-left: -2rpx;
  color: inherit;
  line-height: 1;
}

.integral-upper,
.integral-lower {
  display: block;
  min-height: 0.62em;
  color: inherit;
  font-size: 0.55em;
  font-weight: 700;
  line-height: 0.95;
}

.math-eval {
  display: inline-flex;
  align-items: flex-end;
  margin: 0 4rpx;
  color: inherit;
  line-height: 1;
  vertical-align: middle;
  white-space: nowrap;
}

.eval-bar {
  display: inline-block;
  color: inherit;
  font-size: 1.7em;
  font-weight: 400;
  line-height: 0.9;
}

.eval-condition {
  display: inline-block;
  margin-left: 1rpx;
  color: inherit;
  font-size: 0.58em;
  font-weight: 700;
  line-height: 1;
  transform: translateY(0.22em);
}
</style>
