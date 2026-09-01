<template>
  <view class="page my-posts-page" :class="{ 'has-delete-bar': selectionMode && selectedPostIds.length }" :style="pageInlineStyle">
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
    <AppEmptyState v-else-if="posts.length === 0" label="暂无已发布帖子" />

    <scroll-view v-else scroll-y class="my-posts-list-scroll" @scrolltolower="loadMoreMyPosts">
      <view class="my-posts-list">
      <view
        v-for="post in posts"
        :key="post.id"
        class="my-post-selectable"
        :class="{ 'is-selecting': selectionMode, selected: isPostSelected(post.id) }"
      >
        <button
          class="my-post-selector"
          hover-class="none"
          :aria-label="isPostSelected(post.id) ? '取消选择帖子' : '选择帖子'"
          @tap.stop="togglePostSelection(post.id)"
        ><text v-if="isPostSelected(post.id)">✓</text></button>

        <view class="my-post-card" :class="{ 'has-unread-interaction': isPostUnread(post) }" @tap="handlePostTap(post)">
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
            <view class="my-post-category">{{ post.category }}</view>
          </view>

          <view class="my-post-card-body" :class="{ 'has-cover': post.coverUrl }">
            <view class="my-post-copy">
              <view class="my-post-card-title">{{ post.title || '研圈帖子' }}</view>
              <view class="my-post-content">{{ post.content }}</view>
            </view>
            <image v-if="post.coverUrl" class="my-post-cover" :src="post.coverUrl" mode="aspectFill" />
          </view>

          <view class="my-post-card-footer">
            <view class="my-post-stats">
              <view><image src="/static/ui-icons/png/neutral/circle-like.png" mode="aspectFit" /><text>{{ post.stats.likes }}</text></view>
              <view><image src="/static/ui-icons/png/neutral/circle-comment.png" mode="aspectFit" /><text>{{ post.stats.comments }}</text></view>
              <view><image src="/static/ui-icons/png/neutral/circle-view.png" mode="aspectFit" /><text>{{ post.stats.views }}</text></view>
            </view>
            <text v-if="!selectionMode" class="my-post-detail-link">查看详情 ›</text>
          </view>
        </view>
      </view>
      </view>
      <view class="my-posts-load-state" @tap="loadMoreMyPosts">
        {{ loadingMore ? '正在加载更多…' : hasMore ? '继续下滑加载更多' : '已加载全部帖子' }}
      </view>
    </scroll-view>

    <transition name="my-posts-delete-bar">
      <view v-if="selectionMode && selectedPostIds.length" class="my-posts-delete-bar">
        <text>已选择 {{ selectedPostIds.length }} 篇</text>
        <button :loading="deletingPosts" hover-class="none" @tap="confirmBatchDelete">
          {{ deletingPosts ? '删除中…' : `删除 ${selectedPostIds.length} 篇` }}
        </button>
      </view>
    </transition>

    <!-- #ifdef H5 -->
    <IcpFooter />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import IcpFooter from '../../components/IcpFooter.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import { deleteMyCommunityPosts, fetchMyCommunityPosts } from '../../api/community'
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
const deletingPosts = ref(false)
const loadingMore = ref(false)
const nextCursor = ref('')
const hasMore = ref(false)
const unreadPostTargets = ref({ chat: {}, experience: {} })
let latestUnreadLoadToken = 0
onLoad((options) => {
  const requestedType = String(options?.type || '')
  if (postTypeOptions.some((item) => item.value === requestedType)) {
    activePostType.value = requestedType
  }
})

onShow(() => {
  mpLayoutStyle.value = buildMpPageSafeStyle()
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  void loadUnreadPostTargets()
  void loadMyPosts()
})

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
  return {
    id: String(post.id || ''),
    postType,
    postTypeLabel: postType === 'experience' ? '经验贴' : '研友聊',
    category: String(post.category || '备考日常'),
    author: String(post.author || '研友'),
    avatar: String(post.avatar || '研'),
    avatarUrl: String(post.avatarUrl || post.avatar_url || '').trim(),
    tone: String(post.tone || 'blue'),
    title: String(post.title || ''),
    content: String(post.content || post.summary || ''),
    publishTime: String(post.publishTime || post.publish_time || '刚刚'),
    coverUrl: String(cover?.imageUrl || cover?.image_url || '').trim(),
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
  selectionMode.value = true
}

