<template>
  <view class="resource-management-page">
    <view class="resource-management-heading">
      <view>
        <view class="resource-management-kicker">CIRCLE RESOURCES</view>
        <view class="resource-management-title">资料管理</view>
        <view class="resource-management-subtitle">维护研圈的推荐资料与精选课程，发布后的推荐资料会在用户端提供链接复制。</view>
      </view>
      <button class="resource-management-add" type="button" @tap="openCreateEditor">新增{{ currentTypeLabel }}</button>
    </view>

    <view class="resource-management-type-tabs" role="tablist" aria-label="资料管理分类">
      <button
        v-for="item in typeOptions"
        :key="item.value"
        class="resource-management-type-tab"
        :class="{ active: resourceType === item.value }"
        type="button"
        role="tab"
        :aria-selected="resourceType === item.value"
        @tap="selectResourceType(item.value)"
      >
        <text>{{ item.label }}</text>
        <small>{{ item.description }}</small>
      </button>
    </view>

    <view class="resource-management-workspace">
      <view class="resource-management-toolbar">
        <view class="resource-management-search">
          <input v-model.trim="keyword" maxlength="100" :placeholder="`搜索${currentTypeLabel}名称、分类或简介`" @input="scheduleLoad" @confirm="refresh" />
          <button v-if="keyword" type="button" aria-label="清空搜索" @tap="clearKeyword">×</button>
        </view>
        <AdminSelect
          class="resource-management-status-select"
          :options="statusOptions"
          :value-index="statusIndex"
          aria-label="筛选资料状态"
          menu-align="right"
          @change="changeStatus"
        />
        <button class="resource-management-refresh" type="button" :disabled="loading" @tap="refresh">{{ loading ? '加载中…' : '重新加载' }}</button>
      </view>

      <view v-if="loading" class="resource-management-state">正在读取{{ currentTypeLabel }}…</view>
      <view v-else-if="loadError" class="resource-management-state error">
        <text>{{ loadError }}</text>
        <button type="button" @tap="refresh">重新加载</button>
      </view>
      <view v-else-if="!resources.length" class="resource-management-empty">
        <view class="resource-management-empty-mark">{{ resourceType === 'material' ? '资' : '课' }}</view>
        <strong>{{ resourceType === 'material' ? '暂未添加推荐资料' : '课程正在筹备' }}</strong>
        <text>{{ resourceType === 'material' ? '添加后可先保存草稿，确认网盘链接后再发布。' : '先建立课程信息和标价，内容上线时可直接发布。' }}</text>
        <button type="button" @tap="openCreateEditor">新增{{ currentTypeLabel }}</button>
      </view>
      <view v-else class="resource-management-table-wrap">
        <view class="resource-management-table">
          <view class="resource-management-table-head resource-management-grid">
            <text>{{ resourceType === 'material' ? '资料信息' : '课程信息' }}</text>
            <text>{{ resourceType === 'material' ? '链接 / 提取码' : '讲师 / 标价' }}</text>
            <text>状态</text>
            <text>排序</text>
            <text>更新时间</text>
            <text>操作</text>
          </view>
          <view v-for="item in resources" :key="item.id" class="resource-management-table-row resource-management-grid" @tap="openEditEditor(item)">
            <view class="resource-management-main-cell">
              <view class="resource-management-initial">{{ resourceInitial(item) }}</view>
              <view>
                <strong>{{ item.title }}</strong>
                <text>{{ resourceMeta(item) }}</text>
              </view>
            </view>
            <view class="resource-management-detail-cell">
              <template v-if="resourceType === 'material'">
                <strong :class="{ muted: !item.share_url }">{{ item.share_url ? '链接已填写' : '尚未填写链接' }}</strong>
                <text>{{ item.access_code ? `提取码：${item.access_code}` : '无提取码' }}</text>
              </template>
              <template v-else>
                <strong :class="{ muted: !item.instructor_name }">{{ item.instructor_name || '未填写讲师' }}</strong>
                <text>{{ formatCoursePrice(item.course_price) }}</text>
              </template>
            </view>
            <view><text class="resource-management-status" :class="item.status">{{ statusText(item.status) }}</text></view>
            <text class="resource-management-sort">{{ item.sort_order || 0 }}</text>
            <text class="resource-management-date">{{ formatDate(item.updated_at || item.created_at) }}</text>
            <view class="resource-management-actions">
              <button v-if="item.status !== 'published'" type="button" :disabled="updatingId === item.id" @tap.stop="publishItem(item)">{{ updatingId === item.id ? '处理中…' : '发布' }}</button>
              <button v-else type="button" :disabled="updatingId === item.id" @tap.stop="archiveItem(item)">{{ updatingId === item.id ? '处理中…' : '下架' }}</button>
              <button type="button" @tap.stop="openEditEditor(item)">编辑</button>
            </view>
          </view>
        </view>
        <view class="resource-management-pagination">
          <text>共 {{ resourceCount }} 条，每页 {{ pageSize }} 条</text>
          <view>
            <button type="button" :disabled="page <= 1 || loading" aria-label="上一页" @tap="changePage(page - 1)">‹</button>
            <text>{{ page }} / {{ totalPages }}</text>
            <button type="button" :disabled="page >= totalPages || loading" aria-label="下一页" @tap="changePage(page + 1)">›</button>
          </view>
        </view>
      </view>
    </view>

    <view v-if="editorVisible" class="resource-management-backdrop" @tap="closeEditor">
      <view class="resource-management-editor" role="dialog" aria-modal="true" :aria-label="`${editingId ? '编辑' : '新增'}${currentTypeLabel}`" @tap.stop>
        <view class="resource-management-editor-head">
          <view>
            <view class="resource-management-editor-kicker">{{ editingId ? 'EDIT RESOURCE' : 'NEW RESOURCE' }}</view>
            <view class="resource-management-editor-title">{{ editingId ? `编辑${currentTypeLabel}` : `新增${currentTypeLabel}` }}</view>
          </view>
          <button class="resource-management-editor-close" type="button" aria-label="关闭" :disabled="saving" @tap="closeEditor">×</button>
        </view>

        <scroll-view scroll-y class="resource-management-editor-scroll">
          <view class="resource-management-editor-body">
            <view class="resource-management-form-grid">
              <view class="resource-management-field full">
                <text>名称</text>
                <input v-model.trim="form.title" maxlength="120" :placeholder="resourceType === 'material' ? '例如：Z001 逻辑真题资料包' : '例如：港澳台考研逻辑系统课'" />
              </view>
              <view class="resource-management-field">
                <text>分类</text>
                <input v-model.trim="form.subject" maxlength="80" placeholder="例如：逻辑推理、英语运用" />
              </view>
              <view class="resource-management-field">
                <text>排序</text>
                <input v-model="form.sort_order" type="number" maxlength="6" placeholder="数字越小越靠前" />
              </view>
              <view class="resource-management-field full">
                <text>简介</text>
                <textarea v-model.trim="form.summary" maxlength="1000" :placeholder="resourceType === 'material' ? '介绍资料内容、适用阶段或使用建议' : '介绍课程内容、适用人群或上课节奏'" />
              </view>
              <view class="resource-management-field full">
                <text>标签</text>
                <input v-model.trim="form.tagsText" maxlength="300" placeholder="使用中文逗号或英文逗号分隔，例如：真题, Z001, 冲刺" />
              </view>
              <view class="resource-management-field full">
                <text>封面链接（可选）</text>
                <input v-model.trim="form.cover_url" maxlength="1000" placeholder="填写图片链接后，用户端会显示封面" />
              </view>
              <template v-if="resourceType === 'material'">
                <view class="resource-management-field full required">
                  <text>百度网盘链接</text>
                  <input v-model.trim="form.share_url" maxlength="1000" placeholder="https://pan.baidu.com/s/..." />
                </view>
                <view class="resource-management-field">
                  <text>提取码（可选）</text>
                  <input v-model.trim="form.access_code" maxlength="120" placeholder="例如：gaty" />
                </view>
              </template>
              <template v-else>
                <view class="resource-management-field">
                  <text>讲师（可选）</text>
                  <input v-model.trim="form.instructor_name" maxlength="80" placeholder="例如：港研通教研组" />
                </view>
                <view class="resource-management-field required">
                  <text>课程标价（元）</text>
                  <input v-model="form.course_price" type="digit" maxlength="10" placeholder="例如：99" />
                </view>
              </template>
              <view class="resource-management-field full">
                <text>状态</text>
                <AdminSelect :options="formStatusOptions" :value-index="formStatusIndex" aria-label="设置资源状态" @change="changeFormStatus" />
              </view>
            </view>
          </view>
        </scroll-view>

        <view class="resource-management-editor-footer">
          <button v-if="editingId" class="resource-management-delete" type="button" :disabled="saving" @tap="confirmDelete">删除</button>
          <view>
            <button class="resource-management-cancel" type="button" :disabled="saving" @tap="closeEditor">取消</button>
            <button class="resource-management-save" type="button" :disabled="saving" @tap="save">{{ saving ? '保存中…' : '保存' }}</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import {
  createQuestionAdminResource,
  deleteQuestionAdminResource,
  fetchQuestionAdminResources,
  updateQuestionAdminResource
} from '../api/circleResources'
import AdminSelect from './AdminSelect.vue'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false
  }
})

