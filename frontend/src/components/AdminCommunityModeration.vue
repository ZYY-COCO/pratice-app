<template>
  <view class="community-moderation-page">
    <view class="community-moderation-workspace">
      <view class="community-moderation-toolbar">
        <view class="community-moderation-search"><text>⌕</text><input v-model.trim="filters.keyword" placeholder="搜索举报原因或说明" @input="scheduleLoad" /><button v-if="filters.keyword" @tap="clearSearch">×</button></view>
        <AdminSelect class="community-moderation-select" :options="statusOptions.map((item) => item.label)" :value-index="statusIndex" aria-label="举报状态筛选" @change="changeStatus" />
        <AdminSelect class="community-moderation-select" :options="targetTypeOptions.map((item) => item.label)" :value-index="targetTypeIndex" aria-label="举报内容类型筛选" @change="changeTargetType" />
        <button class="community-moderation-refresh" :disabled="loading" @tap="refresh">{{ loading ? '刷新中…' : '刷新' }}</button>
      </view>

      <view class="community-moderation-table-wrap"><view class="community-moderation-table">
        <view class="community-moderation-grid table-head"><view>举报对象</view><view>举报人</view><view>举报原因</view><view>举报说明</view><view>提交时间</view><view>状态</view><view class="action-cell">操作</view></view>
        <view v-if="loading" class="table-state">正在读取内容举报…</view>
        <view v-else-if="loadError" class="table-state error"><text>内容举报加载失败，请检查网络或权限。</text><button @tap="refresh">重新加载</button></view>
        <view v-else-if="reports.length === 0" class="table-state">当前筛选下没有内容举报</view>
        <view v-for="report in reports" v-else :key="report.id" class="community-moderation-grid table-row" @tap="openDetail(report)">
          <view class="target-cell"><text class="target-kind">{{ report.target_type === 'comment' ? '评论' : '帖子' }}</text><strong>{{ report.post_title || '研圈内容' }}</strong><small>{{ report.target?.display_name || '内容发布者' }}</small></view>
          <view><strong>{{ report.reporter?.display_name || '举报用户' }}</strong><small>{{ shortId(report.reporter?.id) }}</small></view>
          <view><text class="reason-pill">{{ report.reason }}</text></view>
          <view class="report-copy">{{ report.content }}</view>
          <view>{{ formatDateTime(report.created_at) }}</view>
          <view><text class="status-pill" :class="report.status">{{ statusText(report.status) }}</text></view>
          <view class="action-cell"><button class="open-button" @tap.stop="openDetail(report)">处理</button></view>
        </view>
      </view></view>

      <view class="community-moderation-pagination"><view>共 {{ reportCount }} 条，每页 {{ pageSize }} 条</view><view><button :disabled="page <= 1 || loading" @tap="changePage(page - 1)">‹</button><text>{{ page }} / {{ totalPages }}</text><button :disabled="page >= totalPages || loading" @tap="changePage(page + 1)">›</button></view></view>
    </view>

    <view v-if="detailVisible" class="moderation-backdrop" @tap="closeDetail"><view class="moderation-detail" @tap.stop>
      <view class="moderation-detail-head"><view><text>COMMUNITY REPORT</text><strong>内容举报处理</strong></view><button class="admin-modal-close" :disabled="saving" @tap="closeDetail">×</button></view>
      <scroll-view scroll-y class="moderation-detail-scroll"><view v-if="detail" class="moderation-detail-content">
        <view class="moderation-target-card"><view><text>{{ detail.target_type === 'comment' ? '被举报评论所在帖子' : '被举报帖子' }}</text><strong>{{ detail.post_title || '研圈内容' }}</strong><small>发布者：{{ detail.target?.display_name || '用户' }}</small></view><text class="status-pill" :class="detail.status">{{ statusText(detail.status) }}</text></view>
        <view class="moderation-section-title">被举报内容</view><view class="moderation-content-box">{{ detail.target_excerpt || '原内容已由平台留档' }}</view>
        <view class="moderation-section-title">举报说明</view><view class="moderation-content-box"><strong>{{ detail.reason }}</strong><text>{{ detail.content }}</text></view>
        <view class="moderation-parties"><view><text>举报人</text><strong>{{ detail.reporter?.display_name || '用户' }}</strong></view><view><text>举报对象</text><strong>{{ detail.target?.display_name || '用户' }}</strong></view></view>
        <view class="moderation-section-title">处理结论</view>
        <view class="moderation-form"><view><text>处理状态</text><AdminSelect :options="statusOptions.slice(1).map((item) => item.label)" :value-index="detailStatusIndex" aria-label="内容举报处理状态" @change="changeDetailStatus" /></view><view><text>内容处置</text><AdminSelect :options="availableActionOptions.map((item) => item.label)" :value-index="detailActionIndex" aria-label="内容处置动作" @change="changeDetailAction" /></view></view>
        <textarea v-model.trim="adminNote" class="moderation-note" maxlength="1000" placeholder="结案时请给举报人填写清楚、可理解的处理说明" />
        <view class="moderation-note-count">{{ adminNote.length }} / 1000</view>
        <view class="moderation-detail-actions"><button :disabled="saving" @tap="save">{{ saving ? '保存中…' : '保存处理结果' }}</button></view>
      </view></scroll-view>
    </view></view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { fetchQuestionAdminCommunityReports, updateQuestionAdminCommunityReport } from '../api/admin'
