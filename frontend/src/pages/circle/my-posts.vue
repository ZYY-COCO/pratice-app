<template>
  <view class="page my-posts-page" :class="{ 'has-delete-bar': selectionMode }" :style="pageInlineStyle">
    <AppPageHeader title="我的帖子" @back="goBack">
      <template #right>
        <button
          class="my-posts-selection-toggle"
          :class="{ active: selectionMode }"
          hover-class="none"
          @tap="toggleSelectionMode"
        >{{ selectionMode ? '取消' : '多选' }}</button>
      </template>
    </AppPageHeader>

    <view class="my-posts-tabs" role="tablist" aria-label="帖子类型">
      <button
        v-for="item in postTypeOptions"
        :key="item.value"
        class="my-posts-tab"
        :class="{ active: activePostType === item.value }"
        hover-class="none"
        :aria-selected="activePostType === item.value"
        @tap="selectPostType(item.value)"
      >
        <text>{{ item.label }}</text>
        <text v-if="getPostTypeUnreadCount(item.value)" class="my-posts-tab-unread">
          {{ formatUnreadBadge(getPostTypeUnreadCount(item.value)) }}
        </text>
      </button>
    </view>

    <AppPageLoadingState v-if="entryLoading || loading" message="正在整理我的帖子..." />
    <view v-else-if="error" class="my-posts-state-card my-posts-state-card--warning">
      <text>{{ error }}</text>
      <button hover-class="none" @tap="loadMyPosts">重新加载</button>
    </view>
    <AppEmptyState v-else-if="posts.length === 0" label="暂无帖子" />

    <scroll-view v-else scroll-y class="my-posts-list-scroll" @scrolltolower="loadMoreMyPosts">
      <view class="my-posts-list">
      <view
        v-for="post in posts"
        :key="post.id"
        class="my-post-selectable"
        :class="{
          'is-selecting': selectionMode,
          'is-swiping': swipingPostId === post.id,
          'is-delete-preview': isPostDeletePreview(post.id),
          'is-delete-armed': isPostDeleteArmed(post.id),
          'is-removing': isPostRemoving(post.id),
          selected: isPostSelected(post.id)
        }"
        @touchstart="beginPostSwipe($event, post)"
        @touchmove="movePostSwipe($event, post)"
        @touchend="finishPostSwipe($event, post)"
        @touchcancel="cancelPostSwipe(post)"
      >
        <view
          v-if="isPostDeletePreview(post.id)"
          class="my-post-delete-preview"
          :style="postDeletePreviewStyle(post.id)"
        >
          <text>{{ isPostDeleteArmed(post.id) ? '松开删除' : '继续右滑' }}</text>
        </view>

        <button
          class="my-post-selector"
          hover-class="none"
          :aria-label="isPostSelected(post.id) ? '取消选择帖子' : '选择帖子'"
          @tap.stop="togglePostSelection(post.id)"
        ><text v-if="isPostSelected(post.id)">✓</text></button>

        <view
          class="my-post-card"
          :class="{ 'has-unread-interaction': isPostUnread(post) }"
          :style="postSwipeStyle(post.id)"
          @tap="handlePostTap(post)"
        >
          <view class="my-post-card-header">
            <view class="my-post-avatar" :class="`tone-${post.tone}`">
              <image v-if="post.avatarUrl" :src="post.avatarUrl" mode="aspectFill" />
              <text v-else>{{ post.avatar }}</text>
            </view>
            <view class="my-post-author">
              <view class="my-post-author-name">{{ post.author }}</view>
              <view class="my-post-author-meta">{{ post.postTypeLabel }} · {{ post.publishTime }}</view>
            </view>
            <view v-if="isPostUnread(post)" class="my-post-unread-badge">新互动</view>
            <view class="my-post-category-list">
              <view
                v-for="tag in post.tags"
                :key="`${post.id}-${tag}`"
                class="my-post-category"
              >{{ tag }}</view>
            </view>
          </view>

          <view
            class="my-post-review-status"
            :class="postDisplayStatus(post)"
          >{{ postDisplayStatusText(post) }}</view>

          <view class="my-post-card-body" :class="{ 'has-cover': post.coverUrl }">
            <view class="my-post-copy">
              <view class="my-post-card-title">{{ post.title || '研圈帖子' }}</view>
              <view class="my-post-content">{{ post.content }}</view>
            </view>
            <image v-if="post.coverUrl" class="my-post-cover" :src="post.coverUrl" mode="aspectFill" />
          </view>

          <view v-if="post.reviewStatus === 'rejected' && post.reviewNote" class="my-post-review-note">
            <strong>{{ reviewReasonText(post.reviewReasonCode) }}</strong>
            <text>{{ post.reviewNote }}</text>
          </view>

          <view class="my-post-card-footer">
            <view class="my-post-stats">
              <view><image src="/static/ui-icons/png/neutral/circle-like.png" mode="aspectFit" /><text>{{ post.stats.likes }}</text></view>
              <view><image src="/static/ui-icons/png/neutral/circle-comment.png" mode="aspectFit" /><text>{{ post.stats.comments }}</text></view>
              <view><image src="/static/ui-icons/png/neutral/circle-view.png" mode="aspectFit" /><text>{{ post.stats.views }}</text></view>
            </view>
            <view
              v-if="!selectionMode && (post.reviewStatus === 'rejected' || postDisplayStatus(post) === 'approved')"
              class="my-post-card-actions"
            >
              <button
                v-if="post.postType === 'experience' && post.reviewStatus === 'rejected'"
                class="my-post-edit-button"
                hover-class="none"
                @tap.stop="editRejectedPost(post)"
              >修改并重提</button>
              <text v-if="postDisplayStatus(post) === 'approved'" class="my-post-detail-link">查看详情 ›</text>
            </view>
          </view>
        </view>
      </view>
      </view>
      <view class="my-posts-load-state" @tap="loadMoreMyPosts">
        {{ loadingMore ? '正在加载更多…' : hasMore ? '继续下滑加载更多' : '已加载全部帖子' }}
      </view>
    </scroll-view>

    <view
      v-if="selectionMode"
      :key="`my-posts-delete-bar-${selectionSessionKey}`"
      class="my-posts-delete-bar"
    >
      <button class="my-posts-select-all" hover-class="none" @tap="toggleSelectAllLoadedPosts">
        {{ allLoadedPostsSelected ? '取消全选' : '全选' }}
      </button>
      <text class="my-posts-delete-summary">已选 {{ selectedPostIds.length }} 条</text>
      <button
        class="my-posts-delete-action"
        :disabled="deletingPosts || !selectedPostIds.length"
        hover-class="none"
        @tap="confirmBatchDelete"
      >删除</button>
    </view>

    <view v-if="reviewDetailVisible" class="review-detail-backdrop" @tap="closeReviewDetail">
      <view class="review-detail-dialog" @tap.stop>
        <view class="review-detail-header">
          <view>
            <text>经验贴审核记录</text>
            <strong>{{ reviewDetail?.post?.title || '经验贴' }}</strong>
          </view>
          <button aria-label="关闭审核记录" hover-class="none" @tap="closeReviewDetail">
            <CloseIcon />
          </button>
        </view>

        <scroll-view scroll-y class="review-detail-scroll">
          <view v-if="reviewDetailLoading" class="review-detail-state">正在读取审核记录…</view>
          <view v-else-if="reviewDetailError" class="review-detail-state error">
            <text>{{ reviewDetailError }}</text>
            <button hover-class="none" @tap="loadReviewDetail(reviewDetailPostId)">重新加载</button>
          </view>
          <view v-else-if="reviewDetail?.post" class="review-detail-content">
            <view class="review-current-status" :class="reviewDetail.post.review_status">
              <text>当前状态</text>
              <strong>{{ reviewStatusText(reviewDetail.post.review_status) }}</strong>
              <small>{{ reviewCurrentStatusHint(reviewDetail.post) }}</small>
            </view>

            <view v-if="reviewDetail.post.review_status === 'rejected'" class="review-official-note">
              <text>官方理由 · {{ reviewReasonText(reviewDetail.post.review_reason_code) }}</text>
              <strong>{{ reviewDetail.post.review_note }}</strong>
            </view>

            <view class="review-history-heading">历次审核记录</view>
            <view v-if="!reviewDetail.review_history?.length" class="review-history-empty">暂无审核记录</view>
            <view v-else class="review-history-list">
              <view v-for="item in reviewDetail.review_history" :key="item.id" class="review-history-item">
                <view class="review-history-marker" :class="item.action"></view>
                <view class="review-history-copy">
                  <view>
                    <strong>{{ reviewActionText(item.action) }}</strong>
                    <text>第 {{ item.submission_version }} 次提交</text>
                  </view>
                  <small>{{ formatReviewDate(item.created_at) }}</small>
                  <text v-if="item.reason_code || item.review_note" class="review-history-note">
                    {{ item.reason_code ? `${reviewReasonText(item.reason_code)}：` : '' }}{{ item.review_note || '' }}
                  </text>
                </view>
              </view>
            </view>
          </view>
        </scroll-view>

        <view v-if="reviewDetail?.post?.review_status === 'rejected'" class="review-detail-actions">
          <button hover-class="none" @tap="editRejectedPost(reviewDetail.post)">修改并重新提交</button>
        </view>
      </view>
    </view>

    <!-- #ifdef H5 -->
    <IcpFooter />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import IcpFooter from '../../components/IcpFooter.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import CloseIcon from '../../components/CloseIcon.vue'
