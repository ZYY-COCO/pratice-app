<template>
  <view
    class="publish-page"
    :class="{ 'is-leaving': isLeaving }"
    @touchstart="beginPublishEdgeSwipe"
    @touchend="finishPublishEdgeSwipe"
  >
    <view class="publish-header">
      <button class="publish-back" aria-label="返回" @tap="goBack">
        <image src="/static/ui-icons/back.svg" mode="aspectFit" />
      </button>
      <view class="publish-header-title">{{ postType === 'experience' ? '发布经验贴' : '发布话题' }}</view>
      <view class="publish-header-placeholder"></view>
    </view>

    <scroll-view class="publish-scroll" scroll-y>
      <view class="publish-content">
        <view class="publish-card">
          <view class="publish-field-label">话题分类</view>
          <view class="publish-topic-grid">
            <button
              v-for="topic in topics"
              :key="topic"
              class="publish-topic"
              :class="{ active: selectedTopic === topic }"
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
            auto-height
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
                <button class="publish-image-remove" :aria-label="`删除第 ${index + 1} 张图片`" :disabled="submitting" @tap.stop="removeImage(index)">×</button>
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
          </view>
        </view>

        <button class="publish-submit" :disabled="!canPublish || submitting" @tap="publish">
          {{ submitting ? '发布中...' : '发布话题' }}
        </button>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { createCommunityPost, uploadCommunityImage } from '../../api/community'
import { isLoggedIn } from '../../utils/auth'

const communityChatTopics = ['中华文化', '数学基础', '英语运用', '逻辑推理']
const communityExperienceTopics = ['Z001', 'Z002']
const topicSets = {
  chat: communityChatTopics,
  experience: communityExperienceTopics
}
const MAX_IMAGE_COUNT = 9
const postType = ref('chat')
const topics = computed(() => topicSets[postType.value])
const selectedTopic = ref('')
const title = ref('')
const content = ref('')
const selectedImages = ref([])
const submitting = ref(false)
const isLeaving = ref(false)
const publishEdgeSwipeStart = ref(null)

const canPublish = computed(() => Boolean(selectedTopic.value && title.value.trim() && content.value.trim()))

onLoad((options) => {
  postType.value = options?.type === 'experience' ? 'experience' : 'chat'
  selectedTopic.value = ''
  isLeaving.value = false
})

function goBack() {
  if (isLeaving.value) return
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
  if (isLeaving.value) return
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
  uni.navigateTo({
    url: `/pages/login/index?redirect=${encodeURIComponent(`/pages/circle/publish?type=${postType.value}`)}`
  })
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
          uploading: false
        }
      }).filter((image) => image.path)

      selectedImages.value = [...selectedImages.value, ...images].slice(0, MAX_IMAGE_COUNT)
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
}

async function uploadSelectedImages() {
  const media = []
  for (const image of selectedImages.value) {
    if (image.uploadedUrl) {
      media.push({ imageUrl: image.uploadedUrl })
      continue
    }
    image.uploading = true
    try {
      const response = await uploadCommunityImage({
        filePath: image.path,
        file: image.file,
        fileName: image.fileName
      })
      if (!response?.url) {
        throw { detail: '图片上传失败，请重试' }
      }
      image.uploadedUrl = response.url
      media.push({ imageUrl: response.url })
    } finally {
      image.uploading = false
    }
  }

  return media
}

async function publish() {
  if (!canPublish.value || submitting.value) return
  if (!isLoggedIn()) {
    goLogin()
    return
  }

  submitting.value = true
  let published = false
  try {
    const media = await uploadSelectedImages()
    await createCommunityPost({
      post_type: postType.value,
      category: selectedTopic.value,
      title: title.value.trim(),
      content: content.value.trim(),
      media
    })
    uni.setStorageSync(`circle-community-feed-refresh-${postType.value}`, Date.now())
    published = true
    uni.showToast({ title: `已发布到${postType.value === 'experience' ? '经验贴' : '研友聊'}`, icon: 'success' })
    setTimeout(goBack, 500)
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '话题发布失败，请稍后重试'), icon: 'none' })
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
  box-sizing: border-box;
  background: #edf4f4;
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

.publish-header {
  position: relative;
  z-index: 1;
  min-height: calc(env(safe-area-inset-top) + 112rpx);
  padding: env(safe-area-inset-top) 32rpx 0;
  box-sizing: border-box;
  border-bottom: 2rpx solid rgba(215, 229, 226, 0.86);
  background: rgba(248, 252, 251, 0.9);
  display: grid;
  grid-template-columns: 66rpx minmax(0, 1fr) 66rpx;
  align-items: center;
  -webkit-backdrop-filter: blur(18px) saturate(116%);
  backdrop-filter: blur(18px) saturate(116%);
}

.publish-back {
  width: 66rpx;
  height: 66rpx;
  min-width: 66rpx;
  min-height: 66rpx;
  margin: 0;
  padding: 16rpx;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.72);
  color: #2d8580;
  display: flex;
  align-items: center;
  justify-content: center;
}

.publish-back::after,
.publish-topic::after,
.publish-submit::after,
.publish-image-add::after,
.publish-image-remove::after {
  border: 0;
}

.publish-back image {
  width: 100%;
  height: 100%;
}

.publish-header-title {
  color: #1b2725;
  font-size: 30rpx;
  line-height: 1.2;
  font-weight: 800;
  text-align: center;
}

.publish-scroll {
  height: calc(100vh - env(safe-area-inset-top) - 112rpx);
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
  min-height: 276rpx;
  padding: 20rpx 22rpx;
}

.publish-image-field {
  margin-top: 32rpx;
}

.publish-image-field-row {
  margin-top: 0;
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
  aspect-ratio: 9 / 16;
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
  padding: 0 0 4rpx;
  border: 0;
  border-radius: 50%;
  background: rgba(24, 40, 39, 0.62);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  line-height: 1;
}

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

.publish-submit {
  box-sizing: border-box;
  width: 100%;
  min-height: 88rpx;
  margin-top: 28rpx;
  padding: 0 24rpx;
  border: 0;
  border-radius: 24rpx;
  background: #3478f6;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 27rpx;
  line-height: 1.2;
  font-weight: 800;
  box-shadow: 0 14rpx 28rpx rgba(52, 120, 246, 0.24);
  text-align: center;
}

.publish-submit[disabled] {
  opacity: 0.46;
}

.publish-back:active,
.publish-topic:active,
.publish-submit:active,
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
