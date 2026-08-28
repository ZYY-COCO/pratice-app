<template>
  <view class="mentor-support-page" :style="themeInlineStyle">
    <MentorPageHeader title="平台处理进度" @back="goBack" />

    <scroll-view scroll-y class="mentor-support-scroll">
      <view class="mentor-support-content">
        <view class="mentor-support-intro">
          <strong>咨询问题双方都能查进度</strong>
          <text>平台会关联订单、聊天和双方材料核实；你可查看订单状态、退款记录和问题处理结论。</text>
        </view>

        <view v-if="reportLoadError && !loading && !error" class="mentor-support-state warning">
          <strong>问题反馈记录暂未同步完成</strong>
          <text>{{ reportLoadError }}</text>
          <button @tap="load">重新加载</button>
        </view>

        <view v-if="settlementOrders.length" class="mentor-support-orders">
          <view class="mentor-support-orders-heading">
            <view><strong>订单与退款记录</strong><text>已结束订单的状态与退款信息会在这里保留。</text></view>
            <text>{{ settlementOrders.length }} 笔</text>
          </view>
          <view v-for="order in settlementOrders" :key="order.id" class="mentor-support-order-record">
            <view class="mentor-support-order-top">
              <view>
                <strong>{{ order.consultationType === 'booking' ? '预约咨询' : '即时咨询' }}</strong>
                <text>{{ orderResultCopy(order) }}</text>
              </view>
              <text class="mentor-support-order-status" :class="order.orderStatus">{{ orderStatusText(order.orderStatus) }}</text>
            </view>
            <view v-if="order.refundAmount > 0 || order.paymentStatus === 'refunding' || order.paymentStatus === 'refunded' || (order.paymentStatus === 'failed' && order.refundReference)" class="mentor-support-order-refund">
              <text>{{ refundLabel(order) }}</text>
              <strong>{{ refundStatusText(order) }}</strong>
              <small v-if="order.refundReference">退款编号：{{ order.refundReference }}</small>
            </view>
            <view class="mentor-support-order-time">{{ formatDateTime(order.endedAt || order.createdAt) }}</view>
          </view>
        </view>

        <AppPageLoadingState v-if="loading" message="正在整理平台处理进度..." />
        <view v-else-if="error" class="mentor-support-state error">
          <text>{{ error }}</text>
          <button @tap="load">重新加载</button>
        </view>
        <AppEmptyState
          v-else-if="!reportLoadError && reports.length === 0 && settlementOrders.length === 0"
          label="暂时没有平台介入记录"
          title="暂时没有平台介入记录"
          description="遇到咨询问题时，可从聊天右上角进入“举报此咨询”。"
        />

        <template v-else-if="reports.length">
          <view class="mentor-support-filter" role="tablist" aria-label="处理记录分类">
            <button :class="{ active: activeFilter === 'all' }" @tap="activeFilter = 'all'">全部 {{ reports.length }}</button>
            <button :class="{ active: activeFilter === 'reporter' }" @tap="activeFilter = 'reporter'">我发起 {{ reporterReports.length }}</button>
            <button :class="{ active: activeFilter === 'respondent' }" @tap="activeFilter = 'respondent'">涉及我 {{ respondentReports.length }}</button>
          </view>

          <AppEmptyState
            v-if="filteredReports.length === 0"
            compact
            :label="activeFilter === 'reporter' ? '你暂未发起问题反馈' : '暂时没有涉及你的问题反馈'"
            :title="activeFilter === 'reporter' ? '你暂未发起问题反馈' : '暂时没有涉及你的问题反馈'"
          />

          <view v-for="item in filteredReports" v-else :key="item.id" class="mentor-support-record">
            <view class="mentor-support-record-top">
              <view>
                <text class="mentor-support-role">{{ participationText(item) }}</text>
                <strong>{{ item.issue_type || '咨询问题反馈' }}</strong>
              </view>
              <text class="mentor-support-status" :class="item.status">{{ statusText(item.status) }}</text>
            </view>

            <view class="mentor-support-section">
              <text>{{ item.participation_role === 'respondent' ? '对方反馈说明' : '我提交的反馈说明' }}</text>
              <strong>{{ item.content || '未填写具体说明。' }}</strong>
            </view>

            <view v-if="item.first_response_due_at || item.first_response_at" class="mentor-support-sla" :class="item.sla_status">
              <text>平台处理进度</text>
              <strong>{{ reportSlaText(item) }}</strong>
              <small v-if="item.first_response_due_at">首次响应时限：{{ formatDateTime(item.first_response_due_at) }}</small>
            </view>

            <view v-if="item.participation_role === 'respondent'" class="mentor-support-section response">
              <text>我的处理说明</text>
              <strong v-if="item.respondent_content">{{ item.respondent_content }}</strong>
              <strong v-else class="pending-copy">尚未提交说明</strong>
              <button v-if="item.can_respond" class="mentor-support-response-button" @tap="openResponse(item)">
                {{ item.respondent_content ? '更新说明与凭证' : '提交说明与凭证' }}
              </button>
            </view>
            <view v-else-if="item.respondent_content" class="mentor-support-section response">
              <text>对方处理说明</text>
              <strong>{{ item.respondent_content }}</strong>
            </view>

            <view class="mentor-support-evidence">
              <text>凭证情况</text>
              <strong>反馈方 {{ evidenceCount(item, 'reporter') }} 张 · 回应方 {{ evidenceCount(item, 'respondent') }} 张</strong>
            </view>
            <button v-if="canSupplementEvidence(item)" class="mentor-support-response-button" @tap="openEvidence(item)">
              补充凭证（还可上传 {{ maxEvidenceCount - evidenceCount(item, 'reporter') }} 张）
            </button>

            <view v-if="item.admin_note || item.resolution !== 'none'" class="mentor-support-conclusion">
              <text>平台处理结论</text>
              <strong>{{ item.admin_note || '平台已更新本次处理状态。' }}</strong>
              <view v-if="item.resolution && item.resolution !== 'none'" class="mentor-support-resolution">
                {{ resolutionText(item.resolution) }}
              </view>
              <view v-if="refundAmount(item) > 0" class="mentor-support-refund">
                退款金额：¥{{ formatAmount(refundAmount(item)) }}
              </view>
            </view>

            <view v-if="item.appeal_id" class="mentor-support-section response">
              <text>我的复核进度 · {{ appealStatusText(item.appeal_status, item.appeal_decision) }}</text>
              <strong>{{ item.appeal_content || '已提交复核申请，等待平台核实。' }}</strong>
              <view v-if="item.appeal_first_response_due_at || item.appeal_first_response_at" class="mentor-support-sla appeal" :class="item.appeal_sla_status">
                <text>复核处理时限</text>
                <strong>{{ appealSlaText(item) }}</strong>
                <small v-if="item.appeal_first_response_due_at">首次响应时限：{{ formatDateTime(item.appeal_first_response_due_at) }}</small>
              </view>
              <text v-if="item.appeal_admin_note" class="mentor-support-appeal-note-label">平台复核说明</text>
              <strong v-if="item.appeal_admin_note">{{ item.appeal_admin_note }}</strong>
              <button v-if="canSupplementAppealEvidence(item)" class="mentor-support-response-button" @tap="openAppeal(item)">
                补充复核凭证（还可上传 {{ maxEvidenceCount - appealEvidenceCount(item) }} 张）
              </button>
            </view>
            <button v-else-if="canAppeal(item)" class="mentor-support-response-button" @tap="openAppeal(item)">申请复核</button>

            <view class="mentor-support-time">
              {{ item.participation_role === 'respondent' ? '对方提交于' : '提交于' }} {{ formatDateTime(item.created_at) }}
              <text v-if="item.responded_at"> · 回应于 {{ formatDateTime(item.responded_at) }}</text>
              <text v-else-if="item.handled_at"> · 更新于 {{ formatDateTime(item.handled_at) }}</text>
            </view>
          </view>
        </template>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import {
  fetchMyMentorConsultationOrders,
  fetchMyReceivedMentorOrders,
  fetchMyMentorConsultationReports
} from '../../api/mentorConsultation'
import { normalizeMentorConsultationOrder } from '../../data/mentorConsultation'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const reports = ref([])
const orderHistory = ref([])
const loading = ref(false)
const error = ref('')
const reportLoadError = ref('')
const activeFilter = ref('all')
const maxEvidenceCount = 3
const themeKey = ref(getStoredThemeKey())
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))
const reporterReports = computed(() => reports.value.filter((item) => participationRole(item) === 'reporter'))
const respondentReports = computed(() => reports.value.filter((item) => participationRole(item) === 'respondent'))
const filteredReports = computed(() => {
  if (activeFilter.value === 'reporter') return reporterReports.value
  if (activeFilter.value === 'respondent') return respondentReports.value
  return reports.value
})
const settlementOrders = computed(() => orderHistory.value.filter((order) => (
  ['completed', 'rejected', 'timeout', 'refunded', 'cancelled'].includes(order.orderStatus)
)))