const pageSize = 20
const resourceType = ref('material')
const resourceStatus = ref('all')
const keyword = ref('')
const resources = ref([])
const resourceCount = ref(0)
const page = ref(1)
const loading = ref(false)
const loadError = ref('')
const editorVisible = ref(false)
const editingId = ref('')
const saving = ref(false)
const updatingId = ref('')
let searchTimer = null

const form = reactive(createEmptyForm())
const typeOptions = [
  { value: 'material', label: '推荐资料', description: '百度网盘链接' },
  { value: 'course', label: '精选课程', description: '未来课程上架' }
]
const statusOptions = [
  { value: 'all', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'published', label: '已发布' },
  { value: 'archived', label: '已下架' }
]
const formStatusOptions = statusOptions.slice(1)

const currentTypeLabel = computed(() => (resourceType.value === 'material' ? '推荐资料' : '精选课程'))
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex((item) => item.value === resourceStatus.value)))
const formStatusIndex = computed(() => Math.max(0, formStatusOptions.findIndex((item) => item.value === form.status)))
const totalPages = computed(() => Math.max(1, Math.ceil(resourceCount.value / pageSize)))

onMounted(() => {
  void refresh()
})

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
})

defineExpose({ refresh })

function createEmptyForm() {
  return {
    title: '',
    summary: '',
    subject: '',
    tagsText: '',
    cover_url: '',
    share_url: '',
    access_code: '',
    instructor_name: '',
    course_price: '',
    sort_order: 0,
    status: 'draft'
  }
}

