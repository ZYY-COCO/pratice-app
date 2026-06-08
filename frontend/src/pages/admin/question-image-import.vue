<template>
  <view class="image-import-page" :style="themeInlineStyle">
    <view class="import-hero">
      <button class="back-btn" @tap="goBack">
        <image class="back-icon" src="/static/ui-icons/back.svg" mode="aspectFit" />
      </button>
      <view class="hero-copy">
        <view class="hero-title">批量导入图片</view>
        <view class="hero-subtitle">上传截图、校对题目，统一进入待审核</view>
      </view>
    </view>

    <view v-if="loading" class="screen-state">正在验证后台权限...</view>
    <view v-else-if="!allowed" class="screen-state">当前账号无后台权限</view>

    <view v-else class="import-content">
      <view class="step-strip">
        <view v-for="step in steps" :key="step.title" class="step-item" :class="{ active: step.active }">
          <view class="step-index">{{ step.index }}</view>
          <view>
            <view class="step-title">{{ step.title }}</view>
            <view class="step-desc">{{ step.desc }}</view>
          </view>
        </view>
      </view>

      <view class="import-panel">
        <view class="panel-head">
          <view>
            <view class="panel-title">默认分类</view>
            <view class="panel-subtitle">解析出的题目会先套用这里的分类，之后可逐题修改。</view>
          </view>
          <button class="mini-btn" @tap="applyDefaultsToDrafts">应用到全部</button>
        </view>

        <view class="picker-grid">
          <picker :range="subjectLabels" :value="selectedSubjectIndex" @change="handleSubjectChange">
            <view class="picker-pill">{{ importDefaults.subject }}<text>⌄</text></view>
          </picker>
          <picker :range="moduleLabels" :value="selectedModuleIndex" @change="handleModuleChange">
            <view class="picker-pill">{{ importDefaults.module }}<text>⌄</text></view>
          </picker>
          <picker :range="submoduleLabels" :value="selectedSubmoduleIndex" @change="handleSubmoduleChange">
            <view class="picker-pill">{{ importDefaults.submodule }}<text>⌄</text></view>
          </picker>
          <picker :range="difficultyLabels" :value="selectedDifficultyIndex" @change="handleDifficultyChange">
            <view class="picker-pill">难度 {{ importDefaults.difficulty }}<text>⌄</text></view>
          </picker>
        </view>
      </view>

      <view class="import-panel">
        <view class="panel-head">
          <view>
            <view class="panel-title">图片与识别文本</view>
            <view class="panel-subtitle">选择图片后，把 OCR 或人工整理的文本粘贴到对应图片下方。</view>
          </view>
          <button class="primary-mini-btn" @tap="chooseImages">选择图片</button>
        </view>

        <view v-if="imageItems.length === 0" class="upload-empty" @tap="chooseImages">
          <view class="upload-icon">＋</view>
          <view class="upload-title">添加题目图片</view>
          <view class="upload-desc">支持一次选择多张截图，图片用于整理来源，导入数据库前仍需校对文本。</view>
        </view>

        <view v-else class="image-list">
          <view v-for="(item, index) in imageItems" :key="item.id" class="image-row">
            <image class="thumb" :src="item.path" mode="aspectFill" @tap="previewImage(item)" />
            <view class="image-main">
              <view class="image-title-row">
                <view>
                  <view class="image-name">{{ item.name }}</view>
                  <view class="image-meta">第 {{ index + 1 }} 张 · {{ formatSize(item.size) }}</view>
                </view>
                <button class="remove-btn" @tap="removeImage(item.id)">移除</button>
              </view>
              <textarea
                v-model="item.rawText"
                class="ocr-textarea"
                placeholder="粘贴识别文本，例如：题干...&#10;A. ...&#10;B. ...&#10;C. ...&#10;D. ...&#10;答案：B&#10;解析：..."
                @input="markDryRunDirty"
              />
              <view class="image-actions">
                <button class="line-btn" @tap="parseSingleImage(item)">解析这张</button>
                <text class="image-status">{{ item.status || '待解析' }}</text>
              </view>
            </view>
          </view>
        </view>

        <view class="wide-actions">
          <button class="outline-action" @tap="addBlankDraft">手动新增一题</button>
          <button class="filled-action" @tap="parseAllImages">解析全部文本</button>
        </view>
      </view>

      <view class="import-panel">
        <view class="panel-head">
          <view>
            <view class="panel-title">待导入预览</view>
            <view class="panel-subtitle">所有题目会以“已下架 / 待审核”写入，老师再进入审核队列发布。</view>
          </view>
          <view class="count-badge">{{ drafts.length }} 题</view>
        </view>

        <view v-if="drafts.length === 0" class="draft-empty">还没有解析出的题目</view>

        <view v-else class="draft-list">
          <view v-for="(draft, index) in drafts" :key="draft.id" class="draft-card" :class="draftTone(draft, index)">
            <view class="draft-head">
              <view>
                <view class="draft-title">题目 {{ index + 1 }}</view>
                <view class="draft-source">{{ draft.image_name || '手动新增' }}</view>
              </view>
              <view class="draft-status">{{ draftStatusText(draft, index) }}</view>
            </view>

            <view class="draft-picker-grid">
              <picker :range="subjectLabels" :value="draftSubjectIndex(draft)" @change="handleDraftSubjectChange(draft, $event)">
                <view class="draft-picker">{{ draft.subject }}<text>⌄</text></view>
              </picker>
              <picker :range="draftModuleLabels(draft)" :value="draftModuleIndex(draft)" @change="handleDraftModuleChange(draft, $event)">
                <view class="draft-picker">{{ draft.module }}<text>⌄</text></view>
              </picker>
              <picker :range="draftSubmoduleLabels(draft)" :value="draftSubmoduleIndex(draft)" @change="handleDraftSubmoduleChange(draft, $event)">
                <view class="draft-picker">{{ draft.submodule }}<text>⌄</text></view>
              </picker>
              <picker :range="difficultyLabels" :value="difficultyIndex(draft.difficulty)" @change="handleDraftDifficultyChange(draft, $event)">
                <view class="draft-picker">难度 {{ draft.difficulty }}<text>⌄</text></view>
              </picker>
            </view>

            <textarea v-model="draft.stem" class="draft-textarea stem" placeholder="题干" @input="markDryRunDirty" />
            <view class="option-editor">
              <view v-for="option in answerOptions" :key="option" class="option-row" :class="{ selected: draft.answer === option }">
                <button class="answer-dot" @tap="setDraftAnswer(draft, option)">{{ draft.answer === option ? '●' : '○' }}</button>
                <text class="option-label">{{ option }}.</text>
                <input
                  :value="draftOptionValue(draft, option)"
                  class="option-input"
                  :placeholder="`${option} 选项`"
                  @input="handleDraftOptionInput(draft, option, $event)"
                />
              </view>
            </view>
            <textarea v-model="draft.explanation" class="draft-textarea explanation" placeholder="解析 / 答案理由" @input="markDryRunDirty" />

            <view v-if="draftErrors(draft, index).length" class="error-list">
              <view v-for="error in draftErrors(draft, index)" :key="error" class="error-item">{{ error }}</view>
            </view>

            <view class="draft-actions">
              <button class="line-btn" @tap="duplicateDraft(draft)">复制</button>
              <button class="danger-line-btn" @tap="removeDraft(draft.id)">删除</button>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view v-if="allowed" class="import-bottom-bar">
      <view class="bottom-summary">
        <text>草稿 {{ drafts.length }}</text>
        <text>有效 {{ dryRunResult?.valid_count || 0 }}</text>
        <text>问题 {{ (dryRunResult?.invalid_count || 0) + (dryRunResult?.duplicate_count || 0) }}</text>
      </view>
      <button class="bottom-btn outline" :disabled="dryRunLoading || importSaving || drafts.length === 0" @tap="runDryCheck">
        {{ dryRunLoading ? '校验中' : 'Dry-run 校验' }}
      </button>
      <button class="bottom-btn primary" :disabled="!canCommit || importSaving" @tap="commitImport">
        {{ importSaving ? '导入中' : '导入待审核' }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  commitAdminQuestionImageImport,
  dryRunAdminQuestionImageImport,
  fetchAdminMe
} from '../../api/admin'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const loading = ref(true)
const allowed = ref(false)
const imageItems = ref([])
const drafts = ref([])
const dryRunResult = ref(null)
const dryRunLoading = ref(false)
const importSaving = ref(false)
const answerOptions = ['A', 'B', 'C', 'D']