onShow(() => {
  themeKey.value = getStoredThemeKey()
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  void load()
})

async function load() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  reportLoadError.value = ''
  try {
    const [reportResult, applicantOrderResult, receivedOrderResult] = await Promise.allSettled([
      fetchMyMentorConsultationReports({ limit: 100 }),
      fetchMyMentorConsultationOrders({ limit: 100 }),
      fetchMyReceivedMentorOrders({ limit: 100 })
    ])
    const reportsLoaded = reportResult.status === 'fulfilled'
    reports.value = reportsLoaded && Array.isArray(reportResult.value?.items)
      ? reportResult.value.items
      : []
    if (!reportsLoaded) {
      reportLoadError.value = reportResult.reason?.detail || '暂时无法读取问题反馈记录。请重新加载，避免遗漏平台处理结果。'
    }
    const orderHistoryById = new Map()
    const orderResults = [applicantOrderResult, receivedOrderResult]
    orderResults.forEach((result) => {
      if (result.status !== 'fulfilled' || !Array.isArray(result.value?.items)) return
      result.value.items
        .map((order) => normalizeMentorConsultationOrder(order))
        .filter((order) => order.id)
        .forEach((order) => orderHistoryById.set(order.id, order))
    })
    orderHistory.value = [...orderHistoryById.values()]
      .sort((left, right) => String(right.createdAt || '').localeCompare(String(left.createdAt || '')))
    if (reportResult.status !== 'fulfilled' && applicantOrderResult.status !== 'fulfilled' && receivedOrderResult.status !== 'fulfilled') {
      error.value = reportResult.reason?.detail || applicantOrderResult.reason?.detail || receivedOrderResult.reason?.detail || '处理记录读取失败，请稍后重试'
    }
  } catch (requestError) {
    error.value = requestError?.detail || '处理记录读取失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function participationRole(item = {}) {
  return item.participation_role === 'respondent' ? 'respondent' : 'reporter'
}