import AdminSelect from './AdminSelect.vue'

const props = defineProps({ preview: Boolean })
const pageSize = 20
const reports = ref([])
const reportCount = ref(0)
const page = ref(1)
const loading = ref(false)
const loadError = ref(false)
const filters = reactive({ status: '', target_type: '', keyword: '' })
const detail = ref(null)
const detailVisible = ref(false)
const saving = ref(false)
const detailStatus = ref('pending')
const detailAction = ref('none')
const adminNote = ref('')
let debounceTimer = null

const statusOptions = [
  { label: '全部处理状态', value: '' },
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'reviewing' },
  { label: '已处理', value: 'resolved' },
  { label: '已驳回', value: 'dismissed' }
]
const targetTypeOptions = [{ label: '全部内容类型', value: '' }, { label: '帖子', value: 'post' }, { label: '评论', value: 'comment' }]
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex((item) => item.value === filters.status)))
const targetTypeIndex = computed(() => Math.max(0, targetTypeOptions.findIndex((item) => item.value === filters.target_type)))
const detailStatusIndex = computed(() => Math.max(0, statusOptions.slice(1).findIndex((item) => item.value === detailStatus.value)))
const availableActionOptions = computed(() => {
  if (detail.value?.target_type === 'comment') return [
    { label: '不变更内容', value: 'none' },
    { label: '下架评论', value: 'hide_comment' },
    { label: '恢复评论', value: 'restore_comment' }
  ]
  return [
    { label: '不变更内容', value: 'none' },
    { label: '下架帖子', value: 'hide_post' },
    { label: '恢复帖子', value: 'restore_post' }
  ]
})
const detailActionIndex = computed(() => Math.max(0, availableActionOptions.value.findIndex((item) => item.value === detailAction.value)))
const totalPages = computed(() => Math.max(1, Math.ceil(reportCount.value / pageSize)))

refresh()
onBeforeUnmount(() => { if (debounceTimer) clearTimeout(debounceTimer) })
defineExpose({ refresh })

async function refresh() {
  loading.value = true
  loadError.value = false
  try {
    if (props.preview) {
      const filtered = previewReports().filter((item) => (!filters.status || item.status === filters.status) && (!filters.target_type || item.target_type === filters.target_type) && (!filters.keyword || `${item.reason}${item.content}`.includes(filters.keyword)))
      reportCount.value = filtered.length
      reports.value = filtered.slice((page.value - 1) * pageSize, page.value * pageSize)
      return
    }
    const pageResponse = await fetchQuestionAdminCommunityReports({ ...filters, limit: pageSize, offset: (page.value - 1) * pageSize })
    reports.value = Array.isArray(pageResponse?.items) ? pageResponse.items : []
    reportCount.value = Number(pageResponse?.count || 0)
    if (reports.value.length === 0 && reportCount.value && page.value > totalPages.value) { page.value = totalPages.value; return refresh() }
  } catch (error) {
    reports.value = []
    reportCount.value = 0
    loadError.value = true
  } finally { loading.value = false }
}