const importCatalog = {
  中华文化: {
    exam_code: 'COMMON',
    modules: {
      中国哲学常识: ['儒家', '道家', '墨家', '法家', '名家', '纵横家', '后代学派流变', '古代宗教流变'],
      中国历史学常识: ['古代职官与科举', '古代礼俗与称谓', '古代衣食住行', '古代军事战争', '古代经济发展', '古代图书文物', '近现代史学常识'],
      中国文学常识: ['文体流变', '代表作家及作品', '创作群体及文学流派', '文学总集', '民族史诗'],
      中国艺术常识: ['书法', '绘画', '雕塑', '建筑', '音乐', '戏剧', '民俗', '陶瓷'],
      中国古代科技常识: ['天文历法与算学', '地理舆图', '农业水利', '医学', '科技发明']
    }
  },
  英语运用: {
    exam_code: 'COMMON',
    modules: {
      语言知识: ['词汇', '语法', '语用']
    }
  },
  数学基础: {
    exam_code: 'Z002',
    modules: {
      一元函数微分学: ['极限', '连续', '导数', '微分', '高阶导数', '洛必达法则', '单调性', '极值与最值', '凹凸性', '拐点', '渐近线'],
      一元函数积分学: ['原函数', '定积分', '变限积分', '牛顿-莱布尼茨公式', '换元积分', '分部积分', '几何应用', '物理应用'],
      多元函数微分学: ['偏导数', '全微分', '二阶偏导', '链导法则', '隐函数求导', '二元函数极值']
    }
  },
  逻辑推理: {
    exam_code: 'Z001',
    modules: {
      概念判断: ['概念种类', '概念关系', '定义', '划分'],
      论证: ['加强', '削弱', '解释', '谬误识别'],
      削弱加强: ['加强', '削弱'],
      推理规则: ['演绎推理', '归纳推理', '类比推理', '综合推理']
    }
  }
}

