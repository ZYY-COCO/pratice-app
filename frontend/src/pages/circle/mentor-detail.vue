<template>
  <view class="mentor-detail-page">
    <MentorPageHeader title="前辈详情" @back="goBack" />

    <scroll-view scroll-y class="mentor-detail-scroll">
      <view v-if="mentor" class="mentor-detail-content">
        <view class="mentor-detail-hero">
          <view class="mentor-detail-person-row">
            <view class="mentor-detail-avatar" :class="`tone-${mentor.avatarTone || 'blue'}`">
              <image v-if="mentor.avatarUrl" :src="mentor.avatarUrl" mode="aspectFill" />
              <text v-else>{{ mentor.avatar }}</text>
            </view>
            <view class="mentor-detail-person-copy">
              <view class="mentor-detail-name-row">
                <text>{{ mentor.maskedName }}</text>
                <text v-if="mentor.verified" class="mentor-detail-verified">✓ 平台认证</text>
              </view>
              <view class="mentor-detail-status" :class="{ online: mentor.onlineStatus === 'online' }">
                <view></view>
                <text>{{ mentor.availabilityLabel }}</text>
              </view>
            </view>
          </view>

          <view class="mentor-detail-school">{{ mentor.school }}</view>
          <view class="mentor-detail-major">{{ mentor.major }} · {{ mentor.admissionYear }}级</view>
          <view class="mentor-detail-facts">
            <view><text>初试成绩</text><strong>{{ mentor.score }} 分</strong></view>
            <view><text>考试类别</text><strong>{{ mentor.examType }}</strong></view>
            <view><text>用户评分</text><strong class="rating">{{ mentor.ratingCount ? `★ ${Number(mentor.rating).toFixed(1)}` : '暂无评分' }}</strong></view>
            <view><text>已咨询</text><strong>{{ mentor.consultCount }} 人</strong></view>
          </view>
        </view>

        <view class="mentor-detail-section">
          <view class="mentor-detail-section-title">个人简介</view>
          <view class="mentor-detail-copy">{{ mentor.bio }}</view>
        </view>

        <view class="mentor-detail-section">
          <view class="mentor-detail-section-title">擅长咨询</view>
          <view class="mentor-detail-skills">
            <text v-for="skill in mentor.skills" :key="skill">{{ detailSkillLabel(skill) }}</text>
          </view>
        </view>

        <view class="mentor-detail-section">
          <view class="mentor-detail-section-title">上岸经历</view>
          <view class="mentor-detail-copy">{{ mentor.story }}</view>
        </view>

        <view class="mentor-detail-section mentor-detail-review-section">
          <view class="mentor-detail-section-heading">
            <view class="mentor-detail-section-title">用户评价</view>
            <text>共 {{ mentor.reviews?.length || 0 }} 条公开评价</text>
          </view>
          <view v-for="review in mentor.reviews" :key="review.id" class="mentor-review-card">
            <view class="mentor-review-head">
              <text>{{ review.author }}</text>
              <text class="mentor-review-rating">★ {{ Number(review.rating).toFixed(1) }}</text>
              <text>{{ review.date }}</text>
            </view>
            <view class="mentor-review-copy">{{ review.content }}</view>
          </view>
          <view v-if="!mentor.reviews?.length" class="mentor-review-empty">暂无公开评价</view>
        </view>
      </view>

      <view v-else-if="detailLoading" class="mentor-detail-missing">
        <view>正在加载前辈资料…</view>
      </view>
      <view v-else class="mentor-detail-missing">
        <view>该前辈信息暂时不可用</view>
        <button @tap="goHome">返回前辈咨询</button>
      </view>
      <view class="mentor-detail-bottom-space"></view>
    </scroll-view>

    <view v-if="mentor" class="mentor-detail-action-bar" :class="{ 'mentor-detail-action-bar-self': isCurrentMentorProfile }">
      <button class="mentor-detail-favorite" :class="{ active: isFavorite }" @tap="toggleFavorite">
        <text>{{ isFavorite ? '♥' : '♡' }}</text>
        <view>{{ isFavorite ? '已收藏' : '收藏' }}</view>
      </button>
      <view class="mentor-detail-price">
        <strong>{{ mentor.priceLabel }} / 次</strong>
        <text>{{ mentor.consultationWindowMinutes || 60 }}分钟咨询窗口</text>
      </view>
      <button v-if="canShowConsultationAction" class="mentor-detail-primary" @tap="startConsultation">{{ mentor.actionLabel }}</button>
      <view v-else-if="!currentMentorProfileResolved" class="mentor-detail-primary-placeholder" aria-hidden="true"></view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  fetchMentorProfile,
  fetchMyMentorProfile,
  fetchMyMentorFavorites,
  toggleMentorFavoriteRequest
} from '../../api/mentorConsultation'
import {
  cacheMentors,
  getMentorById,
  getMentorFavoriteIds,
  normalizeMentorDetailResponse,
  setMentorFavoriteIds
} from '../../data/mentorConsultation'
import { isLoggedIn } from '../../utils/auth'