function scheduleLoad() { if (debounceTimer) clearTimeout(debounceTimer); debounceTimer = setTimeout(() => { page.value = 1; refresh() }, 360) }
function clearSearch() { filters.keyword = ''; page.value = 1; refresh() }
function changeStatus(event) { filters.status = statusOptions[Number(event?.detail?.value || 0)]?.value || ''; page.value = 1; refresh() }
function changeTargetType(event) { filters.target_type = targetTypeOptions[Number(event?.detail?.value || 0)]?.value || ''; page.value = 1; refresh() }
function changePage(next) { const normalized = Math.max(1, Math.min(totalPages.value, Number(next || 1))); if (normalized !== page.value) { page.value = normalized; refresh() } }
function openDetail(report) { detail.value = { ...report }; detailStatus.value = report.status || 'pending'; detailAction.value = availableActionFor(report); adminNote.value = report.admin_note || ''; detailVisible.value = true }
function availableActionFor(report) { return availableActionsForType(report?.target_type).some((item) => item.value === report?.moderation_action) ? report.moderation_action : 'none' }
function availableActionsForType(type) { return type === 'comment' ? [{ value: 'none' }, { value: 'hide_comment' }, { value: 'restore_comment' }] : [{ value: 'none' }, { value: 'hide_post' }, { value: 'restore_post' }] }
function closeDetail() { if (saving.value) return; detailVisible.value = false; detail.value = null; adminNote.value = '' }
function changeDetailStatus(event) { detailStatus.value = statusOptions.slice(1)[Number(event?.detail?.value || 0)]?.value || 'pending' }
function changeDetailAction(event) { detailAction.value = availableActionOptions.value[Number(event?.detail?.value || 0)]?.value || 'none' }

async function save() {
  if (!detail.value?.id || saving.value) return
  if (['resolved', 'dismissed'].includes(detailStatus.value) && !adminNote.value.trim()) { uni.showToast({ title: '结案时请填写处理说明', icon: 'none' }); return }
  if (detailAction.value !== 'none' && !['resolved', 'dismissed'].includes(detailStatus.value)) { uni.showToast({ title: '内容处置需要同步将举报结案', icon: 'none' }); return }
  if (detailAction.value.startsWith('hide_') && detailStatus.value !== 'resolved') { uni.showToast({ title: '下架内容时请将举报标记为已处理', icon: 'none' }); return }
  if (detailAction.value.startsWith('restore_') && detailStatus.value !== 'dismissed') { uni.showToast({ title: '恢复内容时请将举报标记为已驳回', icon: 'none' }); return }
  saving.value = true
  try {
    const updated = props.preview ? { ...detail.value, status: detailStatus.value, moderation_action: detailAction.value, admin_note: adminNote.value.trim() || null, handled_at: ['resolved', 'dismissed'].includes(detailStatus.value) ? new Date().toISOString() : null } : await updateQuestionAdminCommunityReport(detail.value.id, { status: detailStatus.value, moderation_action: detailAction.value, admin_note: adminNote.value.trim() || null })
    reports.value = reports.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    detail.value = { ...detail.value, ...updated }
    uni.showToast({ title: '内容举报已更新', icon: 'success' })
    await refresh()
  } catch (error) { uni.showToast({ title: error?.detail || '处理结果保存失败', icon: 'none' }) } finally { saving.value = false }
}

function statusText(value) { return { pending: '待处理', reviewing: '处理中', resolved: '已处理', dismissed: '已驳回' }[value] || '待处理' }
function shortId(value) { const id = String(value || ''); return id ? `${id.slice(0, 8)}…` : '—' }
function formatDateTime(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date) }
function previewReports() { return [
  { id: 'preview-community-report-1', target_type: 'post', post_id: 'post-1', reporter: { id: 'user-1', display_name: '同学 A' }, target: { id: 'user-2', display_name: '研友 B' }, post_title: '求助：备考资料整理', target_excerpt: '帖子中含有引流联系方式，请平台核实。', reason: '广告或引流', content: '帖子末尾留下了外部群聊和付费资料链接，影响正常交流。', status: 'pending', moderation_action: 'none', created_at: '2026-08-23T02:00:00Z' },
  { id: 'preview-community-report-2', target_type: 'comment', post_id: 'post-2', comment_id: 'comment-2', reporter: { id: 'user-3', display_name: '同学 C' }, target: { id: 'user-4', display_name: '研友 D' }, post_title: 'Z001 复习节奏分享', target_excerpt: '评论中出现人身攻击内容。', reason: '骚扰、辱骂或不当言行', content: '评论含有明显辱骂内容，希望平台处理。', status: 'reviewing', moderation_action: 'none', created_at: '2026-08-22T06:10:00Z' }
] }
</script>

