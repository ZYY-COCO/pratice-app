<template>
  <view class="mentor-application-page">
    <view class="summary-grid">
      <view class="summary-card"><text>全部申请</text><strong>{{ applicationCount }}</strong><small>已收到的前辈申请</small></view>
      <view class="summary-card pending"><text>待审核</text><strong>{{ pendingCount }}</strong><small>等待管理员处理</small></view>
      <view class="summary-card approved"><text>已通过</text><strong>{{ approvedCount }}</strong><small>已建立前辈档案</small></view>
      <view class="summary-card rejected"><text>未通过</text><strong>{{ rejectedCount }}</strong><small>已完成审核反馈</small></view>
    </view>

    <view class="application-workspace">
      <view class="toolbar"><view class="search"><text>⌕</text><input v-model.trim="filters.keyword" placeholder="搜索申请人、院校或专业" @input="handleSearch" /><button v-if="filters.keyword" @tap="clearSearch">×</button></view><AdminSelect class="status-select" :options="statusOptions.map((item) => item.label)" :value-index="statusIndex" aria-label="申请状态" @change="selectStatus" /><button class="refresh-button" :disabled="loading" @tap="refresh">{{ loading ? '刷新中…' : '刷新' }}</button></view>

      <view class="table-wrap"><view class="table">
        <view class="grid table-head"><view>申请人</view><view>申请信息</view><view>申请留言</view><view>证明材料</view><view>提交时间</view><view>状态</view><view>操作</view></view>
        <view v-if="loading" class="table-state">正在加载前辈申请…</view>
        <view v-else-if="loadError" class="table-state error"><text>前辈申请加载失败，请检查网络和后台权限。</text><button @tap="refresh">重新加载</button></view>
        <view v-else-if="applications.length === 0" class="table-state">当前筛选下没有前辈申请</view>
        <view v-for="item in applications" v-else :key="item.id" class="grid row" @tap="openApplication(item)">
          <view class="applicant"><view class="avatar">{{ item.legal_name?.slice(0, 1) || '前' }}</view><view><strong>{{ item.legal_name || '未填写姓名' }}</strong><text>申请成为前辈</text></view></view>
          <view><strong>{{ item.school }}</strong><text>{{ item.major }} · {{ item.admission_year }}级</text></view>
          <view class="message">{{ item.bio || '未填写个人留言' }}</view>
          <view><text class="document-count">{{ item.document_count || 0 }} 份材料</text></view>
          <view>{{ formatDateTime(item.created_at) }}</view>
          <view><text class="status" :class="item.application_status">{{ statusText(item.application_status) }}</text></view>
          <view><button class="open-button" @tap.stop="openApplication(item)">查看</button></view>
        </view>
      </view></view>

      <view class="mentor-pagination">
        <view class="mentor-pagination-info">共 {{ applicationCount }} 条，每页 {{ applicationPageSize }} 条</view>
        <view class="mentor-pagination-actions">
          <button :disabled="applicationPage <= 1 || loading" @tap="changeApplicationPage(applicationPage - 1)">‹</button>
          <view class="mentor-page-current">{{ applicationPage }}</view>
          <view class="mentor-page-total">/ {{ applicationTotalPages }}</view>
          <button :disabled="applicationPage >= applicationTotalPages || loading" @tap="changeApplicationPage(applicationPage + 1)">›</button>
        </view>
      </view>
    </view>

    <view v-if="detailVisible" class="backdrop" @tap="closeApplication"><view class="detail" @tap.stop>
      <view class="detail-header"><view><text>MENTOR APPLICATION</text><strong>前辈申请详情</strong></view><button :disabled="saving" @tap="closeApplication">×</button></view>
      <view v-if="detailLoading" class="table-state">正在读取申请详情…</view>
      <scroll-view v-else-if="detail?.application" scroll-y class="detail-scroll"><view class="detail-content">
        <view class="applicant-card"><view class="avatar large">{{ detail.application.legal_name?.slice(0, 1) || '前' }}</view><view><strong>{{ detail.applicant?.nickname || detail.application.legal_name }}</strong><text>{{ detail.applicant?.email || detail.applicant?.phone || shortId(detail.application.applicant_user_id) }}</text></view><text class="status" :class="detail.application.application_status">{{ statusText(detail.application.application_status) }}</text></view>
        <view class="application-fields"><view><text>真实姓名</text><strong>{{ detail.application.legal_name }}</strong></view><view><text>录取院校</text><strong>{{ detail.application.school }}</strong></view><view><text>录取专业</text><strong>{{ detail.application.major }}</strong></view><view><text>入学年份</text><strong>{{ detail.application.admission_year }} 年</strong></view><view><text>毕业年份</text><strong>{{ detail.application.graduation_year ? `${detail.application.graduation_year} 年` : '未填写' }}</strong></view><view><text>考试类别</text><strong>{{ examTypeText(detail.application.exam_type) }}</strong></view><view><text>初试成绩</text><strong>{{ detail.application.score }} 分</strong></view><view><text>咨询价格</text><strong>¥{{ formatPrice(detail.application.price) }} / 次</strong></view></view>
        <view class="detail-heading">擅长领域</view><view v-if="detail.application.skills?.length" class="skill-list"><text v-for="skill in detail.application.skills" :key="skill">{{ skill }}</text></view><view v-else class="empty">未填写擅长领域</view>
        <view class="detail-heading">申请留言</view><view class="bio">{{ detail.application.bio || '该申请未填写个人留言。' }}</view>
        <view class="detail-heading">证明材料</view><view v-if="detail.documents?.length" class="documents"><view v-for="document in detail.documents" :key="document.id" class="document"><image :src="document.file_url" mode="aspectFill" /><view><strong>{{ document.file_name }}</strong><text>{{ documentTypeText(document.document_type) }} · {{ formatDateTime(document.created_at) }}</text></view></view></view><view v-else class="empty">该申请暂未上传证明材料</view>
        <view v-if="detail.application.application_status === 'pending'" class="review"><view class="detail-heading">审核备注</view><textarea v-model.trim="reviewNote" maxlength="1000" placeholder="填写给申请人的审核说明（选填）" /><view class="review-actions"><button class="reject-button" :disabled="saving" @tap="decideApplication('reject')">{{ saving && pendingDecision === 'reject' ? '处理中…' : '驳回申请' }}</button><button class="approve-button" :disabled="saving" @tap="decideApplication('approve')">{{ saving && pendingDecision === 'approve' ? '处理中…' : '通过申请' }}</button></view></view>
        <view v-else-if="detail.application.admin_note" class="admin-note"><text>审核备注</text><strong>{{ detail.application.admin_note }}</strong></view>
      </view></scroll-view>
    </view></view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { decideAdminMentorVerificationApplication, fetchAdminMentorVerificationApplication, fetchAdminMentorVerificationApplications } from '../api/admin'