const mentor = ref(null)
const favoriteIds = ref([])
const detailLoading = ref(false)
const currentMentorProfileId = ref('')
const currentMentorProfileResolved = ref(!isLoggedIn())
let currentMentorProfileRequest = null

const isFavorite = computed(() => mentor.value && favoriteIds.value.includes(mentor.value.id))
const isCurrentMentorProfile = computed(() => (
  Boolean(currentMentorProfileId.value)
  && String(mentor.value?.id || '') === currentMentorProfileId.value
))
const canShowConsultationAction = computed(() => (
  currentMentorProfileResolved.value && !isCurrentMentorProfile.value
))

onLoad((options) => {
  const viewerMentorId = String(options?.viewerMentorId || '').trim()
  if (viewerMentorId) {
    // 列表页已确认过本人档案时，详情页直接复用结果，避免先按普通用户闪现操作按钮。
    currentMentorProfileId.value = viewerMentorId
    currentMentorProfileResolved.value = true
  }
  favoriteIds.value = getMentorFavoriteIds()
  void loadFavoriteIds()
  void loadCurrentMentorProfileId({ preserveResolved: Boolean(viewerMentorId) })
  void loadMentorDetail(options?.id)
})

onShow(() => {
  favoriteIds.value = getMentorFavoriteIds()
  void loadFavoriteIds({ silent: true })
  void loadCurrentMentorProfileId({ preserveResolved: true })
})

function detailSkillLabel(skill) {
  return skill === '初试备考' ? '初试规划' : skill
}

async function loadMentorDetail(mentorId) {
  const id = String(mentorId || '')
  if (!id) return

  mentor.value = getMentorById(id)
  detailLoading.value = true
  try {
    const payload = await fetchMentorProfile(id)
    const profile = normalizeMentorDetailResponse(payload)
    if (!profile) throw new Error('前辈详情数据不完整')
    mentor.value = profile
    cacheMentors([profile])
  } catch (error) {
    if (error?.statusCode === 404) {
      mentor.value = null
    } else if (!mentor.value) {
      mentor.value = getMentorById(id)
    }
  } finally {
    detailLoading.value = false
  }
}

async function loadFavoriteIds({ silent = false } = {}) {
  if (!isLoggedIn()) return
  try {
    const payload = await fetchMyMentorFavorites()
    favoriteIds.value = setMentorFavoriteIds(
      Array.isArray(payload?.items)
        ? payload.items.map((item) => item?.mentor_id || item?.mentorId).filter(Boolean)
        : []
    )
  } catch (error) {
    if (!silent) uni.showToast({ title: error?.detail || '收藏状态加载失败', icon: 'none' })
  }
}

function loadCurrentMentorProfileId({ preserveResolved = false } = {}) {
  if (!isLoggedIn()) {
    currentMentorProfileId.value = ''
    currentMentorProfileResolved.value = true
    return Promise.resolve('')
  }
  if (currentMentorProfileRequest) return currentMentorProfileRequest
  if (!preserveResolved) currentMentorProfileResolved.value = false

  currentMentorProfileRequest = fetchMyMentorProfile()
    .then((payload) => {
      currentMentorProfileId.value = String(payload?.mentor?.id || '').trim()
      currentMentorProfileResolved.value = true
      return currentMentorProfileId.value
    })
    .catch((error) => {
      // 404 明确表示当前用户不是已认证前辈；其他网络异常保留中性占位，避免误展示咨询按钮。
      if (Number(error?.statusCode) === 404) {
        currentMentorProfileId.value = ''
        currentMentorProfileResolved.value = true
      } else if (currentMentorProfileId.value) {
        currentMentorProfileResolved.value = true
      }
      return ''
    })
    .finally(() => {
      currentMentorProfileRequest = null
    })

  return currentMentorProfileRequest
}

async function toggleFavorite() {
  if (!mentor.value) return
  if (!isLoggedIn()) {
    uni.showToast({ title: '请先登录后再收藏前辈', icon: 'none' })
    return
  }
  try {
    const result = await toggleMentorFavoriteRequest(mentor.value.id)
    const isFavorited = result?.is_favorited ?? result?.isFavorited
    const nextFavoriteIds = isFavorited
      ? [...favoriteIds.value, mentor.value.id]
      : favoriteIds.value.filter((id) => id !== mentor.value.id)
    favoriteIds.value = setMentorFavoriteIds(nextFavoriteIds)
  } catch (error) {
    uni.showToast({ title: error?.detail || '收藏操作失败，请稍后重试', icon: 'none' })
  }
}

