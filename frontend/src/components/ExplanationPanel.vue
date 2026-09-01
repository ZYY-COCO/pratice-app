<template>
  <view v-if="visible" class="panel">
    <view class="panel-head">
      <view class="title">题目解析</view>
      <view v-if="autoTag" class="tag">{{ autoTag }}</view>
    </view>

    <view class="answer-card">
      <view class="answer-copy">
        <text class="answer-kicker">本题答案</text>
        <text class="answer-hint">先看判断依据，再核对选项边界</text>
      </view>
      <view class="answer-value">{{ answerLetter || correctAnswer || '—' }}</view>
    </view>

    <view v-if="firstScreenBlocks.length" class="insight-list">
      <view
        v-for="block in firstScreenBlocks"
        :key="block.key"
        class="insight-card"
        :class="`insight-card--${block.key}`"
      >
        <view class="block-label">
          <view class="block-dot"></view>
          <text>{{ block.label }}</text>
        </view>
        <MathText class="block-content" :value="block.content" />
      </view>
    </view>

    <view v-if="parsedExplanation.distractors.length" class="comparison-card">
      <view
        class="comparison-toggle"
        role="button"
        :aria-expanded="distractorsExpanded"
        @tap="toggleDistractors"
      >
        <view class="comparison-copy">
          <text class="comparison-title">选项解析</text>
          <text class="comparison-subtitle">
            {{ distractorsExpanded ? '逐项查看判断边界' : (reverseQuestion ? '逆向题建议先看排除逻辑' : '点击展开四项解析') }}
          </text>
        </view>
        <view class="comparison-action">
          <text>{{ distractorsExpanded ? '收起' : '展开' }}</text>
          <text class="comparison-chevron" :class="{ rotated: distractorsExpanded }">⌄</text>
        </view>
      </view>

      <view v-if="distractorsExpanded" class="comparison-body">
        <view
          v-for="item in parsedExplanation.distractors"
          :key="item.key"
          class="distractor-row"
          :class="{ 'distractor-row--correct': item.isCorrect }"
        >
          <view class="option-badge">{{ item.label }}</view>
          <MathText class="distractor-content" :value="item.reason" />
        </view>
      </view>
    </view>

    <view v-if="parsedExplanation.fallback" class="supplement-card">
      <view
        class="supplement-toggle"
        role="button"
        :aria-expanded="supplementExpanded"
        @tap="toggleSupplement"
      >
        <view class="comparison-copy">
          <text class="comparison-title">补充解析</text>
          <text class="comparison-subtitle">{{ supplementExpanded ? '收起补充信息' : '展开查看完整补充信息' }}</text>
        </view>
        <view class="comparison-action">
          <text>{{ supplementExpanded ? '收起' : '展开' }}</text>
          <text class="comparison-chevron" :class="{ rotated: supplementExpanded }">⌄</text>
        </view>
      </view>
      <view v-if="supplementExpanded" class="supplement-body">
        <MathText class="block-content" :value="parsedExplanation.fallback" />
      </view>
    </view>

    <view v-if="!firstScreenBlocks.length && !parsedExplanation.fallback" class="empty-card">
      <text>解析正在同步中，请稍后再试。</text>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import MathText from './MathText.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  correctAnswer: {
    type: String,
    default: ''
  },
  explanation: {
    type: String,
    default: ''
  },
  autoTag: {
    type: String,
    default: ''
  }
})

const V2_MARKER_RE = /(?:^|\n)\s*(解题思路|选项解析|知识点|记忆方法)\s*[：:]\s*/gm
const INLINE_V2_MARKER_RE = /(解题思路|选项解析|知识点|记忆方法)\s*[：:]\s*/g
const LEGACY_STRUCTURED_MARKER_RE = /(?:^|\n)\s*(为什么|关键知识|易混辨析|记忆提醒)\s*[：:]\s*/gm
const INLINE_LEGACY_STRUCTURED_MARKER_RE = /(为什么|关键知识|易混辨析|记忆提醒)\s*[：:]\s*/g
const LEGACY_MARKER_RE = /(?:^|\n)\s*(考点定位|正确项依据|选项辨析|做题提醒|记忆提示)\s*[：:]\s*/gm
const INLINE_LEGACY_MARKER_RE = /(考点定位|正确项依据|选项辨析|做题提醒|记忆提示)\s*[：:]\s*/g
const OPTION_LINE_RE = /(?:^|\n)\s*([ABCD])\s*[.．、:：]\s*/gm
const INLINE_OPTION_RE = /(?:^|[。！？；;])\s*([ABCD])\s*[.．、:：]\s*/g
const REVERSE_MARKER_RE = /不正确|不属于|不包括|并非|不是|不符合|错误的是|错误项|有误的是|不当的是|不同的是|不相同|不能说明|不应|不宜|需排除|排除对象|被排除|不在(?:该|此|本|名单|其中|范围)|设对照|例外|逆向题/

