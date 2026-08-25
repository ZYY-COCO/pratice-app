<template>
  <view class="mentor-appeal-admin-page" :class="{ 'is-compact': compact }">
    <view v-if="!compact" class="appeal-summary-grid">
      <view class="appeal-summary-card"><text>全部复核</text><strong>{{ appealCount }}</strong><small>咨询争议二次处理记录</small></view>
      <view class="appeal-summary-card pending"><text>待受理</text><strong>{{ pendingCount }}</strong><small>需要平台首次核实</small></view>
      <view class="appeal-summary-card reviewing"><text>复核中</text><strong>{{ reviewingCount }}</strong><small>已进入二次核验</small></view>
      <view class="appeal-summary-card closed"><text>已结案</text><strong>{{ closedCount }}</strong><small>已保留复核说明</small></view>
    </view>

    <view class="appeal-workspace">
      <view class="appeal-toolbar">
        <view class="appeal-search"><text>⌕</text><input v-model.trim="filters.keyword" placeholder="搜索复核说明" @confirm="applyFilters" /><button v-if="filters.keyword" @tap="clearSearch">×</button></view>
        <AdminSelect class="appeal-select" :options="statusOptions.map((item) => item.label)" :value-index="statusIndex" aria-label="复核状态筛选" @change="changeStatus" />
        <AdminSelect class="appeal-select" :options="slaOptions.map((item) => item.label)" :value-index="slaIndex" aria-label="复核首响时限" @change="changeSla" />
        <AdminSelect class="appeal-select" :options="priorityFilterOptions.map((item) => item.label)" :value-index="priorityFilterIndex" aria-label="复核优先级" @change="changePriorityFilter" />
        <button class="appeal-refresh" :disabled="loading" @tap="refresh">{{ loading ? '刷新中…' : '刷新' }}</button>
      </view>

      <view class="appeal-table-wrap"><view class="appeal-table">
        <view class="appeal-grid table-head"><view>原问题反馈</view><view>申请人</view><view>复核说明</view><view>凭证</view><view>首响时限</view><view>提交时间</view><view>状态</view><view>操作</view></view>
        <view v-if="loading" class="table-state">正在读取咨询复核申请…</view>
        <view v-else-if="loadError" class="table-state error"><text>复核申请加载失败，请检查网络或权限。</text><button @tap="refresh">重新加载</button></view>
        <view v-else-if="appeals.length === 0" class="table-state">当前筛选下没有复核申请</view>
        <view v-for="appeal in appeals" v-else :key="appeal.id" class="appeal-grid table-row" @tap="openAppeal(appeal)">
          <view class="report-cell"><strong>{{ appeal.report?.issue_type || '咨询问题反馈' }}</strong><small>{{ reportStatusText(appeal.report?.status) }} · {{ resolutionText(appeal.report?.resolution) }}</small></view>
          <view><strong>{{ appeal.appellant?.display_name || '参与方' }}</strong><small>{{ appealRoleText(appeal) }}</small></view>
          <view class="appeal-copy">{{ appeal.content }}</view>
          <view><text class="evidence-pill">{{ appeal.evidence_count || 0 }} 张</text></view>
          <view><text class="sla-pill" :class="appeal.sla_status">{{ appealSlaLabel(appeal) }}</text><small>{{ priorityText(appeal.priority) }}</small></view>
          <view><small>{{ formatDateTime(appeal.created_at) }}</small></view>
          <view><text class="status-pill" :class="appeal.status">{{ appealStatusText(appeal.status) }}</text></view>
          <view><button class="open-button">处理</button></view>
        </view>
      </view></view>

      <view class="appeal-pagination"><view>共 {{ appealCount }} 条，每页 {{ pageSize }} 条</view><view><button :disabled="page <= 1 || loading" @tap="changePage(page - 1)">‹</button><text>{{ page }} / {{ totalPages }}</text><button :disabled="page >= totalPages || loading" @tap="changePage(page + 1)">›</button></view></view>
    </view>

    <view v-if="detailVisible" class="appeal-backdrop" @tap="closeDetail"><view class="appeal-detail" @tap.stop>
      <view class="appeal-detail-head"><view><text>咨询复核</text><strong>{{ detail?.appeal?.report?.issue_type || '问题反馈复核' }}</strong></view><button class="admin-modal-close" :disabled="saving" @tap="closeDetail">×</button></view>
      <scroll-view scroll-y class="appeal-detail-scroll"><view class="appeal-detail-content">
        <view v-if="detailLoading" class="detail-state">正在读取完整处理链路…</view>
        <template v-else-if="detail">
          <view class="appeal-party"><view class="appeal-avatar">{{ initial(detail.appeal?.appellant?.display_name) }}</view><view><text>复核申请人 · {{ appealRoleText(detail.appeal) }}</text><strong>{{ detail.appeal?.appellant?.display_name || '参与方' }}</strong><small>{{ detail.appeal?.order_no || '咨询订单' }}</small></view><text class="status-pill" :class="detail.appeal?.status">{{ appealStatusText(detail.appeal?.status) }}</text></view>

          <view class="detail-heading">复核说明</view>
          <view class="detail-box">{{ detail.appeal?.content || '—' }}</view>

          <view class="detail-heading">首响与优先级</view>
          <view class="detail-sla"><view><text>首次响应时限</text><strong>{{ formatDateTime(detail.appeal?.first_response_due_at) }}</strong></view><view><text>首次响应</text><strong>{{ detail.appeal?.first_response_at ? formatDateTime(detail.appeal.first_response_at) : appealSlaLabel(detail.appeal) }}</strong></view><view><text>当前优先级</text><strong>{{ priorityText(detail.appeal?.priority) }}</strong></view></view>

          <view class="detail-heading">原问题反馈与处理结果</view>
          <view class="detail-box"><strong>{{ detail.report?.issue_type || '咨询问题反馈' }}</strong><text>{{ detail.report?.content || '—' }}</text><text v-if="detail.report?.respondent_content" class="detail-subtitle">被反馈方说明</text><text v-if="detail.report?.respondent_content">{{ detail.report.respondent_content }}</text><text v-if="detail.report?.admin_note" class="detail-subtitle">原平台处理说明</text><text v-if="detail.report?.admin_note">{{ detail.report.admin_note }}</text></view>

          <view class="detail-heading">复核补充凭证（{{ detail.evidence?.length || 0 }}）</view>
          <view v-if="detail.evidence?.length" class="evidence-grid"><image v-for="item in detail.evidence" :key="item.id" :src="item.file_url" mode="aspectFill" @tap="previewImage(item.file_url, detail.evidence)" /></view><view v-else class="detail-empty">申请人未补充图片凭证</view>

          <view class="detail-heading">原案双方凭证（{{ detail.report_evidence?.length || 0 }}）</view>
          <view v-if="detail.report_evidence?.length" class="evidence-grid"><view v-for="item in detail.report_evidence" :key="item.id" class="evidence-item"><image :src="item.file_url" mode="aspectFill" @tap="previewImage(item.file_url, detail.report_evidence)" /><text>{{ item.submitter_role === 'respondent' ? '回应方' : '反馈方' }}</text></view></view><view v-else class="detail-empty">原案未上传图片凭证</view>

          <view class="detail-heading">聊天与订单事件</view>
          <view class="audit-list"><view v-for="message in detail.messages" :key="message.id" class="audit-row"><text>{{ message.sender_role === 'mentor' ? '认证前辈' : message.sender_role === 'applicant' ? '咨询用户' : '平台' }}</text><strong>{{ messageText(message) }}</strong><small>{{ formatDateTime(message.created_at) }}</small></view><view v-for="event in detail.events" :key="`event-${event.id}`" class="audit-row event"><text>{{ eventLabel(event) }}</text><strong>{{ eventDetail(event) }}</strong><small>{{ formatDateTime(event.created_at) }}</small></view></view>

          <view class="appeal-review">
            <view class="review-grid"><view><text>复核状态</text><AdminSelect :options="detailStatusOptions.map((item) => item.label)" :value-index="detailStatusIndex" aria-label="复核处理状态" @change="selectDetailStatus" /></view><view><text>复核优先级</text><AdminSelect :options="priorityOptions.map((item) => item.label)" :value-index="detailPriorityIndex" aria-label="复核优先级" @change="selectDetailPriority" /></view><view><text>复核结论</text><AdminSelect :options="decisionOptions.map((item) => item.label)" :value-index="decisionIndex" aria-label="复核结论" @change="selectDecision" /></view></view>
            <view class="note-field"><text>平台复核说明</text><textarea v-model.trim="adminNote" maxlength="1000" placeholder="写明核验依据、处理结论和双方下一步。" /></view>
            <view class="review-actions"><button :disabled="saving" @tap="saveDecision">{{ saving ? '保存中…' : '保存复核结果' }}</button></view>
          </view>
        </template>
      </view></scroll-view>
    </view></view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import {
  fetchAdminMentorConsultationReportAppeal,
  fetchAdminMentorConsultationReportAppeals,
  updateAdminMentorConsultationReportAppealStatus
} from '../api/admin'
import AdminSelect from './AdminSelect.vue'

