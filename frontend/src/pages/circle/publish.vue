<template>
  <view
    class="publish-page"
    :class="{ 'is-leaving': isLeaving }"
    @touchstart="beginPublishEdgeSwipe"
    @touchend="finishPublishEdgeSwipe"
  >
    <AppPageHeader :title="publishPageTitle" variant="glass" fixed @back="goBack">
      <template #right>
        <button
          class="publish-header-submit"
          :class="{ 'is-progress': submitting }"
          :disabled="!canPublish || submitting"
          :aria-label="headerPublishText"
          @tap="publish"
        >
          {{ headerPublishText }}
        </button>
      </template>
    </AppPageHeader>

    <view v-if="accessChecking" class="publish-access-state">正在校验发布权限…</view>

    <view v-else-if="accessError" class="publish-access-state publish-access-error">
      <view>{{ accessError }}</view>
      <button @tap="initializePublishPage(hasDraftContent())">重新验证</button>
    </view>

    <scroll-view v-else class="publish-scroll" scroll-y>
      <view class="publish-content">
        <view class="publish-card">
          <view class="publish-field-label">{{ postType === 'experience' ? '考试类别' : '话题分类' }}</view>
          <template v-if="postType === 'experience'">
            <view class="publish-topic-grid">
              <button
                v-for="topic in communityExperienceExamCodes"
                :key="topic"
                class="publish-topic"
                :class="{ active: selectedTopic === topic }"
                :aria-pressed="selectedTopic === topic"
                :disabled="submitting"
                @tap="selectedTopic = topic"
              >
                {{ topic }}
              </button>
            </view>
            <view class="publish-field-label publish-stage-label">备考阶段</view>
            <view class="publish-stage-grid">
              <button
                v-for="stage in communityExperienceStages"
                :key="stage"
                class="publish-topic"
                :class="{ active: selectedExperienceStages.includes(stage) }"
                :aria-pressed="selectedExperienceStages.includes(stage)"
                :disabled="submitting"
                @tap="toggleExperienceStage(stage)"
              >
                {{ stage }}
              </button>
            </view>
            <view class="publish-review-note">
              {{ editingPostId ? '修改完成后将重新进入平台审核' : '提交后进入平台审核，通过后公开展示' }}
            </view>
          </template>
          <view v-else class="publish-topic-grid">
            <button
              v-for="topic in topics"
              :key="topic"
              class="publish-topic"
              :class="{ active: selectedTopic === topic }"
              :aria-pressed="selectedTopic === topic"
              :disabled="submitting"
              @tap="selectedTopic = topic"
            >
              {{ topic }}
            </button>
          </view>

          <view class="publish-field-row">
            <view class="publish-field-label">标题</view>
            <text class="publish-counter">{{ title.length }}/80</text>
          </view>
          <input
            v-model="title"
            class="publish-input"
            maxlength="80"
            placeholder="给你的话题起个标题"
            placeholder-class="publish-placeholder"
            :disabled="submitting"
          />

          <view class="publish-field-row">
            <view class="publish-field-label">内容</view>
            <text class="publish-counter">{{ content.length }}/3000</text>
          </view>
          <textarea
            v-model="content"
            class="publish-textarea"
            maxlength="3000"
            placeholder="分享你的问题、计划或心得"
            placeholder-class="publish-placeholder"
            :auto-height="false"
            :disabled="submitting"
          />

          <view class="publish-image-field">
            <view class="publish-field-row publish-image-field-row">
              <view class="publish-field-label">图片</view>
              <text class="publish-counter">{{ selectedImages.length }}/{{ MAX_IMAGE_COUNT }}</text>
            </view>
            <view class="publish-image-grid">
              <view v-for="(image, index) in selectedImages" :key="image.id" class="publish-image-item">
                <image class="publish-image-preview" :src="image.path" mode="aspectFill" />
                <view v-if="image.uploading" class="publish-image-uploading">上传中</view>
                <button class="publish-image-remove" :aria-label="`删除第 ${index + 1} 张图片`" :disabled="submitting" @tap.stop="removeImage(index)"><CloseIcon tone="white" /></button>
              </view>
              <button
                v-if="selectedImages.length < MAX_IMAGE_COUNT"
                class="publish-image-add"
                aria-label="添加图片"
                :disabled="submitting"
                @tap="chooseImages"
              >
                <text>+</text>
              </button>
            </view>
            <view v-if="draftImageNotice" class="publish-draft-notice">{{ draftImageNotice }}</view>
          </view>

          <view
            v-if="publishStatusText"
            class="publish-status"
            :class="{ 'is-error': submitStatus.phase === 'error' }"
            role="status"
          >
            {{ publishStatusText }}
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { onBackPress, onLoad, onUnload } from '@dcloudio/uni-app'
import {
  createCommunityPost,
  fetchMyCommunityPost,
  updateMyCommunityPost,
  uploadCommunityImage
} from '../../api/community'
import { fetchMyMentorProfile } from '../../api/mentorConsultation'
import { getAuthUser, isLoggedIn } from '../../utils/auth'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import CloseIcon from '../../components/CloseIcon.vue'

