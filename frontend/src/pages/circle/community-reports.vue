<template>
  <view class="community-reports-page" :style="themeInlineStyle">
    <AppPageHeader title="我的举报" @back="goBack">
      <template #right><button class="community-reports-refresh" :disabled="loading" aria-label="刷新举报记录" @tap="load"><AppRefreshIcon /></button></template>
    </AppPageHeader>

    <scroll-view scroll-y class="community-reports-scroll">
      <view class="community-reports-content">
        <AppPageLoadingState v-if="entryLoading || loading" message="正在整理我的举报..." />

        <view v-else-if="allSourcesFailed" class="community-reports-state error">
          <text>举报记录读取失败，请稍后重试</text>
          <button @tap="load">重新加载</button>
        </view>

        <AppEmptyState
          v-else-if="unifiedCases.length === 0"
          label="还没有相关记录"
          title="还没有相关记录"
          description="你提交的研圈举报、咨询反馈和申诉会集中显示在这里。"
        />

        <view v-for="item in unifiedCases" v-else :key="item.key" class="community-case-record">
          <view class="community-case-record-top">
            <view>
              <text class="community-case-kind">{{ item.kind }}</text>
              <strong>{{ item.title }}</strong>
            </view>
            <text class="community-case-status" :class="item.statusTone">{{ item.statusLabel }}</text>
          </view>

          <view v-if="item.excerpt" class="community-case-excerpt">{{ item.excerpt }}</view>
          <view v-if="item.reason" class="community-case-reason">{{ item.reasonLabel || '举报原因' }}：{{ item.reason }}</view>

          <view v-if="item.respondentContent" class="community-case-detail">
            <text>对方说明</text>
            <strong>{{ item.respondentContent }}</strong>
          </view>

          <view v-if="item.adminNote || item.resolutionText" class="community-case-detail">
            <text>{{ item.adminNote ? '平台处理说明' : '处理结果' }}</text>
            <strong v-if="item.adminNote">{{ item.adminNote }}</strong>
            <small v-if="item.resolutionText">{{ item.resolutionText }}</small>
          </view>

          <view v-if="item.appeal" class="community-case-appeal">
            <view class="community-case-appeal-top">
              <text>我的申诉</text>
              <small :class="item.appeal.statusTone">{{ item.appeal.statusLabel }}</small>
            </view>
            <strong>{{ item.appeal.content }}</strong>
            <text v-if="item.appeal.adminNote" class="community-case-appeal-note">平台答复：{{ item.appeal.adminNote }}</text>
            <text v-if="item.appeal.decisionText" class="community-case-appeal-result">{{ item.appeal.decisionText }}</text>
          </view>

          <button v-if="item.canAppeal" class="community-case-appeal-button" @tap="openAppeal(item)">提交申诉</button>
          <view class="community-case-time">{{ item.timeLabel }}</view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { fetchMyCommunityContentStatus, fetchMyCommunityReports } from '../../api/community'
import { fetchMyMentorConsultationReportAppeals, fetchMyMentorConsultationReports } from '../../api/mentorConsultation'
import { markUserNotificationReadScope } from '../../api/notifications'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import AppRefreshIcon from '../../components/ui/AppRefreshIcon.vue'

const communityReports = ref([])
const communityContentItems = ref([])
const consultationReports = ref([])
const consultationAppeals = ref([])
const loading = ref(false)
const entryLoading = ref(true)
const failedSourceCount = ref(0)
const themeInlineStyle = buildThemeStyle(getStoredThemeKey())

const allSourcesFailed = computed(() => failedSourceCount.value === 4)
const unifiedCases = computed(() => buildUnifiedCases())

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
    // 未读状态同步失败不应妨碍用户查看统一案件记录。
  }
}

async function load() {
  if (loading.value) return
  loading.value = true
  failedSourceCount.value = 0

  const results = await Promise.allSettled([
    fetchMyCommunityReports({ limit: 100 }),
    fetchMyCommunityContentStatus({ limit: 100 }),
    fetchMyMentorConsultationReports({ limit: 100 }),
    fetchMyMentorConsultationReportAppeals({ limit: 100 })
  ])

  const sourceTargets = [communityReports, communityContentItems, consultationReports, consultationAppeals]
  results.forEach((result, index) => {
    if (result.status === 'fulfilled') {
      sourceTargets[index].value = Array.isArray(result.value?.items) ? result.value.items : []
      return
    }
    sourceTargets[index].value = []
    failedSourceCount.value += 1
  })

  loading.value = false
  entryLoading.value = false
}