function startConsultation() {
  if (!mentor.value) return
  if (isCurrentMentorProfile.value) return
  if (mentor.value.onlineStatus !== 'online' && mentor.value.acceptsBooking === false) {
    uni.showToast({ title: '该前辈暂未开放预约', icon: 'none' })
    return
  }
  const mentorId = encodeURIComponent(mentor.value.id)
  const url = mentor.value.onlineStatus === 'online'
    ? `/pages/circle/mentor-consult-form?mentorId=${mentorId}&mode=instant`
    : `/pages/circle/mentor-booking?mentorId=${mentorId}`
  uni.navigateTo({ url })
}

function goBack() {
  uni.navigateBack({
    fail: goHome
  })
}

function goHome() {
  uni.reLaunch({ url: '/pages/home/index?tab=circle&section=community&communityTab=mentor' })
}
</script>

<style scoped>
.mentor-detail-page {
  height: 100vh;
  /* Safari 的 100vh 会延伸到展开的底部地址栏下方；动态视口让固定操作栏始终停在可视区域上沿。 */
  height: 100dvh;
  overflow: hidden;
  background: #f4f8ff;
  display: flex;
  flex-direction: column;
}

.mentor-detail-scroll {
  min-height: 0;
  flex: 1;
}

.mentor-detail-content {
  padding: 26rpx 24rpx 0;
}

.mentor-detail-hero,
.mentor-detail-section {
  border: 2rpx solid rgba(215, 229, 255, 0.92);
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 14rpx 36rpx rgba(52, 120, 246, 0.07);
}

.mentor-detail-hero {
  padding: 30rpx;
}

.mentor-detail-person-row,
.mentor-detail-name-row,
.mentor-detail-status,
.mentor-detail-section-heading,
.mentor-review-head {
  display: flex;
  align-items: center;
}

.mentor-detail-person-row {
  gap: 18rpx;
}

.mentor-detail-avatar {
  width: 96rpx;
  height: 96rpx;
  border: 3rpx solid #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  font-size: 36rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.mentor-detail-avatar image {
  width: 100%;
  height: 100%;
}