const props = defineProps({ preview: Boolean, compact: Boolean })
const pageSize = 20
const appeals = ref([])
const appealCount = ref(0)
const page = ref(1)
const loading = ref(false)
const loadError = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref(null)
const saving = ref(false)
const adminNote = ref('')
const detailStatus = ref('pending')
const detailPriority = ref('normal')
const detailDecision = ref('none')
const filters = reactive({ keyword: '', status: '', priority: '', sla_state: '' })

const statusOptions = [{ label: '全部复核状态', value: '' }, { label: '待受理', value: 'pending' }, { label: '复核中', value: 'reviewing' }, { label: '已受理', value: 'resolved' }, { label: '维持原结论', value: 'dismissed' }]
const slaOptions = [{ label: '全部首响时限', value: '' }, { label: '已超时', value: 'overdue' }, { label: '临近超时', value: 'due_soon' }, { label: '已升级', value: 'escalated' }]
const priorityFilterOptions = [{ label: '全部优先级', value: '' }, { label: '普通', value: 'normal' }, { label: '高', value: 'high' }, { label: '紧急', value: 'urgent' }]
const priorityOptions = [{ label: '普通', value: 'normal' }, { label: '高', value: 'high' }, { label: '紧急', value: 'urgent' }]
const detailStatusOptions = statusOptions.slice(1)
const decisionOptions = [{ label: '仅更新进度', value: 'none' }, { label: '维持原结论', value: 'uphold' }, { label: '重新开启原案', value: 'reopen' }]
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex((item) => item.value === filters.status)))
const slaIndex = computed(() => Math.max(0, slaOptions.findIndex((item) => item.value === filters.sla_state)))
const priorityFilterIndex = computed(() => Math.max(0, priorityFilterOptions.findIndex((item) => item.value === filters.priority)))
const detailStatusIndex = computed(() => Math.max(0, detailStatusOptions.findIndex((item) => item.value === detailStatus.value)))
const detailPriorityIndex = computed(() => Math.max(0, priorityOptions.findIndex((item) => item.value === detailPriority.value)))
const decisionIndex = computed(() => Math.max(0, decisionOptions.findIndex((item) => item.value === detailDecision.value)))
const totalPages = computed(() => Math.max(1, Math.ceil(appealCount.value / pageSize)))
const pendingCount = computed(() => appeals.value.filter((item) => item.status === 'pending').length)
const reviewingCount = computed(() => appeals.value.filter((item) => item.status === 'reviewing').length)
const closedCount = computed(() => appeals.value.filter((item) => ['resolved', 'dismissed'].includes(item.status)).length)

