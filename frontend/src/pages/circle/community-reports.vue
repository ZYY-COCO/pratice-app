<template>
  <view class="community-reports-page" :style="themeInlineStyle">
    <AppPageHeader title="我的举报" @back="goBack">
      <template #right><button class="community-reports-refresh" :disabled="loading" aria-label="刷新举报记录" @tap="load"><AppRefreshIcon /></button></template>
    </AppPageHeader>

    <scroll-view scroll-y class="community-reports-scroll">
      <view class="community-reports-content">
        <view class="community-reports-intro">
          <strong>{{ activeRecordTab === 'reports' ? '处理进度公开可查' : '内容处置与申诉可追溯' }}</strong>
          <text>{{ activeRecordTab === 'reports' ? '平台会在这里同步核实状态、内容处置和处理说明。' : '被处理的帖子或评论，以及对应申诉进度都集中在这里查看。' }}</text>
        </view>

        <view class="community-record-tabs">
          <button :class="{ active: activeRecordTab === 'reports' }" @tap="activeRecordTab = 'reports'">举报记录</button>
          <button :class="{ active: activeRecordTab === 'content' }" @tap="activeRecordTab = 'content'">内容处理</button>
        </view>

        <view v-if="loading" class="community-reports-state">正在同步{{ activeRecordTab === 'reports' ? '举报记录' : '内容处理记录' }}…</view>
        <view v-else-if="activeError" class="community-reports-state error">
          <text>{{ activeError }}</text>
          <button @tap="load">重新加载</button>
        </view>

        <template v-else-if="activeRecordTab === 'reports'">
          <view v-if="reports.length === 0" class="community-reports-state">
            <strong>还没有提交过举报</strong>
            <text>遇到违规内容时，可在帖子或评论菜单中发起举报。</text>
          </view>

          <view v-for="item in reports" v-else :key="item.id" class="community-report-record">
            <view class="community-report-record-top">
              <view>
                <text class="community-report-type">{{ item.target_type === 'comment' ? '评论举报' : '帖子举报' }}</text>
                <strong>{{ item.target_title || '研圈内容' }}</strong>
              </view>
              <text class="community-report-status" :class="item.status">{{ statusText(item.status) }}</text>
            </view>
            <view class="community-report-excerpt">{{ item.target_excerpt || '原内容已由平台留档' }}</view>
            <view class="community-report-reason">举报原因：{{ item.reason }}</view>
            <view v-if="item.admin_note" class="community-report-note">
              <text>平台处理说明</text>
              <strong>{{ item.admin_note }}</strong>
              <small v-if="item.moderation_action !== 'none'">{{ actionText(item.moderation_action) }}</small>
            </view>
            <view class="community-report-time">提交于 {{ formatDateTime(item.created_at) }}<text v-if="item.handled_at"> · 更新于 {{ formatDateTime(item.handled_at) }}</text></view>
          </view>
        </template>

        <template v-else>
          <view v-if="contentItems.length === 0" class="community-reports-state">
            <strong>暂无需要处理的内容</strong>
            <text>你的帖子和评论当前均正常展示，或尚未进入平台处置流程。</text>
          </view>

          <view v-for="item in contentItems" v-else :key="`${item.target_type}-${item.target_id}`" class="community-content-record">
            <view class="community-content-record-top">
              <view>
                <text class="community-content-kind">{{ item.target_type === 'comment' ? '评论处理' : '帖子处理' }}</text>
                <strong>{{ item.title || '研圈内容' }}</strong>
              </view>
              <text class="community-content-pill" :class="item.is_published ? 'visible' : 'hidden'">{{ item.is_published ? '已恢复展示' : '已下架' }}</text>
            </view>
            <view class="community-content-excerpt">{{ item.excerpt || '原内容已由平台留档' }}</view>
            <view v-if="item.moderation_note" class="community-content-note">
              <text>平台处置说明</text>
              <strong>{{ item.moderation_note }}</strong>
            </view>
            <view v-if="item.appeal" class="community-content-appeal">
              <view><text>我的申诉</text><small :class="item.appeal.status">{{ statusText(item.appeal.status) }}</small></view>
              <strong>{{ item.appeal.content }}</strong>
              <text v-if="item.appeal.admin_note" class="community-content-appeal-note">平台答复：{{ item.appeal.admin_note }}</text>
              <text v-if="item.appeal.moderation_action !== 'none'" class="community-content-appeal-result">{{ appealResultText(item.appeal.moderation_action) }}</text>
            </view>
            <button v-if="canAppeal(item)" class="community-content-appeal-button" @tap="openAppeal(item)">提交申诉</button>
            <view class="community-report-time">{{ item.moderated_at ? `平台处置于 ${formatDateTime(item.moderated_at)}` : `申诉提交于 ${formatDateTime(item.appeal?.created_at)}` }}</view>
          </view>
        </template>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { fetchMyCommunityContentStatus, fetchMyCommunityReports } from '../../api/community'