function normalizeText(value) {
  return String(value ?? '')
    .replace(/\r\n?/g, '\n')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function cleanText(value) {
  return normalizeText(value).replace(/^\s*[：:]\s*/, '').trim()
}

function stripAnswerHeader(value) {
  return cleanText(value)
    .replace(/^【[^】]{1,30}】\s*/, '')
    .replace(/^(?:答案|正确答案)(?:为|是)?\s*[：:]?\s*[ABCD](?:\s*[（(][^）)]*[）)])?\s*[。．、]?\s*/i, '')
    .replace(/^[。．、；;：:\s]+/, '')
    .trim()
}

function compactPlainExplanation(value) {
  const full = stripAnswerHeader(value)
  if (!full) return { short: '', rest: '' }
  const sentences = full.match(/[^。！？；]*[。！？；]?/g)?.filter(Boolean) || [full]
  let short = ''
  for (const sentence of sentences) {
    if (!sentence.trim()) continue
    if (short && short.length + sentence.length > 110) break
    short += sentence
    if (short.length >= 58) break
  }
  short = cleanText(short || full)
  if (short.length > 120) {
    short = `${short.slice(0, 117).replace(/[，、；：: ]+$/, '')}…`
  }
  const rest = full.length > short.length ? full.slice(full.indexOf(short.replace(/…$/, '')) + short.replace(/…$/, '').length).replace(/^[。！？；\s]+/, '') : ''
  return { short, rest }
}

function appendSection(target, key, value) {
  const content = cleanText(value)
  if (!content) return
  target[key] = target[key] ? `${target[key]}\n${content}` : content
}

function findMatches(text, pattern) {
  pattern.lastIndex = 0
  const matches = []
  let match
  while ((match = pattern.exec(text))) {
    matches.push(match)
    if (!match[0]) pattern.lastIndex += 1
  }
  return matches
}

function collectSections(text, markerRe, inlineMarkerRe, markerMap) {
  let matches = findMatches(text, markerRe)
  if (!matches.length) {
    matches = findMatches(text, inlineMarkerRe)
  }
  if (!matches.length) return null

  const sections = {}
  const firstStart = matches[0].index ?? 0
  const prefix = text.slice(0, firstStart)
  matches.forEach((match, index) => {
    const label = match[1]
    const key = markerMap[label]
    if (!key) return
    const start = (match.index ?? 0) + match[0].length
    const end = index + 1 < matches.length ? (matches[index + 1].index ?? text.length) : text.length
    appendSection(sections, key, text.slice(start, end))
  })

  return { sections, prefix }
}

function parseDistractors(value) {
  const text = cleanText(value)
  if (!text) return []

  let matches = findMatches(text, OPTION_LINE_RE)
  const inlineMatches = findMatches(text, INLINE_OPTION_RE)
  if (inlineMatches.length > matches.length) {
    matches = inlineMatches
  }
  if (!matches.length) return []

  const answer = String(props.correctAnswer || '').trim().toUpperCase().match(/[ABCD]/)?.[0] || ''
  return matches
    .map((match, index) => {
      const label = match[1]
      const start = (match.index ?? 0) + match[0].length
      const end = index + 1 < matches.length ? (matches[index + 1].index ?? text.length) : text.length
      let reason = cleanText(text.slice(start, end))
      reason = reason.replace(/^正确答案\s*[：:]\s*/, '正确：')
      reason = reason.replace(/^正确项\s*[：:]\s*/, '正确：')
      return {
        key: `${label}-${index}`,
        label,
        reason,
        isCorrect: Boolean(answer && label === answer)
      }
    })
    .filter((item) => item.reason)
}

