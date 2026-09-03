<template>
  <view class="recycle-page">
    <view class="recycle-policy-bar">
      <view class="recycle-policy-icon" aria-hidden="true">
        <image src="/static/admin-icons/nav-recycle-bin.svg" mode="aspectFit" />
      </view>
      <view class="recycle-policy-copy">
        <strong>帖子回收站</strong>
        <text>删除后的帖子保留 {{ retentionDays }} 天，过期后自动永久清除</text>
      </view>
      <view class="recycle-policy-count"><strong>{{ formatCount(itemCount) }}</strong><text>待清理</text></view>
    </view>

    <view class="recycle-workspace">
      <view class="recycle-toolbar">
        <view class="recycle-search">
          <image src="/static/admin-icons/admin-search.svg" mode="aspectFit" />
          <input
            v-model.trim="filters.search"
            maxlength="80"
            placeholder="搜索帖子、正文或发布人"
            confirm-type="search"
            @input="scheduleSearch"
            @confirm="applyFilters"
          />
          <button v-if="filters.search" aria-label="清空搜索" @tap="clearSearch">×</button>
        </view>
        <AdminSelect
          class="recycle-select"
          :options="typeOptions.map((item) => item.label)"
          :value-index="typeIndex"
          aria-label="帖子类型筛选"
          @change="selectType"
        />
        <AdminSelect
          class="recycle-select sort"
          :options="sortOptions.map((item) => item.label)"
          :value-index="sortIndex"
          aria-label="回收站排序"
          @change="selectSort"
        />
        <button v-if="hasFilters" class="recycle-clear" @tap="clearFilters">清空</button>
        <button class="recycle-refresh" :disabled="loading" @tap="refresh">
          {{ loading ? '刷新中…' : '刷新' }}
        </button>
      </view>

      <view v-if="selectedIds.length" class="recycle-selection-bar">
        <text>已选择 <strong>{{ selectedIds.length }}</strong> 条帖子</text>
        <view>
          <button class="selection-restore" :disabled="saving" @tap="restoreSelected">恢复</button>
          <button class="selection-purge" :disabled="saving" @tap="purgeSelected">永久删除</button>
          <button class="selection-cancel" :disabled="saving" @tap="selectedIds = []">取消选择</button>
        </view>
      </view>

      <view class="recycle-table-wrap">
        <view class="recycle-table">
          <view class="recycle-grid recycle-head">
            <view class="recycle-check-cell">
              <button class="recycle-check" :class="{ checked: allPageSelected }" @tap="toggleSelectPage">
                {{ allPageSelected ? '✓' : '' }}
              </button>
            </view>
            <view>帖子</view>
            <view>发布用户</view>
            <view>类型 / 分类</view>
            <view>删除时间</view>
            <view>自动清除</view>
            <view>删除人</view>
            <view>操作</view>
          </view>

          <view v-if="loading" class="recycle-state">正在读取回收站…</view>
          <view v-else-if="loadError" class="recycle-state error">
            <text>回收站加载失败，请检查网络或数据库迁移状态。</text>
            <button @tap="refresh">重新加载</button>
          </view>
          <view v-else-if="!items.length" class="recycle-state">
            <strong>回收站是空的</strong>
            <text>当前没有等待清理的帖子</text>
          </view>
          <view
            v-for="item in items"
            v-else
            :key="item.id"
            class="recycle-grid recycle-row"
            :class="{ selected: selectedSet.has(item.id) }"
          >
            <view class="recycle-check-cell">
              <button class="recycle-check" :class="{ checked: selectedSet.has(item.id) }" @tap="toggleItem(item.id)">
                {{ selectedSet.has(item.id) ? '✓' : '' }}
              </button>
            </view>
            <view class="recycle-post-cell">
              <strong>{{ item.title || '未填写标题' }}</strong>
              <text>{{ excerpt(item.content) }}</text>
            </view>
            <view class="recycle-author-cell">
              <view>{{ initial(item.author_name) }}</view>
              <text><strong>{{ item.author_name || '研友' }}</strong><small>ID {{ shortId(item.author_id) }}</small></text>
            </view>
            <view class="recycle-category-cell">
              <strong>{{ postTypeText(item.post_type) }}</strong>
              <text>{{ item.category || '未分类' }}</text>
            </view>
            <view class="recycle-time-cell">{{ formatDateTime(item.admin_deleted_at) }}</view>
            <view class="recycle-expiry-cell" :class="{ urgent: isUrgent(item.admin_purge_after) }">
              <strong>{{ remainingLabel(item.admin_purge_after) }}</strong>
              <text>{{ formatDateTime(item.admin_purge_after) }}</text>
            </view>
            <view class="recycle-admin-cell">{{ shortId(item.admin_deleted_by) }}</view>
            <view class="recycle-row-actions">
              <button class="restore" :disabled="saving" @tap="restoreItems([item.id])">恢复</button>
              <button class="purge" :disabled="saving" @tap="purgeItems([item.id])">永久删除</button>
            </view>
          </view>
        </view>
      </view>

      <view class="recycle-pagination">
        <text>共 {{ formatCount(itemCount) }} 条，每页 {{ pageSize }} 条</text>
        <view>
          <button :disabled="page <= 1 || loading" @tap="changePage(page - 1)">‹</button>
          <strong>{{ page }}</strong>
          <text>/ {{ totalPages }}</text>
          <button :disabled="page >= totalPages || loading" @tap="changePage(page + 1)">›</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  fetchQuestionAdminCommunityTrash,
  purgeQuestionAdminCommunityTrash,
  restoreQuestionAdminCommunityTrash
} from '../api/admin'
import AdminSelect from './AdminSelect.vue'

