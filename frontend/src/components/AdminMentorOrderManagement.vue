<template>
  <view class="mentor-orders-page" :class="{ 'is-compact': compact }">
    <view v-if="!compact" class="order-summary-grid">
      <view class="order-summary-card"><text>当前订单</text><strong>{{ orderCount }}</strong><small>符合当前筛选条件的咨询订单</small></view>
      <view class="order-summary-card active"><text>本页进行中</text><strong>{{ activeCount }}</strong><small>待接单、已预约或咨询中的订单</small></view>
      <view class="order-summary-card report"><text>本页涉及投诉</text><strong>{{ reportedCount }}</strong><small>至少关联一条问题反馈</small></view>
      <view class="order-summary-card urgent"><text>本页风险待跟进</text><strong>{{ attentionCount }}</strong><small>投诉、过期服务或结束确认待跟进</small></view>
    </view>

    <view class="order-workspace">
      <view class="order-toolbar">
        <view class="order-search"><text>⌕</text><input v-model.trim="filters.keyword" placeholder="搜索订单号" @input="scheduleSearch" /><button v-if="filters.keyword" @tap="clearSearch">×</button></view>
        <AdminSelect class="order-select status-select" :options="orderStatusOptions.map((item) => item.label)" :value-index="orderStatusIndex" aria-label="订单状态" @change="selectOrderStatus" />
        <AdminSelect class="order-select payment-select" :options="paymentStatusOptions.map((item) => item.label)" :value-index="paymentStatusIndex" aria-label="支付状态" @change="selectPaymentStatus" />
        <AdminSelect class="order-select report-select" :options="reportStateOptions.map((item) => item.label)" :value-index="reportStateIndex" aria-label="投诉状态" @change="selectReportState" />
        <button class="order-refresh" :disabled="loading" @tap="refresh">{{ loading ? '刷新中…' : '刷新' }}</button>
      </view>

      <view class="order-table-wrap"><view class="order-table">
        <view class="order-grid order-table-head"><view>订单</view><view>咨询用户</view><view>认证前辈</view><view>服务信息</view><view>金额 / 支付</view><view>状态 / 预警</view><view>问题反馈</view><view>创建时间</view><view>操作</view></view>
        <view v-if="loading" class="order-state">正在加载咨询订单…</view>
        <view v-else-if="loadError" class="order-state error"><text>咨询订单加载失败，请检查网络或后台权限。</text><button @tap="refresh">重新加载</button></view>
        <view v-else-if="orders.length === 0" class="order-state">当前筛选下没有咨询订单</view>
        <view v-for="item in orders" v-else :key="item.id" class="order-grid order-row" @tap="openOrder(item)">
          <view><strong>{{ item.order_no || shortId(item.id) }}</strong><text>{{ consultationTypeText(item.consultation_type) }}</text></view>
          <view class="order-person"><view class="order-avatar applicant">{{ initial(item.applicant?.display_name, '咨') }}</view><view><strong>{{ item.applicant?.display_name || item.questionnaire?.name || '咨询用户' }}</strong><text>{{ item.questionnaire?.school || '未填写院校' }}</text></view></view>
          <view class="order-person"><view class="order-avatar mentor">{{ initial(item.mentor?.display_name, '前') }}</view><view><strong>{{ item.mentor?.display_name || '认证前辈' }}</strong><text>{{ mentorMeta(item.mentor) }}</text></view></view>
          <view><strong>{{ item.questionnaire?.major || '未填写专业' }}</strong><text>{{ item.consultation_window_minutes || 60 }} 分钟咨询</text></view>
          <view><strong>{{ isLocalRehearsalOrder(item) ? '免支付' : `¥${formatMoney(item.price)}` }}</strong><text class="payment-label" :class="{ [item.payment_status]: true, rehearsal: isLocalRehearsalOrder(item) }">{{ paymentStatusText(item.payment_status, item) }}</text></view>
          <view><text class="order-status" :class="item.order_status">{{ orderStatusText(item.order_status) }}</text><text v-if="item.attention" class="order-attention" :class="item.attention">{{ attentionText(item.attention) }}</text></view>
          <view><text class="report-badge" :class="{ open: item.open_report_count > 0 }">{{ reportBadgeText(item) }}</text></view>
          <view>{{ formatDateTime(item.created_at) }}</view>
          <view><button class="order-open-button" @tap.stop="openOrder(item)">查看</button></view>
        </view>
      </view></view>

      <view class="order-pagination"><view>共 {{ orderCount }} 条，每页 {{ pageSize }} 条</view><view class="order-pagination-actions"><button :disabled="page <= 1 || loading" @tap="changePage(page - 1)">‹</button><view>{{ page }}</view><text>/ {{ totalPages }}</text><button :disabled="page >= totalPages || loading" @tap="changePage(page + 1)">›</button></view></view>
    </view>

    <view v-if="detailVisible" class="order-backdrop" @tap="closeDetail"><view class="order-detail" @tap.stop>
      <view class="order-detail-header"><view><text>CONSULTATION ORDER</text><strong>咨询订单详情</strong></view><button class="admin-modal-close" :disabled="saving" aria-label="关闭咨询订单详情" @tap="closeDetail"><text>×</text></button></view>
      <view v-if="detailLoading" class="order-state">正在读取订单详情…</view>
      <scroll-view v-else-if="detail?.order" scroll-y class="order-detail-scroll"><view class="order-detail-content">
        <view class="order-parties"><view><text>咨询用户</text><strong>{{ detail.order.applicant?.display_name || detail.order.questionnaire?.name || '咨询用户' }}</strong><small>{{ detail.order.applicant?.email || detail.order.applicant?.phone || shortId(detail.order.applicant?.id) }}</small></view><view><text>认证前辈</text><strong>{{ detail.order.mentor?.display_name || '认证前辈' }}</strong><small>{{ mentorMeta(detail.order.mentor) }}</small></view></view>
        <view class="order-fields"><view><text>订单号</text><strong>{{ detail.order.order_no || shortId(detail.order.id) }}</strong></view><view><text>订单状态</text><strong>{{ orderStatusText(detail.order.order_status) }}</strong></view><view><text>支付状态</text><strong>{{ paymentStatusText(detail.order.payment_status, detail.order) }}</strong></view><view><text>订单金额</text><strong>{{ isLocalRehearsalOrder(detail.order) ? '免支付' : `¥${formatMoney(detail.order.price)}` }}</strong></view><view><text>支付流水号</text><strong>{{ detail.order.payment_reference || '待支付' }}</strong></view><view><text>退款流水号</text><strong>{{ detail.order.refund_reference || '—' }}</strong></view><view><text>咨询形式</text><strong>{{ consultationTypeText(detail.order.consultation_type) }}</strong></view><view><text>咨询时长</text><strong>{{ detail.order.consultation_window_minutes || 60 }} 分钟</strong></view><view><text>创建时间</text><strong>{{ formatDateTime(detail.order.created_at) }}</strong></view><view><text>预约时段</text><strong>{{ slotText(detail.order.slot) }}</strong></view></view>
        <view v-if="detail.order.attention_reason" class="order-attention-card" :class="detail.order.attention"><strong>需平台关注 · {{ attentionText(detail.order.attention) }}</strong><text>{{ detail.order.attention_reason }}</text></view>
        <view class="order-detail-heading">咨询需求</view><view class="order-block"><strong>{{ detail.order.questionnaire?.school || '未填写院校' }} · {{ detail.order.questionnaire?.major || '未填写专业' }}</strong><text>{{ detail.order.questionnaire?.question || '用户未填写额外咨询问题。' }}</text></view>
        <template v-if="detail.order.rejection_reason"><view class="order-detail-heading">前辈暂不接单说明</view><view class="order-block"><text>{{ detail.order.rejection_reason }}</text></view></template>
        <view class="order-detail-heading">问题反馈</view><view v-if="detail.reports?.length" class="order-report-list"><view v-for="report in detail.reports" :key="report.id" class="order-report-item"><view><strong>{{ report.issue_type }}</strong><text class="report-status" :class="report.status">{{ reportStatusText(report.status) }}</text></view><small>{{ report.reporter?.display_name || '举报用户' }} → {{ report.target?.display_name || '被举报对象' }} · {{ formatDateTime(report.created_at) }}</small><text>{{ report.content }}</text><text v-if="report.admin_note" class="report-note">平台说明：{{ report.admin_note }}</text></view></view><view v-else class="order-empty">暂无问题反馈</view>
        <view class="order-detail-heading">站内聊天记录</view><view v-if="detail.messages?.length" class="order-message-list"><view v-for="message in detail.messages" :key="message.id || `${message.created_at}-${message.content}`" class="order-message" :class="message.sender_role"><text>{{ messageRoleText(message.sender_role) }}</text><strong>{{ messageText(message) }}</strong><small>{{ formatDateTime(message.created_at) }}</small></view></view><view v-else class="order-empty">暂无站内聊天记录</view>
        <view class="order-detail-heading">订单事件</view><view v-if="detail.events?.length" class="order-event-list"><view v-for="event in detail.events" :key="event.id" class="order-event"><strong>{{ eventLabel(event.event_type) }}</strong><text>{{ eventDetailsText(event.details) }}</text><small>{{ formatDateTime(event.created_at) }}</small></view></view><view v-else class="order-empty">暂未记录可展示的订单事件</view>
        <view class="order-intervention"><view class="order-detail-heading">平台主动介入</view><view v-if="requiresReportQueueResolution" class="order-intervention-warning"><strong>该订单有 {{ detail.order.open_report_count }} 条待处理问题反馈</strong><text>为保留每条反馈的证据、处理结论与复核入口，请先在“问题反馈”队列逐条结案；这里仍可发送提醒。</text></view><view class="order-intervention-grid"><view class="order-field"><text>介入动作</text><AdminSelect class="form-select" :options="availableInterventions.map((item) => item.label)" :value-index="interventionIndex" aria-label="平台介入动作" @change="selectIntervention" /></view><view v-if="interventionAction === 'refund_partial'" class="order-field"><text>部分退款金额（元）</text><input v-model.trim="interventionPartialRefundAmount" type="digit" placeholder="需小于订单总金额" /></view><view class="order-field full"><text>处理说明</text><textarea v-model.trim="interventionNote" maxlength="1000" placeholder="填写平台处理说明；该说明会以系统消息同步给咨询双方，并保留管理日志。" /></view></view><view class="order-intervention-tip">{{ selectedIntervention?.hint || '' }}</view><view class="order-intervention-actions"><button :disabled="saving || !interventionNote.trim()" @tap="submitIntervention">{{ saving ? '处理中…' : '执行平台介入' }}</button></view></view>
      </view></scroll-view>
    </view></view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { fetchAdminMentorConsultationOrder, fetchAdminMentorConsultationOrders, interveneAdminMentorConsultationOrder } from '../api/admin'