function parseExplanation(value) {
  const raw = normalizeText(value)
  if (!raw) {
    return { why: '', knowledge: '', memory: '', distractors: [], fallback: '' }
  }

  // V2 labels are parsed first and therefore win if a migrated row happens
  // to contain both formats.  Legacy labels are used only to fill a missing
  // block, preserving backward compatibility with already-published rows.
  const v2 = collectSections(
    raw,
    V2_MARKER_RE,
    INLINE_V2_MARKER_RE,
    { 解题思路: 'why', 选项解析: 'distractorsText', 知识点: 'knowledge', 记忆方法: 'memory' }
  )

  const legacyStructured = collectSections(
    raw,
    LEGACY_STRUCTURED_MARKER_RE,
    INLINE_LEGACY_STRUCTURED_MARKER_RE,
    { 为什么: 'why', 关键知识: 'knowledge', 易混辨析: 'distractorsText', 记忆提醒: 'memory' }
  )

  if (v2 || legacyStructured) {
    const v2Sections = v2?.sections || {}
    const legacySections = legacyStructured?.sections || {}
    const why = stripAnswerHeader(v2Sections.why || legacySections.why || v2?.prefix || legacyStructured?.prefix || '')
    const knowledge = cleanText(v2Sections.knowledge || legacySections.knowledge)
    const memory = cleanText(v2Sections.memory || legacySections.memory)
    const distractorText = v2Sections.distractorsText || legacySections.distractorsText
    const distractors = parseDistractors(distractorText)
    const fallback = !why && !knowledge && !memory && !distractors.length ? stripAnswerHeader(raw) : ''
    return { why, knowledge, memory, distractors, fallback }
  }

  const legacy = collectSections(
    raw,
    LEGACY_MARKER_RE,
    INLINE_LEGACY_MARKER_RE,
    { 考点定位: 'knowledge', 正确项依据: 'why', 选项辨析: 'distractorsText', 做题提醒: 'memory', 记忆提示: 'memory' }
  )

  if (legacy) {
    const sections = legacy.sections
    const why = stripAnswerHeader(sections.why || legacy.prefix)
    const knowledge = cleanText(sections.knowledge)
    const memory = cleanText(sections.memory)
    const distractors = parseDistractors(sections.distractorsText)
    const remainder = !why && !knowledge && !memory && !distractors.length ? stripAnswerHeader(raw) : ''
    return { why, knowledge, memory, distractors, fallback: remainder }
  }

  const plain = compactPlainExplanation(raw)
  return {
    why: plain.short,
    knowledge: '',
    memory: '',
    distractors: [],
    fallback: plain.rest
  }
}

const parsedExplanation = computed(() => parseExplanation(props.explanation))

const firstScreenBlocks = computed(() =>
  [
    { key: 'why', label: '解题思路', content: parsedExplanation.value.why },
    { key: 'knowledge', label: '知识点', content: parsedExplanation.value.knowledge },
    { key: 'memory', label: '记忆方法', content: parsedExplanation.value.memory }
  ].filter((block) => block.content)
)

const answerLetter = computed(() => String(props.correctAnswer || '').trim().toUpperCase().match(/[ABCD]/)?.[0] || '')

const reverseQuestion = computed(() => {
  const rawLead = parsedExplanation.value.why ? '' : normalizeText(props.explanation).slice(0, 150)
  const parsedLead = parsedExplanation.value.why.slice(0, 180)
  return REVERSE_MARKER_RE.test(`${rawLead} ${parsedLead} ${props.autoTag || ''}`)
})

const distractorsExpanded = ref(false)
const supplementExpanded = ref(false)

watch(
  () => [props.explanation, props.correctAnswer, props.visible],
  () => {
    distractorsExpanded.value = reverseQuestion.value
    supplementExpanded.value = false
  },
  { immediate: true }
)

function toggleDistractors() {
  distractorsExpanded.value = !distractorsExpanded.value
}

function toggleSupplement() {
  supplementExpanded.value = !supplementExpanded.value
}
</script>

<style scoped>
.panel {
  padding: 24rpx;
  border-radius: 32rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 14rpx 34rpx rgba(20, 31, 66, 0.06);
}