import { markUserNotificationReadScope } from '../../api/notifications'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppRefreshIcon from '../../components/ui/AppRefreshIcon.vue'

const reports = ref([])
const contentItems = ref([])
const loading = ref(false)
const reportsError = ref('')
const contentError = ref('')
const activeRecordTab = ref('reports')
const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const activeError = computed(() => activeRecordTab.value === 'reports' ? reportsError.value : contentError.value)

onLoad((options) => {
  activeRecordTab.value = options?.tab === 'content' ? 'content' : 'reports'
})

onShow(() => {
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  void markCommunityReportNotificationsRead()
  void load()
})

async function markCommunityReportNotificationsRead() {
  try {
    await markUserNotificationReadScope('community_reports')
  } catch (error) {
    // 未读状态同步失败不应妨碍用户查看举报与内容处理记录。
  }
}

async function load() {
  if (loading.value) return
  loading.value = true
  reportsError.value = ''
  contentError.value = ''

  const [reportsResult, contentResult] = await Promise.allSettled([
    fetchMyCommunityReports({ limit: 100 }),
    fetchMyCommunityContentStatus({ limit: 100 })
  ])

  if (reportsResult.status === 'fulfilled') {
    reports.value = Array.isArray(reportsResult.value?.items) ? reportsResult.value.items : []
  } else {
    reports.value = []
    reportsError.value = reportsResult.reason?.detail || '举报记录读取失败，请稍后重试'
  }

  if (contentResult.status === 'fulfilled') {
    contentItems.value = Array.isArray(contentResult.value?.items) ? contentResult.value.items : []
  } else {
    contentItems.value = []
    contentError.value = contentResult.reason?.detail || '内容处理记录读取失败，请稍后重试'
  }

  loading.value = false
}

function canAppeal(item = {}) {
  return !item.is_published && !item.appeal
}

function statusText(status) {
  return { pending: '待处理', reviewing: '处理中', resolved: '已处理', dismissed: '已驳回' }[status] || '待处理'
}

function actionText(action) {
  return { hide_post: '相关帖子已下架', restore_post: '相关帖子已恢复', hide_comment: '相关评论已下架', restore_comment: '相关评论已恢复' }[action] || ''
}

function appealResultText(action) {
  return { restore_post: '平台已恢复帖子展示', restore_comment: '平台已恢复评论展示', uphold: '平台维持原内容处置' }[action] || ''
}

function openAppeal(item) {
  if (!canAppeal(item)) return
  const query = [
    `targetType=${encodeURIComponent(item.target_type)}`,
    `targetId=${encodeURIComponent(item.target_id)}`,
    `title=${encodeURIComponent(item.title || '研圈内容')}`
  ].join('&')
  uni.navigateTo({ url: `/pages/circle/community-appeal?${query}` })
}

function formatDateTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '刚刚'
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function goLogin() {
  const destination = activeRecordTab.value === 'content'
    ? '/pages/circle/community-reports?tab=content'
    : '/pages/circle/community-reports'
  uni.reLaunch({ url: `/pages/login/index?redirect=${encodeURIComponent(destination)}` })
}

function goBack() {
  uni.navigateBack({ fail() { uni.reLaunch({ url: '/pages/home/index?tab=profile' }) } })
}
</script>