const communityChatTopics = ['备考日常', '中华文化', '数学基础', '英语运用', '逻辑推理']
const communityExperienceExamCodes = Object.freeze(['Z001', 'Z002'])
const communityExperienceStages = Object.freeze(['申请制', '初试', '复试'])
const topicSets = {
  chat: communityChatTopics,
  experience: communityExperienceExamCodes
}
const MAX_IMAGE_COUNT = 9
const MAX_UPLOAD_CONCURRENCY = 2
const DRAFT_SAVE_DELAY_MS = 650
const DRAFT_STORAGE_VERSION = 2
const postType = ref('chat')
const topics = computed(() => topicSets[postType.value])
const selectedTopic = ref('')
const selectedExperienceStages = ref([])
const title = ref('')
const content = ref('')
const selectedImages = ref([])
const submitting = ref(false)
const isLeaving = ref(false)
const publishEdgeSwipeStart = ref(null)
const accessChecking = ref(true)
const accessError = ref('')
const editingPostId = ref('')
const clientRequestId = ref('')
const submitStatus = ref({ phase: 'idle', completed: 0, total: 0 })
const draftImageNotice = ref('')
let draftSaveTimer = null
let draftReady = false
let publishedSuccessfully = false

const publishPageTitle = computed(() => {
  if (editingPostId.value) return postType.value === 'experience' ? '修改经验贴' : '编辑帖子'
  return postType.value === 'experience' ? '发布经验贴' : '发布话题'
})

const canPublish = computed(() => Boolean(
  !accessChecking.value
  && !accessError.value
  && selectedTopic.value
  && (postType.value !== 'experience' || selectedExperienceStages.value.length)
  && title.value.trim()
  && content.value.trim()
))

const publishStatusText = computed(() => {
  const { phase, completed, total } = submitStatus.value
  if (phase === 'uploading') return `正在上传图片 ${completed}/${total}`
  if (phase === 'posting') return editingPostId.value ? '图片已就绪，正在保存修改…' : '图片已就绪，正在提交…'
  if (phase === 'error') return `提交失败，草稿和图片已保留，可点击右上角“${headerIdleText.value}”重试`
  return ''
})

const headerIdleText = computed(() => {
  if (editingPostId.value) return '保存'
  return '发布'
})

const headerPublishText = computed(() => {
  const { phase, completed, total } = submitStatus.value
  if (phase === 'uploading' && total > 0) return `${completed}/${total}`
  if (phase === 'posting') return '提交中'
  return headerIdleText.value
})

watch(
  [selectedTopic, title, content, selectedExperienceStages],
  () => {
    if (!draftReady) return
    markPayloadChanged()
  },
  { deep: true, flush: 'sync' }
)

onLoad((options) => {
  draftReady = false
  postType.value = options?.type === 'experience' ? 'experience' : 'chat'
  editingPostId.value = String(options?.edit || '').trim()
  selectedTopic.value = ''
  selectedExperienceStages.value = []
  isLeaving.value = false
  publishedSuccessfully = false
  const restoredDraft = restoreDraft()
  draftReady = true
  void initializePublishPage(restoredDraft)
})

onUnload(() => {
  if (publishedSuccessfully) {
    clearDraft()
    return
  }
  flushDraftSave()
})

onBackPress(() => {
  if (!submitting.value || publishedSuccessfully) return false
  showPublishingWaitToast()
  return true
})

function toggleExperienceStage(stage) {
  if (submitting.value || !communityExperienceStages.includes(stage)) return
  const currentStages = selectedExperienceStages.value
  selectedExperienceStages.value = currentStages.includes(stage)
    ? currentStages.filter((item) => item !== stage)
    : [...currentStages, stage]
}