.panel-head {
  min-height: 42rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.title {
  color: #172033;
  font-size: 30rpx;
  line-height: 1.35;
  font-weight: 900;
}

.tag {
  max-width: 48%;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: #f1f5ff;
  color: #4b67c8;
  font-size: 21rpx;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.answer-card {
  margin-top: 18rpx;
  padding: 20rpx 22rpx;
  border-radius: 24rpx;
  border: 2rpx solid #dce7ff;
  background: linear-gradient(135deg, #f5f8ff 0%, #eef4ff 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.answer-copy {
  min-width: 0;
  flex: 1;
}

.answer-kicker {
  display: block;
  color: #2e5fd3;
  font-size: 24rpx;
  line-height: 1.35;
  font-weight: 900;
}

.answer-hint {
  display: block;
  margin-top: 5rpx;
  color: #7180a0;
  font-size: 21rpx;
  line-height: 1.4;
}

.answer-value {
  min-width: 72rpx;
  height: 72rpx;
  padding: 0 14rpx;
  box-sizing: border-box;
  border-radius: 22rpx;
  background: #2f6fec;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  line-height: 1;
  font-weight: 900;
  box-shadow: 0 10rpx 20rpx rgba(47, 111, 236, 0.22);
}

.insight-list {
  margin-top: 18rpx;
}

.insight-card,
.supplement-card,
.empty-card {
  padding: 20rpx 22rpx;
  border-radius: 24rpx;
  border: 2rpx solid #edf0f6;
  background: #fbfcff;
}

.insight-card + .insight-card {
  margin-top: 14rpx;
}

.insight-card--why {
  border-color: #dce7ff;
  background: #f7f9ff;
}

.insight-card--knowledge {
  border-color: #d9eee5;
  background: #f6fcf9;
}

.insight-card--memory {
  border-color: #f4e5c7;
  background: #fffaf1;
}

.block-label {
  display: flex;
  align-items: center;
  color: #263653;
  font-size: 23rpx;
  line-height: 1.35;
  font-weight: 900;
}

.block-dot {
  width: 12rpx;
  height: 12rpx;
  margin-right: 10rpx;
  border-radius: 50%;
  background: #4c79ed;
  flex: 0 0 auto;
}

.insight-card--knowledge .block-dot {
  background: #36a879;
}

.insight-card--memory .block-dot {
  background: #d99632;
}

.block-content {
  display: block;
  margin-top: 10rpx;
  color: #43516d;
  font-size: 25rpx;
  line-height: 1.68;
}

.comparison-card {
  margin-top: 16rpx;
  overflow: hidden;
  border-radius: 24rpx;
  border: 2rpx solid #e5eaf3;
  background: #ffffff;
}

.comparison-toggle {
  min-height: 86rpx;
  padding: 16rpx 20rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.comparison-copy {
  min-width: 0;
  flex: 1;
}

.comparison-title {
  display: block;
  color: #273754;
  font-size: 25rpx;
  line-height: 1.35;
  font-weight: 900;
}

.comparison-subtitle {
  display: block;
  margin-top: 4rpx;
  color: #8290a9;
  font-size: 21rpx;
  line-height: 1.35;
}

.comparison-action {
  display: flex;
  align-items: center;
  color: #4c70cf;
  font-size: 22rpx;
  line-height: 1;
  font-weight: 800;
  flex: 0 0 auto;
}

.comparison-chevron {
  margin-left: 8rpx;
  font-size: 30rpx;
  line-height: 0.7;
  transform: translateY(-3rpx);
  transition: transform 160ms ease;
}

.comparison-chevron.rotated {
  transform: rotate(180deg) translateY(3rpx);
}

.comparison-body {
  border-top: 2rpx solid #edf1f7;
  background: #fbfcff;
}

.distractor-row {
  padding: 16rpx 20rpx;
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  border-bottom: 2rpx solid #edf1f7;
}

.distractor-row:last-child {
  border-bottom: 0;
}

.distractor-row--correct {
  background: #f1f8f4;
}

.option-badge {
  width: 42rpx;
  height: 42rpx;
  border-radius: 14rpx;
  background: #edf2fb;
  color: #5b6a84;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  line-height: 1;
  font-weight: 900;
  flex: 0 0 auto;
}

.distractor-row--correct .option-badge {
  background: #2d9c6c;
  color: #ffffff;
}

.distractor-content {
  min-width: 0;
  flex: 1;
  color: #53617b;
  font-size: 23rpx;
  line-height: 1.6;
}

.supplement-card {
  margin-top: 16rpx;
  overflow: hidden;
}

.supplement-toggle {
  min-height: 82rpx;
  padding: 16rpx 20rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.supplement-body {
  padding: 0 20rpx 18rpx;
  border-top: 2rpx solid #edf1f7;
  background: #fbfcff;
}

.empty-card {
  margin-top: 16rpx;
  color: #8a96aa;
  font-size: 23rpx;
  line-height: 1.6;
  text-align: center;
}
</style>
