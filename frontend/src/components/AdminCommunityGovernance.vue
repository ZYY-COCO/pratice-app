<template>
  <view class="community-governance-page">
    <view class="community-governance-tabs" role="tablist" aria-label="内容治理分类">
      <button
        v-for="item in tabs"
        :key="item.key"
        class="community-governance-tab"
        :class="{ active: activeTab === item.key }"
        :aria-selected="activeTab === item.key"
        @tap="selectTab(item.key)"
      >
        <image :src="item.icon" mode="aspectFit" />
        <view><strong>{{ item.label }}</strong><text>{{ item.description }}</text></view>
      </button>
    </view>

    <view v-if="mountedTabs.reports" v-show="activeTab === 'reports'" class="community-governance-view">
      <AdminCommunityModeration ref="reportsRef" :preview="preview" />
    </view>
    <view v-if="mountedTabs.appeals" v-show="activeTab === 'appeals'" class="community-governance-view">
      <AdminCommunityAppeals ref="appealsRef" :preview="preview" />
    </view>
  </view>
</template>

<script setup>
import { nextTick, reactive, ref, watch } from 'vue'
import AdminCommunityAppeals from './AdminCommunityAppeals.vue'
import AdminCommunityModeration from './AdminCommunityModeration.vue'

const props = defineProps({
  preview: Boolean,
  initialTab: { type: String, default: 'reports' }
})

const tabs = [
  { key: 'reports', label: '举报处理', description: '核查用户举报并处置内容', icon: '/static/ui-icons/report.svg' },
  { key: 'appeals', label: '申诉复核', description: '复核内容处置申诉', icon: '/static/ui-icons/community-comment-heart.svg' }
]
const activeTab = ref('reports')
const mountedTabs = reactive({ reports: true, appeals: false })
const reportsRef = ref(null)
const appealsRef = ref(null)

watch(
  () => props.initialTab,
  (value) => {
    if (!tabs.some((item) => item.key === value)) return
    activeTab.value = value
    mountedTabs[value] = true
  },
  { immediate: true }
)

function selectTab(tab) {
  if (!tabs.some((item) => item.key === tab)) return
  mountedTabs[tab] = true
  activeTab.value = tab
}

async function refresh() {
  await nextTick()
  if (activeTab.value === 'appeals') {
    await appealsRef.value?.refresh?.()
    return
  }
  await reportsRef.value?.refresh?.()
}

defineExpose({ refresh, selectTab })
</script>

<style scoped>
.community-governance-page{min-height:calc(100vh - 158px);display:flex;flex-direction:column}.community-governance-tabs{width:fit-content;margin:0 0 14px;padding:4px;display:grid;grid-template-columns:repeat(2,minmax(190px,1fr));gap:4px;border:1px solid #dfe8eb;border-radius:8px;background:#f3f6f7}.community-governance-tab{min-width:0;min-height:58px;margin:0;padding:9px 14px;border:0;border-radius:6px;background:transparent;color:#6d7e8f;display:flex;align-items:center;gap:10px;text-align:left}.community-governance-tab::after{border:0}.community-governance-tab.active{background:#fff;color:#2b8d79;box-shadow:0 4px 14px rgba(35,64,77,.08)}.community-governance-tab image{width:24px;height:24px;flex:0 0 24px}.community-governance-tab view{min-width:0}.community-governance-tab strong,.community-governance-tab text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.community-governance-tab strong{font-size:12px;line-height:1.25}.community-governance-tab text{margin-top:4px;color:#91a0ae;font-size:9px;line-height:1.25}.community-governance-view{min-height:0;flex:1}@media(max-width:820px){.community-governance-page{min-height:auto}.community-governance-tabs{width:100%;grid-template-columns:repeat(2,minmax(0,1fr))}.community-governance-tab{min-width:0}.community-governance-tab text{display:none}}
</style>
