<template>
  <view class="community-appeals-page">
    <view class="appeal-workspace">
      <view class="appeal-toolbar">
        <view class="appeal-search"><text>⌕</text><input v-model.trim="filters.keyword" placeholder="搜索申诉说明" @input="scheduleSearch" /><button v-if="filters.keyword" @tap="clearSearch">×</button></view>
        <AdminSelect class="appeal-select" :options="statusOptions.map((item) => item.label)" :value-index="statusIndex" aria-label="申诉处理状态" @change="selectStatus" />
        <AdminSelect class="appeal-select target-select" :options="targetTypeOptions.map((item) => item.label)" :value-index="targetTypeIndex" aria-label="申诉内容类型" @change="selectTargetType" />
        <button class="appeal-refresh" :disabled="loading" @tap="refresh">{{ loading ? '刷新中…' : '刷新' }}</button>
      </view>

      <view class="appeal-table-wrap"><view class="appeal-table">
        <view class="appeal-grid appeal-table-head"><view>申诉人</view><view>原内容</view><view>申诉说明</view><view>内容类型</view><view>提交时间</view><view>状态</view><view>操作</view></view>
        <view v-if="loading" class="appeal-state">正在加载内容申诉…</view>
        <view v-else-if="loadError" class="appeal-state error"><text>内容申诉加载失败，请检查网络或后台权限。</text><button @tap="refresh">重新加载</button></view>
        <view v-else-if="appeals.length === 0" class="appeal-state">当前筛选下没有内容申诉</view>
        <view v-for="item in appeals" v-else :key="item.id" class="appeal-grid appeal-row" @tap="openAppeal(item)">
          <view class="appeal-person"><view class="appeal-avatar">{{ initial(item.appellant?.display_name) }}</view><view><strong>{{ item.appellant?.display_name || '内容作者' }}</strong><text>{{ shortId(item.appellant?.id) }}</text></view></view>
          <view class="appeal-target"><strong>{{ item.post_title || '研圈帖子' }}</strong><text>{{ item.target_excerpt || '原内容已由平台留档' }}</text></view>
          <view class="appeal-copy">{{ item.content }}</view>
          <view><text class="appeal-kind">{{ targetTypeText(item.target_type) }}</text></view>
          <view>{{ formatDateTime(item.created_at) }}</view>
          <view><text class="appeal-status" :class="item.status">{{ statusText(item.status) }}</text></view>
          <view><button class="appeal-open-button" @tap.stop="openAppeal(item)">处理</button></view>
        </view>
      </view></view>

      <view class="appeal-pagination">
        <view>共 {{ appealCount }} 条，每页 {{ pageSize }} 条</view>
        <view class="appeal-pagination-actions"><button :disabled="page <= 1 || loading" @tap="changePage(page - 1)">‹</button><view>{{ page }}</view><text>/ {{ totalPages }}</text><button :disabled="page >= totalPages || loading" @tap="changePage(page + 1)">›</button></view>
      </view>
    </view>

    <view v-if="detailVisible" class="appeal-backdrop" @tap="closeDetail"><view class="appeal-detail" @tap.stop>
      <view class="appeal-detail-header"><view><text>COMMUNITY APPEAL</text><strong>内容申诉详情</strong></view><button class="admin-modal-close" :disabled="saving" @tap="closeDetail">×</button></view>
      <scroll-view v-if="detail" scroll-y class="appeal-detail-scroll"><view class="appeal-detail-content">
        <view class="appeal-parties"><view><text>申诉人</text><strong>{{ detail.appellant?.display_name || '内容作者' }}</strong><small>{{ shortId(detail.appellant?.id) }}</small></view><view><text>被处理内容</text><strong>{{ targetTypeText(detail.target_type) }}</strong><small>{{ detail.post_title || '研圈帖子' }}</small></view></view>
        <view class="appeal-detail-heading">原内容</view><view class="appeal-block"><strong>{{ detail.post_title || '研圈帖子' }}</strong><text>{{ detail.target_excerpt || '原内容已由平台留档' }}</text></view>
        <view class="appeal-detail-heading">申诉说明</view><view class="appeal-block appeal-content">{{ detail.content }}</view>
        <view class="appeal-detail-heading">处理申诉</view>
        <view class="appeal-form-grid">
          <view class="appeal-field"><text>处理状态</text><AdminSelect class="form-select" :options="detailStatusOptions.map((item) => item.label)" :value-index="detailStatusIndex" aria-label="申诉处理状态" @change="selectDetailStatus" /></view>
          <view class="appeal-field"><text>内容处置</text><AdminSelect class="form-select" :options="detailActionOptions.map((item) => item.label)" :value-index="detailActionIndex" aria-label="申诉内容处置" @change="selectDetailAction" /></view>
          <view class="appeal-field full"><text>平台处理说明（结案必填）</text><textarea v-model.trim="adminNote" maxlength="1000" placeholder="说明复核结论；申诉人会在“我的举报”的“内容处理”中看到该说明。" /></view>
        </view>
        <view v-if="detail.admin_note" class="appeal-previous-note"><text>上次处理说明</text><strong>{{ detail.admin_note }}</strong></view>
        <view class="appeal-detail-actions"><button :disabled="saving" @tap="saveDetail">{{ saving ? '保存中…' : '保存处理结果' }}</button></view>
      </view></scroll-view>
    </view></view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { fetchQuestionAdminCommunityAppeals, updateQuestionAdminCommunityAppeal } from '../api/admin'