import {
  deleteMyCommunityPosts,
  fetchMyCommunityPost,
  fetchMyCommunityPosts
} from '../../api/community'
import {
  fetchUserNotificationUnreadSummary,
  markUserNotificationReadTarget
} from '../../api/notifications'
import { isLoggedIn } from '../../utils/auth'
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const postTypeOptions = [
  { value: 'all', label: '全部' },
  { value: 'chat', label: '研友聊' },
  { value: 'experience', label: '经验贴' }
]

const POST_SWIPE_EDGE_GUARD_PX = 30
const POST_SWIPE_DIRECTION_LOCK_PX = 10
const POST_SWIPE_TRIGGER_PX = 52
const POST_SWIPE_MAX_OFFSET_PX = 68
const POST_DELETE_SWIPE_TRIGGER_PX = 84
const POST_DELETE_SWIPE_MAX_OFFSET_PX = 108
const POST_SWIPE_HORIZONTAL_RATIO = 1.2
const POST_REMOVE_ANIMATION_MS = 560
const MY_POSTS_REFRESH_REQUIRED_KEY = 'circle-my-posts-refresh-required'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const mpLayoutStyle = ref(buildMpPageSafeStyle())
const pageInlineStyle = computed(() => [themeInlineStyle, mpLayoutStyle.value].filter(Boolean).join(';'))
const activePostType = ref('all')
const posts = ref([])
const loading = ref(false)
const entryLoading = ref(true)
const error = ref('')
const selectionMode = ref(false)
const selectedPostIds = ref([])
const swipingPostId = ref('')
const swipeOffsetPx = ref(0)
const swipeIntent = ref('')
const swipeDeleteProgress = ref(0)
const selectionSessionKey = ref(0)
const removingPostIds = ref([])
const deletingPosts = ref(false)
const loadingMore = ref(false)
const nextCursor = ref('')
const hasMore = ref(false)
const unreadPostTargets = ref({ chat: {}, experience: {} })
const reviewDetailVisible = ref(false)
const reviewDetailLoading = ref(false)
const reviewDetailError = ref('')
const reviewDetail = ref(null)
const reviewDetailPostId = ref('')
const requestedReviewPostId = ref('')
const allLoadedPostsSelected = computed(() => (
  posts.value.length > 0
  && posts.value.every((post) => selectedPostIds.value.includes(post.id))
))
let latestUnreadLoadToken = 0
let postSwipeGesture = null
let suppressedPostTapId = ''
let suppressPostTapUntil = 0
let preserveListOnNextShow = false
onLoad((options) => {
  const requestedType = String(options?.type || '')
  if (postTypeOptions.some((item) => item.value === requestedType)) {
    activePostType.value = requestedType
  }
  requestedReviewPostId.value = String(options?.reviewPostId || '').trim()
})

onShow(() => {
  mpLayoutStyle.value = buildMpPageSafeStyle()
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  const refreshRequired = consumeMyPostsRefreshRequirement()
  const shouldPreserveList = preserveListOnNextShow && posts.value.length > 0 && !refreshRequired
  preserveListOnNextShow = false
  void loadUnreadPostTargets()
  if (shouldPreserveList) {
    entryLoading.value = false
    return
  }
  void loadMyPosts().then(() => {
    const postId = requestedReviewPostId.value
    if (!postId) return
    requestedReviewPostId.value = ''
    void openReviewRecord({ id: postId, postType: 'experience' })
  })
})

function consumeMyPostsRefreshRequirement() {
  try {
    const required = Boolean(uni.getStorageSync(MY_POSTS_REFRESH_REQUIRED_KEY))
    if (required) uni.removeStorageSync(MY_POSTS_REFRESH_REQUIRED_KEY)
    return required
  } catch (error) {
    return false
  }
}

