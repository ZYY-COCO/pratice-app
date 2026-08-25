<template>
  <view class="page liked-posts-page" :style="pageInlineStyle">
    <AppPageHeader title="赞过的帖子" @back="goBack" />

    <view v-if="loading" class="liked-posts-state-card">正在同步你赞过的帖子...</view>
    <view v-else-if="error" class="liked-posts-state-card liked-posts-state-card--warning">
      <text>{{ error }}</text>
      <button hover-class="none" @tap="loadLikedPosts">重新加载</button>
    </view>
    <view v-else-if="likedPosts.length === 0" class="liked-posts-empty-state" aria-label="暂无点赞帖子">
      <image
        class="liked-posts-empty-image"
        src="/static/ui-icons/empty-favorites.svg"
        mode="aspectFit"
        alt="暂无点赞帖子"
      />
    </view>

    <scroll-view v-else scroll-y class="liked-posts-list-scroll" @scrolltolower="loadMoreLikedPosts">
      <view class="liked-posts-list">
      <view v-for="post in likedPosts" :key="post.id" class="liked-post-card" @tap="openPost(post)">
        <view class="liked-post-card-header">
          <view class="liked-post-avatar" :class="`tone-${post.tone}`">
            <image v-if="post.avatarUrl" :src="post.avatarUrl" mode="aspectFill" />
            <text v-else>{{ post.avatar }}</text>
          </view>
          <view class="liked-post-author">
            <view class="liked-post-author-name">{{ post.author }}</view>
            <view class="liked-post-author-meta">{{ post.postTypeLabel }} · {{ post.publishTime }}</view>
          </view>
          <view class="liked-post-category">{{ post.category }}</view>
        </view>

        <view class="liked-post-card-body" :class="{ 'has-cover': post.coverUrl }">
          <view class="liked-post-copy">
            <view class="liked-post-title">{{ post.title || '研圈帖子' }}</view>
            <view class="liked-post-content">{{ post.content }}</view>
          </view>
          <image v-if="post.coverUrl" class="liked-post-cover" :src="post.coverUrl" mode="aspectFill" />
        </view>

        <view class="liked-post-card-footer">
          <view class="liked-post-stats">
            <text>👍 {{ post.stats.likes }}</text>
            <text>💬 {{ post.stats.comments }}</text>
            <text>👁 {{ post.stats.views }}</text>
          </view>
          <view class="liked-post-time">点赞于 {{ formatDateTime(post.likedAt) }}</view>
        </view>

        <view class="liked-post-card-actions">
          <text class="liked-post-detail-link">查看详情 ›</text>
          <button
            class="liked-post-unlike"
            :disabled="likingPostId === post.id"
            hover-class="none"
            @tap.stop="toggleLike(post)"
          >
            {{ likingPostId === post.id ? '处理中…' : '已赞' }}
          </button>
        </view>
      </view>
      </view>
      <view class="liked-posts-load-state" @tap="loadMoreLikedPosts">
        {{ loadingMore ? '正在加载更多…' : hasMore ? '继续下滑加载更多' : '已加载全部点赞' }}
      </view>
    </scroll-view>

    <!-- #ifdef H5 -->
    <IcpFooter />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import IcpFooter from '../../components/IcpFooter.vue'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import { fetchLikedCommunityPosts, toggleCommunityPostLike } from '../../api/community'
import { isLoggedIn } from '../../utils/auth'
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const mpLayoutStyle = ref(buildMpPageSafeStyle())
const pageInlineStyle = computed(() => [themeInlineStyle, mpLayoutStyle.value].filter(Boolean).join(';'))
const likedPosts = ref([])
const loading = ref(false)
const error = ref('')
const likingPostId = ref('')
const loadingMore = ref(false)
const nextCursor = ref('')
const hasMore = ref(false)

onShow(() => {
  mpLayoutStyle.value = buildMpPageSafeStyle()
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  void loadLikedPosts()
})