function buildUnifiedCases() {
  const items = []
  const attachedConsultationAppealIds = new Set()
  const consultationAppealsByReportId = new Map()

  consultationAppeals.value.forEach((appeal) => {
    const reportId = String(appeal?.report_id || '')
    if (reportId) consultationAppealsByReportId.set(reportId, appeal)
  })

  communityReports.value.forEach((report) => {
    const status = String(report?.status || 'pending')
    items.push({
      key: `community-report-${report.id}`,
      kind: report.target_type === 'comment' ? '研圈评论举报' : '研圈帖子举报',
      title: report.target_title || '研圈内容',
      excerpt: report.target_excerpt || '原内容已由平台留档',
      reason: report.reason || '',
      statusLabel: statusText(status),
      statusTone: statusTone(status),
      adminNote: report.admin_note || '',
      resolutionText: actionText(report.moderation_action),
      sortAt: report.handled_at || report.updated_at || report.created_at,
      timeLabel: caseTimeLabel(report.created_at, report.handled_at || report.updated_at),
      canAppeal: false
    })
  })

  communityContentItems.value.forEach((contentItem) => {
    const isVisible = Boolean(contentItem?.is_published)
    const appeal = normalizeCommunityAppeal(contentItem?.appeal)
    items.push({
      key: `community-content-${contentItem.target_type}-${contentItem.target_id}`,
      kind: contentItem.target_type === 'comment' ? '研圈评论处置' : '研圈帖子处置',
      title: contentItem.title || '研圈内容',
      excerpt: contentItem.excerpt || '原内容已由平台留档',
      statusLabel: isVisible ? '已恢复展示' : '已下架',
      statusTone: isVisible ? 'resolved' : 'hidden',
      adminNote: contentItem.moderation_note || '',
      resolutionText: '',
      appeal,
      sortAt: appeal?.handledAt || contentItem.moderated_at || appeal?.createdAt,
      timeLabel: contentItem.moderated_at
        ? `平台处置于 ${formatDateTime(contentItem.moderated_at)}`
        : caseTimeLabel(appeal?.createdAt, appeal?.handledAt),
      canAppeal: !isVisible && !appeal,
      targetType: contentItem.target_type,
      targetId: contentItem.target_id
    })
  })

  consultationReports.value.forEach((report) => {
    const reportId = String(report?.id || '')
    const detailedAppeal = consultationAppealsByReportId.get(reportId)
    const appeal = normalizeConsultationAppeal(detailedAppeal || embeddedConsultationAppeal(report))
    if (appeal?.id) attachedConsultationAppealIds.add(appeal.id)

    const status = String(report?.status || 'pending')
    const isRespondent = report.participation_role === 'respondent'
    items.push({
      key: `consultation-report-${reportId}`,
      kind: isRespondent ? '咨询反馈（对方发起）' : '咨询举报',
      title: report.issue_type || '咨询问题反馈',
      excerpt: report.content || '平台正在核实本次咨询情况',
      respondentContent: report.respondent_content || '',
      statusLabel: statusText(status),
      statusTone: statusTone(status),
      adminNote: report.admin_note || '',
      resolutionText: consultationResolutionText(report.resolution, report.refund_amount),
      appeal,
      sortAt: appeal?.handledAt || report.handled_at || appeal?.createdAt || report.created_at,
      timeLabel: caseTimeLabel(report.created_at, appeal?.handledAt || report.handled_at || appeal?.createdAt),
      canAppeal: false
    })
  })

  consultationAppeals.value.forEach((appealSource) => {
    const appeal = normalizeConsultationAppeal(appealSource)
    if (!appeal || attachedConsultationAppealIds.has(appeal.id)) return
    items.push({
      key: `consultation-appeal-${appeal.id}`,
      kind: '咨询举报申诉',
      title: '咨询案件复核',
      excerpt: '',
      statusLabel: appeal.statusLabel,
      statusTone: appeal.statusTone,
      adminNote: '',
      resolutionText: '',
      appeal,
      sortAt: appeal.handledAt || appeal.createdAt,
      timeLabel: caseTimeLabel(appeal.createdAt, appeal.handledAt),
      canAppeal: false
    })
  })

  return items.sort((left, right) => toTimestamp(right.sortAt) - toTimestamp(left.sortAt))
}