function normalizeUnreadTargets(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {}
  return Object.fromEntries(
    Object.entries(value)
      .map(([id, count]) => [String(id || '').trim(), Math.max(0, Number(count) || 0)])
      .filter(([id, count]) => id && count > 0)
  )
}

async function loadUnreadPostTargets() {
  const loadToken = ++latestUnreadLoadToken
  try {
    const summary = await fetchUserNotificationUnreadSummary()
    if (loadToken !== latestUnreadLoadToken) return
    const targets = summary?.community_post_targets || {}
    unreadPostTargets.value = {
      chat: normalizeUnreadTargets(targets.chat),
      experience: normalizeUnreadTargets(targets.experience)
    }
  } catch (error) {
    // 未读提示同步失败不应妨碍用户查看自己发布的内容。
  }
}

function getPostTypeUnreadCount(postType) {
  const chatCount = Object.values(unreadPostTargets.value.chat || {}).reduce((sum, count) => sum + Number(count || 0), 0)
  const experienceCount = Object.values(unreadPostTargets.value.experience || {}).reduce((sum, count) => sum + Number(count || 0), 0)
  if (postType === 'chat') return chatCount
  if (postType === 'experience') return experienceCount
  return chatCount + experienceCount
}

function formatUnreadBadge(count) {
  return Number(count || 0) > 99 ? '99+' : String(Number(count || 0))
}

function getPostUnreadCount(post = {}) {
  const postType = post.postType === 'experience' ? 'experience' : 'chat'
  return Number(unreadPostTargets.value?.[postType]?.[String(post.id || '')] || 0)
}

function isPostUnread(post) {
  return getPostUnreadCount(post) > 0
}

function markPostNotificationsRead(post = {}) {
  const postId = String(post.id || '').trim()
  const postType = post.postType === 'experience' ? 'experience' : 'chat'
  if (!postId) return
  // 让已经发出的旧摘要请求失效，避免它在已读写入完成前把红点写回页面。
  latestUnreadLoadToken += 1
  const nextTargets = { ...(unreadPostTargets.value?.[postType] || {}) }
  delete nextTargets[postId]
  unreadPostTargets.value = { ...unreadPostTargets.value, [postType]: nextTargets }
  // 先即时移除当前卡片上的红点，再由统一的已读请求协调器完成服务端写入；
  // 写入完成后回读权威摘要，失败时也会把真实未读状态恢复到页面。
  void markUserNotificationReadTarget('community_post', postId)
    .then(() => loadUnreadPostTargets())
    .catch(() => loadUnreadPostTargets())
}

async function loadMyPosts() {
  if (loading.value || loadingMore.value) return
  loading.value = true
  nextCursor.value = ''
  hasMore.value = false
  error.value = ''
  try {
    const response = await fetchMyCommunityPosts({
      post_type: activePostType.value,
      limit: 30
    })
    posts.value = Array.isArray(response?.items)
      ? response.items.map(normalizeMyPost).filter((item) => item.id)
      : []
    nextCursor.value = String(response?.next_cursor || '')
    hasMore.value = response?.has_more === true
  } catch (requestError) {
    error.value = requestError?.detail || '我的帖子读取失败，请稍后重试'
  } finally {
    loading.value = false
    entryLoading.value = false
  }
}

async function loadMoreMyPosts() {
  if (loading.value || loadingMore.value || !hasMore.value || !nextCursor.value) return
  loadingMore.value = true
  try {
    const response = await fetchMyCommunityPosts({
      post_type: activePostType.value,
      limit: 30,
      cursor: nextCursor.value
    })
    const nextItems = Array.isArray(response?.items) ? response.items.map(normalizeMyPost).filter((item) => item.id) : []
    posts.value = [...posts.value, ...nextItems.filter((item) => !posts.value.some((existing) => existing.id === item.id))]
    nextCursor.value = String(response?.next_cursor || '')
    hasMore.value = response?.has_more === true
  } catch (requestError) {
    uni.showToast({ title: requestError?.detail || '更多帖子读取失败', icon: 'none' })
  } finally {
    loadingMore.value = false
  }
}

function normalizeMyPost(post = {}) {
  const media = Array.isArray(post.media) ? post.media.slice(0, 9) : []
  const cover = media.find((item) => String(item?.imageUrl || item?.image_url || '').trim())
  const postType = post.postType || post.post_type || 'chat'
  const category = String(post.category || '备考日常')
  const experienceStages = Array.isArray(post.experienceStages || post.experience_stages)
    ? [...new Set((post.experienceStages || post.experience_stages).map((stage) => String(stage || '').trim()).filter(Boolean))]
    : []
  return {
    id: String(post.id || ''),
    postType,
    postTypeLabel: postType === 'experience' ? '经验贴' : '研友聊',
    category,
    tags: postType === 'experience' ? [category, ...experienceStages] : [category],
    author: String(post.author || '研友'),
    avatar: String(post.avatar || '研'),
    avatarUrl: String(post.avatarUrl || post.avatar_url || '').trim(),
    tone: String(post.tone || 'blue'),
    title: String(post.title || ''),
    content: String(post.content || post.summary || ''),
    publishTime: String(post.publishTime || post.publish_time || '刚刚'),
    media,
    coverUrl: String(cover?.imageUrl || cover?.image_url || '').trim(),
    isPublished: post.isPublished ?? post.is_published ?? true,
    reviewStatus: String(post.reviewStatus || post.review_status || 'approved'),
    reviewVersion: Number(post.reviewVersion ?? post.review_version ?? 0),
    reviewReasonCode: String(post.reviewReasonCode || post.review_reason_code || ''),
    reviewNote: String(post.reviewNote || post.review_note || ''),
    reviewedAt: post.reviewedAt || post.reviewed_at || null,
    submittedAt: post.submittedAt || post.submitted_at || null,
    experienceStages,
    stats: {
      likes: Number(post.stats?.likes ?? post.like_count ?? 0),
      comments: Number(post.stats?.comments ?? post.comment_count ?? 0),
      views: Number(post.stats?.views ?? post.view_count ?? 0)
    }
  }
}

function selectPostType(value) {
  if (!postTypeOptions.some((item) => item.value === value) || activePostType.value === value) return
  activePostType.value = value
  exitSelectionMode()
  void loadMyPosts()
}

function toggleSelectionMode() {
  if (loading.value || !posts.value.length) return
  if (selectionMode.value) {
    exitSelectionMode()
    return
  }
  resetPostSwipe()
  selectionSessionKey.value += 1
  selectionMode.value = true
}