async function loadLikedPosts() {
  if (loading.value || loadingMore.value) return
  loading.value = true
  nextCursor.value = ''
  hasMore.value = false
  error.value = ''
  try {
    const response = await fetchLikedCommunityPosts({ limit: 30 })
    likedPosts.value = Array.isArray(response?.items)
      ? response.items.map(normalizeLikedPost).filter((item) => item.id)
      : []
    nextCursor.value = String(response?.next_cursor || '')
    hasMore.value = response?.has_more === true
  } catch (requestError) {
    error.value = requestError?.detail || '赞过的帖子读取失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function loadMoreLikedPosts() {
  if (loading.value || loadingMore.value || !hasMore.value || !nextCursor.value) return
  loadingMore.value = true
  try {
    const response = await fetchLikedCommunityPosts({ limit: 30, cursor: nextCursor.value })
    const nextItems = Array.isArray(response?.items) ? response.items.map(normalizeLikedPost).filter((item) => item.id) : []
    likedPosts.value = [...likedPosts.value, ...nextItems.filter((item) => !likedPosts.value.some((existing) => existing.id === item.id))]
    nextCursor.value = String(response?.next_cursor || '')
    hasMore.value = response?.has_more === true
  } catch (requestError) {
    uni.showToast({ title: requestError?.detail || '更多点赞记录读取失败', icon: 'none' })
  } finally {
    loadingMore.value = false
  }
}

function normalizeLikedPost(post = {}) {
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
    likedAt: post.likedAt || post.liked_at || '',
    coverUrl: String(cover?.imageUrl || cover?.image_url || '').trim(),
    stats: {
      likes: Number(post.stats?.likes ?? post.like_count ?? 0),
      comments: Number(post.stats?.comments ?? post.comment_count ?? 0),
      views: Number(post.stats?.views ?? post.view_count ?? 0)
    }
  }
}

async function toggleLike(post) {
  if (!post?.id || likingPostId.value === post.id) return
  likingPostId.value = post.id
  try {
    const response = await toggleCommunityPostLike(post.id)
    const isLiked = Boolean(response?.is_liked)
    if (!isLiked) {
      likedPosts.value = likedPosts.value.filter((item) => item.id !== post.id)
      uni.showToast({ title: '已取消点赞', icon: 'none' })
      return
    }
    likedPosts.value = likedPosts.value.map((item) => (
      item.id === post.id
        ? { ...item, stats: { ...item.stats, likes: Number(response?.like_count || 0) } }
        : item
    ))
  } catch (requestError) {
    uni.showToast({ title: requestError?.detail || '点赞状态更新失败，请稍后重试', icon: 'none' })
  } finally {
    likingPostId.value = ''
  }
}

function openPost(post) {
  if (!post?.id) return
  const communityTab = post.postType === 'experience' ? 'experience' : 'chat'
  uni.navigateTo({
    url: `/pages/home/index?tab=circle&section=community&communityTab=${communityTab}&postId=${encodeURIComponent(post.id)}`
  })
}

function goLogin() {
  uni.reLaunch({
    url: `/pages/login/index?redirect=${encodeURIComponent('/pages/circle/liked-posts')}`
  })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=profile' })
    }
  })
}

function formatDateTime(value) {
  if (!value) return '刚刚'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 16)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}
</script>