refresh()
defineExpose({ refresh })

async function refresh() {
  loading.value = true
  loadError.value = false
  try {
    const response = props.preview ? previewPage() : await fetchAdminMentorConsultationReportAppeals({ ...filters, limit: pageSize, offset: (page.value - 1) * pageSize })
    appeals.value = Array.isArray(response?.items) ? response.items : []
    appealCount.value = Number(response?.count || 0)
    if (appealCount.value > 0 && appeals.value.length === 0 && page.value > totalPages.value) { page.value = totalPages.value; await refresh() }
  } catch (error) {
    appeals.value = []
    appealCount.value = 0
    loadError.value = true
  } finally { loading.value = false }
}

function applyFilters() { page.value = 1; refresh() }
function clearSearch() { filters.keyword = ''; applyFilters() }
function changeStatus(event) { filters.status = statusOptions[Number(event?.detail?.value || 0)]?.value || ''; applyFilters() }
function changeSla(event) { filters.sla_state = slaOptions[Number(event?.detail?.value || 0)]?.value || ''; applyFilters() }
function changePriorityFilter(event) { filters.priority = priorityFilterOptions[Number(event?.detail?.value || 0)]?.value || ''; applyFilters() }
function changePage(value) { const next = Math.max(1, Math.min(totalPages.value, Number(value) || 1)); if (next !== page.value) { page.value = next; refresh() } }