function normalizeExperienceStages(stages) {
  const selected = new Set(Array.isArray(stages) ? stages : [])
  return communityExperienceStages.filter((stage) => selected.has(stage))
}

function createClientRequestId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (marker) => {
    const random = Math.floor(Math.random() * 16)
    return (marker === 'x' ? random : ((random & 0x3) | 0x8)).toString(16)
  })
}

function ensureClientRequestId() {
  if (!clientRequestId.value) clientRequestId.value = createClientRequestId()
  return clientRequestId.value
}

function getDraftStorageKey() {
  const userId = String(getAuthUser()?.id || 'guest')
  const editingKey = editingPostId.value ? `-edit-${encodeURIComponent(editingPostId.value)}` : ''
  return `circle-publish-draft-v${DRAFT_STORAGE_VERSION}-${encodeURIComponent(userId)}-${postType.value}${editingKey}`
}

function hasDraftContent() {
  return Boolean(
    selectedTopic.value
    || selectedExperienceStages.value.length
    || title.value.trim()
    || content.value.trim()
  )
}

function getDraftPayload() {
  const uploadedImages = selectedImages.value
    .map((image) => ({
      url: String(image.uploadedUrl || '').trim(),
      thumbnailUrl: String(image.uploadedThumbnailUrl || '').trim()
    }))
    .filter((image) => image.url)
  const uploadedImageUrls = uploadedImages.map((image) => image.url)
  return {
    version: DRAFT_STORAGE_VERSION,
    postType: postType.value,
    category: selectedTopic.value,
    experienceStages: postType.value === 'experience'
      ? normalizeExperienceStages(selectedExperienceStages.value)
      : [],
    title: title.value,
    content: content.value,
    selectedImageCount: selectedImages.value.length,
    uploadedImages,
    uploadedImageUrls,
    editingPostId: editingPostId.value,
    clientRequestId: ensureClientRequestId(),
    updatedAt: Date.now()
  }
}

function restoreDraft() {
  let draft = null
  try {
    draft = uni.getStorageSync(getDraftStorageKey())
  } catch (error) {
    draft = null
  }

  const allowedTopics = topicSets[postType.value]
  if (!draft || typeof draft !== 'object' || draft.postType !== postType.value) {
    clientRequestId.value = createClientRequestId()
    return false
  }
  if (String(draft.editingPostId || '') !== editingPostId.value) {
    clientRequestId.value = createClientRequestId()
    return false
  }

  const restoredTopic = String(draft.category || '').trim()
  selectedTopic.value = allowedTopics.includes(restoredTopic) ? restoredTopic : ''
  title.value = String(draft.title || '').slice(0, 80)
  content.value = String(draft.content || '').slice(0, 3000)
  selectedExperienceStages.value = postType.value === 'experience'
    ? normalizeExperienceStages(draft.experienceStages)
    : []
  const rawUploadedImages = Array.isArray(draft.uploadedImages)
    ? draft.uploadedImages
    : (Array.isArray(draft.uploadedImageUrls) ? draft.uploadedImageUrls : []).map((url) => ({ url }))
  const uploadedImages = rawUploadedImages
    .map((item) => ({
      url: String(item?.url || '').trim(),
      thumbnailUrl: String(item?.thumbnailUrl || item?.thumbnail_url || '').trim()
    }))
    .filter((item, index, items) => /^https?:\/\//i.test(item.url) && items.findIndex((candidate) => candidate.url === item.url) === index)
    .slice(0, MAX_IMAGE_COUNT)
  selectedImages.value = uploadedImages.map((item, index) => ({
    id: `restored-image-${Date.now()}-${index}`,
    path: item.url,
    file: null,
    fileName: `community-image-${index + 1}`,
    uploadedUrl: item.url,
    uploadedThumbnailUrl: item.thumbnailUrl || item.url,
    uploading: false
  }))
  const savedImageCount = Math.min(
    MAX_IMAGE_COUNT,
    Math.max(uploadedImages.length, Number(draft.selectedImageCount) || 0)
  )
  const hasMissingLocalImages = savedImageCount > uploadedImages.length
  draftImageNotice.value = hasMissingLocalImages
    ? '部分尚未上传的本地图片需要重新选择'
    : ''
  const restoredRequestId = String(draft.clientRequestId || '').trim()
  clientRequestId.value = !hasMissingLocalImages && isClientRequestId(restoredRequestId)
    ? restoredRequestId
    : createClientRequestId()
  return true
}

function isClientRequestId(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)
}