function resetForm() {
  Object.assign(form, createEmptyForm())
}

async function refresh() {
  if (loading.value) return
  loading.value = true
  loadError.value = ''
  try {
    if (props.preview) {
      const filtered = previewResources()
        .filter((item) => item.resource_type === resourceType.value)
        .filter((item) => resourceStatus.value === 'all' || item.status === resourceStatus.value)
        .filter((item) => matchesKeyword(item, keyword.value))
      resourceCount.value = filtered.length
      resources.value = filtered.slice((page.value - 1) * pageSize, page.value * pageSize)
      return
    }
    const response = await fetchQuestionAdminResources({
      resource_type: resourceType.value,
      status: resourceStatus.value,
      keyword: keyword.value,
      limit: pageSize,
      offset: (page.value - 1) * pageSize
    })
    resources.value = Array.isArray(response?.items) ? response.items : []
    resourceCount.value = Number(response?.count || 0)
    if (resources.value.length === 0 && resourceCount.value > 0 && page.value > totalPages.value) {
      page.value = totalPages.value
      loading.value = false
      return refresh()
    }
  } catch (error) {
    resources.value = []
    resourceCount.value = 0
    loadError.value = error?.detail || '资料管理读取失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function selectResourceType(type) {
  if (type === resourceType.value) return
  resourceType.value = type
  resourceStatus.value = 'all'
  keyword.value = ''
  page.value = 1
  void refresh()
}

function changeStatus(event) {
  resourceStatus.value = statusOptions[Number(event?.detail?.value || 0)]?.value || 'all'
  page.value = 1
  void refresh()
}

function changeFormStatus(event) {
  form.status = formStatusOptions[Number(event?.detail?.value || 0)]?.value || 'draft'
}

function scheduleLoad() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    void refresh()
  }, 360)
}

function clearKeyword() {
  keyword.value = ''
  page.value = 1
  void refresh()
}

function changePage(nextPage) {
  const normalized = Math.max(1, Math.min(totalPages.value, Number(nextPage || 1)))
  if (normalized === page.value) return
  page.value = normalized
  void refresh()
}

function openCreateEditor() {
  resetForm()
  editingId.value = ''
  editorVisible.value = true
}