async function openAppeal(item) {
  if (!item?.id || detailLoading.value) return
  detailVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = props.preview ? previewDetail(item) : await fetchAdminMentorConsultationReportAppeal(item.id)
    detailStatus.value = detail.value?.appeal?.status || 'pending'
    detailPriority.value = detail.value?.appeal?.priority || 'normal'
    detailDecision.value = detail.value?.appeal?.decision || 'none'
    adminNote.value = detail.value?.appeal?.admin_note || ''
  } catch (error) {
    uni.showToast({ title: error?.detail || '复核详情加载失败', icon: 'none' })
    detailVisible.value = false
  } finally { detailLoading.value = false }
}

function closeDetail() {
  if (saving.value) return
  detailVisible.value = false
  detail.value = null
  adminNote.value = ''
  detailPriority.value = 'normal'
  detailDecision.value = 'none'
}

function selectDetailStatus(event) { detailStatus.value = detailStatusOptions[Number(event?.detail?.value || 0)]?.value || 'pending' }
function selectDetailPriority(event) { detailPriority.value = priorityOptions[Number(event?.detail?.value || 0)]?.value || 'normal' }
function selectDecision(event) { detailDecision.value = decisionOptions[Number(event?.detail?.value || 0)]?.value || 'none' }

async function saveDecision() {
  const appeal = detail.value?.appeal
  if (!appeal?.id || saving.value) return
  if (['resolved', 'dismissed'].includes(detailStatus.value) && !adminNote.value.trim()) { uni.showToast({ title: '结案时请填写复核处理说明', icon: 'none' }); return }
  if (detailDecision.value !== 'none' && !['resolved', 'dismissed'].includes(detailStatus.value)) { uni.showToast({ title: '执行复核结论时请同步将复核申请结案', icon: 'none' }); return }
  if (detailDecision.value === 'reopen' && detailStatus.value !== 'resolved') { uni.showToast({ title: '重新开启原案时请标记为已受理', icon: 'none' }); return }
  if (detailDecision.value === 'uphold' && detailStatus.value !== 'dismissed') { uni.showToast({ title: '维持原结论时请标记为已驳回', icon: 'none' }); return }
  const confirmed = await confirmDecision('保存复核处理结果？', detailDecision.value === 'reopen' ? '原问题反馈会重新进入处理中，双方可继续补充材料。' : '平台复核说明会同步给申请人并保留审计记录。', '确认保存')
  if (!confirmed) return
  saving.value = true
  try {
    const updated = props.preview ? { ...appeal, status: detailStatus.value, priority: detailPriority.value, decision: detailDecision.value, admin_note: adminNote.value || null, first_response_at: appeal.first_response_at || (detailStatus.value === 'pending' ? null : new Date().toISOString()), handled_at: ['resolved', 'dismissed'].includes(detailStatus.value) ? new Date().toISOString() : null } : await updateAdminMentorConsultationReportAppealStatus(appeal.id, { status: detailStatus.value, priority: detailPriority.value, decision: detailDecision.value, admin_note: adminNote.value || null })
    appeals.value = appeals.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    detail.value = { ...detail.value, appeal: { ...appeal, ...updated }, report: detailDecision.value === 'reopen' ? { ...detail.value.report, status: 'reviewing', resolution: 'none', admin_note: '平台已受理复核申请，原处理结果正在重新核实。' } : detail.value.report }
    uni.showToast({ title: '复核处理结果已保存', icon: 'success' })
  } catch (error) { uni.showToast({ title: error?.detail || '复核处理结果保存失败', icon: 'none' }) } finally { saving.value = false }
}

