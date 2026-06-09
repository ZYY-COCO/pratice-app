<template>
  <view class="image-import-page" :style="themeInlineStyle">
    <view class="import-hero">
      <button class="back-btn" @tap="goBack">
        <image class="back-icon" src="/static/ui-icons/back.svg" mode="aspectFit" />
      </button>
      <view class="hero-copy">
        <view class="hero-title">批量导入</view>
        <view class="hero-subtitle">上传文件，识别并校对题目内容</view>
      </view>
      <button class="history-btn" @tap="showImportHistory">
        <text class="history-icon">◷</text>
        <text>导入记录</text>
      </button>
    </view>

    <view v-if="loading" class="screen-state">正在验证后台权限...</view>
    <view v-else-if="!allowed" class="screen-state">当前账号无后台权限</view>

    <view v-else-if="!editorVisible" class="landing-content">
      <view class="file-drop-zone" @tap="chooseImportFiles" @dragover.prevent @drop.prevent="handleDropFiles">
        <view class="file-upload-illustration">
          <view class="file-shape">
            <view class="file-fold"></view>
            <text class="file-arrow">↑</text>
          </view>
          <view class="file-plus">＋</view>
        </view>
        <view class="drop-title">拖拽文件到这里</view>
        <view class="drop-action">或点击选择文件</view>
        <view class="drop-formats">支持图片、JSON、CSV、TXT、XLSX、DOCX、PDF</view>
        <view class="drop-limit">单个文件不超过 20MB</view>
      </view>

      <view v-if="imageItems.length" class="selected-file-list">
        <view v-for="item in imageItems" :key="item.id" class="selected-file-card">
          <view class="file-type-icon" :class="fileTypeTone(item)">
            <text>{{ fileTypeLabel(item) }}</text>
          </view>
          <view class="selected-file-main">
            <view class="selected-file-name">{{ item.name }}</view>
            <view class="selected-file-meta">
              <text>{{ formatSize(item.size) }}</text>
              <text class="ready-status">● {{ fileReadyText(item) }}</text>
            </view>
          </view>
          <button class="file-delete-btn" @tap.stop="removeImage(item.id)">⌫</button>
        </view>
      </view>

      <view class="recognition-card">
        <view class="landing-section-title">识别内容</view>
        <view class="recognition-tags">
          <view class="recognition-tag blue">题干与选项</view>
          <view class="recognition-tag green">正确答案</view>
          <view class="recognition-tag purple">解析与分类</view>
        </view>
        <view class="recognition-copy">识别完成后，题目将进入预览确认页面，不会直接发布。</view>
      </view>

      <view class="flow-card">
        <view class="flow-row">
          <view v-for="(step, index) in landingSteps" :key="step.title" class="flow-step">
            <view class="flow-number">{{ index + 1 }}</view>
            <view class="flow-icon">
              <image class="flow-icon-image" :src="step.iconSrc || ''" mode="aspectFit" />
            </view>
            <view class="flow-title">{{ step.title }}</view>
            <view v-if="index < landingSteps.length - 1" class="flow-arrow">→</view>
          </view>
        </view>
        <view class="flow-note">ⓘ 不会直接发布或进入数据库，请先预览确认后再提交审核。</view>
      </view>
    </view>

    <view v-else class="import-content">
      <view class="editor-toolbar">
        <button class="editor-back-btn" @tap="returnToFileSelection">重新选择文件</button>
        <view class="editor-progress">
          <text>{{ imageItems.length }} 个文件</text>
          <text>{{ drafts.length }} 道草稿</text>
        </view>
      </view>

      <view class="import-panel">
        <view class="panel-head">
          <view>
            <view class="panel-title">默认分类</view>
            <view class="panel-subtitle">识别出的题目会先套用这里的分类，之后可逐题修改。</view>
          </view>
          <button class="mini-btn" @tap="applyDefaultsToDrafts">应用全部</button>
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
            <view class="panel-title">文件与识别文本</view>
            <view class="panel-subtitle">自动提取文件内容；识别失败时可手动粘贴 OCR / 导出文本。</view>
          </view>
          <button class="primary-mini-btn" @tap="chooseImportFiles">添加文件</button>
        </view>

        <view v-if="imageItems.length === 0" class="upload-empty" @tap="chooseImportFiles">
          <view class="upload-icon">＋</view>
          <view class="upload-title">添加题目文件</view>
          <view class="upload-desc">支持多选，识别完成后仍需校对题目内容。</view>
        </view>

        <view v-else class="image-list">
          <view v-for="(item, index) in imageItems" :key="item.id" class="image-row">
            <image v-if="isImageItem(item)" class="thumb" :src="item.path" mode="aspectFill" @tap="previewImage(item)" />
            <view v-else class="thumb file-thumb" :class="fileTypeTone(item)">{{ fileTypeLabel(item) }}</view>
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
                placeholder="粘贴识别文本。单题格式：题干...&#10;A. ...&#10;B. ...&#10;C. ...&#10;D. ...&#10;答案：B&#10;解析：...&#10;&#10;多题可用 1. / 题目1 / --- 分隔。"
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

    <view v-if="allowed && !editorVisible" class="recognize-bottom-bar">
      <button class="recognize-btn" :disabled="imageItems.length === 0 || recognizingCount > 0" @tap="startRecognition">
        <text class="recognize-icon">⌁</text>
        <text>{{ recognizingCount > 0 ? `自动识别中 ${recognizingCount}` : '开始识别' }}</text>
      </button>
      <view class="recognize-hint">{{ recognizingCount > 0 ? '正在提取文件内容，请稍候' : (imageItems.length ? `已完成文件处理，可预览 ${drafts.length} 道草稿` : '请选择文件后自动识别') }}</view>
    </view>

    <view v-if="allowed && editorVisible" class="import-bottom-bar">
      <view class="bottom-summary">
        <text>草稿 {{ drafts.length }}</text>
        <text>有效 {{ dryRunResult?.valid_count || 0 }}</text>
        <text>问题 {{ (dryRunResult?.invalid_count || 0) + (dryRunResult?.duplicate_count || 0) }}</text>
      </view>
      <view class="bottom-actions">
        <button class="bottom-btn outline" :disabled="dryRunLoading || importSaving || drafts.length === 0" @tap="runDryCheck">
          {{ dryRunLoading ? '校验中' : 'Dry-run 校验' }}
        </button>
        <button class="bottom-btn primary" :disabled="!canCommit || importSaving" @tap="commitImport">
          {{ importSaving ? '导入中' : '导入待审核' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  commitAdminQuestionImageImport,
  dryRunAdminQuestionImageImport,
  fetchAdminMe,
  recognizeAdminQuestionImportFile
} from '../../api/admin'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const loading = ref(true)
const allowed = ref(false)
const editorVisible = ref(false)
const imageItems = ref([])
const drafts = ref([])
const dryRunResult = ref(null)
const dryRunLoading = ref(false)
const importSaving = ref(false)
const answerOptions = ['A', 'B', 'C', 'D']
const IMPORT_HISTORY_KEY = 'adminQuestionImportHistory'
const landingSteps = [
  { icon: '▱', title: '选择文件' },
  { icon: '⌗', title: '开始识别' },
  { icon: '▤', title: '预览确认' },
  { icon: '✓', title: '进入待审核' }
]

const landingStepIconPaths = [
  '/static/admin-icons/import-select-file.svg',
  '/static/admin-icons/import-scan.svg',
  '/static/admin-icons/import-preview.svg',
  '/static/admin-icons/import-safe.svg'
]
landingSteps.forEach((step, index) => {
  step.iconSrc = landingStepIconPaths[index]
})

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
const recognizingCount = computed(() => imageItems.value.filter((item) => item.recognizing).length)
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

function chooseImportFiles() {
  if (typeof uni.chooseFile === 'function') {
    uni.chooseFile({
      count: 9,
      extension: ['png', 'jpg', 'jpeg', 'webp', 'json', 'csv', 'txt', 'xlsx', 'docx', 'pdf'],
      success: appendSelectedFiles
    })
    return
  }
  if (typeof uni.chooseMessageFile === 'function') {
    uni.chooseMessageFile({
      count: 9,
      type: 'file',
      extension: ['png', 'jpg', 'jpeg', 'webp', 'json', 'csv', 'txt', 'xlsx', 'docx', 'pdf'],
      success: appendSelectedFiles
    })
    return
  }
  chooseImages()
}

function chooseImages() {
  uni.chooseImage({
    count: 9,
    sizeType: ['compressed', 'original'],
    sourceType: ['album', 'camera'],
    success: appendSelectedFiles
  })
}

function appendSelectedFiles(response) {
  const paths = response.tempFilePaths || []
  const files = response.tempFiles || response.tempFilePaths?.map((path) => ({ path })) || []
  const nextItems = files.map((file, index) => {
    const path = file.path || paths[index] || ''
    const name = file.name || imageNameFromPath(path, imageItems.value.length + index + 1)
    const extension = fileExtension(name)
    return {
      id: `${Date.now()}-${index}-${Math.random().toString(16).slice(2)}`,
      path,
      file: file.file || null,
      name,
      extension,
      size: file.size || 0,
      rawText: '',
      recognizing: false,
      recognitionError: '',
      recognitionProvider: '',
      status: isReadableTextExtension(extension) ? '正在读取' : '文件已就绪'
    }
  })
  imageItems.value = [...imageItems.value, ...nextItems]
  nextItems.forEach(recognizeImportItem)
  markDryRunDirty()
}

function handleDropFiles(event) {
  const files = Array.from(event?.dataTransfer?.files || [])
  if (!files.length) return
  appendNativeFiles(files.slice(0, 9))
}

function appendNativeFiles(files) {
  const nextItems = files.map((file, index) => {
    const name = file.name || `导入文件 ${imageItems.value.length + index + 1}`
    const extension = fileExtension(name)
    return {
      id: `${Date.now()}-${index}-${Math.random().toString(16).slice(2)}`,
      path: '',
      file,
      name,
      extension,
      size: file.size || 0,
      rawText: '',
      recognizing: false,
      recognitionError: '',
      recognitionProvider: '',
      status: isReadableTextExtension(extension) ? '正在读取' : '文件已就绪'
    }
  })
  imageItems.value = [...imageItems.value, ...nextItems]
  nextItems.forEach(recognizeImportItem)
  markDryRunDirty()
}

function fileExtension(name) {
  return String(name || '').split('.').pop()?.toLowerCase() || ''
}

function isReadableTextExtension(extension) {
  return ['json', 'csv', 'txt'].includes(String(extension || '').toLowerCase())
}

function isImageItem(item) {
  return ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'].includes(item?.extension || fileExtension(item?.name))
}

function fileTypeLabel(item) {
  const extension = String(item?.extension || fileExtension(item?.name) || 'FILE').toUpperCase()
  if (['JPG', 'JPEG', 'PNG', 'WEBP'].includes(extension)) return 'IMG'
  return extension.slice(0, 4)
}

function fileTypeTone(item) {
  const extension = String(item?.extension || fileExtension(item?.name)).toLowerCase()
  if (['xlsx', 'csv'].includes(extension)) return 'sheet'
  if (['json', 'txt'].includes(extension)) return 'data'
  if (['pdf', 'docx'].includes(extension)) return 'document'
  return 'image'
}

function fileReadyText(item) {
  if (item?.recognizing) return '识别中...'
  if (item?.recognitionError) return `识别失败：${item.recognitionError}`
  if (String(item?.rawText || '').trim()) return '内容已读取'
  if (isReadableTextExtension(item?.extension)) return item?.status || '等待读取'
  return '文件已就绪'
}

async function recognizeImportItem(item) {
  if (!item?.file && !item?.path) {
    item.status = '缺少文件'
    item.recognitionError = '无法读取上传文件'
    return
  }

  item.recognizing = true
  item.recognitionError = ''
  item.status = '识别中'
  markDryRunDirty()

  try {
    const result = await recognizeAdminQuestionImportFile({
      file: item.file || null,
      filePath: item.path || '',
      fileName: item.name || 'upload'
    })
    if (!imageItems.value.some((current) => current.id === item.id)) return
    item.rawText = result?.text || ''
    item.recognitionProvider = result?.provider || ''
    const parsedCount = item.rawText.trim() ? parseImageItem(item) : 0
    item.status = parsedCount ? `已识别 ${parsedCount} 题` : '未识别到文本'
    if (result?.warnings?.length) {
      item.recognitionError = result.warnings[0]
    }
  } catch (error) {
    if (!imageItems.value.some((current) => current.id === item.id)) return
    item.status = '识别失败'
    item.recognitionError = errorDetail(error)
    if (isReadableTextExtension(item.extension)) {
      hydrateReadableFile(item)
    }
  } finally {
    item.recognizing = false
    markDryRunDirty()
  }
}

function errorDetail(error) {
  const detail = error?.detail || error?.message || error
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || item).join('；')
  }
  if (detail && typeof detail === 'object') {
    return detail.message || JSON.stringify(detail)
  }
  return String(detail || '识别失败')
}