const importDefaults = reactive({
  subject: '英语运用',
  module: '语言知识',
  submodule: '语法',
  difficulty: 2
})

const steps = computed(() => [
  { index: '1', title: '上传图片', desc: `${imageItems.value.length} 张`, active: imageItems.value.length > 0 },
  { index: '2', title: '校对文本', desc: '粘贴 OCR', active: imageItems.value.some((item) => String(item.rawText || '').trim()) },
  { index: '3', title: '预览校验', desc: `${drafts.value.length} 题`, active: drafts.value.length > 0 },
  { index: '4', title: '进入审核', desc: '待发布', active: canCommit.value }
])

const subjectOptions = computed(() => Object.keys(importCatalog))
const subjectLabels = computed(() => subjectOptions.value)
const moduleOptions = computed(() => Object.keys(importCatalog[importDefaults.subject]?.modules || {}))
const moduleLabels = computed(() => moduleOptions.value)
const submoduleOptions = computed(() => importCatalog[importDefaults.subject]?.modules?.[importDefaults.module] || [])
const submoduleLabels = computed(() => submoduleOptions.value)
const difficultyLabels = ['1', '2', '3', '4', '5']
const selectedSubjectIndex = computed(() => optionIndex(subjectOptions.value, importDefaults.subject))
const selectedModuleIndex = computed(() => optionIndex(moduleOptions.value, importDefaults.module))
const selectedSubmoduleIndex = computed(() => optionIndex(submoduleOptions.value, importDefaults.submodule))
const selectedDifficultyIndex = computed(() => difficultyIndex(importDefaults.difficulty))
const canCommit = computed(() => (
  Boolean(dryRunResult.value) &&
  Number(dryRunResult.value.valid_count || 0) > 0 &&
  Number(dryRunResult.value.invalid_count || 0) === 0 &&
  Number(dryRunResult.value.duplicate_count || 0) === 0
))