function confirmDecision(title, content, confirmText) { return new Promise((resolve) => uni.showModal({ title, content, confirmText, success: (result) => resolve(Boolean(result.confirm)) })) }
function appealStatusText(status) { return { pending: '待受理', reviewing: '复核中', resolved: '已受理', dismissed: '维持原结论' }[status] || '待受理' }
function priorityText(priority) { return { normal: '普通', high: '高优先级', urgent: '紧急' }[priority] || '普通' }
function appealSlaLabel(appeal = {}) { if (appeal.first_response_at) return '已首响'; if (appeal.sla_status === 'overdue') return Number(appeal.escalation_level || 0) > 0 ? '超时已升级' : '首响超时'; if (appeal.sla_status === 'due_soon') return '临近超时'; return appeal.first_response_due_at ? '等待首响' : '未设时限' }
function reportStatusText(status) { return { pending: '待处理', reviewing: '处理中', resolved: '已处理', dismissed: '已驳回' }[status] || '待处理' }
function resolutionText(resolution) { return { continue_service: '继续服务', refund_full: '全额退款', refund_partial: '部分退款', close_service: '结束服务', warn_participant: '已提醒', hide_review: '已下架关联评价', restore_review: '已恢复关联评价', none: '未执行裁决' }[resolution] || '未执行裁决' }
function appealRoleText(appeal = {}) { return appeal.appellant_role === 'respondent' ? '被反馈方' : '反馈方' }
function initial(value) { return String(value || '复').slice(0, 1) || '复' }
function formatDateTime(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date) }
function messageText(item) { return item?.content || ({ image: '图片消息', voice: '语音消息', system: '系统消息' }[item?.message_type] || '消息') }
function eventText(event) { return { consultation_order_created: '创建咨询订单', consultation_payment_intent_created: '创建支付订单', consultation_mock_payment_recorded: '已记录历史模拟支付', consultation_demo_payment_recorded: '已记录测试支付', consultation_payment_confirmed: '支付回调确认成功', consultation_payment_failed: '支付回调确认失败', consultation_refund_requested: '已提交退款处理', consultation_refund_completed: '退款回调确认完成', consultation_refund_failed: '退款回调返回异常', mentor_order_decision: '前辈处理接单', consultation_started: '咨询已开始', completion_confirmed: '一方确认结束', consultation_completed: '双方确认完成', order_cancelled_by_applicant: '咨询用户取消订单', order_timed_out: '订单超时自动取消', accepted_start_timed_out: '前辈接单后未开始，订单已取消', booking_no_show_timed_out: '预约未开始，订单已取消', consultation_report_created: '提交问题反馈', consultation_report_responded: '被反馈方提交说明', consultation_report_evidence_uploaded: '补充问题反馈凭证', consultation_report_appeal_created: '提交复核申请', consultation_report_appeal_evidence_uploaded: '补充复核凭证', consultation_report_reopened_after_appeal: '平台重新开启原案', consultation_report_appeal_reviewing: '平台开始复核', consultation_report_appeal_resolved: '平台更新复核结果', consultation_report_resolved: '平台更新处理结果', consultation_review_hidden: '平台下架关联评价', consultation_review_restored: '平台恢复关联评价' }[event?.event_type] || '订单处理事件' }
function eventLabel(event) { return { consultation_report_acknowledged: '平台已受理问题反馈', consultation_report_sla_escalated: '问题反馈首响超时升级', consultation_report_priority_escalated: '问题反馈已调整优先级', consultation_report_appeal_sla_escalated: '复核首响超时升级', consultation_report_appeal_priority_escalated: '复核已调整优先级' }[event?.event_type] || eventText(event) }
function eventDetail(event) { const details = event?.details && typeof event.details === 'object' ? event.details : {}; if (details.issue_type) return `问题类型：${details.issue_type}`; if (event?.event_type === 'consultation_review_hidden') return '关联服务评价已停止对外展示'; if (event?.event_type === 'consultation_review_restored') return '关联服务评价已恢复对外展示'; return details.decision === 'reopen' ? '原问题反馈已重新进入处理中' : '已记录到本次咨询处理链路' }
function previewImage(current, items) { const urls = (Array.isArray(items) ? items : []).map((item) => item?.file_url).filter(Boolean); if (current && urls.length) uni.previewImage({ current, urls }) }