function hydrateReadableFile(item) {
  if (!isReadableTextExtension(item.extension)) return
  if (item.file && typeof FileReader !== 'undefined') {
    const reader = new FileReader()
    reader.onload = () => {
      item.rawText = String(reader.result || '')
      item.status = '内容已读取'
    }
    reader.onerror = () => {
      item.status = '读取失败'
    }
    reader.readAsText(item.file, 'utf-8')
    return
  }
  try {
    const fileSystem = uni.getFileSystemManager?.()
    if (!fileSystem || !item.path) {
      item.status = '需粘贴文本'
      return
    }
    fileSystem.readFile({
      filePath: item.path,
      encoding: 'utf8',
      success: (result) => {
        item.rawText = String(result.data || '')
        item.status = '内容已读取'
      },
      fail: () => {
        item.status = '需粘贴文本'
      }
    })
  } catch (error) {
    item.status = '需粘贴文本'
  }
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

function startRecognition() {
  if (!imageItems.value.length) {
    uni.showToast({ title: '请先选择文件', icon: 'none' })
    return
  }
  const recognizingCount = imageItems.value.filter((item) => item.recognizing).length
  if (recognizingCount) {
    uni.showToast({ title: `还有 ${recognizingCount} 个文件正在识别`, icon: 'none' })
    return
  }
  const readableItems = imageItems.value.filter((item) => String(item.rawText || '').trim())
  if (readableItems.length) {
    const total = readableItems.reduce((sum, item) => sum + parseImageItem(item), 0)
    uni.showToast({ title: `已识别 ${total} 题，请预览确认`, icon: 'success' })
  } else {
    uni.showToast({ title: '未识别到题目，可进入下一步手动粘贴文本', icon: 'none' })
  }
  editorVisible.value = true
  markDryRunDirty()
}

function returnToFileSelection() {
  editorVisible.value = false
}

function showImportHistory() {
  const history = uni.getStorageSync(IMPORT_HISTORY_KEY) || []
  const content = Array.isArray(history) && history.length
    ? history.slice(0, 8).map((item) => `${item.created_at} · ${item.count} 题`).join('\n')
    : '暂无导入记录'
  uni.showModal({
    title: '导入记录',
    content,
    showCancel: false,
    confirmText: '关闭'
  })
}

function parseSingleImage(item) {
  const rawText = String(item.rawText || '').trim()
  if (!rawText) {
    uni.showToast({ title: '请先粘贴识别文本', icon: 'none' })
    return
  }
  const count = parseImageItem(item)
  markDryRunDirty()
  uni.showToast({ title: `已解析 ${count} 题`, icon: 'success' })
}

function parseAllImages() {
  const targets = imageItems.value.filter((item) => String(item.rawText || '').trim())
  if (targets.length === 0) {
    uni.showToast({ title: '请先粘贴至少一张图片的识别文本', icon: 'none' })
    return
  }
  const total = targets.reduce((sum, item) => sum + parseImageItem(item), 0)
  markDryRunDirty()
  uni.showToast({ title: `已解析 ${total} 题`, icon: 'success' })
}

function addBlankDraft() {
  drafts.value = [...drafts.value, createDraftFromText('', null)]
  markDryRunDirty()
}

function parseImageItem(item) {
  const nextDrafts = createDraftsFromText(item.rawText, item)
  drafts.value = [
    ...drafts.value.filter((entry) => entry.image_id !== item.id),
    ...nextDrafts
  ]
  item.status = `已解析 ${nextDrafts.length} 题`
  return nextDrafts.length
}

function createDraftsFromText(rawText, image) {
  const structuredQuestions = parseStructuredQuestions(rawText, image?.extension)
  if (structuredQuestions.length) {
    return structuredQuestions.map((question, index) => (
      createDraftFromQuestionObject(question, image, index, structuredQuestions.length)
    ))
  }
  const blocks = splitQuestionBlocks(rawText)
  return blocks.map((block, index) => createDraftFromText(block, image, index, blocks.length))
}

function parseStructuredQuestions(rawText, extension) {
  const text = String(rawText || '').trim()
  if (!text) return []
  if (extension === 'json' || text.startsWith('[') || text.startsWith('{')) {
    try {
      const parsed = JSON.parse(text)
      const questions = Array.isArray(parsed) ? parsed : parsed?.questions
      if (Array.isArray(questions)) return questions.filter((item) => item && typeof item === 'object')
    } catch (error) {
      return []
    }
  }
  if (extension === 'csv') {
    return parseCsvQuestions(text)
  }
  return []
}

function parseCsvQuestions(text) {
  const rows = String(text || '').split(/\r?\n/).filter((row) => row.trim())
  if (rows.length < 2) return []
  const headers = splitCsvRow(rows[0]).map((header) => header.trim().toLowerCase())
  const knownFields = ['stem', 'question', '题干', 'option_a', 'a', '选项a', 'answer', '答案']
  if (!headers.some((header) => knownFields.includes(header))) return []
  return rows.slice(1).map((row) => {
    const values = splitCsvRow(row)
    return headers.reduce((result, header, index) => {
      result[header] = values[index] || ''
      return result
    }, {})
  })
}

function splitCsvRow(row) {
  const values = []
  let current = ''
  let quoted = false
  for (let index = 0; index < row.length; index += 1) {
    const char = row[index]
    if (char === '"') {
      if (quoted && row[index + 1] === '"') {
        current += '"'
        index += 1
      } else {
        quoted = !quoted
      }
    } else if (char === ',' && !quoted) {
      values.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  values.push(current.trim())
  return values
}

function structuredValue(question, fields, fallback = '') {
  for (const field of fields) {
    if (question?.[field] !== undefined && question?.[field] !== null) {
      return question[field]
    }
  }
  return fallback
}

function createDraftFromQuestionObject(question, image, blockIndex = 0, blockCount = 1) {
  syncDefaults()
  const options = question?.options || {}
  const imageIndex = image ? imageItems.value.findIndex((item) => item.id === image.id) : null
  const imageName = image?.name
    ? (blockCount > 1 ? `${image.name} #${blockIndex + 1}` : image.name)
    : ''
  const subject = String(structuredValue(question, ['subject', '科目'], importDefaults.subject))
  const catalog = importCatalog[subject] || importCatalog[importDefaults.subject]
  const module = String(structuredValue(question, ['module', '模块'], importDefaults.module))
  const submodule = String(structuredValue(question, ['submodule', '考点', '分类'], importDefaults.submodule))
  return {
    id: `${Date.now()}-${blockIndex}-${Math.random().toString(16).slice(2)}`,
    image_id: image?.id || '',
    image_name: imageName,
    image_index: imageIndex,
    exam_code: String(structuredValue(question, ['exam_code', '考试代码'], catalog?.exam_code || 'COMMON')),
    subject,
    module,
    submodule,
    difficulty: Number(structuredValue(question, ['difficulty', '难度'], importDefaults.difficulty)) || 2,
    stem: String(structuredValue(question, ['stem', 'question', '题干'], '')),
    option_a: String(structuredValue(question, ['option_a', 'a', 'A', '选项a', '选项A'], options.A || options.a || '')),
    option_b: String(structuredValue(question, ['option_b', 'b', 'B', '选项b', '选项B'], options.B || options.b || '')),
    option_c: String(structuredValue(question, ['option_c', 'c', 'C', '选项c', '选项C'], options.C || options.c || '')),
    option_d: String(structuredValue(question, ['option_d', 'd', 'D', '选项d', '选项D'], options.D || options.d || '')),
    answer: String(structuredValue(question, ['answer', 'correct_answer', '答案'], 'A')).toUpperCase(),
    explanation: String(structuredValue(question, ['explanation', 'analysis', '解析'], '')),
    check: null
  }
}

function createDraftFromText(rawText, image, blockIndex = 0, blockCount = 1) {
  syncDefaults()
  const parsed = parseQuestionText(rawText)
  const imageIndex = image ? imageItems.value.findIndex((item) => item.id === image.id) : null
  const imageName = image?.name
    ? (blockCount > 1 ? `${image.name} #${blockIndex + 1}` : image.name)
    : ''
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    image_id: image?.id || '',
    image_name: imageName,
    image_index: imageIndex,
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

function splitQuestionBlocks(rawText) {
  const text = String(rawText || '').replace(/\r\n/g, '\n').trim()
  if (!text) return ['']

  const separatorBlocks = text
    .split(/\n\s*(?:-{3,}|={3,}|#{3,}|题目分隔)\s*\n/g)
    .map((block) => block.trim())
    .filter(Boolean)
  if (separatorBlocks.length > 1 && separatorBlocks.filter(hasQuestionShape).length >= 2) {
    return separatorBlocks
  }

  const markerRegex = /(?:^|\n)\s*(?:(?:第\s*)?\d+\s*[题、.．:：)]|题目\s*\d+|Q\s*\d+[\).、:：]?)/gi
  const matches = Array.from(text.matchAll(markerRegex))
  if (matches.length > 1) {
    const blocks = matches
      .map((match, index) => {
        const start = match.index + (match[0].startsWith('\n') ? 1 : 0)
        const end = matches[index + 1]?.index ?? text.length
        return text.slice(start, end).trim()
      })
      .filter(Boolean)
    if (blocks.filter(hasQuestionShape).length >= 2) {
      return blocks
    }
  }

  const stemBlocks = text
    .split(/\n(?=\s*(?:题干|问题|题目)\s*[:：])/g)
    .map((block) => block.trim())
    .filter(Boolean)
  if (stemBlocks.length > 1 && stemBlocks.filter(hasQuestionShape).length >= 2) {
    return stemBlocks
  }

  return [text]
}

function hasQuestionShape(text) {
  const optionCount = (String(text || '').match(/(?:^|\n)\s*[A-D][\.\、:：]/gi) || []).length
  return optionCount >= 3
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
    .replace(/^(?:第\s*)?\d+\s*[题、.．:：)]\s*/, '')
    .replace(/^题目\s*\d+\s*[:：]?\s*/, '')
    .replace(/^Q\s*\d+[\).、:：]?\s*/i, '')
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
    const history = uni.getStorageSync(IMPORT_HISTORY_KEY) || []
    uni.setStorageSync(IMPORT_HISTORY_KEY, [
      {
        created_at: new Date().toLocaleString(),
        count: Number(response.inserted_count || 0)
      },
      ...(Array.isArray(history) ? history : [])
    ].slice(0, 20))
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
  padding: 24rpx 24rpx calc(env(safe-area-inset-bottom) + 260rpx);
  box-sizing: border-box;
  background:
    radial-gradient(circle at 12% 0%, rgba(186, 226, 255, 0.68) 0, rgba(186, 226, 255, 0) 300rpx),
    radial-gradient(circle at 92% 4%, rgba(205, 249, 216, 0.74) 0, rgba(205, 249, 216, 0) 320rpx),
    linear-gradient(180deg, #f7fbff 0%, #ffffff 46%, #f7fbff 100%);
}

.import-hero {
  position: relative;
  min-height: 128rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 210rpx 18rpx 96rpx;
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
.history-btn::after,
.file-delete-btn::after,
.editor-back-btn::after,
.recognize-btn::after,
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
  font-size: 40rpx;
  line-height: 1.15;
  font-weight: 800;
  color: #0f172a;
}

.hero-subtitle {
  margin-top: 10rpx;
  font-size: 23rpx;
  color: #6b7280;
}

.history-btn {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 190rpx;
  height: 68rpx;
  margin: 0;
  padding: 0 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  border-radius: 22rpx;
  border: 1rpx solid #93a7ca;
  color: #0f326f;
  background: rgba(255, 255, 255, 0.9);
  font-size: 23rpx;
  font-weight: 800;
  line-height: 1;
  box-sizing: border-box;
}

.history-icon {
  font-size: 31rpx;
  line-height: 1;
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

.landing-content {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.file-drop-zone {
  min-height: 420rpx;
  padding: 48rpx 28rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2rpx dashed #1769ff;
  border-radius: 28rpx;
  background:
    radial-gradient(circle at 50% 45%, rgba(220, 235, 255, 0.9) 0, rgba(238, 246, 255, 0.72) 42%, rgba(248, 251, 255, 0.96) 100%);
  box-sizing: border-box;
}

.file-upload-illustration {
  position: relative;
  width: 170rpx;
  height: 170rpx;
}

.file-shape {
  position: absolute;
  left: 16rpx;
  top: 4rpx;
  width: 122rpx;
  height: 150rpx;
  border: 7rpx solid #1769ff;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.35);
  box-sizing: border-box;
}

.file-fold {
  position: absolute;
  right: -7rpx;
  top: -7rpx;
  width: 50rpx;
  height: 50rpx;
  border-left: 7rpx solid #1769ff;
  border-bottom: 7rpx solid #1769ff;
  border-radius: 0 12rpx 0 12rpx;
  background: #e9f2ff;
}

.file-arrow {
  position: absolute;
  inset: 50rpx 0 auto;
  color: #1769ff;
  text-align: center;
  font-size: 78rpx;
  font-weight: 500;
  line-height: 1;
}

.file-plus {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 7rpx solid #1769ff;
  border-radius: 50%;
  color: #1769ff;
  background: #eef5ff;
  font-size: 50rpx;
  line-height: 1;
  box-sizing: border-box;
}

.drop-title {
  margin-top: 22rpx;
  color: #0b2454;
  font-size: 34rpx;
  font-weight: 900;
}

.drop-action {
  margin-top: 12rpx;
  color: #1769ff;
  font-size: 28rpx;
  font-weight: 800;
}

.drop-formats,
.drop-limit {
  margin-top: 18rpx;
  color: #657695;
  font-size: 21rpx;
  text-align: center;
}

.drop-limit {
  margin-top: 8rpx;
}

.selected-file-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.selected-file-card {
  min-height: 118rpx;
  padding: 18rpx 20rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
  border: 1rpx solid #dbe3ef;
  border-radius: 22rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 28rpx rgba(15, 23, 42, 0.05);
  box-sizing: border-box;
}

.file-type-icon {
  flex: 0 0 76rpx;
  width: 76rpx;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4rpx solid #1769ff;
  border-radius: 14rpx;
  color: #1769ff;
  background: #f3f7ff;
  font-size: 19rpx;
  font-weight: 900;
  box-sizing: border-box;
}

.file-type-icon.sheet,
.file-thumb.sheet {
  border-color: #16a34a;
  color: #15803d;
  background: #f0fdf4;
}

.file-type-icon.document,
.file-thumb.document {
  border-color: #7c3aed;
  color: #6d28d9;
  background: #f5f3ff;
}

.file-type-icon.data,
.file-thumb.data {
  border-color: #0891b2;
  color: #0e7490;
  background: #ecfeff;
}

.selected-file-main {
  flex: 1;
  min-width: 0;
}

.selected-file-name {
  overflow: hidden;
  color: #0f172a;
  font-size: 27rpx;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-file-meta {
  margin-top: 12rpx;
  display: flex;
  align-items: center;
  gap: 22rpx;
  color: #657695;
  font-size: 22rpx;
}

.ready-status {
  color: #16a34a;
  font-weight: 800;
}

.file-delete-btn {
  flex: 0 0 64rpx;
  width: 64rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1rpx solid #d5deeb;
  border-radius: 50%;
  color: #253a62;
  background: #ffffff;
  font-size: 29rpx;
  line-height: 1;
}

.recognition-card,
.flow-card {
  padding: 26rpx 28rpx;
  border: 1rpx solid #dbe3ef;
  border-radius: 22rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 28rpx rgba(15, 23, 42, 0.04);
}

.landing-section-title {
  color: #0b2454;
  font-size: 28rpx;
  font-weight: 900;
}

.recognition-tags {
  margin-top: 18rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.recognition-tag {
  padding: 10rpx 22rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 800;
}

.recognition-tag.blue {
  color: #1769ff;
  background: #eaf2ff;
}

.recognition-tag.green {
  color: #15803d;
  background: #e5f9ed;
}

.recognition-tag.purple {
  color: #6d28d9;
  background: #f1eefe;
}

.recognition-copy {
  margin-top: 18rpx;
  color: #53647f;
  font-size: 22rpx;
  line-height: 1.55;
}

.flow-card {
  padding: 24rpx 18rpx 18rpx;
}

.flow-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 4rpx;
}

.flow-step {
  position: relative;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.flow-number {
  position: absolute;
  top: -8rpx;
  left: calc(50% - 46rpx);
  z-index: 2;
  width: 30rpx;
  height: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #ffffff;
  background: #1769ff;
  font-size: 17rpx;
  font-weight: 900;
}

.flow-icon {
  width: 68rpx;
  height: 68rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #0f326f;
  background: #f1f5fb;
  font-size: 31rpx;
  font-weight: 900;
}

.flow-icon-image {
  width: 42rpx;
  height: 42rpx;
}

.flow-title {
  margin-top: 12rpx;
  color: #263449;
  font-size: 20rpx;
  font-weight: 800;
  text-align: center;
  white-space: nowrap;
}

.flow-arrow {
  position: absolute;
  top: 18rpx;
  right: -14rpx;
  color: #8ca0bf;
  font-size: 32rpx;
}

.flow-note {
  margin: 20rpx -18rpx -18rpx;
  padding: 14rpx 20rpx;
  border-top: 1rpx solid #e4eaf2;
  color: #61728e;
  background: #fbfcfe;
  font-size: 20rpx;
  line-height: 1.45;
}

.editor-toolbar {
  padding: 14rpx 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  border: 1rpx solid #dbe3ef;
  border-radius: 18rpx;
  background: #ffffff;
}

.editor-back-btn {
  height: 58rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 1rpx solid #1769ff;
  border-radius: 16rpx;
  color: #1769ff;
  background: #ffffff;
  font-size: 21rpx;
  font-weight: 800;
  line-height: 1;
}

.editor-progress {
  display: flex;
  gap: 18rpx;
  color: #657695;
  font-size: 21rpx;
  font-weight: 800;
}

.step-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.step-item {
  min-height: 118rpx;
  padding: 16rpx 10rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
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
  font-size: 23rpx;
  font-weight: 800;
  color: #0f172a;
  text-align: center;
  white-space: nowrap;
}

.step-desc {
  margin-top: 4rpx;
  font-size: 20rpx;
  color: #8b95a7;
  text-align: center;
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

.panel-head > view:first-child {
  flex: 1 1 auto;
  min-width: 0;
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
  flex: 0 0 auto;
  min-width: 144rpx;
  height: 64rpx;
  margin: 0;
  padding: 0 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18rpx;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  box-sizing: border-box;
}

.primary-mini-btn {
  min-width: 154rpx;
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

.file-thumb {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4rpx solid #1769ff;
  color: #1769ff;
  font-size: 24rpx;
  font-weight: 900;
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
  min-height: 150rpx;
  padding: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  border: 1rpx solid rgba(226, 232, 240, 0.92);
  border-radius: 26rpx;
  background: #ffffff;
  box-shadow: 0 20rpx 60rpx rgba(15, 23, 42, 0.14);
  box-sizing: border-box;
}

.recognize-bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  padding: 28rpx 40rpx calc(env(safe-area-inset-bottom) + 26rpx);
  border-radius: 34rpx 34rpx 0 0;
  background: #ffffff;
  box-shadow: 0 -18rpx 50rpx rgba(15, 23, 42, 0.08);
  box-sizing: border-box;
}

.recognize-btn {
  width: 100%;
  height: 86rpx;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
  border: 0;
  border-radius: 22rpx;
  color: #ffffff;
  background: linear-gradient(135deg, #1769ff 0%, #0062ff 100%);
  font-size: 31rpx;
  font-weight: 900;
  line-height: 1;
  box-shadow: 0 14rpx 28rpx rgba(23, 105, 255, 0.22);
}

.recognize-btn[disabled] {
  opacity: 0.52;
  box-shadow: none;
}

.recognize-icon {
  font-size: 38rpx;
  line-height: 1;
}

.recognize-hint {
  margin-top: 18rpx;
  color: #657695;
  font-size: 22rpx;
  text-align: center;
}

.bottom-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  color: #475569;
  font-size: 23rpx;
  font-weight: 800;
  line-height: 1.2;
}

.bottom-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.bottom-btn {
  height: 76rpx;
  min-width: 0;
  margin: 0;
  padding: 0 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20rpx;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1;
  white-space: nowrap;
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