function participationText(item = {}) {
  return participationRole(item) === 'respondent' ? '涉及我的问题反馈' : '我发起的问题反馈'
}

function statusText(status) {
  return { pending: '待处理', reviewing: '处理中', resolved: '已处理', dismissed: '已结案' }[status] || '待处理'
}

function resolutionText(resolution) {
  return {
    continue_service: '平台建议继续在站内完成咨询',
    refund_full: '平台已提交全额退款处理',
    refund_partial: '平台已提交部分退款并结束服务',
    close_service: '平台已结束本次咨询服务',
    warn_participant: '平台已提醒相关参与方',
    hide_review: '平台已暂时下架关联服务评价',
    restore_review: '平台已恢复关联服务评价'
  }[resolution] || ''
}

function appealStatusText(status, decision) {
  if (status === 'resolved' && decision === 'reopen') return '已受理，原案复核中'
  return { pending: '待受理', reviewing: '复核中', resolved: '复核已完成', dismissed: '维持原结论' }[status] || '待受理'
}

function reportSlaText(item = {}) {
  return caseSlaText({
    status: item.status,
    slaStatus: item.sla_status,
    dueAt: item.first_response_due_at,
    firstResponseAt: item.first_response_at,
    priority: item.priority,
    escalationLevel: item.escalation_level
  }, '问题反馈')
}

function appealSlaText(item = {}) {
  return caseSlaText({
    status: item.appeal_status,
    slaStatus: item.appeal_sla_status,
    dueAt: item.appeal_first_response_due_at,
    firstResponseAt: item.appeal_first_response_at,
    priority: item.appeal_priority,
    escalationLevel: item.appeal_escalation_level
  }, '复核申请')
}