const props = defineProps({ preview: Boolean })

const DAY_MS = 24 * 60 * 60 * 1000
const pageSize = 20
const typeOptions = [
  { label: '全部帖子', value: 'all' },
  { label: '研友聊', value: 'chat' },
  { label: '经验贴', value: 'experience' }
]
const sortOptions = [
  { label: '最近删除', value: 'deleted_newest' },
  { label: '最早删除', value: 'deleted_oldest' },
  { label: '即将清除', value: 'expiring_soon' }
]
const previewItems = ref([
  {
    id: 'preview-trash-1', author_id: '31B32A6F', author_name: '钟同学', post_type: 'experience',
    category: 'Z001', title: '我的考研经验', content: '整理后的备考安排与复习节奏。',
    admin_deleted_at: new Date(Date.now() - DAY_MS).toISOString(),
    admin_purge_after: new Date(Date.now() + 6 * DAY_MS).toISOString(), admin_deleted_by: 'ADMIN001'
  },
  {
    id: 'preview-trash-2', author_id: '8FC21C09', author_name: 'Z', post_type: 'chat',
    category: '中华文化', title: '复习打卡', content: '今天完成了中华文化与英语运用的复习。',
    admin_deleted_at: new Date(Date.now() - 6.5 * DAY_MS).toISOString(),
    admin_purge_after: new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString(), admin_deleted_by: 'ADMIN001'
  }
])

const filters = reactive({ post_type: 'all', sort_by: 'deleted_newest', search: '' })
const items = ref([])
const itemCount = ref(0)
const retentionDays = ref(7)
const page = ref(1)
const loading = ref(false)
const saving = ref(false)
const loadError = ref(false)
const selectedIds = ref([])
let searchTimer = null

const totalPages = computed(() => Math.max(1, Math.ceil(itemCount.value / pageSize)))
const selectedSet = computed(() => new Set(selectedIds.value))
const allPageSelected = computed(() => items.value.length > 0 && items.value.every((item) => selectedSet.value.has(item.id)))
const typeIndex = computed(() => Math.max(0, typeOptions.findIndex((item) => item.value === filters.post_type)))
const sortIndex = computed(() => Math.max(0, sortOptions.findIndex((item) => item.value === filters.sort_by)))
const hasFilters = computed(() => filters.post_type !== 'all' || filters.sort_by !== 'deleted_newest' || Boolean(filters.search))