function normalizeCommunityAppeal(appeal) {
  if (!appeal?.id) return null
  const status = String(appeal.status || 'pending')
  return {
    id: String(appeal.id),
    content: appeal.content || '',
    statusLabel: statusText(status),
    statusTone: statusTone(status),
    adminNote: appeal.admin_note || '',
    decisionText: appealResultText(appeal.moderation_action),
    createdAt: appeal.created_at || null,
    handledAt: appeal.handled_at || null
  }
}

function embeddedConsultationAppeal(report = {}) {
  if (!report?.appeal_id) return null
  return {
    id: report.appeal_id,
    content: report.appeal_content,
    status: report.appeal_status,
    decision: report.appeal_decision,
    admin_note: report.appeal_admin_note,
    created_at: report.appeal_created_at,
    handled_at: report.appeal_handled_at
  }
}

function normalizeConsultationAppeal(appeal) {
  if (!appeal?.id) return null
  const status = String(appeal.status || 'pending')
  return {
    id: String(appeal.id),
    content: appeal.content || '已提交复核申请',
    statusLabel: statusText(status),
    statusTone: statusTone(status),
    adminNote: appeal.admin_note || '',
    decisionText: consultationAppealDecisionText(appeal.decision),
    createdAt: appeal.created_at || null,
    handledAt: appeal.handled_at || null
  }
}

function statusText(status) {
  return { pending: '待处理', reviewing: '处理中', resolved: '已处理', dismissed: '已驳回' }[status] || '待处理'
}

function statusTone(status) {
  return { pending: 'pending', reviewing: 'reviewing', resolved: 'resolved', dismissed: 'dismissed' }[status] || 'pending'
}

function actionText(action) {
  return { hide_post: '相关帖子已下架', restore_post: '相关帖子已恢复', hide_comment: '相关评论已下架', restore_comment: '相关评论已恢复' }[action] || ''
}

function appealResultText(action) {
  return { restore_post: '平台已恢复帖子展示', restore_comment: '平台已恢复评论展示', uphold: '平台维持原内容处置' }[action] || ''
}

function consultationResolutionText(resolution, refundAmount) {
  const label = {
    continue_service: '平台建议继续完成咨询服务',
    refund_full: '平台已处理全额退款',
    refund_partial: '平台已处理部分退款',
    close_service: '平台已关闭本次咨询服务',
    warn_participant: '平台已向相关方发出提醒'
  }[resolution] || ''
  const amount = Number(refundAmount || 0)
  return label && amount > 0 ? `${label}（¥${amount.toFixed(2)}）` : label
}

function consultationAppealDecisionText(decision) {
  return { uphold: '平台维持原处理结果', reopen: '平台已重新开启核查' }[decision] || ''
}

function caseTimeLabel(createdAt, updatedAt) {
  if (updatedAt) return `最近更新于 ${formatDateTime(updatedAt)}`
  if (createdAt) return `提交于 ${formatDateTime(createdAt)}`
  return '记录时间待同步'
}

function toTimestamp(value) {
  const timestamp = new Date(value || 0).getTime()
  return Number.isFinite(timestamp) ? timestamp : 0
}