<style scoped>
.liked-posts-page {
  height: 100vh;
  height: 100dvh;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
  background:
    radial-gradient(circle at 91% 2%, var(--gyt-primary-soft, #eef5ff) 0, transparent 30%),
    var(--gyt-page-bg, #f5f7fb);
  display: flex;
  flex-direction: column;
}

.liked-posts-state-card button::after,
.liked-post-unlike::after {
  border: 0;
}

.liked-posts-state-card {
  margin: 0 24rpx;
  padding: 42rpx 30rpx;
  border: 2rpx solid var(--gyt-primary-border, #e4ebf8);
  border-radius: 28rpx;
  background: var(--gyt-panel-bg, rgba(255, 255, 255, 0.94));
  color: #6c7890;
  font-size: 24rpx;
  line-height: 1.6;
  text-align: center;
  box-sizing: border-box;
}

.liked-posts-state-card--warning {
  color: #a05f18;
}

.liked-posts-state-card button {
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

.liked-posts-empty-state {
  width: 100%;
  min-height: 320rpx;
  flex: 1 1 320rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.liked-posts-empty-image {
  width: 240rpx;
  height: 240rpx;
  max-width: 150px;
  max-height: 150px;
  display: block;
  opacity: 0.92;
}

.liked-posts-list {
  padding: 0 24rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.liked-posts-list-scroll { min-height: 0; flex: 1; }
.liked-posts-load-state { padding: 22rpx 24rpx calc(24rpx + env(safe-area-inset-bottom)); color: #8a97aa; font-size: 19rpx; line-height: 1.4; font-weight: 750; text-align: center; }


.liked-post-card {
  padding: 26rpx;
  border: 2rpx solid var(--gyt-primary-border, #e5edf9);
  border-radius: 30rpx;
  background: var(--gyt-panel-bg, rgba(255, 255, 255, 0.96));
  box-shadow: 0 12rpx 30rpx var(--gyt-primary-shadow, rgba(25, 48, 89, 0.055));
  box-sizing: border-box;
}

.liked-post-card:active {
  transform: scale(0.99);
}

.liked-post-card-header {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.liked-post-avatar {
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

.liked-post-avatar.tone-mint {
  color: #148e79;
  background: #e5f8f1;
}

.liked-post-avatar.tone-warm {
  color: #d88722;
  background: #fff4df;
}

.liked-post-avatar.tone-violet {
  color: #725bc9;
  background: #f0ebff;
}

.liked-post-avatar image {
  width: 100%;
  height: 100%;
}

.liked-post-author {
  min-width: 0;
  flex: 1;
}

.liked-post-author-name {
  overflow: hidden;
  color: #27354d;
  font-size: 24rpx;
  line-height: 1.25;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.liked-post-author-meta {
  margin-top: 5rpx;
  color: #8b97aa;
  font-size: 19rpx;
  line-height: 1.25;
}

.liked-post-category {
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

.liked-post-card-body {
  margin-top: 20rpx;
}

.liked-post-card-body.has-cover {
  min-height: 136rpx;
  display: flex;
  align-items: stretch;
  gap: 16rpx;
}

.liked-post-copy {
  min-width: 0;
  flex: 1;
}

.liked-post-title {
  overflow: hidden;
  color: #172033;
  font-size: 27rpx;
  line-height: 1.42;
  font-weight: 900;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.liked-post-content {
  margin-top: 8rpx;
  overflow: hidden;
  color: #66758c;
  font-size: 22rpx;
  line-height: 1.55;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.liked-post-cover {
  width: 144rpx;
  height: 136rpx;
  border-radius: 20rpx;
  background: #edf4ff;
  flex-shrink: 0;
}

.liked-post-card-footer,
.liked-post-card-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.liked-post-card-footer {
  margin-top: 22rpx;
  padding-top: 18rpx;
  border-top: 2rpx solid #edf1f7;
}

.liked-post-stats {
  display: flex;
  align-items: center;
  gap: 14rpx;
  color: #758299;
  font-size: 19rpx;
  line-height: 1.2;
}

.liked-post-time {
  color: #9aa5b6;
  font-size: 18rpx;
  line-height: 1.2;
  text-align: right;
}

.liked-post-card-actions {
  margin-top: 18rpx;
}

.liked-post-detail-link {
  color: var(--gyt-primary, #3478f6);
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 800;
}

.liked-post-unlike {
  min-width: 112rpx;
  height: 58rpx;
  margin: 0;
  padding: 0 22rpx;
  border: 0;
  border-radius: 18rpx;
  background: var(--gyt-primary-soft, #eef5ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 22rpx;
  line-height: 58rpx;
  font-weight: 900;
}

.liked-post-unlike[disabled] {
  opacity: 0.68;
}

</style>
