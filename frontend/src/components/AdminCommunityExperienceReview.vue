<template>
  <view class="experience-review-page">
    <view class="experience-review-summary">
      <view v-for="item in summaryCards" :key="item.key" class="experience-summary-card" :class="item.key">
        <text>{{ item.label }}</text>
        <strong>{{ formatCount(item.value) }}</strong>
        <small>{{ item.note }}</small>
      </view>
    </view>

    <view class="experience-review-workspace">
      <view class="experience-review-toolbar">
        <view class="experience-review-search">
          <image src="/static/admin-icons/admin-search.svg" mode="aspectFit" />
          <input
            v-model.trim="filters.search"
            placeholder="搜索标题、正文或发布人"
            confirm-type="search"
            @input="scheduleSearch"
            @confirm="applyFilters"
          />
          <button v-if="filters.search" aria-label="清空搜索" @tap="clearSearch">×</button>
        </view>

        <AdminSelect
          class="experience-review-select"
          :options="statusOptions.map((item) => item.label)"
          :value-index="statusIndex"
          aria-label="审核状态筛选"
          @change="selectStatus"
        />
        <AdminSelect
          class="experience-review-select compact"
          :options="categoryOptions.map((item) => item.label)"
          :value-index="categoryIndex"
          aria-label="考试类别筛选"
          @change="selectCategory"
        />
        <AdminSelect
          class="experience-review-select compact"
          :options="stageOptions.map((item) => item.label)"
          :value-index="stageIndex"
          aria-label="备考阶段筛选"
          @change="selectStage"
        />
        <view class="experience-review-date-range">
          <input v-model="filters.date_from" type="date" aria-label="提交开始日期" @change="applyFilters" />
          <text>至</text>
          <input v-model="filters.date_to" type="date" aria-label="提交结束日期" @change="applyFilters" />
        </view>
        <AdminSelect
          class="experience-review-select sort"
          :options="sortOptions.map((item) => item.label)"
          :value-index="sortIndex"
          aria-label="提交时间排序"
          @change="selectSort"
        />
        <button v-if="hasFilters" class="experience-review-clear" @tap="clearFilters">清空</button>
        <button class="experience-review-refresh" :disabled="loading" @tap="refresh">
          {{ loading ? '刷新中…' : '刷新' }}
        </button>
      </view>

      <view class="experience-review-table-wrap">
        <view class="experience-review-table">
          <view class="experience-review-grid experience-review-head">
            <view>经验贴</view>
            <view>发布人</view>
            <view>考试 / 阶段</view>
            <view>审核状态</view>
            <view>提交时间</view>
            <view>审核版本</view>
            <view>操作</view>
          </view>

          <view v-if="loading" class="experience-review-state">正在加载经验贴审核队列…</view>
          <view v-else-if="loadError" class="experience-review-state error">
            <text>审核队列加载失败，请检查网络或数据库迁移状态。</text>
            <button @tap="refresh">重新加载</button>
          </view>
          <view v-else-if="reviews.length === 0" class="experience-review-state">当前条件下没有经验贴</view>
          <view
            v-for="item in reviews"
            v-else
            :key="item.id"
            class="experience-review-grid experience-review-row"
            @tap="openReview(item)"
          >
            <view class="experience-review-post">
              <strong>{{ item.title || '未填写标题' }}</strong>
              <text>{{ item.content || '未填写正文' }}</text>
            </view>
            <view class="experience-review-author">
              <view>{{ initial(item.author_name) }}</view>
              <text><strong>{{ item.author_name || '前辈' }}</strong><small>ID {{ shortId(item.author_id) }}</small></text>
            </view>
            <view class="experience-review-tags">
              <strong>{{ item.category || '未分类' }}</strong>
              <text>{{ formatStages(item.experience_stages) }}</text>
            </view>
            <view><text class="experience-review-status" :class="item.review_status">{{ statusText(item.review_status) }}</text></view>
            <view class="experience-review-time">{{ formatDateTime(item.submitted_at || item.created_at) }}</view>
            <view class="experience-review-version">第 {{ Math.max(1, Number(item.review_version || 1)) }} 次</view>
            <view><button class="experience-review-open" @tap.stop="openReview(item)">{{ item.review_status === 'pending' ? '审核' : '查看' }}</button></view>
          </view>
        </view>
      </view>

      <view class="experience-review-pagination">
        <text>共 {{ formatCount(reviewCount) }} 条，每页 {{ pageSize }} 条</text>
        <view>
          <button :disabled="page <= 1 || loading" @tap="changePage(page - 1)">‹</button>
          <strong>{{ page }}</strong>
          <text>/ {{ totalPages }}</text>
          <button :disabled="page >= totalPages || loading" @tap="changePage(page + 1)">›</button>
        </view>
      </view>
    </view>

    <view v-if="detailVisible" class="experience-review-backdrop" @tap="closeDetail">
      <view class="experience-review-dialog" @tap.stop>
        <view class="experience-review-dialog-header">
          <view>
            <text>EXPERIENCE REVIEW</text>
            <strong>{{ detail?.post?.title || activeReview?.title || '经验贴审核' }}</strong>
          </view>
          <button aria-label="关闭审核详情" :disabled="saving" @tap="closeDetail"><CloseIcon /></button>
        </view>

        <scroll-view scroll-y class="experience-review-dialog-scroll">
          <view v-if="detailLoading" class="experience-review-detail-state">正在读取完整内容…</view>
          <view v-else-if="detailError" class="experience-review-detail-state error">
            <text>{{ detailError }}</text>
            <button @tap="loadDetail(activeReview?.id)">重新加载</button>
          </view>
          <view v-else-if="detail?.post" class="experience-review-dialog-content">
            <view class="experience-review-meta">
              <view><text>发布人</text><strong>{{ detail.post.author_name || '前辈' }}</strong><small>ID {{ shortId(detail.post.author_id) }}</small></view>
              <view><text>考试类别</text><strong>{{ detail.post.category }}</strong><small>{{ formatStages(detail.post.experience_stages) }}</small></view>
              <view><text>当前状态</text><strong :class="`status-${detail.post.review_status}`">{{ statusText(detail.post.review_status) }}</strong><small>第 {{ detail.post.review_version }} 次提交</small></view>
              <view><text>提交时间</text><strong>{{ formatDateTime(detail.post.submitted_at || detail.post.created_at) }}</strong><small>{{ detail.post.media?.length || 0 }} 张图片</small></view>
            </view>

            <view class="experience-review-heading">正文内容</view>
            <view class="experience-review-content-block">
              <strong>{{ detail.post.title }}</strong>
              <text>{{ detail.post.content }}</text>
            </view>

            <view v-if="detail.post.media?.length" class="experience-review-media">
              <image
                v-for="(media, index) in detail.post.media"
                :key="`${detail.post.id}-${index}`"
                :src="media.imageUrl || media.image_url"
                mode="aspectFill"
                @tap="previewMedia(detail.post.media, index)"
              />
            </view>

            <view class="experience-review-heading">历次审核记录</view>
            <view v-if="!detail.review_history?.length" class="experience-review-history-empty">暂无审核记录</view>
            <view v-else class="experience-review-history">
              <view v-for="history in detail.review_history" :key="history.id" class="experience-review-history-item">
                <view class="experience-review-history-dot" :class="history.action"></view>
                <view>
                  <view><strong>{{ historyActionText(history.action) }}</strong><text>第 {{ history.submission_version }} 次提交</text></view>
                  <small>{{ formatDateTime(history.created_at) }}<template v-if="history.actor_user_id"> · 操作人 {{ shortId(history.actor_user_id) }}</template></small>
                  <text v-if="history.reason_code || history.review_note" class="experience-review-history-note">{{ history.reason_code ? `${reasonText(history.reason_code)}：` : '' }}{{ history.review_note || '' }}</text>
                </view>
              </view>
            </view>

            <template v-if="detail.post.review_status === 'pending'">
              <view class="experience-review-heading">审核结论</view>
              <view class="experience-review-decision" role="group" aria-label="审核结论">
                <button :class="{ active: decision === 'approved' }" :disabled="saving" @tap="decision = 'approved'">通过并公开</button>
                <button class="reject" :class="{ active: decision === 'rejected' }" :disabled="saving" @tap="decision = 'rejected'">驳回修改</button>
              </view>
              <view v-if="decision === 'rejected'" class="experience-review-form-field">
                <text>官方理由</text>
                <AdminSelect
                  class="experience-review-reason-select"
                  :options="reasonOptions.map((item) => item.label)"
                  :value-index="reasonIndex"
                  aria-label="经验贴驳回理由"
                  @change="selectReason"
                />
              </view>
              <view class="experience-review-form-field">
                <text>{{ decision === 'rejected' ? '官方处理说明（必填）' : '审核备注（选填）' }}</text>
                <textarea
                  v-model.trim="reviewNote"
                  maxlength="1000"
                  :placeholder="decision === 'rejected' ? '写明需要修改的具体内容，作者会看到这段说明' : '可记录审核依据或补充说明'"
                />
              </view>
            </template>

            <view v-else-if="detail.post.review_note" class="experience-review-previous-result">
              <text>{{ detail.post.review_status === 'rejected' ? reasonText(detail.post.review_reason_code) : '审核说明' }}</text>
              <strong>{{ detail.post.review_note }}</strong>
            </view>
          </view>
        </scroll-view>

        <view v-if="detail?.post?.review_status === 'pending'" class="experience-review-dialog-actions">
          <button class="cancel" :disabled="saving" @tap="closeDetail">取消</button>
          <button :class="{ reject: decision === 'rejected' }" :disabled="saving" @tap="submitDecision">
            {{ saving ? '保存中…' : decision === 'approved' ? '确认通过' : '确认驳回' }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import {
  fetchQuestionAdminCommunityExperienceReviewDetail,
  fetchQuestionAdminCommunityExperienceReviews,
  reviewQuestionAdminCommunityExperiencePost
} from '../api/admin'
import AdminSelect from './AdminSelect.vue'
import CloseIcon from './CloseIcon.vue'

const props = defineProps({ preview: Boolean })
const emit = defineEmits(['pending-count'])

const statusOptions = [
  { label: '全部审核状态', value: 'all' },
  { label: '待审核', value: 'pending' },
  { label: '已通过', value: 'approved' },
  { label: '未通过', value: 'rejected' }
]
const categoryOptions = [
  { label: '全部考试', value: 'all' },
  { label: 'Z001', value: 'Z001' },
  { label: 'Z002', value: 'Z002' }
]
const stageOptions = [
  { label: '全部阶段', value: '' },
  { label: '申请制', value: '申请制' },
  { label: '初试', value: '初试' },
  { label: '复试', value: '复试' }
]
const sortOptions = [
  { label: '提交时间：新到旧', value: 'newest' },
  { label: '提交时间：旧到新', value: 'oldest' }
]
const reasonOptions = [
  { label: '请选择官方理由', value: '' },
  { label: '广告营销或站外引流', value: 'advertising_or_diversion' },
  { label: '虚假、夸大或误导性信息', value: 'false_or_misleading' },
  { label: '侵权或未经授权转载', value: 'infringement' },
  { label: '泄露个人隐私', value: 'privacy' },
  { label: '不友善、低俗或违规内容', value: 'inappropriate' },
  { label: '内容不完整或与备考经验无关', value: 'low_quality' },
  { label: '其他原因', value: 'other' }
]

const filters = reactive({
  review_status: 'all',
  category: 'all',
  experience_stage: '',
  search: '',
  date_from: '',
  date_to: '',
  sort_by: 'newest'
})
const counts = reactive({ all: 0, pending: 0, approved: 0, rejected: 0 })
const reviews = ref([])
const reviewCount = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const loadError = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailError = ref('')
const activeReview = ref(null)
const detail = ref(null)
const decision = ref('approved')
const reasonCode = ref('')
const reviewNote = ref('')
const saving = ref(false)
let searchTimer = null

const summaryCards = computed(() => [
  { key: 'all', label: '全部经验贴', value: counts.all, note: '累计提交审核' },
  { key: 'pending', label: '待审核', value: counts.pending, note: '需要工作人员处理' },
  { key: 'approved', label: '已通过', value: counts.approved, note: '当前审核记录' },
  { key: 'rejected', label: '未通过', value: counts.rejected, note: '可修改后重新提交' }
])
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex((item) => item.value === filters.review_status)))
const categoryIndex = computed(() => Math.max(0, categoryOptions.findIndex((item) => item.value === filters.category)))
const stageIndex = computed(() => Math.max(0, stageOptions.findIndex((item) => item.value === filters.experience_stage)))
const sortIndex = computed(() => Math.max(0, sortOptions.findIndex((item) => item.value === filters.sort_by)))
const reasonIndex = computed(() => Math.max(0, reasonOptions.findIndex((item) => item.value === reasonCode.value)))
const totalPages = computed(() => Math.max(1, Math.ceil(reviewCount.value / pageSize)))
const hasFilters = computed(() => Boolean(
  filters.review_status !== 'all'
  || filters.category !== 'all'
  || filters.experience_stage
  || filters.search
  || filters.date_from
  || filters.date_to
  || filters.sort_by !== 'newest'
))