.mentor-detail-avatar.tone-blue { background: #e6efff; color: #3478f6; }
.mentor-detail-avatar.tone-mint { background: #e2f4ef; color: #198777; }
.mentor-detail-avatar.tone-violet { background: #eeeafe; color: #7162bd; }
.mentor-detail-avatar.tone-warm { background: #f9eee1; color: #b66c32; }

.mentor-detail-person-copy { min-width: 0; flex: 1; }

.mentor-detail-name-row { gap: 10rpx; }

.mentor-detail-name-row > text:first-child {
  color: #172033;
  font-size: 34rpx;
  line-height: 1.2;
  font-weight: 900;
}

.mentor-detail-verified {
  padding: 6rpx 11rpx;
  border-radius: 999rpx;
  background: #edf4ff;
  color: #3478f6;
  font-size: 19rpx;
  line-height: 1.2;
  font-weight: 800;
}

.mentor-detail-status {
  gap: 8rpx;
  margin-top: 10rpx;
  color: #718197;
  font-size: 21rpx;
  font-weight: 750;
}

.mentor-detail-status view {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: #abb7c7;
}

.mentor-detail-status.online { color: #238a57; }
.mentor-detail-status.online view { background: #2caf68; box-shadow: 0 0 0 5rpx rgba(44, 175, 104, 0.12); }

.mentor-detail-school {
  margin-top: 28rpx;
  color: #172033;
  font-size: 32rpx;
  line-height: 1.3;
  font-weight: 900;
}

.mentor-detail-major {
  margin-top: 8rpx;
  color: #687a93;
  font-size: 23rpx;
  line-height: 1.4;
  font-weight: 700;
}

.mentor-detail-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 26rpx;
}

.mentor-detail-facts view {
  min-width: 0;
  padding: 16rpx;
  border-radius: 18rpx;
  background: #f7faff;
}

.mentor-detail-facts text,
.mentor-detail-facts strong {
  display: block;
}

.mentor-detail-facts text {
  color: #8290a4;
  font-size: 19rpx;
  line-height: 1.2;
  font-weight: 700;
}

.mentor-detail-facts strong {
  margin-top: 7rpx;
  color: #2d3c56;
  font-size: 25rpx;
  line-height: 1.2;
  font-weight: 900;
}

.mentor-detail-facts .rating { color: #d78a22; }

.mentor-detail-section {
  margin-top: 18rpx;
  padding: 28rpx;
}

.mentor-detail-section-title {
  color: #263650;
  font-size: 27rpx;
  line-height: 1.25;
  font-weight: 900;
}

.mentor-detail-copy {
  margin-top: 16rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.7;
  font-weight: 600;
}

.mentor-detail-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 18rpx;
}

.mentor-detail-skills text {
  padding: 10rpx 14rpx;
  border-radius: 14rpx;
  background: #edf4ff;
  color: #4c70a9;
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 800;
}

.mentor-detail-section-heading { justify-content: space-between; gap: 16rpx; }
.mentor-detail-section-heading > text { color: #92a0b3; font-size: 19rpx; font-weight: 650; }

.mentor-review-card {
  padding-top: 20rpx;
}

.mentor-review-card + .mentor-review-card {
  margin-top: 20rpx;
  border-top: 2rpx solid #eef2f8;
}

.mentor-review-head { gap: 12rpx; color: #7a899e; font-size: 20rpx; line-height: 1.2; font-weight: 700; }
.mentor-review-head > text:first-child { color: #3b4d66; font-weight: 850; }
.mentor-review-rating { color: #d78a22; }

.mentor-review-copy { margin-top: 12rpx; color: #5e6d82; font-size: 23rpx; line-height: 1.6; font-weight: 600; }
.mentor-review-empty { padding: 34rpx 0 12rpx; color: #92a0b3; text-align: center; font-size: 21rpx; line-height: 1.4; font-weight: 650; }

.mentor-detail-missing { padding: 130rpx 48rpx; color: #718197; text-align: center; font-size: 26rpx; font-weight: 750; }
.mentor-detail-missing button { margin-top: 28rpx; border: 0; border-radius: 18rpx; background: #3478f6; color: #fff; font-size: 23rpx; font-weight: 800; }
.mentor-detail-missing button::after { border: 0; }
.mentor-detail-bottom-space { height: calc(170rpx + env(safe-area-inset-bottom)); }

.mentor-detail-action-bar {
  padding: 18rpx 24rpx calc(24rpx + env(safe-area-inset-bottom));
  border-top: 2rpx solid rgba(215, 229, 255, 0.92);
  background: rgba(255, 255, 255, 0.96);
  display: grid;
  grid-template-columns: 78rpx minmax(0, 1fr) 196rpx;
  align-items: center;
  gap: 16rpx;
  box-shadow: 0 -10rpx 30rpx rgba(52, 120, 246, 0.06);
}
.mentor-detail-action-bar-self { grid-template-columns: 78rpx minmax(0, 1fr); }

.mentor-detail-favorite {
  width: 72rpx;
  height: 72rpx;
  min-width: 72rpx;
  min-height: 72rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 18rpx;
  background: #f0f5ff;
  color: #6f86a9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.mentor-detail-favorite::after,
.mentor-detail-primary::after { border: 0; }
.mentor-detail-favorite.active { color: #3478f6; background: #eaf2ff; }
.mentor-detail-favorite text { font-size: 28rpx; line-height: 0.95; }
.mentor-detail-favorite view { margin-top: 4rpx; font-size: 17rpx; line-height: 1.1; font-weight: 750; }

.mentor-detail-price { min-width: 0; }
.mentor-detail-price strong { display: block; color: #202d42; font-size: 27rpx; line-height: 1.2; font-weight: 900; }
.mentor-detail-price text { display: block; margin-top: 5rpx; color: #8a98aa; font-size: 18rpx; line-height: 1.2; font-weight: 650; }

.mentor-detail-primary {
  box-sizing: border-box;
  width: 100%;
  height: 74rpx;
  min-height: 74rpx;
  margin: 0;
  padding: 0 14rpx;
  border: 0;
  border-radius: 20rpx;
  background: #3478f6;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 24rpx;
  line-height: 1;
  font-weight: 900;
  white-space: nowrap;
  box-shadow: 0 10rpx 22rpx rgba(52, 120, 246, 0.2);
}

.mentor-detail-primary-placeholder {
  position: relative;
  width: 100%;
  height: 74rpx;
  min-height: 74rpx;
  overflow: hidden;
  border-radius: 20rpx;
  background: #edf3fb;
}

.mentor-detail-primary-placeholder::after {
  position: absolute;
  inset: 0;
  content: '';
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.66) 50%, transparent 100%);
  transform: translateX(-100%);
  animation: mentor-detail-action-placeholder 1.35s ease-in-out infinite;
}

@keyframes mentor-detail-action-placeholder {
  to { transform: translateX(100%); }
}

@media (max-width: 350px) {
  .mentor-detail-action-bar { grid-template-columns: 66rpx minmax(0, 1fr) 170rpx; gap: 12rpx; padding-right: 18rpx; padding-left: 18rpx; }
  .mentor-detail-action-bar-self { grid-template-columns: 66rpx minmax(0, 1fr); }
  .mentor-detail-primary { font-size: 22rpx; }
}
</style>