function exitSelectionMode() {
  selectionMode.value = false
  selectedPostIds.value = []
  suppressedPostTapId = ''
  suppressPostTapUntil = 0
  resetPostSwipe()
}

function isPostSelected(postId) {
  return selectedPostIds.value.includes(postId)
}

function togglePostSelection(postId) {
  if (!selectionMode.value || !postId) return
  selectedPostIds.value = isPostSelected(postId)
    ? selectedPostIds.value.filter((id) => id !== postId)
    : [...selectedPostIds.value, postId]
}

function toggleSelectAllLoadedPosts() {
  if (!selectionMode.value || deletingPosts.value) return
  selectedPostIds.value = allLoadedPostsSelected.value
    ? []
    : posts.value.map((post) => post.id).filter(Boolean)
}

function postTouchPoint(event, preferChangedTouches = false) {
  const touchLists = preferChangedTouches
    ? [event?.changedTouches, event?.touches]
    : [event?.touches, event?.changedTouches]
  const touch = touchLists.find((items) => items?.length)?.[0]
  if (!touch) return null
  const x = Number(touch.clientX ?? touch.pageX ?? touch.x)
  const y = Number(touch.clientY ?? touch.pageY ?? touch.y)
  return Number.isFinite(x) && Number.isFinite(y) ? { x, y } : null
}

function beginPostSwipe(event, post) {
  const postId = String(post?.id || '')
  if (deletingPosts.value || !postId || event?.touches?.length > 1) return
  const point = postTouchPoint(event)
  if (!point || point.x <= POST_SWIPE_EDGE_GUARD_PX) return
  const intent = selectionMode.value && isPostSelected(postId) ? 'delete' : 'select'
  postSwipeGesture = {
    postId,
    intent,
    startX: point.x,
    startY: point.y,
    axis: '',
    deltaX: 0
  }
  swipeIntent.value = intent
  swipeDeleteProgress.value = 0
}

function movePostSwipe(event, post) {
  const postId = String(post?.id || '')
  if (!postSwipeGesture || postSwipeGesture.postId !== postId) return
  const point = postTouchPoint(event)
  if (!point) return
  const deltaX = point.x - postSwipeGesture.startX
  const deltaY = point.y - postSwipeGesture.startY
  const absX = Math.abs(deltaX)
  const absY = Math.abs(deltaY)

  if (!postSwipeGesture.axis) {
    if (Math.max(absX, absY) < POST_SWIPE_DIRECTION_LOCK_PX) return
    postSwipeGesture.axis = (
      deltaX > 0
      && absX >= absY * POST_SWIPE_HORIZONTAL_RATIO
    ) ? 'horizontal' : 'vertical'
  }
  if (postSwipeGesture.axis !== 'horizontal') return

  postSwipeGesture.deltaX = Math.max(0, deltaX)
  swipingPostId.value = postId
  const deleteIntent = postSwipeGesture.intent === 'delete'
  const maxOffset = deleteIntent ? POST_DELETE_SWIPE_MAX_OFFSET_PX : POST_SWIPE_MAX_OFFSET_PX
  swipeOffsetPx.value = Math.min(postSwipeGesture.deltaX, maxOffset)
  swipeDeleteProgress.value = deleteIntent
    ? Math.min(1, postSwipeGesture.deltaX / POST_DELETE_SWIPE_TRIGGER_PX)
    : 0
  if (typeof event?.preventDefault === 'function') event.preventDefault()
  if (typeof event?.stopPropagation === 'function') event.stopPropagation()
}

function finishPostSwipe(event, post) {
  const postId = String(post?.id || '')
  const gesture = postSwipeGesture
  if (!gesture || gesture.postId !== postId) return

  const point = postTouchPoint(event, true)
  const finalDeltaX = point ? Math.max(0, point.x - gesture.startX) : gesture.deltaX
  const finalDeltaY = point ? Math.abs(point.y - gesture.startY) : 0
  const horizontalSwipe = gesture.axis === 'horizontal'
    || (
      !gesture.axis
      && finalDeltaX >= POST_SWIPE_DIRECTION_LOCK_PX
      && finalDeltaX >= finalDeltaY * POST_SWIPE_HORIZONTAL_RATIO
    )
  const swipeDistance = Math.max(gesture.deltaX, finalDeltaX)
  const deleteIntent = gesture.intent === 'delete'
  const shouldSelect = !deleteIntent && horizontalSwipe && swipeDistance >= POST_SWIPE_TRIGGER_PX
  const shouldDelete = deleteIntent && horizontalSwipe && swipeDistance >= POST_DELETE_SWIPE_TRIGGER_PX

  if (horizontalSwipe && swipeDistance >= POST_SWIPE_DIRECTION_LOCK_PX) {
    suppressedPostTapId = postId
    suppressPostTapUntil = Date.now() + 600
  }

  if (shouldSelect) {
    if (!selectionMode.value) {
      selectionSessionKey.value += 1
    }
    selectionMode.value = true
    if (!selectedPostIds.value.includes(postId)) {
      selectedPostIds.value = [...selectedPostIds.value, postId]
    }
  }
  if (shouldDelete) {
    postSwipeGesture = null
    requestSwipeDelete(post, { fromSwipe: true })
    return
  }
  resetPostSwipe()
}

function cancelPostSwipe(post) {
  const postId = String(post?.id || '')
  if (!postSwipeGesture || postSwipeGesture.postId !== postId) return
  resetPostSwipe()
}

function resetPostSwipe() {
  postSwipeGesture = null
  swipingPostId.value = ''
  swipeOffsetPx.value = 0
  swipeIntent.value = ''
  swipeDeleteProgress.value = 0
}

function postSwipeStyle(postId) {
  if (swipingPostId.value !== String(postId || '') || swipeOffsetPx.value <= 0) return ''
  const styles = [`transform: translate3d(${swipeOffsetPx.value}px, 0, 0)`]
  if (swipeIntent.value === 'delete') {
    const progress = Math.max(0, Math.min(1, swipeDeleteProgress.value))
    styles.push(`--delete-progress: ${progress.toFixed(3)}`)
    styles.push(`border-color: rgba(230, 104, 95, ${(0.18 + progress * 0.34).toFixed(3)})`)
    styles.push(`box-shadow: 0 14rpx 38rpx rgba(222, 87, 78, ${(0.07 + progress * 0.13).toFixed(3)})`)
  }
  return `${styles.join('; ')};`
}

function isPostDeletePreview(postId) {
  return swipingPostId.value === String(postId || '') && swipeIntent.value === 'delete'
}

function isPostDeleteArmed(postId) {
  return isPostDeletePreview(postId) && swipeDeleteProgress.value >= 1
}

function isPostRemoving(postId) {
  return removingPostIds.value.includes(String(postId || ''))
}