import AdminSelect from './AdminSelect.vue'

const props = defineProps({ preview: Boolean, compact: Boolean })
const orders = ref([])
const orderCount = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const loadError = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref(null)
const saving = ref(false)
const interventionAction = ref('notify_participants')
const interventionNote = ref('')
const interventionPartialRefundAmount = ref('')
const filters = reactive({ status: '', payment_status: '', report_state: '', keyword: '' })
let searchTimer = null

const orderStatusOptions = [{ label: '全部订单状态', value: '' }, { label: '待支付', value: 'pending_payment' }, { label: '待接单', value: 'pending_accept' }, { label: '已接单', value: 'accepted' }, { label: '已预约', value: 'booked' }, { label: '咨询中', value: 'in_progress' }, { label: '已完成', value: 'completed' }, { label: '已退款', value: 'refunded' }, { label: '已取消', value: 'cancelled' }, { label: '已拒绝', value: 'rejected' }, { label: '已超时', value: 'timeout' }]
const paymentStatusOptions = [{ label: '全部支付状态', value: '' }, { label: '未支付', value: 'unpaid' }, { label: '已支付', value: 'paid' }, { label: '退款中', value: 'refunding' }, { label: '已退款', value: 'refunded' }, { label: '支付失败', value: 'failed' }]
const reportStateOptions = [{ label: '全部问题反馈', value: '' }, { label: '有问题反馈', value: 'reported' }, { label: '待跟进反馈', value: 'open' }]
const orderStatusIndex = computed(() => Math.max(0, orderStatusOptions.findIndex((item) => item.value === filters.status)))
const paymentStatusIndex = computed(() => Math.max(0, paymentStatusOptions.findIndex((item) => item.value === filters.payment_status)))
const reportStateIndex = computed(() => Math.max(0, reportStateOptions.findIndex((item) => item.value === filters.report_state)))
const totalPages = computed(() => Math.max(1, Math.ceil(orderCount.value / pageSize)))
const activeCount = computed(() => orders.value.filter((item) => ['pending_accept', 'accepted', 'booked', 'in_progress'].includes(item.order_status)).length)
const reportedCount = computed(() => orders.value.filter((item) => Number(item.report_count || 0) > 0).length)
const attentionCount = computed(() => orders.value.filter((item) => Boolean(item.attention)).length)
const requiresReportQueueResolution = computed(() => Number(detail.value?.order?.open_report_count || 0) > 1)
const availableInterventions = computed(() => {
  const order = detail.value?.order || {}
  const options = [{ label: '提醒咨询双方', value: 'notify_participants', hint: '只发送平台处理提醒，不改变订单或支付状态。' }]
  if (!requiresReportQueueResolution.value && isRefundRetryable(order)) {
    options.push({ label: order.payment_status === 'failed' ? '重新发起全额退款' : '全额退款并结束', value: 'refund_full', hint: '提交订单全额退款；支付渠道确认完成后，用户端会自动更新。' })
    options.push({ label: order.payment_status === 'failed' ? '重新发起部分退款' : '部分退款并结束', value: 'refund_partial', hint: '提交部分退款并结束服务；支付渠道确认完成后，用户端会自动更新。' })
  }
  if (!requiresReportQueueResolution.value && !['completed', 'refunded', 'cancelled', 'rejected', 'timeout'].includes(order.order_status)) options.push({ label: '平台结束服务', value: 'close_service', hint: '结束当前服务并保留聊天记录，不自动退款。' })
  return options
})
const interventionIndex = computed(() => Math.max(0, availableInterventions.value.findIndex((item) => item.value === interventionAction.value)))
const selectedIntervention = computed(() => availableInterventions.value[interventionIndex.value])