function openAppeal(item) {
  if (!item?.canAppeal) return
  const query = [
    `targetType=${encodeURIComponent(item.targetType)}`,
    `targetId=${encodeURIComponent(item.targetId)}`,
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
  uni.reLaunch({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/circle/community-reports')}` })
}

function goBack() {
  uni.navigateBack({ fail() { uni.reLaunch({ url: '/pages/home/index?tab=profile' }) } })
}
</script>

<style scoped>
.community-reports-page{height:100vh;height:100dvh;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f4f8ff);color:#2b3d59}
.community-reports-refresh{width:60rpx;height:60rpx;margin:0;padding:0;border:0;border-radius:18rpx;background:transparent;color:var(--gyt-primary,#3478f6);display:flex;align-items:center;justify-content:center}
.community-reports-refresh::after,.community-reports-state button::after,.community-case-appeal-button::after{border:0}
.community-reports-scroll{min-height:0;flex:1}
.community-reports-content{padding:24rpx}
.community-reports-state,.community-case-record{padding:25rpx;border:2rpx solid var(--gyt-primary-border,#dce8fa);border-radius:26rpx;background:rgba(255,255,255,.94);box-shadow:0 12rpx 30rpx rgba(43,73,112,.05)}
.community-reports-state{color:#8191a6;text-align:center;font-size:21rpx;line-height:1.55}
.community-reports-state strong,.community-reports-state text{display:block}
.community-reports-state button{margin-top:14rpx;border:0;background:#edf4ff;color:#5275ad;font-size:20rpx}
.community-reports-state.error{color:#bd655c}
.community-case-record{margin-top:18rpx}
.community-case-record-top{display:flex;align-items:flex-start;justify-content:space-between;gap:12rpx}
.community-case-record-top>view{min-width:0;flex:1}
.community-case-kind{display:block;color:var(--gyt-primary,#3478f6);font-size:18rpx;font-weight:850}
.community-case-record-top strong{display:block;margin-top:6rpx;overflow:hidden;color:#2b3d59;font-size:24rpx;text-overflow:ellipsis;white-space:nowrap}
.community-case-status{flex:none;padding:7rpx 10rpx;border-radius:999rpx;background:#fff4dd;color:#aa792e;font-size:18rpx;font-weight:850}
.community-case-status.reviewing{background:#eaf2fc;color:#517aa9}
.community-case-status.resolved{background:#e6f7f1;color:#238b74}
.community-case-status.dismissed{background:#f0eef2;color:#807987}
.community-case-status.hidden{background:#fff0ec;color:#c16b5d}
.community-case-excerpt{margin-top:13rpx;color:#657991;font-size:20rpx;line-height:1.55;white-space:pre-wrap}
.community-case-reason{margin-top:10rpx;color:#788aa0;font-size:19rpx;line-height:1.5}
.community-case-detail,.community-case-appeal{margin-top:16rpx;padding:15rpx;border-radius:17rpx;background:var(--gyt-primary-tint,#f7faff);color:#5f7187}
.community-case-detail text,.community-case-appeal-top>text{display:block;color:#8293aa;font-size:18rpx}
.community-case-detail strong{display:block;margin-top:6rpx;color:#5f7187;font-size:20rpx;line-height:1.5}
.community-case-detail small{display:block;margin-top:8rpx;color:#2c927d;font-size:18rpx;font-weight:800}
.community-case-appeal-top{display:flex;align-items:center;justify-content:space-between;gap:12rpx}
.community-case-appeal-top small{padding:5rpx 9rpx;border-radius:999rpx;background:#fff4dd;color:#aa792e;font-size:17rpx;font-weight:850}
.community-case-appeal-top small.reviewing{background:#eaf2fc;color:#517aa9}
.community-case-appeal-top small.resolved{background:#e6f7f1;color:#238b74}
.community-case-appeal-top small.dismissed{background:#f0eef2;color:#807987}
.community-case-appeal>strong{display:block;margin-top:6rpx;color:#5f7187;font-size:20rpx;line-height:1.5}
.community-case-appeal-note,.community-case-appeal-result{display:block;margin-top:10rpx;font-size:19rpx;line-height:1.5}
.community-case-appeal-result{color:#268b76;font-weight:850}
.community-case-appeal-button{width:100%;height:66rpx;min-height:66rpx;margin-top:16rpx;padding:0;border:0;border-radius:17rpx;background:var(--gyt-primary-gradient,#3478f6);color:#fff;font-size:21rpx;font-weight:850}
.community-case-time{margin-top:16rpx;color:#9aa7b6;font-size:18rpx}
</style>