function openEditEditor(item) {
  if (!item) return
  editingId.value = item.id
  Object.assign(form, {
    title: item.title || '',
    summary: item.summary || '',
    subject: item.subject || '',
    tagsText: Array.isArray(item.tags) ? item.tags.join('，') : '',
    cover_url: item.cover_url || '',
    share_url: item.share_url || '',
    access_code: item.access_code || '',
    instructor_name: item.instructor_name || '',
    course_price: item.course_price == null ? '' : String(item.course_price),
    sort_order: Number(item.sort_order || 0),
    status: item.status || 'draft'
  })
  editorVisible.value = true
}

function closeEditor() {
  if (saving.value) return
  editorVisible.value = false
  editingId.value = ''
  resetForm()
}

function buildPayload() {
  const title = String(form.title || '').trim()
  if (!title) {
    uni.showToast({ title: '请填写名称', icon: 'none' })
    return null
  }
  const shareUrl = String(form.share_url || '').trim()
  if (resourceType.value === 'material' && form.status === 'published' && !shareUrl) {
    uni.showToast({ title: '发布前请填写百度网盘链接', icon: 'none' })
    return null
  }
  const priceInput = String(form.course_price ?? '').trim()
  const coursePrice = priceInput === '' ? null : Number(priceInput)
  if (resourceType.value === 'course' && form.status === 'published' && (!Number.isFinite(coursePrice) || coursePrice < 0)) {
    uni.showToast({ title: '发布前请填写正确的课程标价', icon: 'none' })
    return null
  }
  if (coursePrice !== null && (!Number.isFinite(coursePrice) || coursePrice < 0)) {
    uni.showToast({ title: '请填写正确的课程标价', icon: 'none' })
    return null
  }
  return {
    resource_type: resourceType.value,
    title,
    summary: String(form.summary || '').trim(),
    subject: String(form.subject || '').trim(),
    tags: String(form.tagsText || '').split(/[，,]/).map((item) => item.trim()).filter(Boolean).slice(0, 12),
    cover_url: String(form.cover_url || '').trim(),
    share_url: shareUrl,
    access_code: String(form.access_code || '').trim(),
    instructor_name: String(form.instructor_name || '').trim(),
    course_price: coursePrice,
    sort_order: Number.isFinite(Number(form.sort_order)) ? Number(form.sort_order) : 0,
    status: form.status
  }
}