refresh()
onBeforeUnmount(() => { if (searchTimer) clearTimeout(searchTimer) })
defineExpose({ refresh })

async function refresh() {
  loading.value = true
  loadError.value = false
  try {
    const response = props.preview ? buildPreviewPage() : await fetchAdminMentorConsultationOrders({ ...filters, limit: pageSize, offset: (page.value - 1) * pageSize })
    orders.value = Array.isArray(response?.items) ? response.items : []
    orderCount.value = Number(response?.count || 0)
    if (orderCount.value > 0 && orders.value.length === 0 && page.value > totalPages.value) { page.value = totalPages.value; await refresh(); return }
  } catch (error) {
    orders.value = []
    orderCount.value = 0
    loadError.value = true
  } finally { loading.value = false }
}

function scheduleSearch() { if (searchTimer) clearTimeout(searchTimer); searchTimer = setTimeout(() => { page.value = 1; refresh() }, 360) }
function clearSearch() { filters.keyword = ''; page.value = 1; refresh() }
function selectOrderStatus(event) { filters.status = orderStatusOptions[Number(event?.detail?.value || 0)]?.value || ''; page.value = 1; refresh() }
function selectPaymentStatus(event) { filters.payment_status = paymentStatusOptions[Number(event?.detail?.value || 0)]?.value || ''; page.value = 1; refresh() }
function selectReportState(event) { filters.report_state = reportStateOptions[Number(event?.detail?.value || 0)]?.value || ''; page.value = 1; refresh() }
function changePage(next) { const target = Math.max(1, Math.min(totalPages.value, Number(next) || 1)); if (target !== page.value) { page.value = target; refresh() } }