import AdminSelect from './AdminSelect.vue'

const props = defineProps({ preview: Boolean })
const applications = ref([])
const applicationCount = ref(0)
const applicationPage = ref(1)
const applicationPageSize = 20
const loading = ref(false)
const loadError = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref(null)
const saving = ref(false)
const pendingDecision = ref('')
const reviewNote = ref('')
const filters = reactive({ keyword: '', application_status: '' })
let searchTimer = null

const statusOptions = [{ label: '全部申请状态', value: '' }, { label: '待审核', value: 'pending' }, { label: '已通过', value: 'approved' }, { label: '未通过', value: 'rejected' }]
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex((item) => item.value === filters.application_status)))
const applicationTotalPages = computed(() => Math.max(1, Math.ceil(applicationCount.value / applicationPageSize)))
const pendingCount = computed(() => applications.value.filter((item) => item.application_status === 'pending').length)
const approvedCount = computed(() => applications.value.filter((item) => item.application_status === 'approved').length)
const rejectedCount = computed(() => applications.value.filter((item) => item.application_status === 'rejected').length)

refresh()
onBeforeUnmount(() => { if (searchTimer) clearTimeout(searchTimer) })
defineExpose({ refresh })

async function refresh() {
  loading.value = true
  loadError.value = false
  try {
    const response = props.preview ? buildPreviewApplicationPage() : await fetchAdminMentorVerificationApplications({
      ...filters,
      limit: applicationPageSize,
      offset: (applicationPage.value - 1) * applicationPageSize
    })
    applications.value = response?.items || []
    applicationCount.value = Number(response?.count || 0)
    if (applicationCount.value > 0 && applications.value.length === 0 && applicationPage.value > applicationTotalPages.value) {
      applicationPage.value = applicationTotalPages.value
      await refresh()
      return
    }
  } catch (error) {
    applications.value = []
    applicationCount.value = 0
    loadError.value = true
  } finally { loading.value = false }
}