function markPostsRemoving(postIds) {
  removingPostIds.value = [...new Set([
    ...removingPostIds.value,
    ...postIds.map((id) => String(id || '')).filter(Boolean)
  ])]
}

function clearPostsRemoving(postIds) {
  const clearedIds = new Set(postIds.map((id) => String(id || '')).filter(Boolean))
  removingPostIds.value = removingPostIds.value.filter((id) => !clearedIds.has(id))
}

function waitForPostRemovalAnimation() {
  return new Promise((resolve) => {
    setTimeout(resolve, POST_REMOVE_ANIMATION_MS)
  })
}

async function restorePostRemovalVisual(postIds) {
  clearPostsRemoving(postIds)
  await nextTick()
  if (postIds.includes(swipingPostId.value)) {
    resetPostSwipe()
  }
}

function postDeletePreviewStyle(postId) {
  if (!isPostDeletePreview(postId)) return ''
  const progress = Math.max(0, Math.min(1, swipeDeleteProgress.value))
  return `opacity: ${Math.max(0.12, progress).toFixed(3)};`
}

function handlePostTap(post) {
  if (suppressedPostTapId === post?.id && Date.now() < suppressPostTapUntil) {
    suppressedPostTapId = ''
    suppressPostTapUntil = 0
    return
  }
  if (selectionMode.value) {
    togglePostSelection(post?.id)
    return
  }
  openPost(post)
}

function isPublicPost(post = {}) {
  return post.isPublished === true && postDisplayStatus(post) === 'approved'
}

function showPublishedDeleteConfirmation(postIds, { singleSwipe = false } = {}) {
  const count = postIds.length
  const selectedSnapshot = [...selectedPostIds.value]
  uni.showModal({
    title: singleSwipe ? '删除这篇已发布帖子？' : `删除 ${count} 篇帖子？`,
    content: singleSwipe
      ? '删除后将同时从研圈撤下，且不会再出现在“我的帖子”中。'
      : '所选内容将从“我的帖子”中删除，其中已发布的帖子也会同步从研圈撤下。',
    confirmText: '删除',
    confirmColor: '#e06b61',
    success(result) {
      if (!result.confirm) {
        selectedPostIds.value = selectedSnapshot
        resetPostSwipe()
        return
      }
      void deleteSelectedPosts(postIds, { exitAfterSuccess: !singleSwipe })
    }
  })
}

function requestSwipeDelete(post, { fromSwipe = false } = {}) {
  const postId = String(post?.id || '')
  if (!postId || deletingPosts.value || !isPostSelected(postId)) {
    if (fromSwipe) resetPostSwipe()
    return
  }
  if (isPublicPost(post)) {
    resetPostSwipe()
    showPublishedDeleteConfirmation([postId], { singleSwipe: true })
    return
  }
  void deleteSelectedPosts([postId], { exitAfterSuccess: false })
}

function confirmBatchDelete() {
  const postIds = [...selectedPostIds.value]
  if (!postIds.length || deletingPosts.value) return
  const selectedIdSet = new Set(postIds)
  const includesPublicPost = posts.value.some((post) => selectedIdSet.has(post.id) && isPublicPost(post))
  if (includesPublicPost) {
    showPublishedDeleteConfirmation(postIds)
    return
  }
  void deleteSelectedPosts(postIds)
}

async function deleteSelectedPosts(postIds, { exitAfterSuccess = true } = {}) {
  const requestedIds = [...new Set(postIds.map((id) => String(id || '')).filter(Boolean))]
  if (!requestedIds.length || deletingPosts.value) return
  deletingPosts.value = true
  try {
    markPostsRemoving(requestedIds)
    await nextTick()
    const deleteRequest = Promise.resolve()
      .then(() => deleteMyCommunityPosts(requestedIds))
      .then(
        (response) => ({ response, error: null }),
        (requestError) => ({ response: null, error: requestError })
      )
    const [requestResult] = await Promise.all([
      deleteRequest,
      waitForPostRemovalAnimation()
    ])
    if (requestResult.error) throw requestResult.error
    const response = requestResult.response
    const deletedIds = Array.isArray(response?.deleted_post_ids)
      ? response.deleted_post_ids.map((id) => String(id || '')).filter(Boolean)
      : []
    if (!deletedIds.length) {
      await restorePostRemovalVisual(requestedIds)
      uni.showToast({ title: '帖子状态已变化，请刷新后重试', icon: 'none' })
      return
    }
    const deletedIdSet = new Set(deletedIds)
    posts.value = posts.value.filter((post) => !deletedIdSet.has(post.id))
    clearPostsRemoving(requestedIds)
    selectedPostIds.value = selectedPostIds.value.filter((id) => !deletedIdSet.has(id))
    const failedCount = requestedIds.filter((id) => !deletedIdSet.has(id)).length
    if (exitAfterSuccess && failedCount === 0) {
      exitSelectionMode()
    } else if (!selectedPostIds.value.length) {
      exitSelectionMode()
    } else {
      resetPostSwipe()
    }
    uni.showToast({
      title: failedCount > 0
        ? `已删除 ${deletedIds.length} 篇，${failedCount} 篇未删除`
        : `已删除 ${deletedIds.length} 篇帖子`,
      icon: failedCount > 0 ? 'none' : 'success'
    })
  } catch (requestError) {
    await restorePostRemovalVisual(requestedIds)
    uni.showToast({ title: requestError?.detail || '删除失败，请稍后重试', icon: 'none' })
  } finally {
    deletingPosts.value = false
  }
}

async function openReviewRecord(post) {
  const postId = String(post?.id || '').trim()
  if (!postId) return
  reviewDetailPostId.value = postId
  reviewDetailVisible.value = true
  await loadReviewDetail(postId)
}

async function loadReviewDetail(postId) {
  if (!postId || reviewDetailLoading.value) return
  reviewDetailLoading.value = true
  reviewDetailError.value = ''
  try {
    reviewDetail.value = await fetchMyCommunityPost(postId)
  } catch (requestError) {
    reviewDetail.value = null
    reviewDetailError.value = requestError?.detail || '审核记录读取失败，请稍后重试'
  } finally {
    reviewDetailLoading.value = false
  }
}

function closeReviewDetail() {
  if (reviewDetailLoading.value) return
  reviewDetailVisible.value = false
  reviewDetail.value = null
  reviewDetailError.value = ''
  reviewDetailPostId.value = ''
}

function editRejectedPost(post) {
  const postId = String(post?.id || '').trim()
  const reviewStatus = String(post?.reviewStatus || post?.review_status || '')
  if (!postId || reviewStatus !== 'rejected') return
  closeReviewDetail()
  uni.navigateTo({
    url: `/pages/circle/publish?type=experience&edit=${encodeURIComponent(postId)}`
  })
}