function caseSlaText(caseItem = {}, label) {
  const dueText = caseItem.dueAt ? formatDateTime(caseItem.dueAt) : ''
  if (caseItem.firstResponseAt) return `平台已于 ${formatDateTime(caseItem.firstResponseAt)} 首次响应，正在同步后续处理进度。`
  if (caseItem.slaStatus === 'overdue') {
    return Number(caseItem.escalationLevel || 0) > 0
      ? `${label}首次响应已超时，平台已升级为优先处理。`
      : `${label}正在加急核实，请留意平台处理通知。`
  }
  if (caseItem.slaStatus === 'due_soon') return `平台将最迟在 ${dueText} 前首次响应。`
  if (caseItem.priority === 'urgent') return `平台已将本案列为优先处理，最迟在 ${dueText} 前首次响应。`
  return dueText ? `平台已受理，最迟在 ${dueText} 前首次响应。` : '平台已受理，正在核实中。'
}

function evidenceCount(item = {}, role) {
  return Math.max(0, Number(role === 'respondent' ? item.respondent_evidence_count : item.reporter_evidence_count) || 0)
}

function refundAmount(item = {}) {
  return Math.max(0, Number(item.refund_amount ?? item.refundAmount ?? 0) || 0)
}

function refundLabel(order = {}) {
  if (order.paymentStatus === 'refunding') return '退款进度'
  if (order.paymentStatus === 'failed' && order.refundReference) return '退款异常'
  return '退款结果'
}

function refundStatusText(order = {}) {
  const amount = Number(order.refundAmount) || 0
  const amountText = amount > 0 ? `¥${formatAmount(amount)}` : '本次订单无需退款'
  if (order.paymentStatus === 'refunding') return `${amountText} · 处理中`
  if (order.paymentStatus === 'failed' && order.refundReference) return `${amountText} · 平台跟进中`
  return amountText
}

function orderStatusText(status) {
  return {
    completed: '已完成',
    rejected: '未接单',
    timeout: '已超时',
    refunded: '已退款',
    cancelled: '已取消'
  }[status] || '已结束'
}

function orderResultCopy(order = {}) {
  const refunded = order.paymentStatus === 'refunded'
  const refunding = order.paymentStatus === 'refunding'
  const refundFailed = order.paymentStatus === 'failed' && Boolean(order.refundReference)
  const refundCopy = refunded ? '退款已完成并将原路退回。' : refunding ? '平台已提交退款处理，完成后会自动同步。' : refundFailed ? '退款出现异常，平台正在继续跟进。' : '订单已自动关闭。'
  if (order.orderStatus === 'timeout') {
    const startTimedOut = Boolean(order.acceptedAt) && !order.startedAt
    const cause = startTimedOut ? '前辈已接单但未按时开始服务' : '服务未按时开始'
    return `${cause}，${refunded || refunding || refundFailed ? refundCopy : '订单已自动关闭。'}`
  }
  if (order.orderStatus === 'rejected') return `前辈未接单，${refunded || refunding || refundFailed ? refundCopy : '订单已关闭。'}`
  if (order.orderStatus === 'cancelled') return refunded || refunding || refundFailed ? `订单已取消，${refundCopy}` : '订单已取消。'
  if (order.orderStatus === 'refunded') return refunded ? '平台已处理本次退款。' : refunding ? '平台已提交本次退款处理。' : refundFailed ? '本次退款需要平台继续跟进。' : '本次退款正在等待支付渠道确认。'
  return '本次咨询已结束，聊天记录会继续保留。'
}

function appealEvidenceCount(item = {}) {
  return Math.max(0, Number(item.appeal_evidence_count) || 0)
}

function formatAmount(value) {
  return Number(value || 0).toFixed(2)
}

function formatDateTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '刚刚'
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function openResponse(item) {
  if (!item?.id || !item?.can_respond) return
  uni.navigateTo({ url: `/pages-sub-consultation/consultation/mentor-response?reportId=${encodeURIComponent(item.id)}` })
}

function canSupplementEvidence(item = {}) {
  return participationRole(item) === 'reporter'
    && ['pending', 'reviewing'].includes(String(item.status || ''))
    && evidenceCount(item, 'reporter') < maxEvidenceCount
}

function openEvidence(item) {
  if (!item?.id || !canSupplementEvidence(item)) return
  uni.navigateTo({ url: `/pages-sub-consultation/consultation/mentor-response?reportId=${encodeURIComponent(item.id)}&mode=evidence` })
}

function canAppeal(item = {}) {
  return Boolean(item.can_appeal)
}

function canSupplementAppealEvidence(item = {}) {
  return Boolean(item.appeal_id)
    && ['pending', 'reviewing'].includes(String(item.appeal_status || ''))
    && appealEvidenceCount(item) < maxEvidenceCount
}

