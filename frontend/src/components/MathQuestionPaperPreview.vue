<template>
  <view class="math-paper-preview">
    <view class="preview-heading">
      <view>
        <text class="preview-kicker">MATH PREVIEW</text>
        <view class="preview-title">数学试卷排版预览</view>
      </view>
      <text class="preview-hint">仅优化显示，不改动原始题目内容</text>
    </view>

    <view class="preview-section question-section">
      <text class="section-label">题目</text>
      <MathText class="preview-stem" :value="stem || '请填写题干'" />
    </view>

    <view class="preview-options">
      <view
        v-for="item in optionItems"
        :key="item.label"
        class="preview-option"
        :class="{ correct: normalizedAnswer === item.label }"
      >
        <text class="option-label">{{ item.label }}.</text>
        <MathText class="option-value" :value="item.value || '未填写选项'" />
      </view>
    </view>

    <view class="preview-answer">
      <text>参考答案</text>
      <text class="answer-value">{{ normalizedAnswer || '未设置' }}</text>
    </view>

    <view class="preview-section explanation-section">
      <text class="section-label">解析</text>
      <MathText class="preview-explanation" :value="explanation || '暂无解析'" />
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import MathText from './MathText.vue'

const props = defineProps({
  stem: {
    type: [String, Number],
    default: ''
  },
  optionA: {
    type: [String, Number],
    default: ''
  },
  optionB: {
    type: [String, Number],
    default: ''
  },
  optionC: {
    type: [String, Number],
    default: ''
  },
  optionD: {
    type: [String, Number],
    default: ''
  },
  answer: {
    type: [String, Number],
    default: ''
  },
  explanation: {
    type: [String, Number],
    default: ''
  }
})

const normalizedAnswer = computed(() => String(props.answer || '').trim().toUpperCase())
const optionItems = computed(() => [
  { label: 'A', value: props.optionA },
  { label: 'B', value: props.optionB },
  { label: 'C', value: props.optionC },
  { label: 'D', value: props.optionD }
])
</script>

<style scoped>
.math-paper-preview {
  padding: 16px;
  border: 1px solid #d8e4e8;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 8px 22px rgba(28, 54, 73, 0.06);
  box-sizing: border-box;
}

.preview-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8eef1;
}

.preview-kicker {
  display: block;
  color: #33a990;
  font-size: 9px;
  font-weight: 900;
  letter-spacing: 1.2px;
}

.preview-title {
  margin-top: 4px;
  color: #10243d;
  font-size: 14px;
  font-weight: 900;
}

.preview-hint {
  color: #8795a7;
  font-size: 9px;
  line-height: 1.5;
  text-align: right;
}

.preview-section {
  margin-top: 13px;
}

.section-label {
  display: block;
  margin-bottom: 7px;
  color: #607189;
  font-size: 10px;
  font-weight: 800;
}

.preview-stem {
  color: #111f34;
  font-family: 'Times New Roman', 'Noto Serif SC', 'Songti SC', serif;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.8;
}

.preview-options {
  margin-top: 13px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.preview-option {
  min-height: 42px;
  padding: 9px 11px;
  display: flex;
  align-items: flex-start;
  gap: 9px;
  border: 1px solid #e1e8ec;
  border-radius: 9px;
  color: #25364c;
  background: #fbfcfd;
  box-sizing: border-box;
}

.preview-option.correct {
  border-color: #65cdb7;
  background: #f0faf7;
}

.option-label {
  flex: 0 0 auto;
  color: #51647c;
  font-size: 12px;
  font-weight: 900;
  line-height: 1.65;
}

.preview-option.correct .option-label {
  color: #16836e;
}

.option-value {
  min-width: 0;
  color: inherit;
  font-family: 'Times New Roman', 'Noto Serif SC', 'Songti SC', serif;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.65;
}

.preview-answer {
  margin-top: 11px;
  display: flex;
  align-items: center;
  gap: 9px;
  color: #66768b;
  font-size: 10px;
  font-weight: 700;
}

.answer-value {
  min-width: 25px;
  height: 25px;
  padding: 0 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  color: #167563;
  background: #dff5ef;
  font-size: 11px;
  font-weight: 900;
  box-sizing: border-box;
}

.explanation-section {
  padding: 11px 12px;
  border-radius: 9px;
  background: #f5f8fa;
}

.preview-explanation {
  color: #47586e;
  font-family: 'Times New Roman', 'Noto Serif SC', 'Songti SC', serif;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.75;
}

@media (max-width: 720px) {
  .preview-heading {
    flex-direction: column;
  }

  .preview-hint {
    text-align: left;
  }

  .preview-options {
    grid-template-columns: 1fr;
  }
}
</style>