function applyApplicationFilters() { applicationPage.value = 1; refresh() }
function handleSearch() { if (searchTimer) clearTimeout(searchTimer); searchTimer = setTimeout(applyApplicationFilters, 360) }
function clearSearch() { filters.keyword = ''; applyApplicationFilters() }
function selectStatus(event) { filters.application_status = statusOptions[Number(event?.detail?.value || 0)]?.value || ''; applyApplicationFilters() }
function changeApplicationPage(page) { const next = Math.max(1, Math.min(applicationTotalPages.value, Number(page) || 1)); if (next !== applicationPage.value) { applicationPage.value = next; refresh() } }

async function openApplication(item) {
  if (!item?.id || detailLoading.value) return
  detailVisible.value = true; detailLoading.value = true; detail.value = null; reviewNote.value = ''
  try {
    detail.value = props.preview ? previewApplicationDetail(item) : await fetchAdminMentorVerificationApplication(item.id)
    reviewNote.value = detail.value?.application?.admin_note || ''
  } catch (error) {
    uni.showToast({ title: error?.detail || '申请详情加载失败', icon: 'none' })
    detailVisible.value = false
  } finally { detailLoading.value = false }
}

function closeApplication() { if (!saving.value) { detailVisible.value = false; detail.value = null; reviewNote.value = '' } }

async function decideApplication(decision) {
  const application = detail.value?.application
  if (!application?.id || saving.value) return
  const approving = decision === 'approve'
  const confirmed = await confirmDecision(approving ? '通过这份前辈申请？' : '驳回这份前辈申请？', approving ? '通过后将建立前辈档案并向用户端公开。' : '驳回后申请人可查看审核备注。', approving ? '确认通过' : '确认驳回')
  if (!confirmed) return
  saving.value = true; pendingDecision.value = decision
  try {
    const updated = props.preview ? { ...application, application_status: approving ? 'approved' : 'rejected', admin_note: reviewNote.value || null, reviewed_at: new Date().toISOString() } : await decideAdminMentorVerificationApplication(application.id, { decision, admin_note: reviewNote.value || null })
    applications.value = applications.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    detail.value = { ...detail.value, application: { ...detail.value.application, ...updated } }
    uni.showToast({ title: approving ? '申请已通过' : '申请已驳回', icon: 'success' })
  } catch (error) { uni.showToast({ title: error?.detail || '审核处理失败', icon: 'none' }) } finally { saving.value = false; pendingDecision.value = '' }
}