function markPayloadChanged() {
  clientRequestId.value = createClientRequestId()
  if (submitStatus.value.phase === 'error') {
    submitStatus.value = { phase: 'idle', completed: 0, total: 0 }
  }
  scheduleDraftSave()
}

function scheduleDraftSave() {
  if (draftSaveTimer) clearTimeout(draftSaveTimer)
  draftSaveTimer = setTimeout(() => {
    draftSaveTimer = null
    saveDraftNow()
  }, DRAFT_SAVE_DELAY_MS)
}

function saveDraftNow() {
  try {
    if (!hasDraftContent()) {
      uni.removeStorageSync(getDraftStorageKey())
      return
    }
    uni.setStorageSync(getDraftStorageKey(), getDraftPayload())
  } catch (error) {
    // 本地存储空间不足时不打断编辑和发布。
  }
}

function flushDraftSave() {
  if (draftSaveTimer) {
    clearTimeout(draftSaveTimer)
    draftSaveTimer = null
  }
  saveDraftNow()
}

function clearDraft() {
  if (draftSaveTimer) {
    clearTimeout(draftSaveTimer)
    draftSaveTimer = null
  }
  try {
    uni.removeStorageSync(getDraftStorageKey())
  } catch (error) {
    // 发布成功后的存储清理不影响页面返回。
  }
}

async function initializePublishPage(restoredDraft = false) {
  const hasAccess = await verifyPublishAccess()
  if (!hasAccess || !editingPostId.value) return
  accessChecking.value = true
  try {
    const response = await fetchMyCommunityPost(editingPostId.value)
    const post = response?.post || {}
    const remotePostType = (post.post_type || post.postType) === 'experience' ? 'experience' : 'chat'
    if (remotePostType !== postType.value) {
      accessError.value = '帖子类型与当前编辑页面不一致，请返回后重试。'
      return
    }
    if (!restoredDraft) populateEditingPost(post)
  } catch (error) {
    accessError.value = getSafeError(error, '经验贴原稿读取失败，请检查网络后重试。')
  } finally {
    accessChecking.value = false
  }
}

function populateEditingPost(post = {}) {
  draftReady = false
  const media = Array.isArray(post.media) ? post.media.slice(0, MAX_IMAGE_COUNT) : []
  const allowedTopics = topicSets[postType.value]
  selectedTopic.value = allowedTopics.includes(String(post.category || '')) ? String(post.category) : ''
  selectedExperienceStages.value = normalizeExperienceStages(
    post.experience_stages || post.experienceStages
  )
  title.value = String(post.title || '').slice(0, 80)
  content.value = String(post.content || post.summary || '').slice(0, 3000)
  selectedImages.value = media
    .map((item) => ({
      url: String(item?.imageUrl || item?.image_url || '').trim(),
      thumbnailUrl: String(item?.thumbnailUrl || item?.thumbnail_url || '').trim()
    }))
    .filter((item) => item.url)
    .map((item, index) => ({
      id: `editing-image-${editingPostId.value}-${index}`,
      path: item.url,
      file: null,
      fileName: `community-image-${index + 1}`,
      uploadedUrl: item.url,
      uploadedThumbnailUrl: item.thumbnailUrl || item.url,
      uploading: false
    }))
  clientRequestId.value = createClientRequestId()
  draftImageNotice.value = ''
  draftReady = true
  scheduleDraftSave()
}

async function verifyPublishAccess() {
  accessChecking.value = true
  accessError.value = ''
  if (!isLoggedIn()) {
    goLogin()
    return false
  }

  if (postType.value === 'experience') {
    try {
      const profile = await fetchMyMentorProfile()
      if (!profile?.mentor?.verified) {
        uni.showToast({ title: '经验贴仅支持认证前辈发布', icon: 'none' })
        uni.redirectTo({ url: '/pages-sub-consultation/consultation/mentor-apply?mode=apply' })
        return false
      }
    } catch (error) {
      const statusCode = Number(error?.statusCode || error?.status || 0)
      if (statusCode === 404) {
        uni.showToast({ title: '经验贴仅支持认证前辈发布', icon: 'none' })
        uni.redirectTo({ url: '/pages-sub-consultation/consultation/mentor-apply?mode=apply' })
        return false
      }
      if (statusCode === 401) {
        goLogin()
        return false
      }
      accessError.value = '认证状态暂时无法验证，请检查网络后重试。'
      accessChecking.value = false
      return false
    }
  }

  accessChecking.value = false
  return true
}