function reviewStatusText(value) {
  return {
    pending: '待审核',
    approved: '已通过',
    rejected: '已下架'
  }[value] || '已通过'
}

function postDisplayStatus(post = {}) {
  if (String(post.reviewStatus || '') === 'pending') return 'pending'
  if (String(post.reviewStatus || '') === 'rejected' || post.isPublished === false) return 'archived'
  return 'approved'
}

function postDisplayStatusText(post = {}) {
  return {
    pending: '待审核',
    approved: '已通过',
    archived: '已下架'
  }[postDisplayStatus(post)]
}

function reviewReasonText(value) {
  return {
    advertising_or_diversion: '广告营销或站外引流',
    false_or_misleading: '虚假、夸大或误导性信息',
    infringement: '侵权或未经授权转载',
    privacy: '泄露个人隐私',
    inappropriate: '不友善、低俗或违规内容',
    low_quality: '内容不完整或与备考经验无关',
    other: '其他原因'
  }[value] || '平台审核说明'
}

function reviewActionText(value) {
  return {
    submitted: '已提交审核',
    approved: '审核通过',
    rejected: '审核未通过'
  }[value] || '审核状态更新'
}

function reviewCurrentStatusHint(post = {}) {
  if (post.review_status === 'pending') return '工作人员正在审核，通过后将自动公开展示'
  if (post.review_status === 'rejected') return '可以根据官方理由修改内容后重新提交'
  return post.is_published ? '内容已在经验贴公开展示' : '内容已通过审核，当前处于下架状态'
}

function formatReviewDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '时间待同步'
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(date)
}

function openPost(post) {
  if (!post?.id) return
  markPostNotificationsRead(post)
  const communityTab = post.postType === 'experience' ? 'experience' : 'chat'
  preserveListOnNextShow = true
  uni.navigateTo({
    url: `/pages/home/index?tab=circle&section=community&communityTab=${communityTab}&postId=${encodeURIComponent(post.id)}&entry=my-posts&ownerPreview=1`,
    fail() {
      preserveListOnNextShow = false
      uni.showToast({ title: '帖子内容打开失败，请重试', icon: 'none' })
    }
  })
}

function goLogin() {
  uni.reLaunch({
    url: `/pages/login/index?redirect=${encodeURIComponent('/pages/circle/my-posts')}`
  })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=profile' })
    }
  })
}
</script>