function confirmDecision(title, content, confirmText) { return new Promise((resolve) => uni.showModal({ title, content, confirmText, success: (result) => resolve(Boolean(result.confirm)) })) }
function buildPreviewApplicationPage() {
  const keyword = filters.keyword.trim().toLowerCase()
  const filtered = previewApplications().filter((item) => {
    if (filters.application_status && item.application_status !== filters.application_status) return false
    if (!keyword) return true
    return [item.legal_name, item.school, item.major].some((value) => String(value || '').toLowerCase().includes(keyword))
  })
  const offset = (applicationPage.value - 1) * applicationPageSize
  return { items: filtered.slice(offset, offset + applicationPageSize), count: filtered.length }
}
function previewApplications() { return [
  { id: 'preview-mentor-application-001', applicant_user_id: 'preview-user-001', legal_name: '陈同学', school: '暨南大学', major: '应用经济学', admission_year: 2025, graduation_year: 2027, exam_type: 'Z001', score: 110, skills: ['院校选择', '初试备考', '复试经验'], bio: '我已录取暨南大学应用经济学，希望帮助同样准备 Z001 的同学梳理院校选择和备考节奏。', price: 39, application_status: 'pending', document_count: 2, created_at: '2026-08-21T02:30:00Z' },
  { id: 'preview-mentor-application-002', applicant_user_id: 'preview-user-002', legal_name: '林同学', school: '中山大学', major: '金融学', admission_year: 2024, graduation_year: 2026, exam_type: 'Z002', score: 122, skills: ['学习规划', '复试经验'], bio: '有完整复试准备经验，愿意分享备考规划。', price: 49, application_status: 'approved', document_count: 1, created_at: '2026-08-18T09:20:00Z', admin_note: '资料核验通过。' },
  { id: 'preview-mentor-application-003', applicant_user_id: 'preview-user-003', legal_name: '周同学', school: '华南理工大学', major: '工商管理', admission_year: 2025, graduation_year: 2027, exam_type: 'application', score: 0, skills: ['院校选择'], bio: '希望分享申请制项目的准备经历。', price: 39, application_status: 'rejected', document_count: 0, created_at: '2026-08-16T03:10:00Z', admin_note: '请补充录取证明后重新申请。' }
] }
function previewApplicationDetail(application) { return { application: { ...application }, applicant: { nickname: application.legal_name, email: 'mentor-applicant@example.com' }, documents: Array.from({ length: application.document_count || 0 }, (_, index) => ({ id: `preview-document-${index}`, file_url: '/static/ui-icons/circle-community.svg', file_name: index ? '学生证照片' : '录取通知书', document_type: index ? 'student_card' : 'admission_notice', created_at: application.created_at })) } }
function statusText(value) { return { pending: '待审核', approved: '已通过', rejected: '未通过' }[value] || '待审核' }
function examTypeText(value) { return { Z001: 'Z001', Z002: 'Z002', application: '申请制' }[value] || value || '—' }
function documentTypeText(value) { return { admission_notice: '录取通知书', student_card: '学生证', other: '其他证明' }[value] || '证明材料' }
function formatPrice(value) { const price = Number(value || 0); return Number.isInteger(price) ? price : price.toFixed(2) }
function shortId(value) { const id = String(value || ''); return id ? `${id.slice(0, 8)}…${id.slice(-4)}` : '—' }
function formatDateTime(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date) }
</script>