function goBack() {
  if (isLeaving.value) return
  if (submitting.value && !publishedSuccessfully) {
    showPublishingWaitToast()
    return
  }
  isLeaving.value = true

  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=circle' })
    }
  })
}

function getTouchPoint(event) {
  return event?.touches?.[0] || event?.changedTouches?.[0] || null
}

function beginPublishEdgeSwipe(event) {
  if (isLeaving.value || (submitting.value && !publishedSuccessfully)) return
  const touch = getTouchPoint(event)
  if (!touch) return
  publishEdgeSwipeStart.value = {
    x: Number(touch.clientX ?? touch.pageX ?? 0),
    y: Number(touch.clientY ?? touch.pageY ?? 0)
  }
}

function finishPublishEdgeSwipe(event) {
  const start = publishEdgeSwipeStart.value
  publishEdgeSwipeStart.value = null
  if (!start || isLeaving.value) return

  const touch = getTouchPoint(event)
  if (!touch) return
  const deltaX = Number(touch.clientX ?? touch.pageX ?? 0) - start.x
  const deltaY = Number(touch.clientY ?? touch.pageY ?? 0) - start.y
  if (start.x <= 28 && deltaX >= 72 && Math.abs(deltaX) > Math.abs(deltaY) * 1.35) {
    goBack()
  }
}

function goLogin() {
  const editQuery = editingPostId.value ? `&edit=${encodeURIComponent(editingPostId.value)}` : ''
  uni.redirectTo({
    url: `/pages/login/index?redirect=${encodeURIComponent(`/pages/circle/publish?type=${postType.value}${editQuery}`)}`
  })
}

function showPublishingWaitToast() {
  uni.showToast({ title: '正在提交，请稍候', icon: 'none' })
}

function chooseImages() {
  const remainingCount = MAX_IMAGE_COUNT - selectedImages.value.length
  if (remainingCount <= 0 || submitting.value) return

  uni.chooseImage({
    count: remainingCount,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success(result) {
      const tempFiles = Array.isArray(result.tempFiles) ? result.tempFiles : []
      const tempFilePaths = Array.isArray(result.tempFilePaths) ? result.tempFilePaths : []
      const images = tempFilePaths.map((path, index) => {
        const tempFile = tempFiles[index]
        const fileCandidate = tempFile?.file || tempFile?.fileObject || tempFile
        const file = typeof Blob !== 'undefined' && fileCandidate instanceof Blob ? fileCandidate : null
        return {
          id: `image-${Date.now()}-${index}-${Math.random().toString(36).slice(2, 8)}`,
          path: path || tempFile?.path || tempFile?.tempFilePath || '',
          file,
          fileName: tempFile?.name || file?.name || `community-image-${index + 1}`,
          uploadedUrl: '',
          uploadedThumbnailUrl: '',
          uploading: false
        }
      }).filter((image) => image.path)

      selectedImages.value = [...selectedImages.value, ...images].slice(0, MAX_IMAGE_COUNT)
      if (images.length) {
        draftImageNotice.value = ''
        markPayloadChanged()
      }
    },
    fail(error) {
      const message = String(error?.errMsg || '')
      if (!message.includes('cancel')) {
        uni.showToast({ title: '图片选择失败，请重试', icon: 'none' })
      }
    }
  })
}

function removeImage(index) {
  if (submitting.value) return
  selectedImages.value.splice(index, 1)
  draftImageNotice.value = ''
  markPayloadChanged()
}