import AdminSelect from './AdminSelect.vue'

const props = defineProps({ preview: Boolean })
const appeals = ref([])
const appealCount = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const loadError = ref(false)
const detailVisible = ref(false)
const detail = ref(null)
const saving = ref(false)
const detailStatus = ref('pending')
const detailAction = ref('none')
const adminNote = ref('')
const filters = reactive({ status: '', target_type: '', keyword: '' })
let searchTimer = null

const statusOptions = [{ label: '全部处理状态', value: '' }, { label: '待处理', value: 'pending' }, { label: '处理中', value: 'reviewing' }, { label: '已处理', value: 'resolved' }, { label: '已驳回', value: 'dismissed' }]
const targetTypeOptions = [{ label: '全部内容类型', value: '' }, { label: '帖子申诉', value: 'post' }, { label: '评论申诉', value: 'comment' }]
const detailStatusOptions = statusOptions.slice(1)
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex((item) => item.value === filters.status)))
const targetTypeIndex = computed(() => Math.max(0, targetTypeOptions.findIndex((item) => item.value === filters.target_type)))
const detailStatusIndex = computed(() => Math.max(0, detailStatusOptions.findIndex((item) => item.value === detailStatus.value)))
const detailActionOptions = computed(() => {
  const restore = detail.value?.target_type === 'comment'
    ? { label: '恢复评论展示', value: 'restore_comment' }
    : { label: '恢复帖子展示', value: 'restore_post' }
  return [{ label: '不调整内容', value: 'none' }, restore, { label: '维持原内容处置', value: 'uphold' }]
})
const detailActionIndex = computed(() => Math.max(0, detailActionOptions.value.findIndex((item) => item.value === detailAction.value)))
const totalPages = computed(() => Math.max(1, Math.ceil(appealCount.value / pageSize)))
refresh()
onBeforeUnmount(() => { if (searchTimer) clearTimeout(searchTimer) })
defineExpose({ refresh })

async function refresh() {
  loading.value = true
  loadError.value = false
  try {
    const response = props.preview ? buildPreviewPage() : await fetchQuestionAdminCommunityAppeals({
      ...filters,
      limit: pageSize,
      offset: (page.value - 1) * pageSize
    })
    appeals.value = Array.isArray(response?.items) ? response.items : []
    appealCount.value = Number(response?.count || 0)
    if (appealCount.value > 0 && appeals.value.length === 0 && page.value > totalPages.value) {
      page.value = totalPages.value
      await refresh()
      return
    }
  } catch (error) {
    appeals.value = []
    appealCount.value = 0
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function scheduleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; refresh() }, 360)
}