async function openOrder(item) {
  if (!item?.id || detailLoading.value) return
  detailVisible.value = true
  detailLoading.value = true
  detail.value = null
  interventionAction.value = 'notify_participants'
  interventionNote.value = ''
  interventionPartialRefundAmount.value = ''
  try {
    detail.value = props.preview ? previewOrderDetail(item) : await fetchAdminMentorConsultationOrder(item.id)
  } catch (error) {
    uni.showToast({ title: error?.detail || '订单详情加载失败', icon: 'none' })
    detailVisible.value = false
  } finally { detailLoading.value = false }
}

function closeDetail() { if (!saving.value) { detailVisible.value = false; detail.value = null; interventionNote.value = ''; interventionPartialRefundAmount.value = '' } }
function selectIntervention(event) { interventionAction.value = availableInterventions.value[Number(event?.detail?.value || 0)]?.value || 'notify_participants'; if (interventionAction.value !== 'refund_partial') interventionPartialRefundAmount.value = '' }

async function submitIntervention() {
  const order = detail.value?.order
  if (!order?.id || saving.value || !interventionNote.value.trim()) return
  const action = selectedIntervention.value
  if (!action) return
  const partialRefundAmount = Number(interventionPartialRefundAmount.value)
  const orderAmount = Number(order.price || 0)
  if (action.value === 'refund_partial' && (!Number.isFinite(partialRefundAmount) || partialRefundAmount <= 0 || partialRefundAmount >= orderAmount)) {
    uni.showToast({ title: '部分退款金额需大于 0 且小于订单总金额', icon: 'none' })
    return
  }
  const confirmed = await new Promise((resolve) => uni.showModal({ title: `确认${action.label}？`, content: action.hint, confirmText: '确认执行', success: (result) => resolve(Boolean(result.confirm)) }))
  if (!confirmed) return
  saving.value = true
  try {
    const updated = props.preview ? previewIntervention(order, action.value, partialRefundAmount) : await interveneAdminMentorConsultationOrder(order.id, { action: action.value, refund_amount: action.value === 'refund_partial' ? partialRefundAmount : 0, admin_note: interventionNote.value.trim() })
    orders.value = orders.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    if (props.preview) {
      detail.value = { ...detail.value, order: { ...detail.value.order, ...updated } }
    } else {
      detail.value = await fetchAdminMentorConsultationOrder(order.id)
    }
    interventionNote.value = ''
    interventionAction.value = 'notify_participants'
    interventionPartialRefundAmount.value = ''
    uni.showToast({ title: '平台介入已执行', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '平台介入失败', icon: 'none' })
  } finally { saving.value = false }
}

function buildPreviewPage() {
  const keyword = filters.keyword.trim().toLowerCase()
  const list = previewOrders().filter((item) => {
    if (filters.status && item.order_status !== filters.status) return false
    if (filters.payment_status && item.payment_status !== filters.payment_status) return false
    if (filters.report_state === 'reported' && !item.report_count) return false
    if (filters.report_state === 'open' && !item.open_report_count) return false
    return !keyword || String(item.order_no || '').toLowerCase().includes(keyword)
  })
  const offset = (page.value - 1) * pageSize
  return { items: list.slice(offset, offset + pageSize), count: list.length }
}

function previewOrders() {
  return [
    { id: 'preview-order-001', order_no: 'MC202608230001', applicant: { id: 'preview-user-001', display_name: '同学 A', email: 'student-a@example.com' }, mentor: { id: 'preview-mentor-001', display_name: '钟*宏', school: '暨南大学', major: '应用经济学' }, consultation_type: 'booking', order_status: 'booked', payment_status: 'paid', questionnaire: { name: '同学 A', school: '华南师范大学', major: '应用经济学', question: '想确认接下来三个月的复习重点。' }, price: 39, consultation_window_minutes: 60, slot: { id: 'preview-slot-001', starts_at: '2026-08-25T11:00:00Z', ends_at: '2026-08-25T12:00:00Z', status: 'booked' }, report_count: 1, open_report_count: 1, latest_report_status: 'pending', attention: 'open_report', attention_reason: '有 1 条待处理问题反馈，建议优先介入。', created_at: '2026-08-23T03:20:00Z' },
    { id: 'preview-order-002', order_no: 'MC202608220002', applicant: { id: 'preview-user-002', display_name: '同学 B' }, mentor: { id: 'preview-mentor-002', display_name: '陈前辈', school: '中山大学', major: '金融学' }, consultation_type: 'instant', order_status: 'in_progress', payment_status: 'paid', questionnaire: { name: '同学 B', school: '广东财经大学', major: '金融学', question: '希望咨询复试准备节奏。' }, price: 49, consultation_window_minutes: 60, applicant_completion_confirmed_at: '2026-08-22T10:20:00Z', report_count: 0, open_report_count: 0, attention: 'completion_pending', attention_reason: '一方已确认结束，正在等待认证前辈确认。', created_at: '2026-08-22T08:30:00Z' },
    { id: 'preview-order-003', order_no: 'MC202608210003', applicant: { id: 'preview-user-003', display_name: '同学 C' }, mentor: { id: 'preview-mentor-003', display_name: '林前辈', school: '华南理工大学', major: '工商管理' }, consultation_type: 'instant', order_status: 'completed', payment_status: 'paid', questionnaire: { name: '同学 C', school: '深圳大学', major: '工商管理', question: '请分享择校思路。' }, price: 39, consultation_window_minutes: 60, report_count: 1, open_report_count: 0, latest_report_status: 'resolved', created_at: '2026-08-21T09:00:00Z' }
  ]
}