<style scoped>
.community-moderation-page{min-height:calc(100vh - 158px);color:#31465d}.community-moderation-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.summary-card{min-height:112px;padding:18px 20px;border:1px solid #e2eaee;border-top:3px solid #8b9bad;border-radius:9px;background:#fff;box-shadow:0 8px 24px rgba(39,62,79,.04)}.summary-card text,.summary-card strong,.summary-card small{display:block}.summary-card text{color:#7d8d9e;font-size:11px;font-weight:700}.summary-card strong{margin-top:10px;color:#314a65;font-size:28px}.summary-card small{margin-top:7px;color:#9aa7b4;font-size:10px}.summary-card.pending{border-top-color:#dbaf55}.summary-card.reviewing{border-top-color:#7197c3}.summary-card.resolved{border-top-color:#57cdb7}.community-moderation-workspace{min-height:0;margin-top:18px;border:1px solid #e0e8ec;border-radius:10px;background:#fff;overflow:hidden;box-shadow:0 10px 30px rgba(38,59,77,.04)}.community-moderation-toolbar{padding:14px 18px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #edf1f3;background:#fbfcfd}.community-moderation-search{height:38px;min-width:260px;flex:1;padding:0 10px;display:flex;align-items:center;gap:8px;border:1px solid #dae4e8;border-radius:8px;background:#fff}.community-moderation-search input{min-width:0;flex:1;height:36px;font-size:11px}.community-moderation-search button{width:26px;height:26px;margin:0;padding:0;border:0;background:transparent;color:#93a1af}.community-moderation-select{width:154px;flex:0 0 154px}.community-moderation-refresh{height:36px;min-width:76px;margin:0;padding:0 14px;border:1px solid #d7e3e6;border-radius:7px;background:#fff;color:#617286;font-size:10px;font-weight:750}.community-moderation-refresh::after,.community-moderation-search button::after,.open-button::after,.moderation-detail button::after{border:0}.community-moderation-table-wrap{overflow-x:auto}.community-moderation-table{min-width:1080px}.community-moderation-grid{display:grid;grid-template-columns:1.2fr .85fr 1fr 1.75fr .78fr .72fr 60px;align-items:center;gap:14px;padding:0 18px}.table-head{min-height:42px;color:#8796a4;background:#f7f9fa;font-size:10px;font-weight:800}.table-row{min-height:76px;border-top:1px solid #edf1f3;cursor:pointer;font-size:11px}.table-row:hover{background:#fbfefd}.table-row strong,.table-row small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.table-row strong{color:#394f65;font-size:11px}.table-row small{margin-top:4px;color:#98a5b2;font-size:9px}.target-cell{min-width:0}.target-kind,.reason-pill,.status-pill{display:inline-flex!important;margin:0!important;padding:5px 8px;border-radius:99px;font-size:9px!important;font-weight:800}.target-kind{margin-bottom:5px!important;background:#edf4ff;color:#577cab!important}.reason-pill{max-width:100%;overflow:hidden;background:#fff5df;color:#80672f!important;text-overflow:ellipsis;white-space:nowrap}.report-copy{overflow:hidden;display:-webkit-box;color:#718297;font-size:10px;line-height:1.4;-webkit-box-orient:vertical;-webkit-line-clamp:2}.status-pill.pending{background:#fff4df;color:#ae7a29}.status-pill.reviewing{background:#eaf2fc;color:#4e78a7}.status-pill.resolved{background:#e8f7f2;color:#238b75}.status-pill.dismissed{background:#f0eef1;color:#817783}.open-button{height:30px;margin:0;padding:0 11px;border:0;border-radius:6px;background:#eef7f5;color:#278b78;font-size:10px;font-weight:800}.table-state{padding:54px 20px;color:#91a0ae;text-align:center;font-size:12px}.table-state.error{color:#ba6962}.table-state button{display:block;margin:12px auto 0;font-size:11px}.community-moderation-pagination{min-height:58px;padding:0 18px;display:flex;align-items:center;justify-content:space-between;border-top:1px solid #eaf0f2;color:#90a0af;font-size:10px}.community-moderation-pagination>view:last-child{display:flex;align-items:center;gap:8px}.community-moderation-pagination button{width:34px;height:34px;margin:0;padding:0;border:1px solid #dfe8eb;border-radius:7px;background:#fff;color:#718295;font-size:16px}.community-moderation-pagination button:disabled{color:#c4cdd5;background:#f8fafb}.community-moderation-pagination button::after{border:0}.moderation-backdrop{position:fixed;z-index:6000;inset:0;padding:24px;display:flex;align-items:center;justify-content:center;background:rgba(24,39,55,.38);backdrop-filter:blur(4px)}.moderation-detail{width:min(760px,calc(100vw - 48px));height:min(760px,calc(100vh - 48px));display:flex;flex-direction:column;overflow:hidden;border:1px solid #dfe8eb;border-radius:12px;background:#fff;box-shadow:0 30px 90px rgba(26,42,58,.24)}.moderation-detail-head{padding:18px 22px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e9eef1}.moderation-detail-head text,.moderation-detail-head strong{display:block}.moderation-detail-head text{color:#35a78f;font-size:9px;font-weight:850;letter-spacing:.12em}.moderation-detail-head strong{margin-top:5px;color:#30465d;font-size:17px}.moderation-detail-head button{width:34px;height:34px;margin:0;padding:0;border:0;border-radius:50%;background:#f2f5f7;color:#768695;font-size:20px}.moderation-detail-scroll{min-height:0;flex:1}.moderation-detail-content{padding:22px}.moderation-target-card{padding-bottom:17px;display:flex;align-items:center;justify-content:space-between;gap:14px;border-bottom:1px solid #e8eef1}.moderation-target-card>view{min-width:0}.moderation-target-card text,.moderation-target-card strong,.moderation-target-card small{display:block}.moderation-target-card>view>text,.moderation-target-card small{color:#98a7b6;font-size:10px}.moderation-target-card strong{margin-top:5px;overflow:hidden;color:#40566c;font-size:13px;text-overflow:ellipsis;white-space:nowrap}.moderation-target-card small{margin-top:5px}.moderation-section-title{margin:20px 0 9px;color:#40566c;font-size:12px;font-weight:800}.moderation-content-box{padding:13px;border:1px solid #e3ebee;border-radius:8px;color:#52677b;font-size:11px;line-height:1.65;background:#fbfcfd;white-space:pre-wrap}.moderation-content-box strong,.moderation-content-box text{display:block}.moderation-content-box strong{margin-bottom:7px;color:#40566c}.moderation-parties,.moderation-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.moderation-parties{margin-top:16px}.moderation-parties>view{padding:12px;border:1px solid #e4edef;border-radius:8px}.moderation-parties text,.moderation-parties strong{display:block}.moderation-parties text{color:#98a7b6;font-size:10px}.moderation-parties strong{margin-top:5px;color:#40566c;font-size:11px}.moderation-form>view>text{display:block;margin-bottom:8px;color:#718397;font-size:10px;font-weight:800}.moderation-note{width:100%;min-height:92px;margin-top:14px;padding:10px 11px;border:1px dashed #9fcfc4;border-radius:7px;box-sizing:border-box;color:#40566d;font-size:11px;line-height:1.5;background:#fbfefd}.moderation-note-count{margin-top:5px;color:#9aa8b6;text-align:right;font-size:9px}.moderation-detail-actions{margin-top:14px;display:flex;justify-content:flex-end}.moderation-detail-actions button{min-width:124px;height:36px;margin:0;border:0;border-radius:7px;background:#34b399;color:#fff;font-size:10px;font-weight:800}@media(max-width:960px){.community-moderation-summary{grid-template-columns:repeat(2,minmax(0,1fr))}.community-moderation-toolbar{flex-wrap:wrap}.community-moderation-search{flex-basis:100%}}@media(max-width:820px){.community-moderation-page{min-height:auto}.moderation-backdrop{padding:14px}.moderation-detail{width:100%;height:calc(100vh - 28px)}.moderation-detail-content{padding:18px}.moderation-parties,.moderation-form{grid-template-columns:1fr}.community-moderation-pagination{align-items:flex-start;flex-direction:column;justify-content:center;padding-top:12px;padding-bottom:12px}}
</style>

<style scoped>
.community-moderation-workspace {
  margin-top: 0;
}

.community-moderation-refresh,
.open-button,
.moderation-detail-head button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  line-height: 1;
  text-align: center;
}

.moderation-detail-head button {
  flex: 0 0 34px;
  padding: 0;
}

.target-cell {
  align-self: stretch;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 0;
  text-align: center;
}

.action-cell {
  align-self: stretch;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}
</style>