onLoad(async () => {
  if (!isLoggedIn()) {
    uni.redirectTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/admin/question-image-import')}` })
    return
  }
  try {
    const me = await fetchAdminMe()
    allowed.value = Boolean(me?.is_admin)
    if (!allowed.value) {
      uni.showToast({ title: '无后台权限', icon: 'none' })
    }
  } catch (error) {
    allowed.value = false
    uni.showToast({ title: '权限验证失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})

function optionIndex(options, value) {
  const index = options.findIndex((item) => item === value)
  return index >= 0 ? index : 0
}

function difficultyIndex(value) {
  const index = difficultyLabels.findIndex((item) => Number(item) === Number(value))
  return index >= 0 ? index : 1
}

function syncDefaults() {
  const catalog = importCatalog[importDefaults.subject] || importCatalog['英语运用']
  importDefaults.subject = importCatalog[importDefaults.subject] ? importDefaults.subject : '英语运用'
  const modules = Object.keys(catalog.modules)
  if (!modules.includes(importDefaults.module)) {
    importDefaults.module = modules[0] || ''
  }
  const submodules = catalog.modules[importDefaults.module] || []
  if (!submodules.includes(importDefaults.submodule)) {
    importDefaults.submodule = submodules[0] || ''
  }
}

function handleSubjectChange(event) {
  importDefaults.subject = subjectOptions.value[Number(event?.detail?.value || 0)] || '英语运用'
  importDefaults.module = ''
  importDefaults.submodule = ''
  syncDefaults()
  markDryRunDirty()
}

function handleModuleChange(event) {
  importDefaults.module = moduleOptions.value[Number(event?.detail?.value || 0)] || ''
  importDefaults.submodule = ''
  syncDefaults()
  markDryRunDirty()
}

function handleSubmoduleChange(event) {
  importDefaults.submodule = submoduleOptions.value[Number(event?.detail?.value || 0)] || ''
  markDryRunDirty()
}

function handleDifficultyChange(event) {
  importDefaults.difficulty = Number(difficultyLabels[Number(event?.detail?.value || 1)] || 2)
  markDryRunDirty()
}

function chooseImages() {
  uni.chooseImage({
    count: 9,
    sizeType: ['compressed', 'original'],
    sourceType: ['album', 'camera'],
    success: (response) => {
      const paths = response.tempFilePaths || []
      const files = response.tempFiles || []
      const nextItems = paths.map((path, index) => ({
        id: `${Date.now()}-${index}-${Math.random().toString(16).slice(2)}`,
        path,
        name: files[index]?.name || imageNameFromPath(path, imageItems.value.length + index + 1),
        size: files[index]?.size || 0,
        rawText: '',
        status: '待粘贴文本'
      }))
      imageItems.value = [...imageItems.value, ...nextItems]
      markDryRunDirty()
    }
  })
}

function imageNameFromPath(path, index) {
  const name = String(path || '').split(/[\\/]/).filter(Boolean).pop()
  return name || `题目图片 ${index}`
}

function formatSize(size) {
  const bytes = Number(size || 0)
  if (!bytes) return '未知大小'
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function previewImage(item) {
  uni.previewImage({
    current: item.path,
    urls: imageItems.value.map((image) => image.path)
  })
}

function removeImage(id) {
  imageItems.value = imageItems.value.filter((item) => item.id !== id)
  drafts.value = drafts.value.filter((draft) => draft.image_id !== id)
  markDryRunDirty()
}

function parseSingleImage(item) {
  const rawText = String(item.rawText || '').trim()
  if (!rawText) {
    uni.showToast({ title: '请先粘贴识别文本', icon: 'none' })
    return
  }
  const draft = createDraftFromText(rawText, item)
  const existingIndex = drafts.value.findIndex((entry) => entry.image_id === item.id)
  if (existingIndex >= 0) {
    drafts.value.splice(existingIndex, 1, draft)
  } else {
    drafts.value = [...drafts.value, draft]
  }
  item.status = '已解析'
  markDryRunDirty()
}

function parseAllImages() {
  const targets = imageItems.value.filter((item) => String(item.rawText || '').trim())
  if (targets.length === 0) {
    uni.showToast({ title: '请先粘贴至少一张图片的识别文本', icon: 'none' })
    return
  }
  targets.forEach(parseSingleImage)
  uni.showToast({ title: `已解析 ${targets.length} 张图片`, icon: 'success' })
}

function addBlankDraft() {
  drafts.value = [...drafts.value, createDraftFromText('', null)]
  markDryRunDirty()
}

function createDraftFromText(rawText, image) {
  syncDefaults()
  const parsed = parseQuestionText(rawText)
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    image_id: image?.id || '',
    image_name: image?.name || '',
    image_index: image ? imageItems.value.findIndex((item) => item.id === image.id) : null,
    exam_code: importCatalog[importDefaults.subject]?.exam_code || 'COMMON',
    subject: importDefaults.subject,
    module: importDefaults.module,
    submodule: importDefaults.submodule,
    difficulty: importDefaults.difficulty,
    stem: parsed.stem,
    option_a: parsed.option_a,
    option_b: parsed.option_b,
    option_c: parsed.option_c,
    option_d: parsed.option_d,
    answer: parsed.answer,
    explanation: parsed.explanation,
    check: null
  }
}

function parseQuestionText(rawText) {
  const text = String(rawText || '').replace(/\r\n/g, '\n').trim()
  if (!text) {
    return emptyParsedQuestion()
  }
  const explanationMatch = text.match(/(?:答案解析|解析|解题思路)\s*[:：]\s*([\s\S]*)$/)
  const explanation = explanationMatch ? explanationMatch[1].trim() : ''
  const beforeExplanation = explanationMatch ? text.slice(0, explanationMatch.index).trim() : text
  const answerMatch = beforeExplanation.match(/(?:正确答案|答案)\s*[:：]?\s*([ABCD])/i) || text.match(/(?:正确答案|答案)\s*[:：]?\s*([ABCD])/i)
  const answer = answerOptions.includes(String(answerMatch?.[1] || '').toUpperCase())
    ? String(answerMatch[1]).toUpperCase()
    : 'A'
  const body = beforeExplanation
    .replace(/(?:正确答案|答案)\s*[:：]?\s*[ABCD].*$/im, '')
    .trim()

  const options = {}
  const optionRegex = /(?:^|\n)\s*([A-D])[\.\、:：]\s*([\s\S]*?)(?=(?:\n\s*[A-D][\.\、:：])|\n\s*(?:正确答案|答案|答案解析|解析|解题思路)\s*[:：]?|$)/gi
  let match
  while ((match = optionRegex.exec(body))) {
    options[match[1].toUpperCase()] = cleanOptionText(match[2])
  }
  const firstOptionIndex = body.search(/(?:^|\n)\s*A[\.\、:：]/i)
  const stem = cleanStem(firstOptionIndex >= 0 ? body.slice(0, firstOptionIndex) : body)

  return {
    stem,
    option_a: options.A || '',
    option_b: options.B || '',
    option_c: options.C || '',
    option_d: options.D || '',
    answer,
    explanation
  }
}

function emptyParsedQuestion() {
  return {
    stem: '',
    option_a: '',
    option_b: '',
    option_c: '',
    option_d: '',
    answer: 'A',
    explanation: ''
  }
}

function cleanStem(value) {
  return String(value || '')
    .replace(/^(题干|问题|题目)\s*[:：]/, '')
    .replace(/\n{2,}/g, '\n')
    .trim()
}

function cleanOptionText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim()
}

function getDraftCatalog(draft) {
  return importCatalog[draft.subject] || importCatalog['英语运用']
}

function draftModuleOptions(draft) {
  return Object.keys(getDraftCatalog(draft).modules || {})
}

function draftModuleLabels(draft) {
  return draftModuleOptions(draft)
}

function draftSubmoduleOptions(draft) {
  return getDraftCatalog(draft).modules?.[draft.module] || []
}

function draftSubmoduleLabels(draft) {
  return draftSubmoduleOptions(draft)
}

function draftSubjectIndex(draft) {
  return optionIndex(subjectOptions.value, draft.subject)
}

function draftModuleIndex(draft) {
  return optionIndex(draftModuleOptions(draft), draft.module)
}

function draftSubmoduleIndex(draft) {
  return optionIndex(draftSubmoduleOptions(draft), draft.submodule)
}

function handleDraftSubjectChange(draft, event) {
  draft.subject = subjectOptions.value[Number(event?.detail?.value || 0)] || '英语运用'
  const catalog = getDraftCatalog(draft)
  draft.exam_code = catalog.exam_code
  draft.module = Object.keys(catalog.modules)[0] || ''
  draft.submodule = catalog.modules[draft.module]?.[0] || ''
  markDryRunDirty()
}

function handleDraftModuleChange(draft, event) {
  draft.module = draftModuleOptions(draft)[Number(event?.detail?.value || 0)] || ''
  draft.submodule = draftSubmoduleOptions(draft)[0] || ''
  markDryRunDirty()
}

function handleDraftSubmoduleChange(draft, event) {
  draft.submodule = draftSubmoduleOptions(draft)[Number(event?.detail?.value || 0)] || ''
  markDryRunDirty()
}

function handleDraftDifficultyChange(draft, event) {
  draft.difficulty = Number(difficultyLabels[Number(event?.detail?.value || 1)] || 2)
  markDryRunDirty()
}

function setDraftAnswer(draft, answer) {
  draft.answer = answer
  markDryRunDirty()
}

function draftOptionValue(draft, option) {
  return draft[`option_${String(option).toLowerCase()}`] || ''
}

function handleDraftOptionInput(draft, option, event) {
  draft[`option_${String(option).toLowerCase()}`] = event?.detail?.value || ''
  markDryRunDirty()
}

function applyDefaultsToDrafts() {
  syncDefaults()
  drafts.value = drafts.value.map((draft) => ({
    ...draft,
    exam_code: importCatalog[importDefaults.subject]?.exam_code || 'COMMON',
    subject: importDefaults.subject,
    module: importDefaults.module,
    submodule: importDefaults.submodule,
    difficulty: importDefaults.difficulty
  }))
  markDryRunDirty()
  uni.showToast({ title: '已应用默认分类', icon: 'success' })
}

function duplicateDraft(draft) {
  drafts.value = [
    ...drafts.value,
    {
      ...draft,
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      image_name: `${draft.image_name || '手动新增'} 副本`,
      check: null
    }
  ]
  markDryRunDirty()
}

function removeDraft(id) {
  drafts.value = drafts.value.filter((draft) => draft.id !== id)
  markDryRunDirty()
}

function draftErrors(draft, index) {
  const errors = []
  const required = [
    ['subject', '科目'],
    ['module', '模块'],
    ['submodule', '考点'],
    ['stem', '题干'],
    ['option_a', 'A 选项'],
    ['option_b', 'B 选项'],
    ['option_c', 'C 选项'],
    ['option_d', 'D 选项']
  ]
  required.forEach(([field, label]) => {
    if (!String(draft[field] || '').trim()) {
      errors.push(`${label}不能为空`)
    }
  })
  if (!answerOptions.includes(draft.answer)) errors.push('答案必须为 A-D')
  if (Number(draft.difficulty) < 1 || Number(draft.difficulty) > 5) errors.push('难度必须为 1-5')
  const serverErrors = dryRunResult.value?.items?.find((item) => item.index === index)?.errors || []
  return [...errors, ...serverErrors]
}

function draftTone(draft, index) {
  const errors = draftErrors(draft, index)
  if (errors.length) return 'invalid'
  const check = dryRunResult.value?.items?.find((item) => item.index === index)
  return check?.valid ? 'valid' : ''
}

function draftStatusText(draft, index) {
  const errors = draftErrors(draft, index)
  if (errors.length) return '需修正'
  const check = dryRunResult.value?.items?.find((item) => item.index === index)
  return check?.valid ? '可导入' : '待校验'
}

function buildImportPayload() {
  return {
    questions: drafts.value.map((draft, index) => {
      const catalog = getDraftCatalog(draft)
      return {
        exam_code: catalog.exam_code || draft.exam_code || 'COMMON',
        subject: draft.subject,
        module: draft.module,
        submodule: draft.submodule,
        question_type: 'single_choice',
        stem: draft.stem,
        option_a: draft.option_a,
        option_b: draft.option_b,
        option_c: draft.option_c,
        option_d: draft.option_d,
        answer: draft.answer,
        explanation: draft.explanation,
        difficulty: Number(draft.difficulty || 2),
        source_type: 'source_extracted',
        source_year: null,
        image_name: draft.image_name || null,
        image_index: draft.image_index ?? index
      }
    })
  }
}

function markDryRunDirty() {
  dryRunResult.value = null
}

async function runDryCheck() {
  if (drafts.value.length === 0) {
    uni.showToast({ title: '请先解析或新增题目', icon: 'none' })
    return
  }
  const localInvalidCount = drafts.value.filter((draft, index) => draftErrors(draft, index).length > 0).length
  if (localInvalidCount > 0 && !dryRunResult.value) {
    uni.showToast({ title: '请先补全草稿必填项', icon: 'none' })
    return
  }
  dryRunLoading.value = true
  try {
    const response = await dryRunAdminQuestionImageImport(buildImportPayload())
    dryRunResult.value = response
    if (response.invalid_count || response.duplicate_count) {
      uni.showToast({ title: '校验发现问题，请逐题修正', icon: 'none' })
      return
    }
    uni.showToast({ title: `校验通过 ${response.valid_count} 题`, icon: 'success' })
  } catch (error) {
    uni.showToast({ title: 'dry-run 校验失败', icon: 'none' })
  } finally {
    dryRunLoading.value = false
  }
}

async function commitImport() {
  if (!canCommit.value) {
    uni.showToast({ title: '请先通过 dry-run 校验', icon: 'none' })
    return
  }
  const confirmed = await new Promise((resolve) => {
    uni.showModal({
      title: '确认导入待审核？',
      content: `将 ${dryRunResult.value.valid_count} 道题写入题库，并保持下架状态进入审核队列。`,
      confirmText: '导入',
      confirmColor: '#1769ff',
      success: (result) => resolve(Boolean(result.confirm)),
      fail: () => resolve(false)
    })
  })
  if (!confirmed) return

  importSaving.value = true
  try {
    const response = await commitAdminQuestionImageImport(buildImportPayload())
    uni.showToast({ title: `已导入 ${response.inserted_count || 0} 题`, icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/admin/index?tab=questions' })
    }, 500)
  } catch (error) {
    const dryRun = error?.detail?.dry_run
    if (dryRun) {
      dryRunResult.value = dryRun
    }
    uni.showToast({ title: '导入失败，请重新校验', icon: 'none' })
  } finally {
    importSaving.value = false
  }
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.redirectTo({ url: '/pages/admin/index?tab=questions' })
    }
  })
}
</script>

<style scoped>
.image-import-page {
  min-height: 100vh;
  padding: 24rpx 24rpx calc(env(safe-area-inset-bottom) + 190rpx);
  box-sizing: border-box;
  background:
    radial-gradient(circle at 12% 0%, rgba(186, 226, 255, 0.68) 0, rgba(186, 226, 255, 0) 300rpx),
    radial-gradient(circle at 92% 4%, rgba(205, 249, 216, 0.74) 0, rgba(205, 249, 216, 0) 320rpx),
    linear-gradient(180deg, #f7fbff 0%, #ffffff 46%, #f7fbff 100%);
}

.import-hero {
  position: relative;
  min-height: 112rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 96rpx 18rpx;
  box-sizing: border-box;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 50%;
  width: 72rpx;
  height: 72rpx;
  padding: 0;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 22rpx;
  background: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(15, 23, 42, 0.08);
}

.back-btn::after,
.mini-btn::after,
.primary-mini-btn::after,
.remove-btn::after,
.line-btn::after,
.outline-action::after,
.filled-action::after,
.answer-dot::after,
.danger-line-btn::after,
.bottom-btn::after {
  border: 0;
}

.back-icon {
  width: 30rpx;
  height: 30rpx;
}

.hero-copy {
  text-align: center;
}

.hero-title {
  font-size: 48rpx;
  line-height: 1.15;
  font-weight: 800;
  color: #0f172a;
}

.hero-subtitle {
  margin-top: 10rpx;
  font-size: 24rpx;
  color: #6b7280;
}

.screen-state {
  margin-top: 160rpx;
  text-align: center;
  font-size: 28rpx;
  color: #64748b;
}

.import-content {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.step-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14rpx;
}

.step-item {
  min-height: 108rpx;
  padding: 16rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
  border: 1rpx solid rgba(148, 163, 184, 0.22);
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.76);
  box-sizing: border-box;
}

.step-item.active {
  border-color: rgba(37, 99, 235, 0.48);
  background: #ffffff;
  box-shadow: 0 12rpx 28rpx rgba(37, 99, 235, 0.08);
}

.step-index {
  flex: 0 0 38rpx;
  width: 38rpx;
  height: 38rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #eef4ff;
  color: #2563eb;
  font-size: 22rpx;
  font-weight: 800;
}

.step-title {
  font-size: 22rpx;
  font-weight: 800;
  color: #0f172a;
  white-space: nowrap;
}

.step-desc {
  margin-top: 4rpx;
  font-size: 18rpx;
  color: #8b95a7;
  white-space: nowrap;
}

.import-panel {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 18rpx 50rpx rgba(15, 23, 42, 0.07);
  box-sizing: border-box;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 22rpx;
}

.panel-title {
  font-size: 30rpx;
  font-weight: 800;
  color: #0f172a;
}

.panel-subtitle {
  margin-top: 6rpx;
  font-size: 22rpx;
  line-height: 1.45;
  color: #64748b;
}

.mini-btn,
.primary-mini-btn,
.remove-btn {
  min-width: 130rpx;
  height: 64rpx;
  padding: 0 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18rpx;
  font-size: 24rpx;
  font-weight: 700;
  box-sizing: border-box;
}

.mini-btn,
.remove-btn {
  border: 1rpx solid #dbe3ef;
  color: #475569;
  background: #ffffff;
}

.primary-mini-btn {
  color: #ffffff;
  border: 0;
  background: linear-gradient(135deg, #1769ff, #0ea5a8);
}

.picker-grid,
.draft-picker-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.picker-pill,
.draft-picker {
  min-height: 74rpx;
  padding: 0 22rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  border: 1rpx solid #dbe3ef;
  border-radius: 18rpx;
  background: #ffffff;
  color: #263449;
  font-size: 26rpx;
  font-weight: 700;
  box-sizing: border-box;
}

.upload-empty {
  min-height: 250rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2rpx dashed #b8c6da;
  border-radius: 22rpx;
  background: #f8fbff;
  text-align: center;
  box-sizing: border-box;
}

.upload-icon {
  width: 76rpx;
  height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 22rpx;
  color: #1769ff;
  background: #eaf2ff;
  font-size: 46rpx;
  font-weight: 700;
}

.upload-title {
  margin-top: 18rpx;
  font-size: 28rpx;
  font-weight: 800;
  color: #0f172a;
}

.upload-desc {
  width: 86%;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.5;
  color: #64748b;
}

.image-list,
.draft-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.image-row {
  display: flex;
  gap: 18rpx;
  padding: 18rpx;
  border: 1rpx solid #e2e8f0;
  border-radius: 22rpx;
  background: #fbfdff;
}

.thumb {
  flex: 0 0 150rpx;
  width: 150rpx;
  height: 180rpx;
  border-radius: 16rpx;
  background: #eef2f7;
}

.image-main {
  flex: 1;
  min-width: 0;
}

.image-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.image-name {
  max-width: 320rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 26rpx;
  font-weight: 800;
  color: #0f172a;
}

.image-meta,
.image-status,
.draft-source {
  margin-top: 4rpx;
  font-size: 21rpx;
  color: #8b95a7;
}

.ocr-textarea {
  width: 100%;
  min-height: 170rpx;
  margin-top: 14rpx;
  padding: 18rpx;
  border: 1rpx solid #dbe3ef;
  border-radius: 18rpx;
  background: #ffffff;
  font-size: 24rpx;
  line-height: 1.45;
  color: #0f172a;
  box-sizing: border-box;
}

.image-actions,
.draft-actions,
.wide-actions {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 16rpx;
}

.wide-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.line-btn,
.danger-line-btn,
.outline-action,
.filled-action {
  height: 70rpx;
  padding: 0 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18rpx;
  font-size: 25rpx;
  font-weight: 800;
  box-sizing: border-box;
}

.line-btn,
.outline-action {
  border: 1rpx solid #1769ff;
  color: #1769ff;
  background: #ffffff;
}

.danger-line-btn {
  border: 1rpx solid #fecaca;
  color: #dc2626;
  background: #fff7f7;
}

.filled-action {
  color: #ffffff;
  border: 0;
  background: linear-gradient(135deg, #1769ff, #0ea5a8);
}

.count-badge {
  min-width: 88rpx;
  height: 54rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18rpx;
  background: #eef4ff;
  color: #1769ff;
  font-size: 24rpx;
  font-weight: 800;
}

.draft-empty {
  padding: 70rpx 0;
  text-align: center;
  color: #8b95a7;
  font-size: 25rpx;
}

.draft-card {
  padding: 22rpx;
  border: 1rpx solid #e2e8f0;
  border-radius: 22rpx;
  background: #ffffff;
}

.draft-card.valid {
  border-color: rgba(22, 163, 74, 0.42);
}

.draft-card.invalid {
  border-color: rgba(249, 115, 22, 0.52);
  background: #fffaf5;
}

.draft-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 18rpx;
}

.draft-title {
  font-size: 28rpx;
  font-weight: 800;
  color: #0f172a;
}

.draft-status {
  min-width: 100rpx;
  height: 52rpx;
  padding: 0 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  background: #f1f5f9;
  color: #64748b;
  font-size: 22rpx;
  font-weight: 800;
}

.draft-card.valid .draft-status {
  color: #16a34a;
  background: #dcfce7;
}

.draft-card.invalid .draft-status {
  color: #f97316;
  background: #fff3e6;
}

.draft-picker-grid {
  margin-bottom: 16rpx;
}

.draft-picker {
  min-height: 66rpx;
  font-size: 23rpx;
}

.draft-textarea {
  width: 100%;
  padding: 18rpx;
  border: 1rpx solid #dbe3ef;
  border-radius: 18rpx;
  background: #fbfdff;
  font-size: 25rpx;
  line-height: 1.5;
  color: #0f172a;
  box-sizing: border-box;
}

.draft-textarea.stem {
  min-height: 150rpx;
  margin-bottom: 14rpx;
}

.draft-textarea.explanation {
  min-height: 132rpx;
  margin-top: 14rpx;
}

.option-editor {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.option-row {
  min-height: 70rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 0 16rpx;
  border: 1rpx solid #e2e8f0;
  border-radius: 18rpx;
  background: #ffffff;
  box-sizing: border-box;
}

.option-row.selected {
  border-color: #1769ff;
  background: #f5f9ff;
}

.answer-dot {
  width: 48rpx;
  height: 48rpx;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  color: #1769ff;
  background: transparent;
  font-size: 25rpx;
}

.option-label {
  width: 42rpx;
  color: #0f172a;
  font-size: 25rpx;
  font-weight: 800;
}

.option-input {
  flex: 1;
  min-width: 0;
  height: 68rpx;
  font-size: 25rpx;
  color: #0f172a;
}

.error-list {
  margin-top: 16rpx;
  padding: 16rpx;
  border-radius: 16rpx;
  background: #fff7ed;
}

.error-item {
  font-size: 22rpx;
  line-height: 1.45;
  color: #c2410c;
}

.import-bottom-bar {
  position: fixed;
  left: 24rpx;
  right: 24rpx;
  bottom: calc(env(safe-area-inset-bottom) + 20rpx);
  z-index: 20;
  min-height: 112rpx;
  padding: 16rpx;
  display: grid;
  grid-template-columns: 1fr 1.1fr 1.1fr;
  align-items: center;
  gap: 14rpx;
  border: 1rpx solid rgba(226, 232, 240, 0.92);
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 20rpx 60rpx rgba(15, 23, 42, 0.14);
  box-sizing: border-box;
}

.bottom-summary {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  color: #475569;
  font-size: 21rpx;
  font-weight: 700;
}

.bottom-btn {
  height: 78rpx;
  padding: 0 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20rpx;
  font-size: 25rpx;
  font-weight: 800;
  box-sizing: border-box;
}

.bottom-btn.outline {
  border: 1rpx solid #1769ff;
  color: #1769ff;
  background: #ffffff;
}

.bottom-btn.primary {
  border: 0;
  color: #ffffff;
  background: linear-gradient(135deg, #1769ff, #0ea5a8);
}

.bottom-btn[disabled] {
  opacity: 0.48;
}
</style>