function previewOrderDetail(order) {
  const reports = order.report_count ? [{ id: `preview-report-${order.id}`, issue_type: '服务态度与沟通问题', reporter: order.applicant, target: order.mentor, content: '希望平台协助核实本次站内聊天记录。', status: order.open_report_count ? 'pending' : 'resolved', admin_note: order.open_report_count ? null : '已向双方同步平台处理说明。', created_at: order.created_at }] : []
  return { order: { ...order }, reports, messages: [{ id: 'preview-message-1', sender_role: 'applicant', content: '你好，想咨询一下备考安排。', created_at: order.created_at }, { id: 'preview-message-2', sender_role: 'mentor', content: '好的，请先说明你的报考方向。', created_at: order.created_at }], events: [{ id: 'preview-event-1', event_type: 'consultation_order_created', details: {}, created_at: order.created_at }] }
}

function previewIntervention(order, action, partialRefundAmount = 0) {
  if (action === 'refund_full') return { ...order, order_status: 'refunded', payment_status: 'refunding', refund_amount: order.price, refund_reference: `ADMIN-${order.order_no}`, attention: null, attention_reason: null }
  if (action === 'refund_partial') return { ...order, order_status: 'completed', payment_status: 'refunding', refund_amount: partialRefundAmount, refund_reference: `ADMIN-PARTIAL-${order.order_no}`, attention: null, attention_reason: null }
  if (action === 'close_service') return { ...order, order_status: 'completed', ended_at: new Date().toISOString(), attention: null, attention_reason: null }
  return { ...order }
}

function initial(value, fallback) { return String(value || fallback).slice(0, 1) || fallback }
function shortId(value) { const id = String(value || ''); return id ? `${id.slice(0, 8)}…${id.slice(-4)}` : '—' }
function formatMoney(value) { const amount = Number(value || 0); return Number.isInteger(amount) ? String(amount) : amount.toFixed(2) }
function mentorMeta(mentor) { return [mentor?.school, mentor?.major].filter(Boolean).join(' · ') || '认证前辈' }
function consultationTypeText(value) { return value === 'booking' ? '预约咨询' : '即时咨询' }
function isLocalRehearsalOrder(order = {}) { return String(order?.payment_reference || '').toUpperCase().startsWith('DEMO-') }
function isRefundRetryable(order = {}) { return !isLocalRehearsalOrder(order) && (order.payment_status === 'paid' || (order.payment_status === 'failed' && Boolean(order.refund_reference))) }
function paymentStatusText(value, order = {}) { if (isLocalRehearsalOrder(order)) return '免支付'; if (value === 'failed' && order?.refund_reference) return '退款异常'; return { unpaid: '未支付', paid: '已支付', refunding: '退款中', refunded: '已退款', failed: '支付失败' }[value] || '未支付' }
function orderStatusText(value) { return { draft: '草稿', pending_payment: '待支付', pending_accept: '待接单', accepted: '已接单', booked: '已预约', in_progress: '咨询中', completed: '已完成', rejected: '已拒绝', timeout: '已超时', refunded: '已退款', cancelled: '已取消' }[value] || '处理中' }
function reportStatusText(value) { return { pending: '待处理', reviewing: '处理中', resolved: '已处理', dismissed: '已驳回' }[value] || '待处理' }
function reportBadgeText(order) { return Number(order.open_report_count || 0) > 0 ? `${order.open_report_count} 条待跟进` : Number(order.report_count || 0) > 0 ? `${order.report_count} 条已处理` : '无反馈' }
function attentionText(value) { return { open_report: '待处理反馈', report_sla_overdue: '反馈首响超时', report_sla_escalated: '反馈已升级', start_overdue: '接单未开始', booking_elapsed: '预约已过期', completion_pending: '等待确认', service_window_elapsed: '服务已超时' }[value] || '需关注' }
function slotText(slot) { return slot?.starts_at ? `${formatDateTime(slot.starts_at)}${slot?.ends_at ? `—${formatDateTime(slot.ends_at)}` : ''}` : '非预约订单' }
function messageRoleText(role) { return { applicant: '咨询用户', mentor: '认证前辈', system: '平台系统' }[role] || '平台系统' }
function messageText(message) { return message?.content || (message?.message_type === 'image' ? '图片消息' : message?.message_type === 'voice' ? '语音消息' : '系统消息') }
function eventText(value) { return { consultation_order_created: '创建咨询订单', consultation_payment_intent_created: '创建支付订单', consultation_demo_payment_recorded: '免支付确认', consultation_payment_confirmed: '支付回调确认成功', consultation_payment_failed: '支付回调确认失败', consultation_refund_requested: '已提交退款处理', consultation_refund_completed: '退款回调确认完成', consultation_refund_failed: '退款回调返回异常', mentor_order_decision: '前辈处理接单', consultation_started: '咨询已开始', consultation_started_at_backfilled: '补录咨询开始时间', completion_confirmed: '一方确认结束', consultation_completed: '双方确认完成', consultation_auto_completed: '服务到期自动完成', order_cancelled_by_applicant: '咨询用户取消订单', consultation_report_created: '提交问题反馈', consultation_report_responded: '被反馈方提交说明', consultation_report_evidence_uploaded: '补充处理凭证', consultation_report_appeal_created: '提交复核申请', consultation_report_appeal_evidence_uploaded: '补充复核凭证', consultation_report_appeal_reviewing: '平台开始复核', consultation_report_reopened_after_appeal: '平台重新开启原案', consultation_report_appeal_resolved: '平台更新复核结果', consultation_report_resolved: '举报处理完成', consultation_review_hidden: '平台下架关联评价', consultation_review_restored: '平台恢复关联评价', order_timed_out: '订单超时自动取消', accepted_start_timed_out: '前辈接单后未开始，订单已取消', booking_no_show_timed_out: '预约未开始，订单已取消', admin_order_intervention: '平台主动介入' }[value] || value || '订单事件' }
function eventLabel(value) { return { consultation_report_acknowledged: '平台已受理问题反馈', consultation_report_sla_escalated: '问题反馈首响超时升级', consultation_report_priority_escalated: '问题反馈已调整优先级', consultation_report_appeal_sla_escalated: '复核首响超时升级', consultation_report_appeal_priority_escalated: '复核已调整优先级' }[value] || eventText(value) }
function eventDetailsText(details) { if (!details || typeof details !== 'object' || !Object.keys(details).length) return '已记录订单状态变化'; if (details.admin_note) return String(details.admin_note); if (details.rejection_reason) return `前辈说明：${details.rejection_reason}`; if (details.decision === 'accept') return '前辈确认接单，咨询已开始'; if (details.decision === 'reject') return '前辈暂不接受本次咨询'; if (details.is_published === false) return '关联服务评价已停止对外展示'; if (details.is_published === true) return '关联服务评价已恢复对外展示'; if (details.action) return `处理动作：${details.action}`; return Object.entries(details).map(([key, value]) => `${key}：${String(value)}`).join(' · ') }
function formatDateTime(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date) }
</script>