function clearSearch() { filters.keyword = ''; page.value = 1; refresh() }
function selectStatus(event) { filters.status = statusOptions[Number(event?.detail?.value || 0)]?.value || ''; page.value = 1; refresh() }
function selectTargetType(event) { filters.target_type = targetTypeOptions[Number(event?.detail?.value || 0)]?.value || ''; page.value = 1; refresh() }
function changePage(next) { const target = Math.max(1, Math.min(totalPages.value, Number(next) || 1)); if (target !== page.value) { page.value = target; refresh() } }

function openAppeal(item) {
  if (!item || saving.value) return
  detail.value = { ...item }
  detailStatus.value = item.status || 'pending'
  detailAction.value = item.moderation_action || 'none'
  adminNote.value = item.admin_note || ''
  detailVisible.value = true
}

function closeDetail() {
  if (saving.value) return
  detailVisible.value = false
  detail.value = null
  adminNote.value = ''
  detailAction.value = 'none'
}

function selectDetailStatus(event) { detailStatus.value = detailStatusOptions[Number(event?.detail?.value || 0)]?.value || 'pending' }
function selectDetailAction(event) { detailAction.value = detailActionOptions.value[Number(event?.detail?.value || 0)]?.value || 'none' }

async function saveDetail() {
  const appeal = detail.value
  if (!appeal?.id || saving.value) return
  const terminal = ['resolved', 'dismissed'].includes(detailStatus.value)
  if (terminal && !adminNote.value.trim()) {
    uni.showToast({ title: '结案时请填写对申诉人的处理说明', icon: 'none' })
    return
  }
  if (detailAction.value.startsWith('restore_') && detailStatus.value !== 'resolved') {
    uni.showToast({ title: '恢复内容时请将申诉标记为已处理', icon: 'none' })
    return
  }
  if (detailAction.value === 'uphold' && detailStatus.value !== 'dismissed') {
    uni.showToast({ title: '维持原处置时请将申诉标记为已驳回', icon: 'none' })
    return
  }
  const confirmed = await new Promise((resolve) => uni.showModal({ title: '保存申诉处理结果？', content: '内容处置和平台说明会同步给申诉人，并保留管理员操作记录。', confirmText: '确认保存', success: (result) => resolve(Boolean(result.confirm)) }))
  if (!confirmed) return
  saving.value = true
  try {
    const updated = props.preview
      ? { ...appeal, status: detailStatus.value, moderation_action: detailAction.value, admin_note: adminNote.value.trim() || null, handled_at: terminal ? new Date().toISOString() : null }
      : await updateQuestionAdminCommunityAppeal(appeal.id, { status: detailStatus.value, moderation_action: detailAction.value, admin_note: adminNote.value.trim() || null })
    appeals.value = appeals.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    detail.value = { ...appeal, ...updated }
    uni.showToast({ title: '申诉处理结果已保存', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '申诉处理结果保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

function buildPreviewPage() {
  const keyword = filters.keyword.trim().toLowerCase()
  const list = previewAppeals().filter((item) => {
    if (filters.status && item.status !== filters.status) return false
    if (filters.target_type && item.target_type !== filters.target_type) return false
    return !keyword || [item.content, item.post_title, item.target_excerpt].some((value) => String(value || '').toLowerCase().includes(keyword))
  })
  const offset = (page.value - 1) * pageSize
  return { items: list.slice(offset, offset + pageSize), count: list.length }
}

function previewAppeals() {
  return [
    { id: 'preview-community-appeal-001', target_type: 'post', post_id: 'preview-post-001', appellant: { id: 'preview-user-001', display_name: '同学 A' }, target: { id: 'preview-user-001', display_name: '同学 A' }, post_title: 'Z001 备考节奏分享', target_excerpt: '整理了我三个月的复习安排，希望能给同学们一些参考。', content: '该帖分享的是本人真实复习经历，没有广告或收费引流信息，希望平台结合完整内容重新核实。', status: 'pending', moderation_action: 'none', created_at: '2026-08-23T03:20:00Z' },
    { id: 'preview-community-appeal-002', target_type: 'comment', post_id: 'preview-post-002', comment_id: 'preview-comment-002', appellant: { id: 'preview-user-002', display_name: '同学 B' }, target: { id: 'preview-user-002', display_name: '同学 B' }, post_title: '复试经验交流', target_excerpt: '我只是补充了自己的公开查询路径，并未发布任何联系方式。', content: '请复核该评论的上下文；内容没有引导站外交易，也没有留下外部联系方式。', status: 'reviewing', moderation_action: 'none', created_at: '2026-08-22T06:10:00Z' },
    { id: 'preview-community-appeal-003', target_type: 'post', post_id: 'preview-post-003', appellant: { id: 'preview-user-003', display_name: '同学 C' }, target: { id: 'preview-user-003', display_name: '同学 C' }, post_title: '复习资料互助', target_excerpt: '请大家私信交流。', content: '我认为原帖属于正常学习讨论，申请恢复展示。', status: 'dismissed', moderation_action: 'uphold', admin_note: '经复核，内容包含站外交易引导，平台维持原处置。', created_at: '2026-08-20T09:00:00Z', handled_at: '2026-08-20T11:10:00Z' }
  ]
}

function initial(value) { return String(value || '申').slice(0, 1) || '申' }
function shortId(value) { const id = String(value || ''); return id ? `${id.slice(0, 8)}…${id.slice(-4)}` : '—' }
function targetTypeText(value) { return value === 'comment' ? '评论申诉' : '帖子申诉' }
function statusText(value) { return { pending: '待处理', reviewing: '处理中', resolved: '已处理', dismissed: '已驳回' }[value] || '待处理' }
function formatDateTime(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date) }
</script>

<style scoped>
.community-appeals-page{min-height:calc(100vh - 158px);display:flex;flex-direction:column;color:#31465d}.appeal-summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.appeal-summary-card{min-height:112px;padding:18px 20px;border:1px solid #e2eaee;border-top:3px solid #8495a5;border-radius:9px;background:#fff;box-shadow:0 8px 24px rgba(39,62,79,.04)}.appeal-summary-card text,.appeal-summary-card strong,.appeal-summary-card small{display:block}.appeal-summary-card text{color:#7d8d9e;font-size:11px;font-weight:700}.appeal-summary-card strong{margin-top:10px;color:#314a65;font-size:28px}.appeal-summary-card small{margin-top:7px;color:#9aa7b4;font-size:10px}.appeal-summary-card.pending{border-top-color:#dbaf55}.appeal-summary-card.reviewing{border-top-color:#7b9cc7}.appeal-summary-card.closed{border-top-color:#57cdb7}.appeal-workspace{min-height:0;flex:1;display:flex;flex-direction:column;margin-top:18px;overflow:hidden;border:1px solid #e0e8ec;border-radius:10px;background:#fff;box-shadow:0 10px 30px rgba(38,59,77,.04)}.appeal-toolbar{padding:14px 18px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #edf1f3;background:#fbfcfd}.appeal-search{width:min(360px,42vw);height:38px;padding:0 10px;display:flex;align-items:center;gap:8px;flex:0 1 360px;border:1px solid #dae4e8;border-radius:8px;background:#fff}.appeal-search>text{color:#91a0af}.appeal-search input{min-width:0;height:36px;flex:1;font-size:11px}.appeal-search button{width:26px;height:26px;margin:0;padding:0;border:0;background:transparent;color:#93a1af}.appeal-select{width:158px;flex:0 0 158px}.target-select{width:142px;flex-basis:142px}.appeal-refresh,.appeal-open-button,.appeal-detail-actions button{display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;line-height:1;text-align:center}.appeal-refresh{min-width:76px;height:36px;margin:0;padding:0 14px;flex:0 0 auto;border:1px solid #d7e3e6;border-radius:7px;background:#fff;color:#617286;font-size:10px;font-weight:750}.appeal-search button::after,.appeal-refresh::after,.appeal-open-button::after,.appeal-detail button::after,.appeal-pagination button::after{border:0}.appeal-table-wrap{min-height:0;flex:1;overflow-x:auto}.appeal-table{min-width:1150px;min-height:100%}.appeal-grid{display:grid;grid-template-columns:1.1fr 1.35fr 1.8fr .72fr .85fr .75fr 60px;align-items:center;gap:14px;padding:0 18px}.appeal-table-head{min-height:42px;color:#8796a4;background:#f7f9fa;font-size:10px;font-weight:800}.appeal-row{min-height:76px;border-top:1px solid #edf1f3;cursor:pointer;font-size:11px}.appeal-row:hover{background:#fbfefd}.appeal-row strong,.appeal-row text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.appeal-row strong{color:#394f65;font-size:11px}.appeal-row>view:not(.appeal-person) text,.appeal-person text{margin-top:4px;color:#98a5b2;font-size:9px}.appeal-person{min-width:0;display:flex;align-items:center;gap:10px}.appeal-avatar{width:36px;height:36px;display:flex;align-items:center;justify-content:center;flex:0 0 36px;border-radius:50%;background:#edf2ff;color:#526ed5;font-size:13px;font-weight:900}.appeal-target,.appeal-copy{min-width:0}.appeal-copy{overflow:hidden;display:-webkit-box;color:#718297;font-size:10px;line-height:1.4;-webkit-box-orient:vertical;-webkit-line-clamp:2}.appeal-kind,.appeal-status{display:inline-flex!important;margin:0!important;padding:5px 8px;border-radius:99px;font-size:9px!important;font-weight:800}.appeal-kind{background:#eef5fc;color:#5880a6!important}.appeal-status{background:#fff4df;color:#ae7a29!important}.appeal-status.reviewing{background:#eaf2fc;color:#4d78a6!important}.appeal-status.resolved{background:#e8f7f2;color:#238b75!important}.appeal-status.dismissed{background:#f0eef1;color:#8a7680!important}.appeal-open-button{height:30px;margin:0;padding:0 11px;border:0;border-radius:6px;background:#eef7f5;color:#278b78;font-size:10px;font-weight:800}.appeal-state{padding:54px 20px;color:#91a0ae;text-align:center;font-size:12px}.appeal-state.error{color:#ba6962}.appeal-state button{display:block;margin:12px auto 0;font-size:11px}.appeal-pagination{min-height:58px;padding:0 18px;display:flex;align-items:center;justify-content:space-between;gap:14px;border-top:1px solid #eaf0f2;color:#90a0af;background:#fff;font-size:10px}.appeal-pagination-actions{display:flex;align-items:center;gap:8px;color:#9aa8b6}.appeal-pagination-actions button,.appeal-pagination-actions>view{width:34px;height:34px;margin:0;padding:0;display:inline-flex;align-items:center;justify-content:center;border:1px solid #dfe8eb;border-radius:7px;box-sizing:border-box;color:#718295;background:#fff;font-size:16px;line-height:1}.appeal-pagination-actions>view{border-color:#d6eee8;color:#268b78;background:#eaf8f4;font-size:11px;font-weight:800}.appeal-pagination-actions button:disabled{color:#c4cdd5;background:#f8fafb}.appeal-backdrop{position:fixed;z-index:6000;inset:0;padding:24px;display:flex;align-items:center;justify-content:center;background:rgba(24,39,55,.38);backdrop-filter:blur(4px)}.appeal-detail{width:min(760px,calc(100vw - 48px));height:min(760px,calc(100vh - 48px));display:flex;flex-direction:column;overflow:hidden;border:1px solid #dfe8eb;border-radius:12px;background:#fff;box-shadow:0 30px 90px rgba(26,42,58,.24)}.appeal-detail-header{padding:18px 22px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e9eef1}.appeal-detail-header text,.appeal-detail-header strong{display:block}.appeal-detail-header text{color:#526ed5;font-size:9px;font-weight:850;letter-spacing:.12em}.appeal-detail-header strong{margin-top:5px;color:#30465d;font-size:17px}.appeal-detail-header button{width:34px;height:34px;margin:0;padding:0;border:0;border-radius:50%;background:#f2f5f7;color:#768695;font-size:20px}.appeal-detail-scroll{min-height:0;flex:1}.appeal-detail-content{padding:22px}.appeal-parties{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));overflow:hidden;border:1px solid #e4edef;border-radius:8px}.appeal-parties>view{min-width:0;min-height:74px;padding:13px 14px;display:flex;flex-direction:column;justify-content:center}.appeal-parties>view+view{border-left:1px solid #e7edf0}.appeal-parties text,.appeal-parties small{color:#98a7b6;font-size:10px}.appeal-parties strong{margin-top:5px;overflow:hidden;color:#40566c;font-size:12px;text-overflow:ellipsis;white-space:nowrap}.appeal-parties small{margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.appeal-detail-heading{margin:20px 0 9px;color:#40566c;font-size:12px;font-weight:800}.appeal-block{padding:13px;border:1px solid #e3ebee;border-radius:8px;color:#52677b;background:#fbfcfd}.appeal-block strong,.appeal-block text{display:block}.appeal-block strong{color:#40566c;font-size:11px}.appeal-block text,.appeal-content{margin-top:5px;font-size:11px;line-height:1.65;white-space:pre-wrap}.appeal-content{margin-top:0}.appeal-form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.appeal-field{min-width:0}.appeal-field>text{display:block;color:#8291a0;font-size:10px;font-weight:750}.appeal-field.full{grid-column:1/-1}.appeal-field textarea{width:100%;min-height:88px;margin-top:8px;padding:10px 11px;box-sizing:border-box;border:1px dashed #a8bad3;border-radius:7px;color:#40566d;font-size:11px;line-height:1.5;background:#fbfcff}.form-select{margin-top:8px}.appeal-previous-note{margin-top:18px;padding:12px 13px;border:1px solid #e1eaed;border-radius:8px;background:#fbfcfd}.appeal-previous-note text,.appeal-previous-note strong{display:block}.appeal-previous-note text{color:#93a1ae;font-size:9px}.appeal-previous-note strong{margin-top:5px;color:#52677b;font-size:11px;line-height:1.5}.appeal-detail-actions{margin-top:18px;display:flex;justify-content:flex-end}.appeal-detail-actions button{min-width:126px;height:36px;margin:0;border:0;border-radius:7px;background:#526ed5;color:#fff;font-size:10px;font-weight:800}@media(max-width:960px){.appeal-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.appeal-toolbar{flex-wrap:wrap}.appeal-search{width:100%;flex-basis:100%}}@media(max-width:820px){.community-appeals-page{min-height:auto}.appeal-detail{width:100%;height:calc(100vh - 28px)}.appeal-backdrop{padding:14px}.appeal-parties,.appeal-form-grid{grid-template-columns:1fr}.appeal-parties>view+view{border-top:1px solid #e7edf0;border-left:0}.appeal-field.full{grid-column:auto}.appeal-pagination{align-items:flex-start;flex-direction:column;justify-content:center;padding-top:12px;padding-bottom:12px}}
</style>

<style scoped>
.appeal-workspace {
  margin-top: 0;
}
</style>