<style scoped>
.mentor-application-page{color:#31465d}.summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.summary-card{min-height:112px;padding:18px 20px;border:1px solid #e2eaee;border-top:3px solid #9aa9b8;border-radius:9px;background:#fff;box-shadow:0 8px 24px rgba(39,62,79,.04)}.summary-card text,.summary-card strong,.summary-card small{display:block}.summary-card text{color:#7d8d9e;font-size:11px;font-weight:700}.summary-card strong{margin-top:10px;color:#314a65;font-size:28px}.summary-card small{margin-top:7px;color:#9aa7b4;font-size:10px}.summary-card.pending{border-top-color:#dbaf55}.summary-card.approved{border-top-color:#57cdb7}.summary-card.rejected{border-top-color:#de9088}.application-workspace{margin-top:18px;border:1px solid #e0e8ec;border-radius:10px;background:#fff;overflow:hidden;box-shadow:0 10px 30px rgba(38,59,77,.04)}.heading{min-height:76px;padding:0 22px;display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid #e9eef1}.title{font-size:15px;font-weight:800}.subtitle{margin-top:5px;color:#8c9aa8;font-size:10px}.refresh-button{height:36px;margin:0;padding:0 16px;border:1px solid #d7e3e6;border-radius:7px;background:#fff;color:#617286;font-size:10px;font-weight:750}.toolbar{padding:14px 18px;display:grid;grid-template-columns:minmax(260px,1fr) 170px;gap:10px;border-bottom:1px solid #edf1f3;background:#fbfcfd}.search{height:38px;padding:0 10px;display:flex;align-items:center;gap:8px;border:1px solid #dae4e8;border-radius:8px;background:#fff}.search>text{color:#91a0af}.search input{min-width:0;flex:1;height:36px;font-size:11px}.search button{width:26px;height:26px;margin:0;padding:0;border:0;background:transparent;color:#93a1af}.refresh-button::after,.search button::after,.open-button::after,.detail button::after{border:0}.table-wrap{overflow-x:auto}.table{min-width:1050px}.grid{display:grid;grid-template-columns:1.1fr 1.3fr 1.8fr .7fr .85fr .75fr 60px;align-items:center;gap:14px;padding:0 18px}.table-head{min-height:42px;color:#8796a4;background:#f7f9fa;font-size:10px;font-weight:800}.row{min-height:76px;border-top:1px solid #edf1f3;cursor:pointer;font-size:11px}.row:hover{background:#fbfefd}.row strong,.row text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.row strong{color:#394f65;font-size:11px}.row>view:not(.applicant) text,.applicant text{margin-top:4px;color:#98a5b2;font-size:9px}.applicant{display:flex;align-items:center;gap:10px;min-width:0}.avatar{width:36px;height:36px;flex:0 0 36px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:#e4f5f0;color:#278d77;font-size:13px;font-weight:900}.message{overflow:hidden;display:-webkit-box;color:#718297;font-size:10px;line-height:1.4;-webkit-box-orient:vertical;-webkit-line-clamp:2}.document-count,.status{display:inline-flex!important;margin:0!important;padding:5px 8px;border-radius:99px;font-size:9px!important;font-weight:800}.document-count{background:#eef5fc;color:#5880a6!important}.status.pending{background:#fff4df;color:#ae7a29}.status.approved{background:#e8f7f2;color:#238b75}.status.rejected{background:#fceceb;color:#b45f59}.open-button{height:30px;margin:0;padding:0 11px;border:0;border-radius:6px;background:#eef7f5;color:#278b78;font-size:10px;font-weight:800}.table-state{padding:54px 20px;color:#91a0ae;text-align:center;font-size:12px}.table-state.error{color:#ba6962}.table-state button{display:block;margin:12px auto 0;font-size:11px}.backdrop{position:fixed;z-index:6000;inset:0;padding:24px;display:flex;align-items:center;justify-content:center;background:rgba(24,39,55,.38);backdrop-filter:blur(4px)}.detail{width:min(760px,calc(100vw - 48px));height:min(760px,calc(100vh - 48px));display:flex;flex-direction:column;overflow:hidden;border:1px solid #dfe8eb;border-radius:12px;background:#fff;box-shadow:0 30px 90px rgba(26,42,58,.24)}.detail-header{padding:18px 22px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e9eef1}.detail-header text,.detail-header strong{display:block}.detail-header text{color:#35a78f;font-size:9px;font-weight:850;letter-spacing:.12em}.detail-header strong{margin-top:5px;color:#30465d;font-size:17px}.detail-header button{width:34px;height:34px;margin:0;padding:0;border:0;border-radius:50%;background:#f2f5f7;color:#768695;font-size:20px}.detail-scroll{min-height:0;flex:1}.detail-content{padding:22px}.applicant-card{display:flex;align-items:center;gap:11px;padding-bottom:17px;border-bottom:1px solid #e8eef1}.avatar.large{width:46px;height:46px;flex-basis:46px;font-size:17px}.applicant-card strong,.applicant-card text{display:block}.applicant-card strong{color:#3b5269;font-size:13px}.applicant-card text{margin-top:5px;color:#98a6b4;font-size:10px}.applicant-card .status{margin-left:auto!important}.application-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));margin-top:18px;border:1px solid #e4edef;border-radius:8px;overflow:hidden}.application-fields>view{min-height:62px;padding:12px 14px;display:flex;flex-direction:column;justify-content:center;border-top:1px solid #e7edf0;border-left:1px solid #e7edf0}.application-fields>view:nth-child(-n+2){border-top:0}.application-fields>view:nth-child(odd){border-left:0}.application-fields text{color:#98a7b6;font-size:10px}.application-fields strong{margin-top:5px;color:#40566c;font-size:11px}.detail-heading{margin:20px 0 9px;color:#40566c;font-size:12px;font-weight:800}.skill-list{display:flex;flex-wrap:wrap;gap:7px}.skill-list text{padding:6px 9px;border-radius:99px;background:#eaf7f3;color:#297f6e;font-size:10px;font-weight:750}.bio,.empty{padding:13px;border:1px solid #e3ebee;border-radius:8px;color:#708196;font-size:11px;line-height:1.6;background:#fbfcfd}.empty{border-style:dashed;text-align:center}.documents{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.document{min-width:0;overflow:hidden;border:1px solid #e1e9ec;border-radius:8px;background:#fff}.document image{width:100%;height:104px;background:#f4f8fb}.document>view{padding:9px}.document strong,.document text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.document strong{color:#41566b;font-size:10px}.document text{margin-top:4px;color:#96a5b2;font-size:8px}.review{margin-top:20px;padding-top:1px;border-top:1px solid #e8eef1}.review textarea{box-sizing:border-box;width:100%;min-height:78px;padding:10px 11px;border:1px dashed #9fcfc4;border-radius:7px;color:#40566d;font-size:11px;line-height:1.5;background:#fbfefd}.review-actions{margin-top:12px;display:flex;justify-content:flex-end;gap:9px}.review-actions button{min-width:92px;height:34px;margin:0;border-radius:7px;font-size:10px;font-weight:800}.reject-button{border:1px solid #ecc8c3;background:#fff7f5;color:#b36258}.approve-button{border:0;background:#34b399;color:#fff}.admin-note{margin-top:20px;padding:12px 13px;border:1px solid #e1eaed;border-radius:8px;background:#fbfcfd}.admin-note text,.admin-note strong{display:block}.admin-note text{color:#93a1ae;font-size:9px}.admin-note strong{margin-top:5px;color:#52677b;font-size:11px;line-height:1.5}@media(max-width:1180px){.summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:820px){.summary-grid,.toolbar,.application-fields{grid-template-columns:1fr}.detail{width:100%;height:calc(100vh - 28px)}.backdrop{padding:14px}.application-fields>view{border-left:0}.application-fields>view:nth-child(2){border-top:1px solid #e7edf0}.documents{grid-template-columns:1fr 1fr}.heading{align-items:flex-start;flex-direction:column;padding:16px 18px}.detail-content{padding:18px}.review-actions button{flex:1}}
.refresh-button,
.open-button,
.review-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  line-height: 1;
  text-align: center;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar .search {
  width: min(360px, 42vw);
  flex: 0 1 360px;
}

.toolbar .status-select {
  width: 170px;
  flex: 0 0 170px;
}

.toolbar .refresh-button {
  min-width: 76px;
  padding: 0 14px;
  flex: 0 0 auto;
}

.mentor-pagination {
  min-height: 58px;
  padding: 0 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  border-top: 1px solid #eaf0f2;
  box-sizing: border-box;
  background: #ffffff;
}

.mentor-pagination-info {
  color: #90a0af;
  font-size: 10px;
}

.mentor-pagination-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9aa8b6;
  font-size: 10px;
}