<style scoped>
.mentor-orders-page{min-height:calc(100vh - 158px);display:flex;flex-direction:column;color:#31465d}.order-summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.order-summary-card{min-height:112px;padding:18px 20px;border:1px solid #e2eaee;border-top:3px solid #9aa9b8;border-radius:9px;background:#fff;box-shadow:0 8px 24px rgba(39,62,79,.04)}.order-summary-card text,.order-summary-card strong,.order-summary-card small{display:block}.order-summary-card text{color:#7d8d9e;font-size:11px;font-weight:700}.order-summary-card strong{margin-top:10px;color:#314a65;font-size:28px}.order-summary-card small{margin-top:7px;color:#9aa7b4;font-size:10px}.order-summary-card.active{border-top-color:#5e94d9}.order-summary-card.report{border-top-color:#d8a553}.order-summary-card.urgent{border-top-color:#c9826e}.order-workspace{min-height:0;flex:1;display:flex;flex-direction:column;margin-top:18px;overflow:hidden;border:1px solid #e0e8ec;border-radius:10px;background:#fff;box-shadow:0 10px 30px rgba(38,59,77,.04)}.order-toolbar{padding:14px 18px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #edf1f3;background:#fbfcfd}.order-search{width:min(280px,30vw);height:38px;padding:0 10px;display:flex;align-items:center;gap:8px;flex:0 1 280px;border:1px solid #dae4e8;border-radius:8px;background:#fff}.order-search>text{color:#91a0af}.order-search input{min-width:0;height:36px;flex:1;font-size:11px}.order-search button{width:26px;height:26px;margin:0;padding:0;border:0;background:transparent;color:#93a1af}.order-select{width:142px;flex:0 0 142px}.report-select{width:148px;flex-basis:148px}.order-refresh,.order-open-button,.order-intervention-actions button{display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;line-height:1;text-align:center}.order-refresh{min-width:76px;height:36px;margin:0;padding:0 14px;flex:0 0 auto;border:1px solid #d7e3e6;border-radius:7px;background:#fff;color:#617286;font-size:10px;font-weight:750}.order-search button::after,.order-refresh::after,.order-open-button::after,.order-detail button::after,.order-pagination button::after{border:0}.order-table-wrap{min-height:0;flex:1;overflow-x:auto}.order-table{min-width:1380px;min-height:100%}.order-grid{display:grid;grid-template-columns:1.05fr 1.25fr 1.25fr 1.15fr .82fr .82fr .86fr .78fr 60px;align-items:center;gap:14px;padding:0 18px}.order-table-head{min-height:42px;color:#8796a4;background:#f7f9fa;font-size:10px;font-weight:800}.order-row{min-height:76px;border-top:1px solid #edf1f3;cursor:pointer;font-size:11px}.order-row:hover{background:#fbfefd}.order-row strong,.order-row text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.order-row strong{color:#394f65;font-size:11px}.order-row>view:not(.order-person) text,.order-person text{margin-top:4px;color:#98a5b2;font-size:9px}.order-person{min-width:0;display:flex;align-items:center;gap:9px}.order-avatar{width:34px;height:34px;display:flex;align-items:center;justify-content:center;flex:0 0 34px;border-radius:50%;font-size:12px;font-weight:900}.order-avatar.applicant{color:#4a78aa;background:#e8f2ff}.order-avatar.mentor{color:#287d6d;background:#e4f5f0}.payment-label,.order-status,.report-badge,.report-status{display:inline-flex!important;margin:0!important;padding:5px 8px;border-radius:99px;font-size:9px!important;font-weight:800}.payment-label{background:#f0f3f7;color:#7c8995!important}.payment-label.paid{background:#e8f7f2;color:#238b75!important}.payment-label.refunded{background:#fceceb;color:#b45f59!important}.order-status{background:#eef4ff;color:#5279ad!important}.order-status.pending_payment,.order-status.pending_accept,.order-status.booked{background:#fff4df;color:#ae7a29!important}.order-status.in_progress{background:#e8f7f2;color:#238b75!important}.order-status.completed{background:#edf0f3;color:#677684!important}.order-status.refunded,.order-status.cancelled,.order-status.rejected,.order-status.timeout{background:#fceceb;color:#b45f59!important}.report-badge{background:#eef3f7;color:#7a8998!important}.report-badge.open{background:#fff0e9;color:#bb695a!important}.order-open-button{height:30px;margin:0;padding:0 11px;border:0;border-radius:6px;background:#eef7f5;color:#278b78;font-size:10px;font-weight:800}.order-state{padding:54px 20px;color:#91a0ae;text-align:center;font-size:12px}.order-state.error{color:#ba6962}.order-state button{display:block;margin:12px auto 0;font-size:11px}.order-pagination{min-height:58px;padding:0 18px;display:flex;align-items:center;justify-content:space-between;gap:14px;border-top:1px solid #eaf0f2;color:#90a0af;background:#fff;font-size:10px}.order-pagination-actions{display:flex;align-items:center;gap:8px;color:#9aa8b6}.order-pagination-actions button,.order-pagination-actions>view{width:34px;height:34px;margin:0;padding:0;display:inline-flex;align-items:center;justify-content:center;border:1px solid #dfe8eb;border-radius:7px;box-sizing:border-box;color:#718295;background:#fff;font-size:16px;line-height:1}.order-pagination-actions>view{border-color:#d6eee8;color:#268b78;background:#eaf8f4;font-size:11px;font-weight:800}.order-pagination-actions button:disabled{color:#c4cdd5;background:#f8fafb}.order-backdrop{position:fixed;z-index:6000;inset:0;padding:24px;display:flex;align-items:center;justify-content:center;background:rgba(24,39,55,.38);backdrop-filter:blur(4px)}.order-detail{width:min(860px,calc(100vw - 48px));height:min(820px,calc(100vh - 48px));display:flex;flex-direction:column;overflow:hidden;border:1px solid #dfe8eb;border-radius:12px;background:#fff;box-shadow:0 30px 90px rgba(26,42,58,.24)}.order-detail-header{padding:18px 22px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e9eef1}.order-detail-header text,.order-detail-header strong{display:block}.order-detail-header text{color:#287d6d;font-size:9px;font-weight:850;letter-spacing:.12em}.order-detail-header strong{margin-top:5px;color:#30465d;font-size:17px}.order-detail-header button{width:34px;height:34px;margin:0;padding:0;border:0;border-radius:50%;background:#f2f5f7;color:#768695;font-size:20px}.order-detail-scroll{min-height:0;flex:1}.order-detail-content{padding:22px}.order-parties,.order-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));overflow:hidden;border:1px solid #e4edef;border-radius:8px}.order-parties>view,.order-fields>view{min-width:0;min-height:70px;padding:13px 14px;display:flex;flex-direction:column;justify-content:center}.order-parties>view+view,.order-fields>view:nth-child(even){border-left:1px solid #e7edf0}.order-fields>view:nth-child(n+3){border-top:1px solid #e7edf0}.order-parties text,.order-parties small,.order-fields text{color:#98a7b6;font-size:10px}.order-parties strong,.order-fields strong{margin-top:5px;overflow:hidden;color:#40566c;font-size:12px;text-overflow:ellipsis;white-space:nowrap}.order-parties small{margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.order-detail-heading{margin:20px 0 9px;color:#40566c;font-size:12px;font-weight:800}.order-block,.order-empty{padding:13px;border:1px solid #e3ebee;border-radius:8px;color:#708196;font-size:11px;line-height:1.65;background:#fbfcfd}.order-block strong,.order-block text{display:block}.order-block strong{color:#40566c;font-size:11px}.order-block text{margin-top:5px;white-space:pre-wrap}.order-empty{border-style:dashed;text-align:center}.order-report-list,.order-message-list,.order-event-list{display:grid;gap:8px}.order-report-item,.order-message,.order-event{padding:11px 12px;border:1px solid #e4ecef;border-radius:8px;background:#fbfcfd}.order-report-item>view{display:flex;align-items:center;justify-content:space-between;gap:10px}.order-report-item strong,.order-report-item small,.order-report-item>text,.order-message text,.order-message strong,.order-message small,.order-event strong,.order-event text,.order-event small{display:block}.order-report-item strong,.order-event strong{color:#4b6177;font-size:11px}.order-report-item small,.order-message text,.order-message small,.order-event text,.order-event small{margin-top:4px;color:#95a4b1;font-size:9px}.order-report-item>text{margin-top:7px;color:#52677b;font-size:11px;line-height:1.55;white-space:pre-wrap}.order-report-item .report-note{color:#287d6d}.report-status{background:#fff4df;color:#ae7a29!important}.report-status.reviewing{background:#eaf2fc;color:#4d78a6!important}.report-status.resolved{background:#e8f7f2;color:#238b75!important}.report-status.dismissed{background:#f0eef1;color:#8a7680!important}.order-message.mentor{border-color:#d7ebe5;background:#f2fbf8}.order-message.system{border-color:#e4e7f5;background:#f6f7fd}.order-message strong{margin-top:4px;color:#4b6177;font-size:11px;font-weight:650;line-height:1.55;white-space:pre-wrap}.order-event{position:relative;padding-left:18px}.order-event::before{position:absolute;top:17px;left:8px;width:5px;height:5px;border-radius:50%;background:#66a99b;content:''}.order-intervention{margin-top:20px;padding-top:1px;border-top:1px solid #e8eef1}.order-intervention-grid{display:grid;grid-template-columns:minmax(180px,.65fr) minmax(0,1.35fr);gap:14px}.order-field>text{display:block;color:#8291a0;font-size:10px;font-weight:750}.order-field.full{grid-column:1/-1}.form-select{margin-top:8px}.order-field textarea{width:100%;min-height:88px;margin-top:8px;padding:10px 11px;box-sizing:border-box;border:1px dashed #9fcfc4;border-radius:7px;color:#40566d;font-size:11px;line-height:1.5;background:#fbfefd}.order-intervention-tip{margin-top:10px;color:#8291a0;font-size:10px;line-height:1.5}.order-intervention-actions{margin-top:14px;display:flex;justify-content:flex-end}.order-intervention-actions button{min-width:126px;height:36px;margin:0;border:0;border-radius:7px;background:#287d6d;color:#fff;font-size:10px;font-weight:800}.order-intervention-actions button[disabled]{opacity:.55}@media(max-width:1100px){.order-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.order-toolbar{flex-wrap:wrap}.order-search{width:100%;flex-basis:100%}}@media(max-width:820px){.mentor-orders-page{min-height:auto}.order-detail{width:100%;height:calc(100vh - 28px)}.order-backdrop{padding:14px}.order-parties,.order-fields,.order-intervention-grid{grid-template-columns:1fr}.order-parties>view+view,.order-fields>view:nth-child(even){border-top:1px solid #e7edf0;border-left:0}.order-fields>view{border-top:1px solid #e7edf0}.order-fields>view:first-child{border-top:0}.order-field.full{grid-column:auto}.order-pagination{align-items:flex-start;flex-direction:column;justify-content:center;padding-top:12px;padding-bottom:12px}}

.order-attention{display:inline-flex!important;margin:5px 0 0!important;padding:5px 8px;border-radius:99px;background:#fff0e9;color:#bb695a!important;font-size:9px!important;font-weight:800}.order-attention.booking_elapsed,.order-attention.service_window_elapsed{background:#fff4df;color:#ae7a29!important}.order-attention.completion_pending{background:#eaf2fc;color:#4d78a6!important}.order-attention-card{margin-top:14px;padding:13px;border:1px solid #f0c8bb;border-radius:8px;background:#fff8f5}.order-attention-card strong,.order-attention-card text{display:block}.order-attention-card strong{color:#b45f59;font-size:11px}.order-attention-card text{margin-top:5px;color:#7a6570;font-size:11px;line-height:1.55}.order-attention-card.booking_elapsed,.order-attention-card.service_window_elapsed{border-color:#eed6a7;background:#fffaf0}.order-attention-card.booking_elapsed strong,.order-attention-card.service_window_elapsed strong{color:#a9792e}.order-attention-card.completion_pending{border-color:#c9dcef;background:#f6faff}.order-attention-card.completion_pending strong{color:#4d78a6}.order-field input{width:100%;height:36px;margin-top:8px;padding:0 11px;border:1px dashed #9fcfc4;border-radius:7px;box-sizing:border-box;color:#40566d;background:#fbfefd;font-size:11px}
.order-intervention-warning{margin:0 0 14px;padding:12px 13px;border:1px solid #efd6a8;border-radius:8px;background:#fffaf0}.order-intervention-warning strong,.order-intervention-warning text{display:block}.order-intervention-warning strong{color:#a9792e;font-size:11px}.order-intervention-warning text{margin-top:5px;color:#877457;font-size:10px;line-height:1.55}
.payment-label.refunding{background:#fff4df;color:#ae7a29!important}.payment-label.failed{background:#fceceb;color:#b45f59!important}
.order-detail-header button{box-sizing:border-box;width:34px;height:34px;margin:0;padding:0;border:0;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;line-height:1;text-align:center}
.order-detail-header button text{width:100%;height:100%;display:flex;align-items:center;justify-content:center;line-height:1;text-align:center}
</style>

<style scoped>
.mentor-orders-page.is-compact {
  min-height: 0;
}

.mentor-orders-page.is-compact .order-workspace {
  margin-top: 0;
}
</style>