async function uploadSelectedImages() {
  const images = [...selectedImages.value]
  const media = new Array(images.length)
  const pendingIndexes = []
  let completed = 0
  let nextPending = 0
  let firstError = null

  images.forEach((image, index) => {
    if (image.uploadedUrl) {
      media[index] = {
        imageUrl: image.uploadedUrl,
        thumbnailUrl: image.uploadedThumbnailUrl || image.uploadedUrl
      }
      completed += 1
      return
    }
    pendingIndexes.push(index)
  })

  submitStatus.value = { phase: 'uploading', completed, total: images.length }
  if (!pendingIndexes.length) return media

  async function uploadWorker() {
    while (nextPending < pendingIndexes.length) {
      const imageIndex = pendingIndexes[nextPending]
      nextPending += 1
      const image = images[imageIndex]
      image.uploading = true
      try {
        const response = await uploadCommunityImage({
          filePath: image.path,
          file: image.file,
          fileName: image.fileName
        })
        if (!response?.url) throw { detail: '图片上传失败，请重试' }
        image.uploadedUrl = response.url
        image.uploadedThumbnailUrl = response.thumbnail_url || response.thumbnailUrl || response.url
        media[imageIndex] = {
          imageUrl: response.url,
          thumbnailUrl: image.uploadedThumbnailUrl
        }
        completed += 1
        submitStatus.value = { phase: 'uploading', completed, total: images.length }
        saveDraftNow()
      } catch (error) {
        if (!firstError) firstError = error
      } finally {
        image.uploading = false
      }
    }
  }

  const workerCount = Math.min(MAX_UPLOAD_CONCURRENCY, pendingIndexes.length)
  await Promise.all(Array.from({ length: workerCount }, () => uploadWorker()))
  if (firstError) throw firstError
  return media
}

async function publish() {
  if (!canPublish.value || submitting.value) return
  if (!isLoggedIn()) {
    goLogin()
    return
  }

  submitting.value = true
  flushDraftSave()
  let published = false
  try {
    const media = await uploadSelectedImages()
    submitStatus.value = { phase: 'posting', completed: media.length, total: media.length }
    const postPayload = {
      post_type: postType.value,
      category: selectedTopic.value,
      experience_stages: postType.value === 'experience'
        ? normalizeExperienceStages(selectedExperienceStages.value)
        : [],
      title: title.value.trim(),
      content: content.value.trim(),
      media,
      client_request_id: ensureClientRequestId()
    }
    if (editingPostId.value) {
      await updateMyCommunityPost(editingPostId.value, postPayload)
    } else {
      await createCommunityPost(postPayload)
    }
    uni.setStorageSync(`circle-community-feed-refresh-${postType.value}`, Date.now())
    published = true
    publishedSuccessfully = true
    clearDraft()
    submitStatus.value = { phase: 'idle', completed: 0, total: 0 }
    const successText = postType.value === 'experience'
      ? editingPostId.value ? '修改已提交审核' : '已提交审核'
      : editingPostId.value ? '帖子已更新' : '已发布到研友聊'
    uni.showToast({ title: successText, icon: 'success' })
    setTimeout(goBack, 500)
  } catch (error) {
    submitStatus.value = {
      phase: 'error',
      completed: submitStatus.value.completed,
      total: submitStatus.value.total
    }
    flushDraftSave()
    uni.showToast({ title: getSafeError(error, '内容提交失败，请稍后重试'), icon: 'none' })
  } finally {
    if (!published) {
      submitting.value = false
    }
  }
}

function getSafeError(error, fallback) {
  return error?.detail || error?.message || fallback
}
</script>