function openAppeal(item) {
  if (!item?.id || (!canAppeal(item) && !item.appeal_id)) return
  uni.navigateTo({ url: `/pages-sub-consultation/consultation/mentor-appeal?reportId=${encodeURIComponent(item.id)}` })
}

function goLogin() {
  uni.reLaunch({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages-sub-consultation/consultation/mentor-support')}` })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=circle&section=community&communityTab=mentor' })
    }
  })
}
</script>

<style scoped>
.mentor-support-page{height:100vh;height:100dvh;overflow:hidden;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f4f8ff);color:#2d405d}.mentor-support-scroll{min-height:0;flex:1}.mentor-support-content{padding:24rpx}.mentor-support-intro,.mentor-support-orders,.mentor-support-record,.mentor-support-state{padding:26rpx;border:2rpx solid var(--gyt-primary-border,#d9e7fc);border-radius:27rpx;background:var(--gyt-panel-bg,#fff);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-support-intro strong,.mentor-support-intro text{display:block}.mentor-support-intro strong{font-size:27rpx;line-height:1.3;font-weight:900}.mentor-support-intro text{margin-top:8rpx;color:#8293aa;font-size:20rpx;line-height:1.55;font-weight:650}.mentor-support-orders{margin-top:18rpx}.mentor-support-orders-heading,.mentor-support-order-top{display:flex;align-items:flex-start;justify-content:space-between;gap:14rpx}.mentor-support-orders-heading>view,.mentor-support-order-top>view{min-width:0;flex:1}.mentor-support-orders-heading strong,.mentor-support-orders-heading text,.mentor-support-order-top strong,.mentor-support-order-top text{display:block}.mentor-support-orders-heading strong{font-size:25rpx;line-height:1.35}.mentor-support-orders-heading text,.mentor-support-order-top text{margin-top:6rpx;color:#8293aa;font-size:18rpx;line-height:1.5}.mentor-support-orders-heading>text{padding:7rpx 11rpx;border-radius:999rpx;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-size:18rpx;font-weight:850}.mentor-support-order-record{margin-top:16rpx;padding:17rpx;border:2rpx solid var(--gyt-primary-border,#e4edf9);border-radius:20rpx;background:var(--gyt-primary-tint,#fbfdff)}.mentor-support-order-top strong{font-size:22rpx;line-height:1.35}.mentor-support-order-status{flex:none;padding:7rpx 11rpx;border-radius:999rpx;background:#f0eef2;color:#807987;font-size:18rpx;font-weight:850}.mentor-support-order-status.completed{background:#e6f7f1;color:#238b74}.mentor-support-order-status.timeout,.mentor-support-order-status.rejected{background:#fff4dd;color:#aa792e}.mentor-support-order-status.refunded,.mentor-support-order-status.cancelled{background:#fff0ec;color:#bf695c}.mentor-support-order-refund{display:grid;grid-template-columns:auto 1fr;gap:5rpx 12rpx;align-items:baseline;margin-top:14rpx;padding:13rpx;border-radius:16rpx;background:#fff7eb}.mentor-support-order-refund text{color:#9d7a43;font-size:18rpx}.mentor-support-order-refund strong{color:#a46d2b;font-size:21rpx}.mentor-support-order-refund small{grid-column:1/-1;color:#9b8a6d;font-size:17rpx}.mentor-support-order-time{margin-top:14rpx;color:#9aa7b6;font-size:18rpx}.mentor-support-state{margin-top:18rpx;color:#8191a6;text-align:center;font-size:21rpx;line-height:1.55}.mentor-support-state.compact{padding:28rpx}.mentor-support-state strong,.mentor-support-state text{display:block}.mentor-support-state button{margin-top:14rpx;border:0;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-size:20rpx}.mentor-support-state button::after{border:0}.mentor-support-state.error{color:#bd655c}.mentor-support-filter{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10rpx;margin-top:18rpx;padding:8rpx;border:2rpx solid var(--gyt-primary-border,#dce8f8);border-radius:20rpx;background:var(--gyt-primary-tint,#f7faff)}.mentor-support-filter button{min-width:0;height:58rpx;margin:0;padding:0 8rpx;border:0;border-radius:14rpx;background:transparent;color:#7d8fa8;font-size:18rpx;font-weight:800;white-space:nowrap}.mentor-support-filter button.active{background:var(--gyt-panel-bg,#fff);color:var(--gyt-primary,#3478f6);box-shadow:0 4rpx 13rpx rgba(52,120,246,.11)}.mentor-support-filter button::after{border:0}.mentor-support-record{margin-top:18rpx}.mentor-support-record-top{display:flex;align-items:flex-start;justify-content:space-between;gap:14rpx}.mentor-support-record-top>view{min-width:0;flex:1}.mentor-support-role{display:block;color:var(--gyt-primary,#3478f6);font-size:18rpx;font-weight:850}.mentor-support-record-top strong{display:block;margin-top:6rpx;overflow:hidden;font-size:25rpx;line-height:1.35;text-overflow:ellipsis;white-space:nowrap}.mentor-support-status{flex:none;padding:7rpx 11rpx;border-radius:999rpx;background:#fff4dd;color:#aa792e;font-size:18rpx;font-weight:850}.mentor-support-status.reviewing{background:#eaf2fc;color:#517aa9}.mentor-support-status.resolved{background:#e6f7f1;color:#238b74}.mentor-support-status.dismissed{background:#f0eef2;color:#807987}.mentor-support-section{margin-top:17rpx;padding:16rpx;border-radius:18rpx;background:var(--gyt-primary-tint,#f7faff);color:#5f7187}.mentor-support-section text,.mentor-support-section strong{display:block}.mentor-support-section text{color:#8293aa;font-size:18rpx}.mentor-support-section strong{margin-top:7rpx;font-size:20rpx;line-height:1.55;font-weight:650;white-space:pre-wrap}.mentor-support-section.response{background:#f4fbf8}.mentor-support-section .pending-copy{color:#9a8b70}.mentor-support-response-button{width:100%;height:62rpx;min-height:62rpx;margin:16rpx 0 0;padding:0;border:0;border-radius:16rpx;background:var(--gyt-primary-gradient,#3478f6);color:#fff;display:flex;align-items:center;justify-content:center;font-size:20rpx;line-height:1;font-weight:850}.mentor-support-response-button::after{border:0}.mentor-support-evidence{display:flex;align-items:center;justify-content:space-between;gap:14rpx;margin-top:15rpx;padding:0 3rpx}.mentor-support-evidence text{color:#8a9aad;font-size:18rpx}.mentor-support-evidence strong{color:#6c7e94;font-size:18rpx;font-weight:750}.mentor-support-conclusion{margin-top:17rpx;padding:16rpx;border-radius:18rpx;background:var(--gyt-primary-tint,#f7faff);color:#5f7187}.mentor-support-conclusion text,.mentor-support-conclusion strong{display:block}.mentor-support-conclusion text{color:#8293aa;font-size:18rpx}.mentor-support-conclusion strong{margin-top:7rpx;font-size:20rpx;line-height:1.55}.mentor-support-resolution,.mentor-support-refund{margin-top:10rpx;color:#238b74;font-size:19rpx;line-height:1.4;font-weight:850}.mentor-support-refund{color:#ad7433}.mentor-support-time{margin-top:17rpx;color:#9aa7b6;font-size:18rpx;line-height:1.4}
.mentor-support-sla{margin-top:17rpx;padding:16rpx;border:2rpx solid #dce8f8;border-radius:18rpx;background:#f7faff}.mentor-support-sla text,.mentor-support-sla strong,.mentor-support-sla small{display:block}.mentor-support-sla text{color:#6e87a6;font-size:18rpx;font-weight:800}.mentor-support-sla strong{margin-top:7rpx;color:#536d8b;font-size:20rpx;line-height:1.5}.mentor-support-sla small{margin-top:7rpx;color:#8a9aad;font-size:17rpx}.mentor-support-sla.due_soon{border-color:#efd7a6;background:#fffaf0}.mentor-support-sla.due_soon text,.mentor-support-sla.due_soon strong{color:#98712c}.mentor-support-sla.overdue{border-color:#efc0b5;background:#fff7f4}.mentor-support-sla.overdue text,.mentor-support-sla.overdue strong{color:#b85f54}.mentor-support-sla.responded{border-color:#bde8dc;background:#f3fbf8}.mentor-support-sla.responded text,.mentor-support-sla.responded strong{color:#237f6d}.mentor-support-sla.appeal{margin-top:15rpx}.mentor-support-state.warning{border-color:#efdaad;background:#fffaf0;color:#9c7a37}.mentor-support-state.warning strong{color:#966d20}
</style>