<style scoped>
.my-posts-page {
  height: 100vh;
  height: 100dvh;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
  background: linear-gradient(180deg, #fbfcff 0%, #f4f7fb 100%);
  display: flex;
  flex-direction: column;
}

.my-posts-selection-toggle::after,
.my-posts-state-card button::after,
.my-posts-tab::after,
.my-post-selector::after,
.my-posts-delete-bar button::after,
.my-post-edit-button::after,
.review-detail-dialog button::after {
  border: 0;
}

.my-posts-selection-toggle {
  width: 88rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  line-height: 1;
  font-weight: 850;
}

.my-posts-selection-toggle.active,
.my-posts-selection-toggle:active {
  background: var(--gyt-primary-soft, #eef5ff);
}

.my-post-copy,
.my-post-author {
  min-width: 0;
  flex: 1;
}

.my-posts-tabs {
  box-sizing: border-box;
  margin: 0 22rpx 22rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10rpx;
  padding: 8rpx;
  border: 0;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 12rpx 34rpx rgba(25, 48, 89, 0.06);
}

.my-posts-tab {
  min-height: 64rpx;
  margin: 0;
  padding: 0 8rpx;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #667085;
  font-size: 25rpx;
  line-height: 64rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7rpx;
}

.my-posts-tab.active {
  background: var(--gyt-primary, #3478f6);
  color: #ffffff;
  box-shadow: none;
}

.my-posts-tab-unread {
  box-sizing: border-box;
  min-width: 28rpx;
  height: 28rpx;
  padding: 0 7rpx;
  border-radius: 999rpx;
  background: #f25555;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16rpx;
  line-height: 1;
  font-weight: 900;
}

.my-posts-state-card {
  margin-right: 22rpx;
  margin-left: 22rpx;
  padding: 42rpx 30rpx;
  border: 2rpx solid #edf2fb;
  border-radius: 28rpx;
  background: #ffffff;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.6;
  text-align: center;
  box-sizing: border-box;
  box-shadow: 0 14rpx 38rpx rgba(25, 48, 89, 0.07);
}

.my-posts-state-card--warning {
  color: #a05f18;
}

.my-posts-state-card button {
  min-width: 140rpx;
  height: 60rpx;
  margin: 22rpx auto 0;
  padding: 0 22rpx;
  border: 0;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft, #eef5ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 22rpx;
  line-height: 60rpx;
  font-weight: 800;
}

.my-posts-list {
  padding: 0 22rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.my-posts-list-scroll { min-height: 0; flex: 1; }
.my-posts-load-state { padding: 22rpx 24rpx calc(24rpx + env(safe-area-inset-bottom)); color: #8a97aa; font-size: 19rpx; line-height: 1.4; font-weight: 750; text-align: center; }


.my-post-selectable {
  position: relative;
  padding-left: 0;
  isolation: isolate;
  transition: padding-left 260ms cubic-bezier(.22,.8,.28,1);
}

.my-post-selectable.is-selecting {
  padding-left: 70rpx;
}

.my-post-delete-preview {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 0;
  padding-left: 24rpx;
  border-radius: 28rpx;
  overflow: hidden;
  background: linear-gradient(90deg, #ee7770 0%, #f39a91 54%, rgba(248, 207, 202, .72) 100%);
  box-shadow: 0 12rpx 30rpx rgba(222, 87, 78, .2);
  display: flex;
  align-items: center;
  box-sizing: border-box;
  pointer-events: none;
}

.my-post-delete-preview text {
  color: #ffffff;
  font-size: 21rpx;
  line-height: 1;
  font-weight: 900;
  letter-spacing: 1rpx;
  white-space: nowrap;
}

.my-post-selectable.is-delete-armed .my-post-delete-preview {
  background: linear-gradient(90deg, #df625b 0%, #ee7770 58%, #f5aaa2 100%);
}

.my-post-selector {
  position: absolute;
  top: 50%;
  left: 0;
  z-index: 4;
  width: 46rpx;
  height: 46rpx;
  min-height: 46rpx;
  margin: 0;
  padding: 0;
  border: 2rpx solid #bfd0e9;
  border-radius: 50%;
  background: rgba(255, 255, 255, .92);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1;
  opacity: 0;
  pointer-events: none;
  transform: translateY(-50%) scale(.62);
  transition: opacity 190ms ease, transform 240ms cubic-bezier(.22,.8,.28,1), background 160ms ease, border-color 160ms ease;
}

.my-post-selectable.is-selecting .my-post-selector {
  left: 12rpx;
  opacity: 1;
  pointer-events: auto;
  transform: translateY(-50%) scale(1);
}

.my-post-selectable.is-swiping .my-post-selector {
  opacity: .72;
  transform: translateY(-50%) scale(.9);
}

.my-post-selectable.selected .my-post-selector {
  border-color: var(--gyt-primary, #3478f6);
  background: var(--gyt-primary, #3478f6);
  box-shadow: 0 6rpx 14rpx rgba(52, 120, 246, .22);
}

.my-post-card {
  position: relative;
  z-index: 1;
  padding: 26rpx 24rpx;
  border: 2rpx solid #edf2fb;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 14rpx 38rpx rgba(25, 48, 89, 0.07);
  box-sizing: border-box;
  transition: background-color 140ms ease, border-color 160ms ease, transform 180ms cubic-bezier(.22,.8,.28,1);
}

.my-post-selectable.is-delete-preview .my-post-card::after {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 3;
  width: 34%;
  border-radius: 0 26rpx 26rpx 0;
  background: linear-gradient(90deg, rgba(238, 119, 112, 0), rgba(226, 91, 84, .24));
  opacity: var(--delete-progress, 0);
  content: '';
  pointer-events: none;
}

.my-post-selectable.is-swiping .my-post-card {
  transition: none;
}

.my-post-selectable.is-removing {
  pointer-events: none;
}

.my-post-selectable.is-removing .my-post-card {
  opacity: 0;
  transform: translate3d(calc(100vw + 120rpx), 0, 0) scale(.98) !important;
  transition: transform 560ms cubic-bezier(.2,.72,.18,1), opacity 420ms ease 80ms !important;
  will-change: transform, opacity;
}

.my-post-selectable.is-removing .my-post-delete-preview,
.my-post-selectable.is-removing .my-post-selector {
  opacity: 0 !important;
  transition: opacity 300ms ease !important;
}

.my-post-card.has-unread-interaction {
  border-color: rgba(242, 85, 85, 0.2);
}

.my-post-selectable.selected .my-post-card {
  border-color: var(--gyt-primary-border, #d7e5ff);
}

.my-post-card:active {
  background: var(--gyt-primary-tint, #f4f8ff);
  transform: none;
}

.my-post-card-header {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.my-post-avatar {
  width: 62rpx;
  height: 62rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  color: #3478f6;
  background: #edf4ff;
  font-size: 25rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.my-post-avatar.tone-mint { color: #148e79; background: #e5f8f1; }
.my-post-avatar.tone-warm { color: #d88722; background: #fff4df; }
.my-post-avatar.tone-violet { color: #725bc9; background: #f0ebff; }
.my-post-avatar image { width: 100%; height: 100%; }

.my-post-author-name {
  overflow: hidden;
  color: #101828;
  font-size: 24rpx;
  line-height: 1.25;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.my-post-author-meta {
  margin-top: 5rpx;
  color: #8a95a8;
  font-size: 20rpx;
  line-height: 1.25;
}

.my-post-category {
  max-width: 132rpx;
  padding: 7rpx 12rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: var(--gyt-primary-soft, #eef5ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 19rpx;
  line-height: 1.2;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.my-post-category-list {
  min-width: 0;
  max-width: 286rpx;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 6rpx;
  flex: 0 1 auto;
}

.my-post-category-list .my-post-category {
  max-width: none;
  flex: 0 0 auto;
}

.my-post-unread-badge {
  flex: 0 0 auto;
  padding: 7rpx 11rpx;
  border-radius: 999rpx;
  background: rgba(242, 85, 85, 0.1);
  color: #d94b4b;
  font-size: 18rpx;
  line-height: 1;
  font-weight: 900;
  white-space: nowrap;
}

.my-post-review-status {
  width: fit-content;
  margin-top: 16rpx;
  padding: 7rpx 11rpx;
  border-radius: 999rpx;
  background: #e8f7f2;
  color: #238b75;
  font-size: 18rpx;
  line-height: 1;
  font-weight: 900;
  white-space: nowrap;
  display: inline-flex;
}

.my-post-review-status.pending { background: #fff4df; color: #a86f1c; }
.my-post-review-status.archived { background: #fff0ed; color: #c45e52; }

.my-post-card-body { margin-top: 20rpx; }

.my-post-card-body.has-cover {
  min-height: 136rpx;
  display: flex;
  align-items: stretch;
  gap: 16rpx;
}

.my-post-card-title {
  overflow: hidden;
  color: #101828;
  font-size: 28rpx;
  line-height: 1.35;
  font-weight: 900;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.my-post-content {
  margin-top: 8rpx;
  overflow: hidden;
  color: #475467;
  font-size: 25rpx;
  line-height: 1.55;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.my-post-cover {
  width: 144rpx;
  height: 136rpx;
  border-radius: 20rpx;
  background: #edf4ff;
  flex-shrink: 0;
}

.my-post-review-note {
  margin-top: 16rpx;
  padding: 16rpx 18rpx;
  border-left: 5rpx solid #e78376;
  border-radius: 12rpx;
  background: #fff6f3;
}

.my-post-review-note strong,
.my-post-review-note text {
  display: block;
}

.my-post-review-note strong {
  color: #b65349;
  font-size: 21rpx;
  line-height: 1.35;
}

.my-post-review-note text {
  margin-top: 6rpx;
  overflow: hidden;
  color: #765650;
  font-size: 21rpx;
  line-height: 1.5;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.my-post-card-footer {
  margin-top: 18rpx;
  padding-top: 0;
  border-top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.my-post-stats {
  display: flex;
  align-items: center;
  gap: 14rpx;
  color: #8a95a8;
  font-size: 22rpx;
  line-height: 1.4;
}

.my-post-stats > view {
  display: inline-flex;
  align-items: center;
  gap: 5rpx;
}

.my-post-stats image {
  display: block;
  width: 24rpx;
  height: 24rpx;
}

.my-post-detail-link {
  color: var(--gyt-primary, #3478f6);
  font-size: 22rpx;
  line-height: 1.4;
  font-weight: 900;
  white-space: nowrap;
}

.my-post-card-actions {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.my-post-edit-button {
  min-width: 128rpx;
  height: 54rpx;
  margin: 0;
  padding: 0 14rpx;
  border: 0;
  border-radius: 16rpx;
  background: #edf8f5;
  color: #268d79;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  line-height: 1;
  font-weight: 850;
}

.review-detail-backdrop {
  position: fixed;
  z-index: 80;
  inset: 0;
  padding: 32rpx 24rpx;
  box-sizing: border-box;
  background: rgba(23, 37, 54, .42);
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-backdrop-filter: blur(6rpx);
  backdrop-filter: blur(6rpx);
}

.review-detail-dialog {
  width: min(680rpx, calc(100vw - 48rpx));
  max-height: min(980rpx, calc(100dvh - 64rpx));
  overflow: hidden;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 32rpx 90rpx rgba(20, 35, 54, .24);
  display: flex;
  flex-direction: column;
}

.review-detail-header {
  padding: 26rpx 26rpx 22rpx;
  border-bottom: 2rpx solid #edf1f5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.review-detail-header > view { min-width: 0; }
.review-detail-header text,
.review-detail-header strong { display: block; }
.review-detail-header text { color: #2d8d79; font-size: 19rpx; font-weight: 850; }
.review-detail-header strong { margin-top: 7rpx; overflow: hidden; color: #26384c; font-size: 27rpx; text-overflow: ellipsis; white-space: nowrap; }

.review-detail-header button {
  width: 58rpx;
  height: 58rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #f2f5f7;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 58rpx;
}

.review-detail-header :deep(.close-icon-image) { width: 28rpx; height: 28rpx; }
.review-detail-scroll { min-height: 0; flex: 1; }
.review-detail-content { padding: 24rpx 26rpx 30rpx; }
.review-detail-state { padding: 80rpx 28rpx; color: #8795a6; font-size: 23rpx; text-align: center; }
.review-detail-state.error { color: #b85d55; }
.review-detail-state button { min-width: 154rpx; height: 60rpx; margin: 20rpx auto 0; border: 0; border-radius: 16rpx; background: #edf8f5; color: #278d79; font-size: 21rpx; }

.review-current-status {
  padding: 20rpx;
  border-left: 6rpx solid #4dbda5;
  border-radius: 14rpx;
  background: #effaf7;
}

.review-current-status.pending { border-left-color: #d7a747; background: #fff8e9; }
.review-current-status.rejected { border-left-color: #df766a; background: #fff4f1; }
.review-current-status text,
.review-current-status strong,
.review-current-status small { display: block; }
.review-current-status text { color: #7c8b99; font-size: 19rpx; }
.review-current-status strong { margin-top: 7rpx; color: #31495f; font-size: 28rpx; }
.review-current-status small { margin-top: 7rpx; color: #6f8091; font-size: 21rpx; line-height: 1.5; }

.review-official-note {
  margin-top: 20rpx;
  padding: 19rpx 20rpx;
  border: 2rpx solid #f1d5cf;
  border-radius: 14rpx;
  background: #fffafa;
}

.review-official-note text,
.review-official-note strong { display: block; }
.review-official-note text { color: #c15d52; font-size: 20rpx; font-weight: 850; }
.review-official-note strong { margin-top: 9rpx; color: #6d514d; font-size: 22rpx; line-height: 1.6; }

.review-history-heading { margin: 28rpx 0 15rpx; color: #40556b; font-size: 23rpx; font-weight: 900; }
.review-history-empty { padding: 28rpx; border-radius: 14rpx; background: #f7f9fb; color: #98a4b0; font-size: 21rpx; text-align: center; }
.review-history-list { display: flex; flex-direction: column; gap: 0; }
.review-history-item { position: relative; padding: 0 0 24rpx 34rpx; }
.review-history-item:not(:last-child)::before { width: 2rpx; content: ''; position: absolute; top: 14rpx; bottom: -2rpx; left: 10rpx; background: #dce6e9; }
.review-history-marker { width: 20rpx; height: 20rpx; position: absolute; top: 5rpx; left: 1rpx; border: 5rpx solid #fff; border-radius: 50%; box-shadow: 0 0 0 2rpx #d7e3e7; background: #5bbfa9; }
.review-history-marker.rejected { background: #df766a; }
.review-history-marker.submitted { background: #d6a54c; }
.review-history-copy > view { display: flex; align-items: center; justify-content: space-between; gap: 14rpx; }
.review-history-copy strong { color: #40566b; font-size: 22rpx; }
.review-history-copy > view text { color: #93a1ae; font-size: 18rpx; }
.review-history-copy small { display: block; margin-top: 6rpx; color: #9aa6b2; font-size: 18rpx; }
.review-history-note { display: block; margin-top: 8rpx; color: #65778a; font-size: 20rpx; line-height: 1.55; }

.review-detail-actions {
  padding: 18rpx 26rpx calc(env(safe-area-inset-bottom) + 20rpx);
  border-top: 2rpx solid #edf1f5;
  background: #ffffff;
}

.review-detail-actions button {
  width: 100%;
  height: 74rpx;
  margin: 0;
  border: 0;
  border-radius: 18rpx;
  background: #2ea78d;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 23rpx;
  font-weight: 900;
}

.my-posts-delete-bar {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 40;
  min-height: 124rpx;
  padding: 16rpx 24rpx calc(env(safe-area-inset-bottom) + 18rpx);
  border-top: 2rpx solid #dbe7f7;
  background: rgba(255, 255, 255, .96);
  box-shadow: 0 -14rpx 36rpx rgba(25, 48, 89, .1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
  box-sizing: border-box;
  -webkit-backdrop-filter: blur(18rpx);
  backdrop-filter: blur(18rpx);
}

.my-posts-delete-summary {
  min-width: 0;
  flex: 1;
  color: #566b88;
  font-size: 22rpx;
  line-height: 1.35;
  font-weight: 800;
  text-align: center;
  white-space: nowrap;
}

.my-posts-delete-bar .my-posts-select-all,
.my-posts-delete-bar .my-posts-delete-action {
  min-height: 72rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 0;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 900;
}

.my-posts-delete-bar .my-posts-select-all {
  min-width: 142rpx;
  background: var(--gyt-primary-soft, #eef5ff);
  color: var(--gyt-primary, #3478f6);
}

.my-posts-delete-bar .my-posts-delete-action {
  min-width: 150rpx;
  background: #e7786c;
  color: #ffffff;
  box-shadow: 0 10rpx 22rpx rgba(215, 96, 86, .2);
}

.my-posts-delete-bar .my-posts-delete-action[disabled] {
  opacity: .46;
  box-shadow: none;
}

.my-posts-page.has-delete-bar {
  padding-bottom: calc(env(safe-area-inset-bottom) + 124rpx);
}
</style>