async function save() {
  const payload = buildPayload()
  if (!payload || saving.value) return
  saving.value = true
  let persisted = false
  try {
    if (props.preview) {
      applyPreviewSave(payload)
    } else if (editingId.value) {
      await updateQuestionAdminResource(editingId.value, payload)
    } else {
      await createQuestionAdminResource(payload)
    }
    persisted = true
    uni.showToast({ title: '资料已保存', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '资料保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
  if (!persisted) return
  closeEditor()
  await refresh()
}

async function publishItem(item) {
  if (item.resource_type === 'material' && !item.share_url) {
    uni.showToast({ title: '请先补充百度网盘链接', icon: 'none' })
    openEditEditor(item)
    return
  }
  if (item.resource_type === 'course' && item.course_price == null) {
    uni.showToast({ title: '请先补充课程标价', icon: 'none' })
    openEditEditor(item)
    return
  }
  await updateItemStatus(item, 'published')
}

async function archiveItem(item) {
  await updateItemStatus(item, 'archived')
}

async function updateItemStatus(item, nextStatus) {
  if (!item?.id || updatingId.value) return
  updatingId.value = item.id
  try {
    const payload = itemPayload(item, nextStatus)
    if (props.preview) {
      item.status = nextStatus
      item.updated_at = new Date().toISOString()
    } else {
      await updateQuestionAdminResource(item.id, payload)
    }
    uni.showToast({ title: nextStatus === 'published' ? '已发布到用户端' : '已下架', icon: 'success' })
    await refresh()
  } catch (error) {
    uni.showToast({ title: error?.detail || '状态更新失败', icon: 'none' })
  } finally {
    updatingId.value = ''
  }
}

function itemPayload(item, nextStatus) {
  return {
    resource_type: item.resource_type,
    title: item.title || '',
    summary: item.summary || '',
    subject: item.subject || '',
    tags: Array.isArray(item.tags) ? item.tags : [],
    cover_url: item.cover_url || '',
    share_url: item.share_url || '',
    access_code: item.access_code || '',
    instructor_name: item.instructor_name || '',
    course_price: item.course_price == null ? null : Number(item.course_price),
    sort_order: Number(item.sort_order || 0),
    status: nextStatus
  }
}

function confirmDelete() {
  if (!editingId.value || saving.value) return
  uni.showModal({
    title: `删除${currentTypeLabel.value}`,
    content: '删除后用户端将不再展示，确定继续吗？',
    confirmText: '删除',
    success: (result) => {
      if (result.confirm) void deleteCurrentItem()
    }
  })
}

async function deleteCurrentItem() {
  if (!editingId.value) return
  saving.value = true
  let deleted = false
  try {
    if (props.preview) {
      const target = resources.value.find((item) => item.id === editingId.value)
      if (target) target.status = 'archived'
    } else {
      await deleteQuestionAdminResource(editingId.value)
    }
    deleted = true
    uni.showToast({ title: '资料已删除', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '资料删除失败', icon: 'none' })
  } finally {
    saving.value = false
  }
  if (!deleted) return
  closeEditor()
  await refresh()
}

function applyPreviewSave(payload) {
  const now = new Date().toISOString()
  if (editingId.value) {
    const item = resources.value.find((candidate) => candidate.id === editingId.value)
    if (item) Object.assign(item, payload, { updated_at: now })
    return
  }
  resources.value.unshift({ id: `preview-resource-${Date.now()}`, ...payload, created_at: now, updated_at: now })
}

function resourceInitial(item) {
  return String(item?.title || currentTypeLabel.value).trim().slice(0, 1) || '资'
}

function resourceMeta(item) {
  const parts = [item.subject, ...(Array.isArray(item.tags) ? item.tags.slice(0, 2) : [])].filter(Boolean)
  return parts.join(' · ') || item.summary || '暂未填写简介'
}

function statusText(value) {
  return { draft: '草稿', published: '已发布', archived: '已下架' }[value] || '草稿'
}

function formatCoursePrice(value) {
  if (value == null || value === '') return '暂未标价'
  const number = Number(value)
  if (!Number.isFinite(number)) return '暂未标价'
  if (number === 0) return '免费'
  return `¥${Number.isInteger(number) ? number : number.toFixed(2)}`
}

function formatDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(date)
}

function matchesKeyword(item, input) {
  const needle = String(input || '').trim().toLowerCase()
  if (!needle) return true
  return [item.title, item.summary, item.subject, ...(item.tags || [])].join(' ').toLowerCase().includes(needle)
}

function previewResources() {
  return [
    {
      id: 'preview-material-1', resource_type: 'material', title: 'Z001 逻辑冲刺资料包', summary: '真题练习与错题复盘资料。', subject: '逻辑推理', tags: ['Z001', '冲刺'], share_url: 'https://pan.baidu.com/s/preview', access_code: 'gaty', instructor_name: '', course_price: null, sort_order: 10, status: 'published', updated_at: '2026-08-25T04:00:00Z'
    },
    {
      id: 'preview-course-1', resource_type: 'course', title: '港澳台考研逻辑系统课', summary: '从基础到冲刺的逻辑训练课程。', subject: '逻辑推理', tags: ['系统课'], share_url: '', access_code: '', instructor_name: '港研通教研组', course_price: 99, sort_order: 10, status: 'draft', updated_at: '2026-08-25T04:00:00Z'
    }
  ]
}
</script>

<style scoped>
.resource-management-page{min-height:calc(100vh - 158px);color:#33475e}.resource-management-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:18px}.resource-management-kicker,.resource-management-editor-kicker{color:#8494a4;font-size:10px;font-weight:850;letter-spacing:.12em}.resource-management-title{margin-top:6px;color:#2c4058;font-size:24px;font-weight:850;line-height:1.2}.resource-management-subtitle{max-width:720px;margin-top:8px;color:#8090a0;font-size:11px;line-height:1.6}.resource-management-add,.resource-management-empty button{height:38px;margin:0;padding:0 16px;display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:7px;background:#35b79d;color:#fff;font-size:11px;font-weight:800;line-height:1;text-align:center}.resource-management-add::after,.resource-management-empty button::after,.resource-management-toolbar button::after,.resource-management-actions button::after,.resource-management-editor button::after{border:0}.resource-management-type-tabs{margin-top:18px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.resource-management-type-tab{min-height:76px;margin:0;padding:14px 16px;display:flex;align-items:flex-start;flex-direction:column;justify-content:center;border:1px solid #dfe8eb;border-radius:8px;background:#fff;color:#657689;text-align:left}.resource-management-type-tab text{color:#4c6175;font-size:13px;font-weight:850}.resource-management-type-tab small{margin-top:6px;color:#97a4af;font-size:10px}.resource-management-type-tab.active{border-color:#8fd9cb;background:#fbfffe;box-shadow:0 8px 22px rgba(48,183,157,.08)}.resource-management-type-tab.active text{color:#23836f}.resource-management-workspace{margin-top:16px;overflow:hidden;border:1px solid #dfe8eb;border-radius:9px;background:#fff;box-shadow:0 10px 30px rgba(36,55,73,.04)}.resource-management-toolbar{padding:14px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #edf1f3;background:#fbfcfd}.resource-management-search{height:38px;min-width:240px;flex:1;padding:0 10px;display:flex;align-items:center;gap:8px;border:1px solid #dae4e8;border-radius:8px;background:#fff}.resource-management-search input{min-width:0;flex:1;height:36px;color:#52677b;font-size:11px}.resource-management-search button{width:26px;height:26px;margin:0;padding:0;border:0;background:transparent;color:#95a3af;font-size:19px;line-height:1}.resource-management-status-select{width:140px;flex:0 0 140px}.resource-management-refresh{height:36px;min-width:82px;margin:0;padding:0 12px;display:inline-flex;align-items:center;justify-content:center;border:1px solid #d7e3e6;border-radius:7px;background:#fff;color:#617286;font-size:10px;font-weight:750;line-height:1;text-align:center}.resource-management-state{min-height:240px;padding:28px;display:flex;align-items:center;justify-content:center;color:#91a0ae;font-size:12px;text-align:center}.resource-management-state.error{flex-direction:column;gap:14px;color:#bb6d66}.resource-management-state button{height:34px;margin:0;padding:0 13px;border:1px solid #dce5e8;border-radius:7px;background:#fff;color:#607489;font-size:10px}.resource-management-empty{min-height:284px;padding:34px;display:flex;align-items:center;flex-direction:column;justify-content:center;text-align:center}.resource-management-empty-mark{width:52px;height:52px;display:grid;place-items:center;border-radius:8px;background:#eaf8f4;color:#2ba38a;font-size:18px;font-weight:850}.resource-management-empty strong{margin-top:16px;color:#43576c;font-size:14px}.resource-management-empty text{max-width:420px;margin-top:9px;color:#93a1ae;font-size:11px;line-height:1.6}.resource-management-empty button{margin-top:17px}.resource-management-table-wrap{overflow-x:auto}.resource-management-table{min-width:960px}.resource-management-grid{display:grid;grid-template-columns:minmax(240px,1.5fr) minmax(150px,.86fr) 80px 52px 88px 138px;align-items:center;gap:14px;padding:0 18px}.resource-management-table-head{min-height:42px;color:#8796a4;background:#f7f9fa;font-size:10px;font-weight:800}.resource-management-table-row{min-height:78px;border-top:1px solid #edf1f3;cursor:pointer;font-size:11px}.resource-management-table-row:hover{background:#fbfefd}.resource-management-main-cell{min-width:0;display:flex;align-items:center;gap:11px}.resource-management-initial{width:38px;height:38px;flex:0 0 38px;display:grid;place-items:center;border-radius:8px;background:#e8f5f2;color:#288b77;font-size:15px;font-weight:850}.resource-management-main-cell>view:last-child,.resource-management-detail-cell{min-width:0}.resource-management-main-cell strong,.resource-management-main-cell text,.resource-management-detail-cell strong,.resource-management-detail-cell text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.resource-management-main-cell strong,.resource-management-detail-cell strong{color:#40556a;font-size:11px}.resource-management-main-cell text,.resource-management-detail-cell text{margin-top:5px;color:#98a5b2;font-size:9px}.resource-management-detail-cell strong.muted{color:#9daab5}.resource-management-status{display:inline-flex;min-width:46px;height:24px;align-items:center;justify-content:center;border-radius:99px;font-size:9px;font-weight:800}.resource-management-status.draft{background:#f0f3f5;color:#7e8c99}.resource-management-status.published{background:#e4f7f1;color:#258770}.resource-management-status.archived{background:#f5f1f1;color:#9b7272}.resource-management-sort,.resource-management-date{color:#7f90a0;font-size:10px}.resource-management-actions{align-self:stretch;display:flex;align-items:center;justify-content:center;gap:7px}.resource-management-actions button{height:30px;margin:0;padding:0 10px;display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:6px;background:#eef7f5;color:#278b78;font-size:10px;font-weight:800;line-height:1;text-align:center}.resource-management-actions button+button{background:#f3f6f8;color:#708093}.resource-management-actions button:disabled{opacity:.62}.resource-management-pagination{min-height:58px;padding:0 18px;display:flex;align-items:center;justify-content:space-between;border-top:1px solid #eaf0f2;color:#90a0af;font-size:10px}.resource-management-pagination>view{display:flex;align-items:center;gap:8px}.resource-management-pagination button{width:34px;height:34px;margin:0;padding:0;display:inline-flex;align-items:center;justify-content:center;border:1px solid #dfe8eb;border-radius:7px;background:#fff;color:#718295;font-size:16px;line-height:1}.resource-management-pagination button:disabled{color:#c4cdd5;background:#f8fafb}.resource-management-backdrop{position:fixed;z-index:6200;inset:0;padding:24px;display:flex;align-items:center;justify-content:center;box-sizing:border-box;background:rgba(24,39,55,.38);backdrop-filter:blur(4px)}.resource-management-editor{width:min(760px,calc(100vw - 48px));height:min(760px,calc(100vh - 48px));display:flex;flex-direction:column;overflow:hidden;border:1px solid #dfe8eb;border-radius:10px;background:#fff;box-shadow:0 30px 90px rgba(26,42,58,.24)}.resource-management-editor-head{padding:18px 22px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e9eef1}.resource-management-editor-title{margin-top:5px;color:#30465d;font-size:17px;font-weight:850}.resource-management-editor-close{width:34px;height:34px;flex:0 0 34px;margin:0;padding:0;display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:50%;background:#f2f5f7;color:#768695;font-size:20px;line-height:1}.resource-management-editor-scroll{min-height:0;flex:1}.resource-management-editor-body{padding:20px 22px}.resource-management-form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}.resource-management-field{min-width:0}.resource-management-field.full{grid-column:1 / -1}.resource-management-field>text{display:block;margin-bottom:7px;color:#718397;font-size:10px;font-weight:800}.resource-management-field.required>text::after{margin-left:4px;color:#d67c70;content:'*'}.resource-management-field input,.resource-management-field textarea{width:100%;box-sizing:border-box;border:1px solid #dbe5e8;border-radius:7px;background:#fff;color:#40566c;font-size:11px}.resource-management-field input{height:38px;padding:0 10px}.resource-management-field textarea{min-height:96px;padding:10px;line-height:1.55}.resource-management-field input:focus,.resource-management-field textarea:focus{border-color:#8fd8ca;background:#fbfffe;outline:0;box-shadow:0 0 0 3px rgba(67,183,157,.08)}.resource-management-editor-footer{min-height:70px;padding:0 22px;display:flex;align-items:center;justify-content:space-between;border-top:1px solid #e8eef1}.resource-management-editor-footer>view{display:flex;gap:9px}.resource-management-editor-footer button{height:36px;margin:0;padding:0 14px;display:inline-flex;align-items:center;justify-content:center;border-radius:7px;font-size:10px;font-weight:800;line-height:1;text-align:center}.resource-management-delete{border:0;background:#fff0ef;color:#b45f57}.resource-management-cancel{border:1px solid #dfe8eb;background:#fff;color:#6d7f91}.resource-management-save{border:0;background:#34b399;color:#fff}.resource-management-editor-footer button:disabled{opacity:.6}@media(max-width:960px){.resource-management-toolbar{flex-wrap:wrap}.resource-management-search{flex-basis:100%}}@media(max-width:820px){.resource-management-page{min-height:auto}.resource-management-heading{align-items:flex-start;flex-direction:column}.resource-management-type-tabs{grid-template-columns:1fr}.resource-management-add{width:100%}.resource-management-backdrop{padding:14px}.resource-management-editor{width:100%;height:calc(100vh - 28px)}.resource-management-editor-body{padding:18px}.resource-management-form-grid{grid-template-columns:1fr}.resource-management-field.full{grid-column:auto}.resource-management-pagination{align-items:flex-start;flex-direction:column;justify-content:center;padding-top:12px;padding-bottom:12px}.resource-management-editor-footer{padding:0 16px}.resource-management-editor-footer button{padding:0 11px}}
</style>