<style scoped>
.community-reports-page{height:100vh;height:100dvh;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f4f8ff);color:#2b3d59}
.community-reports-topbar{height:96rpx;padding:calc(env(safe-area-inset-top) + 14rpx) 24rpx 14rpx;display:grid;grid-template-columns:60rpx 1fr 60rpx;align-items:center;box-sizing:content-box;background:rgba(255,255,255,.88);box-shadow:0 8rpx 22rpx rgba(37,57,90,.05)}
.community-reports-topbar button{width:60rpx;height:60rpx;margin:0;padding:0;border:0;border-radius:18rpx;background:#f1f6ff;color:var(--gyt-primary,#3478f6);font-size:32rpx}
.community-reports-topbar button::after,.community-reports-state button::after,.community-record-tabs button::after,.community-content-appeal-button::after{border:0}
.community-reports-topbar image{width:28rpx;height:28rpx}
.community-reports-topbar>view{text-align:center;font-size:30rpx;font-weight:900}
.community-reports-refresh{font-size:30rpx!important}
.community-reports-scroll{min-height:0;flex:1}
.community-reports-content{padding:24rpx}
.community-reports-intro,.community-report-record,.community-content-record,.community-reports-state{padding:25rpx;border:2rpx solid var(--gyt-primary-border,#dce8fa);border-radius:26rpx;background:var(--gyt-panel-bg,#fff);box-shadow:0 12rpx 30rpx rgba(43,73,112,.05)}
.community-reports-intro strong,.community-reports-intro text{display:block}
.community-reports-intro strong{font-size:27rpx}
.community-reports-intro text{margin-top:8rpx;color:#8495aa;font-size:20rpx;line-height:1.5}
.community-record-tabs{display:flex;gap:8rpx;margin-top:18rpx;padding:6rpx;border:2rpx solid var(--gyt-primary-border,#dce8fa);border-radius:20rpx;background:rgba(255,255,255,.7)}
.community-record-tabs button{flex:1;height:56rpx;margin:0;padding:0;border:0;border-radius:14rpx;background:transparent;color:#7a8da4;font-size:20rpx;font-weight:800;line-height:56rpx}
.community-record-tabs button.active{background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6)}
.community-reports-state{margin-top:18rpx;color:#8191a6;text-align:center;font-size:21rpx;line-height:1.55}
.community-reports-state strong,.community-reports-state text{display:block}
.community-reports-state button{margin-top:14rpx;border:0;background:#edf4ff;color:#5275ad;font-size:20rpx}
.community-reports-state.error{color:#bd655c}
.community-report-record,.community-content-record{margin-top:18rpx}
.community-report-record-top,.community-content-record-top{display:flex;align-items:flex-start;justify-content:space-between;gap:12rpx}
.community-report-record-top>view,.community-content-record-top>view{min-width:0;flex:1}
.community-report-type,.community-content-kind{display:block;color:var(--gyt-primary,#3478f6);font-size:18rpx;font-weight:850}
.community-report-record-top strong,.community-content-record-top strong{display:block;margin-top:6rpx;overflow:hidden;font-size:24rpx;text-overflow:ellipsis;white-space:nowrap}
.community-report-status,.community-content-pill{flex:none;padding:7rpx 10rpx;border-radius:999rpx;background:#fff4dd;color:#aa792e;font-size:18rpx;font-weight:850}
.community-report-status.reviewing{background:#eaf2fc;color:#517aa9}
.community-report-status.resolved,.community-content-pill.visible{background:#e6f7f1;color:#238b74}
.community-report-status.dismissed{background:#f0eef2;color:#807987}
.community-content-pill.hidden{background:#fff0ec;color:#c16b5d}
.community-report-excerpt,.community-content-excerpt{margin-top:13rpx;color:#657991;font-size:20rpx;line-height:1.55;white-space:pre-wrap}
.community-report-reason{margin-top:10rpx;color:#788aa0;font-size:19rpx}
.community-report-note,.community-content-note,.community-content-appeal{margin-top:16rpx;padding:15rpx;border-radius:17rpx;background:var(--gyt-primary-tint,#f7faff);color:#5f7187}
.community-report-note text,.community-report-note strong,.community-report-note small,.community-content-note text,.community-content-note strong,.community-content-appeal>strong{display:block}
.community-report-note text,.community-content-note text,.community-content-appeal>view>text{color:#8293aa;font-size:18rpx}
.community-report-note strong,.community-content-note strong,.community-content-appeal>strong{margin-top:6rpx;font-size:20rpx;line-height:1.5}
.community-report-note small{margin-top:8rpx;color:#2c927d;font-size:18rpx;font-weight:800}
.community-content-appeal>view{display:flex;align-items:center;justify-content:space-between;gap:12rpx}
.community-content-appeal small{padding:5rpx 9rpx;border-radius:999rpx;background:#fff4dd;color:#aa792e;font-size:17rpx;font-weight:850}
.community-content-appeal small.reviewing{background:#eaf2fc;color:#517aa9}
.community-content-appeal small.resolved{background:#e6f7f1;color:#238b74}
.community-content-appeal small.dismissed{background:#f0eef2;color:#807987}
.community-content-appeal-note,.community-content-appeal-result{display:block;margin-top:10rpx;font-size:19rpx;line-height:1.5}
.community-content-appeal-result{color:#268b76;font-weight:850}
.community-content-appeal-button{width:100%;height:66rpx;min-height:66rpx;margin-top:16rpx;padding:0;border:0;border-radius:17rpx;background:var(--gyt-primary-gradient,#3478f6);color:#fff;font-size:21rpx;font-weight:850}
.community-report-time{margin-top:16rpx;color:#9aa7b6;font-size:18rpx}
</style>