.mentor-pagination-actions button,
.mentor-page-current {
  width: 34px;
  height: 34px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dfe8eb;
  border-radius: 7px;
  box-sizing: border-box;
  color: #718295;
  background: #ffffff;
  font-size: 16px;
  line-height: 1;
}

.mentor-page-current {
  border-color: #d6eee8;
  color: #268b78;
  background: #eaf8f4;
  font-size: 11px;
  font-weight: 800;
}

.mentor-pagination-actions button:disabled {
  color: #c4cdd5;
  background: #f8fafb;
}

.mentor-pagination-actions button::after {
  border: 0;
}

.detail-header button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  line-height: 1;
  text-align: center;
}

.mentor-application-page {
  display: flex;
  min-height: calc(100vh - 158px);
  flex-direction: column;
}

.application-workspace {
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.application-workspace .table-wrap {
  min-height: 0;
  flex: 1;
}

.application-workspace .table {
  min-height: 100%;
}

@media (max-width: 820px) {
  .mentor-application-page {
    min-height: auto;
  }

  .toolbar {
    flex-wrap: wrap;
  }

  .toolbar .search {
    width: 100%;
    flex-basis: 100%;
  }

  .mentor-pagination {
    align-items: flex-start;
    flex-direction: column;
    justify-content: center;
    padding-top: 12px;
    padding-bottom: 12px;
  }
}
</style>