refresh()
onBeforeUnmount(() => { if (searchTimer) clearTimeout(searchTimer) })
defineExpose({ refresh })

async function refresh() {
  if (loading.value) return
  loading.value = true
  loadError.value = false
  try {
    const [listResponse, summary] = await Promise.all([
      fetchReviewPage(),
      fetchReviewSummary()
    ])
    reviews.value = Array.isArray(listResponse?.items) ? listResponse.items : []
    reviewCount.value = Number(listResponse?.count || 0)
    Object.assign(counts, summary)
    emit('pending-count', counts.pending)
    if (reviewCount.value > 0 && reviews.value.length === 0 && page.value > totalPages.value) {
      page.value = totalPages.value
      loading.value = false
      await refresh()
      return
    }
  } catch (error) {
    reviews.value = []
    reviewCount.value = 0
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function fetchReviewPage() {
  if (props.preview) return Promise.resolve(buildPreviewPage())
  return fetchQuestionAdminCommunityExperienceReviews({
    review_status: filters.review_status,
    category: filters.category,
    experience_stage: filters.experience_stage || undefined,
    search: filters.search.trim() || undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    sort_by: filters.sort_by,
    limit: pageSize,
    offset: (page.value - 1) * pageSize
  })
}

async function fetchReviewSummary() {
  if (props.preview) {
    const source = previewReviews()
    return {
      all: source.length,
      pending: source.filter((item) => item.review_status === 'pending').length,
      approved: source.filter((item) => item.review_status === 'approved').length,
      rejected: source.filter((item) => item.review_status === 'rejected').length
    }
  }
  const statuses = ['all', 'pending', 'approved', 'rejected']
  const responses = await Promise.all(statuses.map((reviewStatus) => (
    fetchQuestionAdminCommunityExperienceReviews({ review_status: reviewStatus, limit: 1, offset: 0 })
  )))
  return Object.fromEntries(statuses.map((reviewStatus, index) => [reviewStatus, Number(responses[index]?.count || 0)]))
}

function scheduleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; refresh() }, 360)
}
function applyFilters() { page.value = 1; refresh() }
function clearSearch() { filters.search = ''; applyFilters() }
function selectStatus(event) { filters.review_status = statusOptions[Number(event?.detail?.value || 0)]?.value || 'all'; applyFilters() }
function selectCategory(event) { filters.category = categoryOptions[Number(event?.detail?.value || 0)]?.value || 'all'; applyFilters() }
function selectStage(event) { filters.experience_stage = stageOptions[Number(event?.detail?.value || 0)]?.value || ''; applyFilters() }
function selectSort(event) { filters.sort_by = sortOptions[Number(event?.detail?.value || 0)]?.value || 'newest'; applyFilters() }
function selectReason(event) { reasonCode.value = reasonOptions[Number(event?.detail?.value || 0)]?.value || '' }
function clearFilters() {
  Object.assign(filters, { review_status: 'all', category: 'all', experience_stage: '', search: '', date_from: '', date_to: '', sort_by: 'newest' })
  applyFilters()
}
function changePage(next) {
  const target = Math.max(1, Math.min(totalPages.value, Number(next) || 1))
  if (target === page.value) return
  page.value = target
  refresh()
}

