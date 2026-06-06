<template>
  <!-- #ifdef H5 || APP-PLUS -->
  <view class="math-text katex-math-text" v-html="renderedHtml"></view>
  <!-- #endif -->

  <!-- #ifdef MP-WEIXIN -->
  <view class="math-text math-text-plain">
    <block v-for="part in miniProgramParts" :key="part.key">
      <image
        v-if="part.type === 'image' && !imageFailed"
        class="math-formula-image"
        :src="part.src"
        :style="{ width: `${part.displayRpx}rpx` }"
        mode="widthFix"
        @error="handleImageError"
      />
      <text v-else class="math-text-inner">{{ part.text }}</text>
    </block>
  </view>
  <!-- #endif -->
</template>

<script setup>
import { computed, ref, watch } from 'vue'
// #ifdef H5 || APP-PLUS
import katex from 'katex'
import 'katex/dist/katex.min.css'
// #endif
// #ifdef MP-WEIXIN
import { API_BASE_URL } from '../api/config'
// #endif
import {
  escapeMathTextHtml,
  estimateMathImageDisplayRpx,
  formatMathText,
  shouldUseMathImage,
  splitMathTextForKatex
} from '../utils/mathText'

const props = defineProps({
  value: {
    type: [String, Number],
    default: ''
  }
})

// #ifdef H5 || APP-PLUS
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
// #endif

// #ifdef MP-WEIXIN
const plainText = computed(() => formatMathText(props.value))
const imageFailed = ref(false)

function getWindowWidthPx() {
  try {
    return uni.getSystemInfoSync().windowWidth || 375
  } catch (error) {
    return 375
  }
}

const windowWidthPx = getWindowWidthPx()

function mergeTrailingFormulaPunctuation(parts) {
  const merged = []
  parts.forEach((part) => {
    const content = String(part.content ?? '')
    const previous = merged[merged.length - 1]
    const match = !part.math ? content.match(/^([,.;:?!，。；：？！、）)\]]+)([\s\S]*)$/) : null

    if (match && previous?.math) {
      previous.content = `${previous.content}${match[1]}`
      if (match[2]) {
        merged.push({ ...part, content: match[2] })
      }
      return
    }

    merged.push({ ...part })
  })
  return merged
}

const miniProgramParts = computed(() => {
  const parts = mergeTrailingFormulaPunctuation(splitMathTextForKatex(props.value))
  if (!parts.length) {
    return [{ key: 'plain-0', type: 'text', text: plainText.value }]
  }

  return parts.map((part, index) => {
    if (!part.math || !shouldUseMathImage(part.content)) {
      return {
        key: `text-${index}`,
        type: 'text',
        text: part.math ? formatMathText(part.content) : part.content
      }
    }

    const displayRpx = estimateMathImageDisplayRpx(part.content)
    const renderWidthPx = Math.max(80, Math.round((displayRpx / 750) * windowWidthPx))
    const text = encodeURIComponent(String(part.content ?? ''))
    return {
      key: `image-${index}`,
      type: 'image',
      text: formatMathText(part.content),
      displayRpx,
      src: `${API_BASE_URL}/formula/svg?text=${text}&width=${renderWidthPx}&size=24&v=4`
    }
  })
})

watch(
  () => props.value,
  () => {
    imageFailed.value = false
  }
)

function handleImageError() {
  imageFailed.value = true
  // eslint-disable-next-line no-console
  console.warn('[math-render-failed]', props.value)
}
// #endif
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

.math-text-plain {
  display: inline;
  white-space: normal;
  text-align: left;
}

.math-text-inner {
  display: inline;
  color: inherit;
  font-size: inherit;
  font-weight: inherit;
  line-height: inherit;
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.math-formula-image {
  display: inline-block;
  max-width: 100%;
  margin: 0 6rpx;
  vertical-align: -0.2em;
}

/* #ifdef H5 */
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
/* #endif */

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

.math-cases {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  margin: 0 6rpx;
  color: inherit;
  line-height: 1.12;
  vertical-align: middle;
}

.cases-brace {
  display: inline-block;
  margin-right: 8rpx;
  color: inherit;
  font-family: 'Times New Roman', 'STIX Two Math', serif;
  font-size: 2.45em;
  font-weight: 400;
  line-height: 0.9;
  transform: scaleX(0.74);
}

.cases-rows {
  display: inline-flex;
  flex-direction: column;
  gap: 7rpx;
  min-width: 0;
}

.cases-row {
  display: flex;
  align-items: center;
  min-width: 0;
  color: inherit;
  font-size: 0.88em;
  line-height: 1.14;
}

.cases-expression {
  display: inline-flex;
  min-width: 0;
  color: inherit;
  font-size: inherit;
  font-weight: inherit;
  line-height: inherit;
}

.cases-condition {
  display: inline-block;
  margin-left: 12rpx;
  color: inherit;
  font-size: 0.92em;
  font-weight: inherit;
  line-height: 1.14;
  white-space: nowrap;
}
</style>