function previewPage() {
  const rows = [
    { id: 'preview-appeal-001', report_id: 'preview-report-001', appellant_role: 'reporter', content: '希望平台重新核对咨询时长和聊天记录，原处理结论未覆盖已约定的服务内容。', status: 'pending', decision: 'none', priority: 'urgent', escalation_level: 1, sla_status: 'overdue', first_response_due_at: '2026-08-22T03:00:00Z', evidence_count: 2, created_at: '2026-08-21T03:00:00Z', appellant: { display_name: '同学 A' }, report: { issue_type: '爽约或未提供服务', status: 'resolved', resolution: 'warn_participant' }, order_no: 'MC202608230001' },
    { id: 'preview-appeal-002', report_id: 'preview-report-002', appellant_role: 'respondent', content: '希望平台复核我提交的聊天说明和预约时间，原结论与实际到场情况不一致。', status: 'reviewing', decision: 'none', priority: 'high', sla_status: 'responded', first_response_due_at: '2026-08-22T11:20:00Z', first_response_at: '2026-08-22T06:00:00Z', evidence_count: 1, created_at: '2026-08-22T05:20:00Z', appellant: { display_name: '林前辈' }, report: { issue_type: '恶意占用时段或爽约', status: 'dismissed', resolution: 'none' }, order_no: 'MC202608220002' }
  ]
  const keyword = filters.keyword.toLowerCase()
  const filtered = rows.filter((item) => (!filters.status || item.status === filters.status) && (!filters.priority || item.priority === filters.priority) && (!filters.sla_state || (filters.sla_state === 'escalated' ? Number(item.escalation_level || 0) > 0 : item.sla_status === filters.sla_state)) && (!keyword || item.content.toLowerCase().includes(keyword)))
  return { items: filtered.slice((page.value - 1) * pageSize, page.value * pageSize), count: filtered.length }
}

function previewDetail(appeal) {
  const report = { id: appeal.report_id, issue_type: appeal.report.issue_type, content: '已提交的原问题反馈说明会在这里完整展示，便于管理员结合上下文复核。', respondent_content: '被反馈方已补充咨询经过和时间说明。', status: appeal.report.status, resolution: appeal.report.resolution, admin_note: '原处理结论已记录，等待本次复核处理。' }
  return { appeal: { ...appeal }, report, evidence: Array.from({ length: appeal.evidence_count || 0 }, (_, index) => ({ id: `appeal-evidence-${index}`, file_url: '/static/ui-icons/report.svg', file_name: `复核凭证 ${index + 1}` })), report_evidence: [{ id: 'report-evidence-1', file_url: '/static/ui-icons/report.svg', file_name: '原案凭证', submitter_role: 'reporter' }], messages: [{ id: 'message-1', sender_role: 'applicant', message_type: 'text', content: '想确认一下这次咨询的具体安排。', created_at: appeal.created_at }, { id: 'message-2', sender_role: 'mentor', message_type: 'text', content: '好的，我会按约定时间完成咨询。', created_at: appeal.created_at }], events: [{ id: 'event-1', event_type: 'consultation_report_created', details: { issue_type: report.issue_type }, created_at: appeal.created_at }, { id: 'event-2', event_type: 'consultation_report_appeal_created', details: {}, created_at: appeal.created_at }] }
}
</script>