<style scoped>
.publish-page {
  min-height: 100vh;
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  background: var(--gyt-page-bg, #f4f8ff);
  color: #1d2928;
  isolation: isolate;
  contain: paint;
  overflow-x: hidden;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
}

.publish-page.is-leaving {
  pointer-events: none;
}

.publish-header-submit::after,
.publish-topic::after,
.publish-image-add::after,
.publish-image-remove::after {
  border: 0;
}

.publish-scroll {
  min-height: 0;
  flex: 1;
}

.publish-header-submit {
  box-sizing: border-box;
  min-width: 82rpx;
  height: 58rpx;
  margin: 0;
  padding: 0 10rpx;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #3478f6;
  font-size: 25rpx;
  line-height: 1;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.publish-header-submit[disabled] {
  color: #a9b6c7;
  opacity: 0.72;
}

.publish-header-submit.is-progress {
  padding: 0;
  color: #3478f6;
  font-size: 22rpx;
  opacity: 1;
}

.publish-content {
  width: 100%;
  max-width: 860rpx;
  margin: 0 auto;
  padding: 40rpx 32rpx calc(env(safe-area-inset-bottom) + 52rpx);
  box-sizing: border-box;
}

.publish-card {
  padding: 30rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.86);
  border-radius: 30rpx;
  background: rgba(252, 254, 253, 0.9);
  box-shadow: 0 18rpx 44rpx rgba(37, 63, 60, 0.1);
  -webkit-backdrop-filter: blur(18px) saturate(112%);
  backdrop-filter: blur(18px) saturate(112%);
}

.publish-field-row {
  margin-top: 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.publish-field-label {
  color: #405553;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 800;
}

.publish-counter {
  color: #9aa8a6;
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 600;
}

.publish-topic-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.publish-stage-grid {
  margin-top: 12rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.publish-stage-label {
  margin-top: 22rpx;
}

.publish-review-note {
  margin-top: 14rpx;
  color: #5d7188;
  font-size: 20rpx;
  line-height: 1.45;
  font-weight: 650;
}

.publish-topic {
  box-sizing: border-box;
  min-height: 68rpx;
  margin: 0;
  padding: 0 16rpx;
  border: 2rpx solid rgba(212, 225, 235, 0.92);
  border-radius: 18rpx;
  background: #f7fbff;
  color: #637582;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 700;
  text-align: center;
}

.publish-topic.active {
  border-color: rgba(52, 120, 246, 0.18);
  background: #eaf2ff;
  color: #3478f6;
}

.publish-input,
.publish-textarea {
  width: 100%;
  box-sizing: border-box;
  margin-top: 14rpx;
  border: 2rpx solid #e3edf1;
  border-radius: 20rpx;
  background: #ffffff;
  color: #1d2928;
  font-size: 25rpx;
  line-height: 1.55;
  font-weight: 600;
}

.publish-input {
  height: 82rpx;
  padding: 0 22rpx;
}

.publish-textarea {
  height: 360rpx;
  min-height: 360rpx;
  max-height: 360rpx;
  padding: 20rpx 22rpx;
  overflow-y: auto;
}

.publish-image-field {
  margin-top: 32rpx;
}

.publish-image-field-row {
  margin-top: 0;
}

.publish-draft-notice {
  margin-top: 12rpx;
  color: #b16a37;
  font-size: 20rpx;
  line-height: 1.45;
  font-weight: 600;
}

.publish-image-grid {
  margin-top: 14rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.publish-image-item,
.publish-image-add {
  position: relative;
  box-sizing: border-box;
  aspect-ratio: 1 / 1;
  border-radius: 18rpx;
  overflow: hidden;
}

.publish-image-item {
  background: #eaf0ef;
}

.publish-image-preview {
  width: 100%;
  height: 100%;
  display: block;
}

.publish-image-uploading {
  position: absolute;
  inset: 0;
  background: rgba(20, 38, 37, 0.46);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  font-weight: 700;
}

.publish-image-remove {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  width: 42rpx;
  height: 42rpx;
  min-width: 42rpx;
  min-height: 42rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(24, 40, 39, 0.62);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.publish-status {
  margin-top: 24rpx;
  padding: 16rpx 18rpx;
  border-radius: 16rpx;
  background: #edf4ff;
  color: #3478f6;
  font-size: 21rpx;
  line-height: 1.45;
  font-weight: 700;
  text-align: center;
}

.publish-status.is-error {
  background: #fff3ef;
  color: #c15b3d;
}
.publish-image-remove :deep(.close-icon-image) { width: 26rpx; height: 26rpx; }

.publish-image-add {
  width: 100%;
  min-height: 0;
  margin: 0;
  padding: 0;
  border: 2rpx dashed rgba(52, 120, 246, 0.36);
  background: rgba(234, 242, 255, 0.78);
  color: #3478f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.publish-image-add text {
  margin-top: -4rpx;
  font-size: 58rpx;
  line-height: 1;
  font-weight: 300;
}

.publish-placeholder {
  color: #a2afad;
  font-weight: 500;
}

.publish-access-state {
  min-height: 42vh;
  padding: 48rpx;
  color: #6d7f98;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 22rpx;
  font-size: 24rpx;
  font-weight: 700;
  text-align: center;
}

.publish-access-error button {
  min-width: 184rpx;
  min-height: 64rpx;
  margin: 0;
  padding: 0 22rpx;
  border: 0;
  border-radius: 18rpx;
  background: #3478f6;
  color: #ffffff;
  font-size: 22rpx;
  font-weight: 800;
}

.publish-access-error button::after {
  border: 0;
}

.publish-back:active,
.publish-header-submit:active,
.publish-topic:active,
.publish-image-add:active,
.publish-image-remove:active {
  transform: scale(0.98);
}

@media (min-width: 750px) {
  .publish-content {
    padding-left: 48rpx;
    padding-right: 48rpx;
  }
}

</style>