async function openReview(item) {
  if (!item?.id || saving.value) return
  activeReview.value = item
  detailVisible.value = true
  decision.value = 'approved'
  reasonCode.value = ''
  reviewNote.value = ''
  await loadDetail(item.id)
}

async function loadDetail(postId) {
  if (!postId || detailLoading.value) return
  detailLoading.value = true
  detailError.value = ''
  try {
    detail.value = props.preview
      ? buildPreviewDetail(postId)
      : await fetchQuestionAdminCommunityExperienceReviewDetail(postId)
  } catch (error) {
    detail.value = null
    detailError.value = error?.detail || '经验贴审核详情读取失败'
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  if (saving.value) return
  detailVisible.value = false
  detail.value = null
  activeReview.value = null
  detailError.value = ''
  reviewNote.value = ''
  reasonCode.value = ''
}

async function submitDecision() {
  const post = detail.value?.post
  if (!post?.id || post.review_status !== 'pending' || saving.value) return
  if (decision.value === 'rejected' && (!reasonCode.value || !reviewNote.value.trim())) {
    uni.showToast({ title: '驳回时请选择官方理由并填写处理说明', icon: 'none' })
    return
  }
  const confirmed = await new Promise((resolve) => uni.showModal({
    title: decision.value === 'approved' ? '通过这篇经验贴？' : '驳回这篇经验贴？',
    content: decision.value === 'approved'
      ? '通过后内容会立即公开，并向作者发送审核通知。'
      : '官方理由和处理说明会发送给作者，作者可修改后重新提交。',
    confirmText: decision.value === 'approved' ? '确认通过' : '确认驳回',
    confirmColor: decision.value === 'approved' ? '#2da58b' : '#d96c60',
    success: (result) => resolve(Boolean(result.confirm))
  }))
  if (!confirmed) return
  saving.value = true
  try {
    const updated = props.preview
      ? { ...post, review_status: decision.value, review_reason_code: decision.value === 'rejected' ? reasonCode.value : null, review_note: reviewNote.value.trim() || null, reviewed_at: new Date().toISOString(), is_published: decision.value === 'approved' }
      : await reviewQuestionAdminCommunityExperiencePost(post.id, {
          decision: decision.value,
          reason_code: decision.value === 'rejected' ? reasonCode.value : null,
          review_note: reviewNote.value.trim() || null
        })
    reviews.value = reviews.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    detail.value = {
      ...detail.value,
      post: { ...post, ...updated },
      review_history: [
        {
          id: `local-${updated.id}-${Date.now()}`,
          submission_version: updated.review_version,
          action: updated.review_status,
          from_status: 'pending',
          to_status: updated.review_status,
          reason_code: updated.review_reason_code,
          review_note: updated.review_note,
          created_at: updated.reviewed_at || new Date().toISOString()
        },
        ...(detail.value?.review_history || [])
      ]
    }
    await fetchAndApplySummary()
    uni.showToast({ title: decision.value === 'approved' ? '经验贴已通过并公开' : '已驳回并通知作者', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '审核结果保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function fetchAndApplySummary() {
  try {
    Object.assign(counts, await fetchReviewSummary())
    emit('pending-count', counts.pending)
  } catch (error) {
    // 主审核结果已保存时，汇总刷新失败不覆盖当前详情。
  }
}

function buildPreviewPage() {
  const keyword = filters.search.trim().toLowerCase()
  const source = previewReviews().filter((item) => {
    if (filters.review_status !== 'all' && item.review_status !== filters.review_status) return false
    if (filters.category !== 'all' && item.category !== filters.category) return false
    if (filters.experience_stage && !item.experience_stages.includes(filters.experience_stage)) return false
    if (keyword && !`${item.title} ${item.content} ${item.author_name}`.toLowerCase().includes(keyword)) return false
    if (filters.date_from && String(item.submitted_at).slice(0, 10) < filters.date_from) return false
    if (filters.date_to && String(item.submitted_at).slice(0, 10) > filters.date_to) return false
    return true
  })
  source.sort((left, right) => {
    const newestFirst = new Date(right.submitted_at) - new Date(left.submitted_at)
    return filters.sort_by === 'oldest' ? -newestFirst : newestFirst
  })
  const offset = (page.value - 1) * pageSize
  return { items: source.slice(offset, offset + pageSize), count: source.length }
}

function buildPreviewDetail(postId) {
  const post = previewReviews().find((item) => item.id === postId)
  return {
    post,
    review_history: [
      { id: `${postId}-history-1`, submission_version: post.review_version, action: 'submitted', from_status: post.review_version > 1 ? 'rejected' : null, to_status: 'pending', actor_user_id: post.author_id, created_at: post.submitted_at }
    ]
  }
}

function previewReviews() {
  return [
    { id: 'preview-experience-review-001', author_id: '8fc21c09-1111-4444-8888-111111111111', author_name: '陈学姐', author_avatar: '陈', post_type: 'experience', category: 'Z001', experience_stages: ['申请制', '初试'], title: '从材料准备到初试复盘：我的 Z001 备考方法', content: '我把申请材料、公共课和专业课拆成三个阶段，每周固定复盘一次。这里整理了时间安排、错题归档和复试准备的具体方法。', media: [], review_status: 'pending', review_version: 1, is_published: false, submitted_at: '2026-09-01T02:30:00Z', created_at: '2026-09-01T02:30:00Z' },
    { id: 'preview-experience-review-002', author_id: '311b32a6-2222-4444-8888-222222222222', author_name: '林前辈', author_avatar: '林', post_type: 'experience', category: 'Z002', experience_stages: ['初试'], title: '数学基础错题复盘的四步法', content: '按概念、计算、审题和时间分配记录错因，再安排隔日与一周后的二次练习。', media: [], review_status: 'approved', review_version: 1, is_published: true, submitted_at: '2026-08-30T08:15:00Z', reviewed_at: '2026-08-30T09:20:00Z', created_at: '2026-08-30T08:15:00Z' },
    { id: 'preview-experience-review-003', author_id: '7a6123e4-3333-4444-8888-333333333333', author_name: '周学长', author_avatar: '周', post_type: 'experience', category: 'Z001', experience_stages: ['复试'], title: '复试资料分享与交流', content: '正文包含需要进一步核对的外部联系方式和资料说明。', media: [], review_status: 'rejected', review_version: 1, review_reason_code: 'advertising_or_diversion', review_note: '请删除站外付费引流和联系方式，补充本人真实复试经历后重新提交。', is_published: false, submitted_at: '2026-08-28T03:10:00Z', reviewed_at: '2026-08-28T05:00:00Z', created_at: '2026-08-28T03:10:00Z' }
  ]
}

function previewMedia(media, index) {
  const urls = (Array.isArray(media) ? media : []).map((item) => item?.imageUrl || item?.image_url).filter(Boolean)
  if (!urls.length) return
  uni.previewImage({ urls, current: urls[Math.max(0, Number(index) || 0)] })
}
function initial(value) { return String(value || '前').slice(0, 1) || '前' }
function shortId(value) { const id = String(value || ''); return id ? `${id.slice(0, 8)}…${id.slice(-4)}` : '—' }
function formatCount(value) { return new Intl.NumberFormat('zh-CN').format(Math.max(0, Number(value) || 0)) }
function formatStages(value) { return Array.isArray(value) && value.length ? value.join(' / ') : '阶段未填写' }
function statusText(value) { return { pending: '待审核', approved: '已通过', rejected: '未通过' }[value] || '待审核' }
function historyActionText(value) { return { submitted: '提交审核', approved: '审核通过', rejected: '审核未通过' }[value] || '状态更新' }
function reasonText(value) { return reasonOptions.find((item) => item.value === value)?.label || '平台审核说明' }
function formatDateTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date)
}
</script>

<style scoped>
.experience-review-page{min-height:calc(100vh - 158px);display:flex;flex-direction:column;color:#31465d}.experience-review-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.experience-summary-card{min-height:104px;padding:17px 19px;border:1px solid #e0e8ec;border-top:3px solid #8c9ba9;border-radius:8px;background:#fff;box-shadow:0 8px 24px rgba(39,62,79,.04)}.experience-summary-card text,.experience-summary-card strong,.experience-summary-card small{display:block}.experience-summary-card text{color:#7d8d9e;font-size:11px;font-weight:750}.experience-summary-card strong{margin-top:9px;color:#314a65;font-size:27px}.experience-summary-card small{margin-top:6px;color:#9aa7b4;font-size:10px}.experience-summary-card.pending{border-top-color:#d9aa4c}.experience-summary-card.approved{border-top-color:#4fc4aa}.experience-summary-card.rejected{border-top-color:#dd786d}.experience-review-workspace{min-height:0;flex:1;margin-top:18px;overflow:hidden;border:1px solid #e0e8ec;border-radius:8px;background:#fff;box-shadow:0 10px 30px rgba(38,59,77,.04);display:flex;flex-direction:column}.experience-review-toolbar{padding:13px 16px;display:flex;align-items:center;gap:9px;flex-wrap:wrap;border-bottom:1px solid #edf1f3;background:#fbfcfd}.experience-review-search{width:min(310px,34vw);height:38px;padding:0 10px;display:flex;align-items:center;gap:8px;flex:1 1 280px;border:1px solid #dae4e8;border-radius:7px;background:#fff;box-sizing:border-box}.experience-review-search image{width:15px;height:15px;flex:0 0 15px}.experience-review-search input{min-width:0;height:36px;flex:1;font-size:11px}.experience-review-search button{width:24px;height:24px;margin:0;padding:0;border:0;background:transparent;color:#91a0af;font-size:15px}.experience-review-select{width:142px;flex:0 0 142px}.experience-review-select.compact{width:112px;flex-basis:112px}.experience-review-select.sort{width:156px;flex-basis:156px}.experience-review-date-range{height:38px;padding:0 8px;display:flex;align-items:center;gap:6px;border:1px solid #dae4e8;border-radius:7px;background:#fff;box-sizing:border-box}.experience-review-date-range input{width:105px;height:34px;color:#5d7186;font-size:10px}.experience-review-date-range text{color:#9aa6b3;font-size:9px}.experience-review-clear,.experience-review-refresh{height:36px;margin:0;padding:0 13px;border-radius:7px;display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;font-size:10px;line-height:1;font-weight:800}.experience-review-clear{border:0;background:#f1f5f7;color:#718194}.experience-review-refresh{border:1px solid #d7e3e6;background:#fff;color:#5c6e82}.experience-review-search button::after,.experience-review-clear::after,.experience-review-refresh::after,.experience-review-open::after,.experience-review-pagination button::after,.experience-review-dialog button::after{border:0}.experience-review-table-wrap{min-height:0;flex:1;overflow-x:auto}.experience-review-table{min-width:1140px;min-height:100%}.experience-review-grid{display:grid;grid-template-columns:2.2fr 1.15fr 1fr .72fr .9fr .64fr 60px;align-items:center;gap:13px;padding:0 17px}.experience-review-head{min-height:42px;color:#8796a4;background:#f7f9fa;font-size:10px;font-weight:800}.experience-review-row{min-height:78px;border-top:1px solid #edf1f3;cursor:pointer;font-size:11px}.experience-review-row:hover{background:#fbfefd}.experience-review-post,.experience-review-tags{min-width:0}.experience-review-post strong,.experience-review-post text,.experience-review-tags strong,.experience-review-tags text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.experience-review-post strong{color:#3a5066;font-size:11px}.experience-review-post text{margin-top:5px;color:#8795a4;font-size:9px}.experience-review-author{min-width:0;display:flex;align-items:center;gap:9px}.experience-review-author>view{width:34px;height:34px;display:flex;align-items:center;justify-content:center;flex:0 0 34px;border-radius:50%;background:#e9f6f2;color:#248c77;font-size:12px;font-weight:900}.experience-review-author>text{min-width:0}.experience-review-author strong,.experience-review-author small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.experience-review-author strong{color:#40566c;font-size:10px}.experience-review-author small{margin-top:4px;color:#9aa6b2;font-size:8px}.experience-review-tags strong{color:#465e75;font-size:10px}.experience-review-tags text{margin-top:4px;color:#8796a5;font-size:9px}.experience-review-status{display:inline-flex;padding:5px 8px;border-radius:99px;background:#fff4df;color:#a77423;font-size:9px;font-weight:850}.experience-review-status.approved{background:#e8f7f2;color:#238b75}.experience-review-status.rejected{background:#fff0ed;color:#bd5f55}.experience-review-time,.experience-review-version{color:#77889a;font-size:10px}.experience-review-open{height:30px;margin:0;padding:0 11px;border:0;border-radius:6px;background:#eaf7f4;color:#278b78;font-size:10px;font-weight:850}.experience-review-state{padding:58px 20px;color:#91a0ae;text-align:center;font-size:12px}.experience-review-state.error{color:#ba6962}.experience-review-state text{display:block}.experience-review-state button{min-width:88px;height:34px;margin:13px auto 0;border:0;border-radius:7px;background:#eef7f5;color:#278b78;font-size:10px}.experience-review-pagination{min-height:58px;padding:0 17px;border-top:1px solid #eaf0f2;display:flex;align-items:center;justify-content:space-between;gap:14px;color:#90a0af;background:#fff;font-size:10px}.experience-review-pagination>view{display:flex;align-items:center;gap:8px}.experience-review-pagination button,.experience-review-pagination strong{width:34px;height:34px;margin:0;padding:0;border:1px solid #dfe8eb;border-radius:7px;background:#fff;display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;color:#718295;font-size:16px}.experience-review-pagination strong{border-color:#d6eee8;color:#268b78;background:#eaf8f4;font-size:11px}.experience-review-pagination button:disabled{color:#c4cdd5;background:#f8fafb}.experience-review-backdrop{position:fixed;z-index:6500;inset:0;padding:24px;display:flex;align-items:center;justify-content:center;background:rgba(24,39,55,.4);backdrop-filter:blur(4px)}.experience-review-dialog{width:min(900px,calc(100vw - 48px));height:min(820px,calc(100vh - 48px));overflow:hidden;border:1px solid #dfe8eb;border-radius:10px;background:#fff;box-shadow:0 30px 90px rgba(26,42,58,.24);display:flex;flex-direction:column}.experience-review-dialog-header{padding:17px 21px;border-bottom:1px solid #e9eef1;display:flex;align-items:center;justify-content:space-between;gap:18px}.experience-review-dialog-header>view{min-width:0}.experience-review-dialog-header text,.experience-review-dialog-header strong{display:block}.experience-review-dialog-header text{color:#2b967f;font-size:9px;font-weight:850;letter-spacing:.12em}.experience-review-dialog-header strong{margin-top:5px;overflow:hidden;color:#30465d;font-size:17px;text-overflow:ellipsis;white-space:nowrap}.experience-review-dialog-header button{width:34px;height:34px;margin:0;padding:0;border:0;border-radius:50%;background:#f2f5f7;display:flex;align-items:center;justify-content:center;flex:0 0 34px}.experience-review-dialog-header :deep(.close-icon-image){width:16px;height:16px}.experience-review-dialog-scroll{min-height:0;flex:1}.experience-review-dialog-content{padding:21px}.experience-review-detail-state{padding:80px 24px;color:#91a0ae;text-align:center;font-size:12px}.experience-review-detail-state.error{color:#ba6962}.experience-review-detail-state text{display:block}.experience-review-detail-state button{height:34px;margin:14px auto 0;border:0;border-radius:7px;background:#eef7f5;color:#278b78;font-size:10px}.experience-review-meta{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));overflow:hidden;border:1px solid #e3eaed;border-radius:8px}.experience-review-meta>view{min-width:0;min-height:76px;padding:13px 14px;display:flex;flex-direction:column;justify-content:center}.experience-review-meta>view+view{border-left:1px solid #e7edf0}.experience-review-meta text,.experience-review-meta small{color:#98a7b6;font-size:9px}.experience-review-meta strong{margin-top:5px;overflow:hidden;color:#40566c;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.experience-review-meta small{margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.experience-review-meta .status-pending{color:#a77423}.experience-review-meta .status-approved{color:#238b75}.experience-review-meta .status-rejected{color:#bd5f55}.experience-review-heading{margin:20px 0 9px;color:#40566c;font-size:12px;font-weight:850}.experience-review-content-block{padding:15px;border:1px solid #e3ebee;border-radius:8px;background:#fbfcfd}.experience-review-content-block strong,.experience-review-content-block text{display:block}.experience-review-content-block strong{color:#344a60;font-size:13px}.experience-review-content-block text{margin-top:9px;color:#52677b;font-size:12px;line-height:1.75;white-space:pre-wrap}.experience-review-media{margin-top:12px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.experience-review-media image{width:100%;aspect-ratio:1;border-radius:7px;background:#edf2f4;cursor:pointer}.experience-review-history-empty{padding:24px;border-radius:7px;background:#f7f9fa;color:#98a6b3;font-size:10px;text-align:center}.experience-review-history-item{position:relative;padding:0 0 18px 27px}.experience-review-history-item:not(:last-child)::before{width:1px;content:'';position:absolute;top:11px;bottom:-2px;left:7px;background:#dce6e9}.experience-review-history-dot{width:12px;height:12px;position:absolute;top:4px;left:1px;border:3px solid #fff;border-radius:50%;box-shadow:0 0 0 1px #d7e3e7;background:#55bda6}.experience-review-history-dot.submitted{background:#d7a94f}.experience-review-history-dot.rejected{background:#dc766a}.experience-review-history-item>view>view{display:flex;align-items:center;justify-content:space-between;gap:12px}.experience-review-history-item strong{color:#40566c;font-size:11px}.experience-review-history-item>view>view text{color:#93a1ae;font-size:9px}.experience-review-history-item small{display:block;margin-top:4px;color:#9aa6b2;font-size:9px}.experience-review-history-note{display:block;margin-top:6px;color:#65778a;font-size:10px;line-height:1.55}.experience-review-decision{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.experience-review-decision button{height:38px;margin:0;border:1px solid #dbe6e8;border-radius:7px;background:#fff;color:#65778b;font-size:11px;font-weight:800}.experience-review-decision button.active{border-color:#75cfba;background:#eaf8f4;color:#248b76}.experience-review-decision button.reject.active{border-color:#e6a099;background:#fff1ee;color:#bb5e54}.experience-review-form-field{margin-top:15px}.experience-review-form-field>text{display:block;color:#7f8f9f;font-size:10px;font-weight:750}.experience-review-reason-select{width:100%;margin-top:8px}.experience-review-form-field textarea{width:100%;min-height:92px;margin-top:8px;padding:11px 12px;box-sizing:border-box;border:1px dashed #a8bad3;border-radius:7px;color:#40566d;background:#fbfcff;font-size:11px;line-height:1.55}.experience-review-previous-result{margin-top:18px;padding:13px 14px;border:1px solid #e4eaed;border-radius:8px;background:#fbfcfd}.experience-review-previous-result text,.experience-review-previous-result strong{display:block}.experience-review-previous-result text{color:#8b9aa8;font-size:9px}.experience-review-previous-result strong{margin-top:6px;color:#53687b;font-size:11px;line-height:1.55}.experience-review-dialog-actions{padding:14px 21px;border-top:1px solid #e9eef1;background:#fff;display:flex;justify-content:flex-end;gap:10px}.experience-review-dialog-actions button{min-width:112px;height:36px;margin:0;border:0;border-radius:7px;background:#2da58b;color:#fff;font-size:10px;font-weight:850}.experience-review-dialog-actions button.reject{background:#d96c60}.experience-review-dialog-actions button.cancel{border:1px solid #dfe7ea;background:#fff;color:#718194}@media(max-width:1180px){.experience-review-summary{grid-template-columns:repeat(2,minmax(0,1fr))}.experience-review-search{width:100%;flex-basis:100%}}@media(max-width:820px){.experience-review-page{min-height:auto}.experience-review-dialog{width:100%;height:calc(100vh - 28px)}.experience-review-backdrop{padding:14px}.experience-review-meta{grid-template-columns:repeat(2,minmax(0,1fr))}.experience-review-meta>view:nth-child(3){border-left:0;border-top:1px solid #e7edf0}.experience-review-meta>view:nth-child(4){border-top:1px solid #e7edf0}.experience-review-media{grid-template-columns:repeat(2,minmax(0,1fr))}.experience-review-dialog-actions{padding-bottom:calc(env(safe-area-inset-bottom) + 14px)}}
</style>