<style scoped>
.mentor-appeal-admin-page{min-height:calc(100vh - 158px);color:#31465d}.appeal-summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.appeal-summary-card{min-height:112px;padding:18px 20px;border:1px solid #e2eaee;border-top:3px solid #8b9bad;border-radius:9px;background:#fff;box-shadow:0 8px 24px rgba(39,62,79,.04)}.appeal-summary-card text,.appeal-summary-card strong,.appeal-summary-card small{display:block}.appeal-summary-card text{color:#7d8d9e;font-size:11px;font-weight:700}.appeal-summary-card strong{margin-top:10px;color:#314a65;font-size:28px}.appeal-summary-card small{margin-top:7px;color:#9aa7b4;font-size:10px}.appeal-summary-card.pending{border-top-color:#dbaf55}.appeal-summary-card.reviewing{border-top-color:#7197c3}.appeal-summary-card.closed{border-top-color:#57cdb7}.appeal-workspace{min-height:0;margin-top:18px;border:1px solid #e0e8ec;border-radius:10px;background:#fff;overflow:hidden;box-shadow:0 10px 30px rgba(38,59,77,.04)}.appeal-toolbar{padding:14px 18px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #edf1f3;background:#fbfcfd}.appeal-search{height:38px;min-width:260px;flex:1;padding:0 10px;display:flex;align-items:center;gap:8px;border:1px solid #dae4e8;border-radius:8px;background:#fff}.appeal-search input{min-width:0;flex:1;height:36px;font-size:11px}.appeal-search button{width:26px;height:26px;margin:0;padding:0;border:0;background:transparent;color:#93a1af}.appeal-select{width:154px;flex:0 0 154px}.appeal-refresh{height:36px;min-width:76px;margin:0;padding:0 14px;border:1px solid #d7e3e6;border-radius:7px;background:#fff;color:#617286;font-size:10px;font-weight:750}.appeal-refresh::after,.appeal-search button::after,.open-button::after,.appeal-detail button::after{border:0}.appeal-table-wrap{overflow-x:auto}.appeal-table{min-width:1080px}.appeal-grid{display:grid;grid-template-columns:1.25fr .85fr 1.7fr .55fr .8fr .75fr 60px;align-items:center;gap:14px;padding:0 18px}.table-head{min-height:42px;color:#8796a4;background:#f7f9fa;font-size:10px;font-weight:800}.table-row{min-height:76px;border-top:1px solid #edf1f3;cursor:pointer;font-size:11px}.table-row:hover{background:#fbfefd}.table-row strong,.table-row small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.table-row strong{color:#394f65;font-size:11px}.table-row small{margin-top:4px;color:#98a5b2;font-size:9px}.appeal-copy{overflow:hidden;display:-webkit-box;color:#718297;font-size:10px;line-height:1.4;-webkit-box-orient:vertical;-webkit-line-clamp:2}.evidence-pill,.status-pill{display:inline-flex!important;margin:0!important;padding:5px 8px;border-radius:99px;font-size:9px!important;font-weight:800}.evidence-pill{background:#eef5fc;color:#5880a6}.status-pill.pending{background:#fff4df;color:#ae7a29}.status-pill.reviewing{background:#eaf2fc;color:#4e78a7}.status-pill.resolved{background:#e8f7f2;color:#238b75}.status-pill.dismissed{background:#f0eef1;color:#817783}.open-button{height:30px;margin:0;padding:0 11px;border:0;border-radius:6px;background:#eef7f5;color:#278b78;font-size:10px;font-weight:800}.table-state{padding:54px 20px;color:#91a0ae;text-align:center;font-size:12px}.table-state.error{color:#ba6962}.table-state button{display:block;margin:12px auto 0;font-size:11px}.appeal-pagination{min-height:58px;padding:0 18px;display:flex;align-items:center;justify-content:space-between;border-top:1px solid #eaf0f2;color:#90a0af;font-size:10px}.appeal-pagination>view:last-child{display:flex;align-items:center;gap:8px}.appeal-pagination button{width:34px;height:34px;margin:0;padding:0;border:1px solid #dfe8eb;border-radius:7px;background:#fff;color:#718295;font-size:16px}.appeal-pagination button:disabled{color:#c4cdd5;background:#f8fafb}.appeal-pagination button::after{border:0}.appeal-backdrop{position:fixed;z-index:6000;inset:0;padding:24px;display:flex;align-items:center;justify-content:center;background:rgba(24,39,55,.38);backdrop-filter:blur(4px)}.appeal-detail{width:min(800px,calc(100vw - 48px));height:min(790px,calc(100vh - 48px));display:flex;flex-direction:column;overflow:hidden;border:1px solid #dfe8eb;border-radius:12px;background:#fff;box-shadow:0 30px 90px rgba(26,42,58,.24)}.appeal-detail-head{padding:18px 22px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e9eef1}.appeal-detail-head text,.appeal-detail-head strong{display:block}.appeal-detail-head text{color:#35a78f;font-size:9px;font-weight:850;letter-spacing:.12em}.appeal-detail-head strong{margin-top:5px;color:#30465d;font-size:17px}.appeal-detail-head button{width:34px;height:34px;margin:0;padding:0;border:0;border-radius:50%;background:#f2f5f7;color:#768695;font-size:20px}.appeal-detail-scroll{min-height:0;flex:1}.appeal-detail-content{padding:22px}.detail-state{padding:50px 0;color:#91a0ae;text-align:center}.appeal-party{display:flex;align-items:center;gap:11px;padding-bottom:17px;border-bottom:1px solid #e8eef1}.appeal-avatar{width:46px;height:46px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:#e4f5f0;color:#278d77;font-size:17px;font-weight:900}.appeal-party>view:nth-child(2){min-width:0;flex:1}.appeal-party text,.appeal-party strong,.appeal-party small{display:block}.appeal-party text,.appeal-party small{color:#98a6b4;font-size:10px}.appeal-party strong{margin-top:4px;color:#3b5269;font-size:13px}.appeal-party small{margin-top:4px}.detail-heading{margin:20px 0 9px;color:#40566c;font-size:12px;font-weight:800}.detail-box{padding:13px;border:1px solid #e3ebee;border-radius:8px;color:#52677b;font-size:11px;line-height:1.65;background:#fbfcfd;white-space:pre-wrap}.detail-box strong,.detail-box text{display:block}.detail-box strong{margin-bottom:7px;color:#40566c}.detail-subtitle{margin-top:13px;color:#8495a5!important;font-size:10px}.evidence-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.evidence-grid image{width:100%;height:112px;border:1px solid #e1e9ec;border-radius:8px;background:#f4f8fb}.evidence-item{min-width:0}.evidence-item text{display:block;margin-top:5px;color:#8a9aad;font-size:9px}.detail-empty{padding:13px;border:1px dashed #dce7eb;border-radius:8px;color:#94a2af;text-align:center;font-size:10px}.audit-list{display:grid;gap:8px}.audit-row{padding:10px 12px;border:1px solid #e4ecef;border-radius:8px;background:#fbfcfd}.audit-row.event{background:#f4fbf8;border-color:#d7ebe5}.audit-row text,.audit-row strong,.audit-row small{display:block}.audit-row text,.audit-row small{color:#95a4b1;font-size:9px}.audit-row strong{margin-top:4px;color:#4b6177;font-size:11px;font-weight:650;line-height:1.55;white-space:pre-wrap}.audit-row small{margin-top:5px}.appeal-review{margin-top:20px;padding-top:1px;border-top:1px solid #e8eef1}.review-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.review-grid>view>text,.note-field>text{display:block;margin-bottom:8px;color:#718397;font-size:10px;font-weight:800}.note-field{margin-top:14px}.note-field textarea{width:100%;min-height:92px;padding:10px 11px;border:1px dashed #9fcfc4;border-radius:7px;box-sizing:border-box;color:#40566d;font-size:11px;line-height:1.5;background:#fbfefd}.review-actions{margin-top:14px;display:flex;justify-content:flex-end}.review-actions button{min-width:124px;height:36px;margin:0;border:0;border-radius:7px;background:#34b399;color:#fff;font-size:10px;font-weight:800}@media(max-width:960px){.appeal-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.appeal-toolbar{flex-wrap:wrap}.appeal-search{flex-basis:100%}}@media(max-width:820px){.mentor-appeal-admin-page{min-height:auto}.appeal-backdrop{padding:14px}.appeal-detail{width:100%;height:calc(100vh - 28px)}.appeal-detail-content{padding:18px}.review-grid{grid-template-columns:1fr}.evidence-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.appeal-pagination{align-items:flex-start;flex-direction:column;justify-content:center;padding-top:12px;padding-bottom:12px}}
.appeal-table{min-width:1220px}.appeal-grid{grid-template-columns:1.15fr .8fr 1.45fr .52fr .82fr .76fr .7fr 60px}.sla-pill{display:inline-flex!important;margin:0!important;padding:5px 8px;border-radius:99px;background:#eef4ff;color:#5279ad;font-size:9px!important;font-weight:800}.sla-pill.due_soon{background:#fff4df;color:#a7772c}.sla-pill.overdue{background:#fceceb;color:#b45f59}.sla-pill.responded,.sla-pill.closed{background:#e8f7f2;color:#238b75}.detail-sla{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));overflow:hidden;border:1px solid #e3ebee;border-radius:8px;background:#fbfcfd}.detail-sla>view{min-width:0;padding:12px;border-left:1px solid #e7edf0}.detail-sla>view:first-child{border-left:0}.detail-sla text,.detail-sla strong{display:block}.detail-sla text{color:#8a9aaa;font-size:9px}.detail-sla strong{margin-top:5px;overflow:hidden;color:#4b6177;font-size:10px;text-overflow:ellipsis;white-space:nowrap}@media(max-width:820px){.detail-sla{grid-template-columns:1fr}.detail-sla>view{border-top:1px solid #e7edf0;border-left:0}.detail-sla>view:first-child{border-top:0}}
</style>

<style scoped>
.mentor-appeal-admin-page.is-compact {
  min-height: 0;
}

.mentor-appeal-admin-page.is-compact .appeal-workspace {
  margin-top: 0;
}
</style>