onMounted(refresh)

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer)
})

function previewFilteredItems() {
  const term = filters.search.toLowerCase()
  const filtered = previewItems.value.filter((item) => {
    if (filters.post_type !== 'all' && item.post_type !== filters.post_type) return false
    if (!term) return true
    return [item.title, item.content, item.author_name].some((value) => String(value || '').toLowerCase().includes(term))
  })
  return filtered.sort((left, right) => {
    const field = filters.sort_by === 'expiring_soon' ? 'admin_purge_after' : 'admin_deleted_at'
    const direction = filters.sort_by === 'deleted_newest' ? -1 : 1
    return (new Date(left[field]).getTime() - new Date(right[field]).getTime()) * direction
  })
}

async function refresh() {
  if (loading.value) return
  loading.value = true
  loadError.value = false
  try {
    if (props.preview) {
      const filtered = previewFilteredItems()
      itemCount.value = filtered.length
      items.value = filtered.slice((page.value - 1) * pageSize, page.value * pageSize)
    } else {
      const response = await fetchQuestionAdminCommunityTrash({
        post_type: filters.post_type,
        sort_by: filters.sort_by,
        search: filters.search,
        limit: pageSize,
        offset: (page.value - 1) * pageSize
      })
      items.value = Array.isArray(response?.items) ? response.items : []
      itemCount.value = Number(response?.count || 0)
      retentionDays.value = Number(response?.retention_days || 7)
    }
    const lastPage = Math.max(1, Math.ceil(itemCount.value / pageSize))
    if (page.value > lastPage) {
      page.value = lastPage
      loading.value = false
      await refresh()
      return
    }
    selectedIds.value = selectedIds.value.filter((id) => items.value.some((item) => item.id === id))
  } catch (error) {
    items.value = []
    itemCount.value = 0
    selectedIds.value = []
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function scheduleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(applyFilters, 350)
}

async function applyFilters() {
  if (searchTimer) clearTimeout(searchTimer)
  page.value = 1
  selectedIds.value = []
  await refresh()
}

async function clearSearch() {
  filters.search = ''
  await applyFilters()
}

async function clearFilters() {
  filters.post_type = 'all'
  filters.sort_by = 'deleted_newest'
  filters.search = ''
  await applyFilters()
}

async function selectType(event) {
  filters.post_type = typeOptions[Number(event?.detail?.value) || 0]?.value || 'all'
  await applyFilters()
}

async function selectSort(event) {
  filters.sort_by = sortOptions[Number(event?.detail?.value) || 0]?.value || 'deleted_newest'
  await applyFilters()
}

async function changePage(nextPage) {
  const target = Math.min(totalPages.value, Math.max(1, Number(nextPage) || 1))
  if (target === page.value) return
  page.value = target
  selectedIds.value = []
  await refresh()
}

function toggleItem(id) {
  selectedIds.value = selectedSet.value.has(id)
    ? selectedIds.value.filter((item) => item !== id)
    : [...selectedIds.value, id]
}

function toggleSelectPage() {
  const pageIds = new Set(items.value.map((item) => item.id))
  if (allPageSelected.value) {
    selectedIds.value = selectedIds.value.filter((id) => !pageIds.has(id))
    return
  }
  selectedIds.value = Array.from(new Set([...selectedIds.value, ...pageIds]))
}

function confirmAction(title, content, confirmText) {
  return new Promise((resolve) => {
    uni.showModal({ title, content, confirmText, cancelText: '取消', success: (result) => resolve(Boolean(result.confirm)) })
  })
}

async function restoreItems(ids) {
  if (!ids.length || saving.value) return
  const confirmed = await confirmAction(
    `确认恢复 ${ids.length} 条帖子？`,
    '帖子将回到内容管理，并恢复到删除前的公开与精选状态。',
    '恢复'
  )
  if (!confirmed) return
  saving.value = true
  try {
    let affectedCount = 0
    if (props.preview) {
      const targets = new Set(ids)
      const before = previewItems.value.length
      previewItems.value = previewItems.value.filter((item) => !targets.has(item.id))
      affectedCount = before - previewItems.value.length
    } else {
      const response = await restoreQuestionAdminCommunityTrash({ ids })
      affectedCount = Number(response?.affected_count || 0)
    }
    selectedIds.value = selectedIds.value.filter((id) => !ids.includes(id))
    uni.showToast({ title: affectedCount ? `已恢复 ${affectedCount} 条` : '帖子已过期或已处理', icon: affectedCount ? 'success' : 'none' })
    await refresh()
  } catch (error) {
    uni.showToast({ title: '恢复失败，请稍后重试', icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function purgeItems(ids) {
  if (!ids.length || saving.value) return
  const confirmed = await confirmAction(
    `永久删除 ${ids.length} 条帖子？`,
    '帖子、评论、点赞、浏览及相关治理记录将被彻底清除，此操作不可恢复。',
    '永久删除'
  )
  if (!confirmed) return
  saving.value = true
  try {
    let affectedCount = 0
    if (props.preview) {
      const targets = new Set(ids)
      const before = previewItems.value.length
      previewItems.value = previewItems.value.filter((item) => !targets.has(item.id))
      affectedCount = before - previewItems.value.length
    } else {
      const response = await purgeQuestionAdminCommunityTrash({ ids })
      affectedCount = Number(response?.affected_count || 0)
    }
    selectedIds.value = selectedIds.value.filter((id) => !ids.includes(id))
    uni.showToast({ title: affectedCount ? `已永久删除 ${affectedCount} 条` : '帖子已被清理', icon: affectedCount ? 'success' : 'none' })
    await refresh()
  } catch (error) {
    uni.showToast({ title: '永久删除失败，请稍后重试', icon: 'none' })
  } finally {
    saving.value = false
  }
}

function restoreSelected() {
  return restoreItems([...selectedIds.value])
}

function purgeSelected() {
  return purgeItems([...selectedIds.value])
}

function excerpt(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  return text.length > 68 ? `${text.slice(0, 68)}…` : text || '暂无正文'
}

function initial(value) {
  return String(value || '研').trim().slice(0, 1) || '研'
}

function shortId(value) {
  const text = String(value || '').replace(/-/g, '').toUpperCase()
  return text ? text.slice(0, 8) : '—'
}

function postTypeText(value) {
  return value === 'experience' ? '经验贴' : '研友聊'
}

function formatCount(value) {
  return Number(value || 0).toLocaleString('zh-CN')
}

function formatDateTime(value) {
  if (!value) return '—'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return '—'
  return parsed.toLocaleString('zh-CN', { hour12: false, month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function remainingLabel(value) {
  const expiresAt = new Date(value).getTime()
  if (!Number.isFinite(expiresAt)) return '—'
  const remaining = expiresAt - Date.now()
  if (remaining <= 0) return '清理中'
  if (remaining < DAY_MS) return `${Math.max(1, Math.ceil(remaining / (60 * 60 * 1000)))} 小时`
  return `${Math.ceil(remaining / DAY_MS)} 天`
}

function isUrgent(value) {
  const expiresAt = new Date(value).getTime()
  return Number.isFinite(expiresAt) && expiresAt - Date.now() <= 2 * DAY_MS
}

defineExpose({ refresh })
</script>

<style scoped>
.recycle-page{min-height:calc(100vh - 126px);display:flex;flex-direction:column;gap:14px}.recycle-policy-bar{min-height:74px;padding:13px 18px;display:flex;align-items:center;gap:13px;border:1px solid #dce8e7;border-radius:8px;box-sizing:border-box;background:#f6fbfa}.recycle-policy-icon{width:40px;height:40px;display:flex;align-items:center;justify-content:center;flex:0 0 40px;border:1px solid #c9e8e0;border-radius:8px;background:#e7f6f2}.recycle-policy-icon image{width:21px;height:21px;opacity:.76}.recycle-policy-copy{min-width:0;display:flex;flex-direction:column;gap:5px}.recycle-policy-copy strong{color:#2c4352;font-size:14px}.recycle-policy-copy text{color:#7f909d;font-size:10px}.recycle-policy-count{margin-left:auto;min-width:70px;display:flex;flex-direction:column;align-items:flex-end;gap:3px}.recycle-policy-count strong{color:#218370;font-size:20px}.recycle-policy-count text{color:#91a0aa;font-size:9px}.recycle-workspace{min-height:0;display:flex;flex:1;flex-direction:column;border:1px solid #e2e9ec;border-radius:8px;overflow:hidden;background:#fff}.recycle-toolbar{min-height:60px;padding:10px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #e8eef0;box-sizing:border-box;background:#fbfcfd}.recycle-search{width:300px;height:38px;padding:0 10px;display:flex;align-items:center;gap:8px;border:1px solid #dce5e9;border-radius:8px;box-sizing:border-box;background:#fff}.recycle-search image{width:16px;height:16px;opacity:.62}.recycle-search input{min-width:0;height:36px;flex:1;color:#435568;font-size:11px}.recycle-search button{width:24px;height:24px;min-height:24px;margin:0;padding:0;display:flex;align-items:center;justify-content:center;border:0;border-radius:50%;color:#8b98a5;background:#eef2f4;font-size:15px;line-height:1}.recycle-search button::after,.recycle-toolbar button::after,.recycle-check::after,.recycle-row-actions button::after,.recycle-selection-bar button::after,.recycle-pagination button::after,.recycle-state button::after{border:0}.recycle-select{width:126px;--admin-select-height:38px;--admin-select-font-size:10px;--admin-select-menu-min-width:136px}.recycle-select.sort{width:142px;--admin-select-menu-min-width:142px}.recycle-clear,.recycle-refresh{width:66px;height:38px;min-height:38px;margin:0;padding:0;display:inline-flex;align-items:center;justify-content:center;border-radius:8px;box-sizing:border-box;font-size:10px;font-weight:700;line-height:1}.recycle-clear{border:1px solid #dce5e8;color:#7b8996;background:#fff}.recycle-refresh{margin-left:auto;border:1px solid #b9ded5;color:#247a69;background:#eef9f6}.recycle-refresh[disabled]{opacity:.58}.recycle-selection-bar{min-height:48px;padding:7px 16px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #cae9e1;box-sizing:border-box;background:#effaf7}.recycle-selection-bar>text{margin-right:auto;color:#60736f;font-size:10px}.recycle-selection-bar>text strong{color:#16816e}.recycle-selection-bar>view{display:flex;align-items:center;gap:8px}.recycle-selection-bar button,.recycle-row-actions button{height:30px;min-height:30px;margin:0;padding:0 11px;display:inline-flex;align-items:center;justify-content:center;border-radius:7px;box-sizing:border-box;font-size:9px;font-weight:700;line-height:1;white-space:nowrap}.selection-restore,.recycle-row-actions .restore{border:1px solid #bde2d8;color:#247c6b;background:#edf9f6}.selection-purge,.recycle-row-actions .purge{border:1px solid #edc3bf;color:#ad554f;background:#fff2f0}.selection-cancel{border:1px solid #dbe4e7;color:#778694;background:#fff}.recycle-table-wrap{min-height:0;overflow:auto;flex:1}.recycle-table{min-width:1100px}.recycle-grid{width:100%;padding:0 15px;display:grid;grid-template-columns:42px minmax(260px,2.2fr) minmax(130px,1fr) 100px 104px 118px 86px 150px;align-items:center;box-sizing:border-box}.recycle-head{min-height:42px;color:#8795a2;background:#f7f9fa;font-size:10px;font-weight:700}.recycle-row{min-height:80px;border-top:1px solid #edf1f3;color:#596a7b;background:#fff;font-size:10px}.recycle-row:hover{background:#f8fbfa}.recycle-row.selected{background:#f1faf7}.recycle-check-cell{display:flex;align-items:center}.recycle-check{width:20px;height:20px;min-height:20px;margin:0;padding:0;display:flex;align-items:center;justify-content:center;border:1px solid #cedadd;border-radius:5px;color:#fff;background:#fff;font-size:11px;line-height:1}.recycle-check.checked{border-color:#61cdb4;background:#61cdb4}.recycle-post-cell,.recycle-author-cell,.recycle-category-cell,.recycle-expiry-cell{min-width:0}.recycle-post-cell{padding-right:20px}.recycle-post-cell strong,.recycle-post-cell text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.recycle-post-cell strong{color:#2c3e51;font-size:12px}.recycle-post-cell text{margin-top:7px;color:#93a0aa;font-size:9px}.recycle-author-cell{display:flex;align-items:center;gap:8px}.recycle-author-cell>view{width:31px;height:31px;display:flex;align-items:center;justify-content:center;flex:0 0 31px;border:1px solid #d8ebe6;border-radius:7px;color:#397d70;background:#eef8f5;font-size:10px;font-weight:800}.recycle-author-cell>text{min-width:0}.recycle-author-cell strong,.recycle-author-cell small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.recycle-author-cell strong{color:#405466;font-size:10px}.recycle-author-cell small{margin-top:4px;color:#9ba6af;font-size:8px}.recycle-category-cell{display:flex;flex-direction:column;gap:4px}.recycle-category-cell strong{color:#455b6b}.recycle-category-cell text{color:#98a3ad;font-size:9px}.recycle-time-cell,.recycle-admin-cell{color:#788895;font-size:9px}.recycle-expiry-cell{display:flex;flex-direction:column;gap:4px}.recycle-expiry-cell strong{color:#398171;font-size:10px}.recycle-expiry-cell text{color:#9ba7b0;font-size:8px}.recycle-expiry-cell.urgent strong{color:#c46058}.recycle-row-actions{display:flex;align-items:center;gap:7px}.recycle-row-actions button{width:66px;padding:0}.recycle-row-actions .purge{width:70px}.recycle-state{min-height:240px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:9px;color:#8997a2;font-size:11px}.recycle-state strong{color:#536674;font-size:13px}.recycle-state.error{color:#ad625c}.recycle-state button{width:82px;height:32px;min-height:32px;margin:4px 0 0;padding:0;display:flex;align-items:center;justify-content:center;border:1px solid #d9e4e7;border-radius:7px;color:#5d7780;background:#fff;font-size:9px;line-height:1}.recycle-pagination{min-height:52px;padding:8px 16px;display:flex;align-items:center;justify-content:space-between;border-top:1px solid #e8eef0;box-sizing:border-box;color:#8a98a4;font-size:9px;background:#fbfcfd}.recycle-pagination>view{display:flex;align-items:center;gap:8px}.recycle-pagination button{width:30px;height:30px;min-height:30px;margin:0;padding:0;display:flex;align-items:center;justify-content:center;border:1px solid #dbe4e7;border-radius:7px;color:#627583;background:#fff;font-size:15px;line-height:1}.recycle-pagination button[disabled]{opacity:.42}.recycle-pagination strong{min-width:20px;color:#257d6c;font-size:11px;text-align:center}@media(max-width:900px){.recycle-toolbar{flex-wrap:wrap}.recycle-search{width:100%}.recycle-refresh{margin-left:0}.recycle-policy-count{display:none}}
</style>

<style scoped>
.recycle-table {
  min-width: 900px;
}

.recycle-grid {
  grid-template-columns: 36px minmax(190px, 2fr) minmax(105px, 0.9fr) 88px 88px 100px 68px 152px;
}

.recycle-post-cell {
  padding-right: 16px;
}

.recycle-row-actions button,
.recycle-row-actions .purge {
  width: 72px;
}

.recycle-selection-bar button {
  width: 72px;
  padding: 0;
}
</style>