function exitSelectionMode() {
  selectionMode.value = false
  selectedPostIds.value = []
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

function handlePostTap(post) {
  if (selectionMode.value) {
    togglePostSelection(post?.id)
    return
  }
  openPost(post)
}

function confirmBatchDelete() {
  const postIds = [...selectedPostIds.value]
  if (!postIds.length || deletingPosts.value) return
  uni.showModal({
    title: `删除 ${postIds.length} 篇帖子？`,
    content: '帖子及其点赞、评论和浏览记录会一并删除，删除后不可恢复。',
    confirmText: '删除',
    confirmColor: '#e06b61',
    success(result) {
      if (!result.confirm) return
      void deleteSelectedPosts(postIds)
    }
  })
}

async function deleteSelectedPosts(postIds) {
  deletingPosts.value = true
  try {
    const response = await deleteMyCommunityPosts(postIds)
    const deletedIds = Array.isArray(response?.deleted_post_ids)
      ? response.deleted_post_ids.map((id) => String(id || '')).filter(Boolean)
      : []
    if (!deletedIds.length) {
      uni.showToast({ title: '帖子状态已变化，请刷新后重试', icon: 'none' })
      return
    }
    const deletedIdSet = new Set(deletedIds)
    posts.value = posts.value.filter((post) => !deletedIdSet.has(post.id))
    exitSelectionMode()
    uni.showToast({ title: `已删除 ${deletedIds.length} 篇帖子`, icon: 'success' })
  } catch (requestError) {
    uni.showToast({ title: requestError?.detail || '删除失败，请稍后重试', icon: 'none' })
  } finally {
    deletingPosts.value = false
  }
}

function openPost(post) {
  if (!post?.id) return
  markPostNotificationsRead(post)
  const communityTab = post.postType === 'experience' ? 'experience' : 'chat'
  uni.navigateTo({
    url: `/pages/home/index?tab=circle&section=community&communityTab=${communityTab}&postId=${encodeURIComponent(post.id)}`
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
.my-posts-delete-bar button::after {
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
  transition: padding-left 260ms cubic-bezier(.22,.8,.28,1);
}

.my-post-selectable.is-selecting {
  padding-left: 70rpx;
}

.my-post-selector {
  position: absolute;
  top: 50%;
  left: 0;
  z-index: 2;
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
  opacity: 1;
  pointer-events: auto;
  transform: translateY(-50%) scale(1);
}

.my-post-selectable.selected .my-post-selector {
  border-color: var(--gyt-primary, #3478f6);
  background: var(--gyt-primary, #3478f6);
  box-shadow: 0 6rpx 14rpx rgba(52, 120, 246, .22);
}

.my-post-card {
  padding: 26rpx 24rpx;
  border: 2rpx solid #edf2fb;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 14rpx 38rpx rgba(25, 48, 89, 0.07);
  box-sizing: border-box;
  transition: background-color 140ms ease, border-color 160ms ease;
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
  gap: 18rpx;
  box-sizing: border-box;
  -webkit-backdrop-filter: blur(18rpx);
  backdrop-filter: blur(18rpx);
}

.my-posts-delete-bar > text {
  min-width: 0;
  color: #566b88;
  font-size: 22rpx;
  line-height: 1.35;
  font-weight: 750;
}

.my-posts-delete-bar button {
  min-width: 196rpx;
  min-height: 72rpx;
  margin: 0;
  padding: 0 22rpx;
  border: 0;
  border-radius: 22rpx;
  background: #e7786c;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 900;
  box-shadow: 0 10rpx 22rpx rgba(215, 96, 86, .2);
}

.my-posts-delete-bar button[disabled] {
  opacity: .72;
}

.my-posts-delete-bar-enter-active,
.my-posts-delete-bar-leave-active {
  transition: opacity 240ms ease, transform 300ms cubic-bezier(.22,.8,.28,1);
}

.my-posts-delete-bar-enter-from,
.my-posts-delete-bar-leave-to {
  opacity: 0;
  transform: translateY(calc(100% + env(safe-area-inset-bottom)));
}

.my-posts-page.has-delete-bar {
  padding-bottom: calc(env(safe-area-inset-bottom) + 124rpx);
}
</style>
