<template>
  <view class="consultation-management-page">
    <view class="consultation-view-tabs" role="tablist" aria-label="咨询管理">
      <button
        v-for="item in workspaceItems"
        :key="item.key"
        class="consultation-view-tab"
        :class="{ active: activeView === item.key }"
        role="tab"
        :aria-selected="activeView === item.key"
        @tap="selectWorkspace(item.key)"
      >
        <image class="consultation-view-icon" :src="item.icon" mode="aspectFit" />
        <view class="consultation-view-copy">
          <strong>{{ item.label }}</strong>
          <text>{{ item.description }}</text>
        </view>
        <text class="consultation-view-arrow">›</text>
      </button>
    </view>

    <view class="consultation-workspace" :class="`workspace-${activeView}`">
      <view v-if="activeView === 'applications'" class="consultation-workspace-body">
        <AdminMentorManagement
          ref="mentorManagementRef"
          :preview="preview"
          :compact="true"
          mailbox="applications"
          :show-mailbox-switch="false"
        />
      </view>

      <view v-else-if="activeView === 'orders'" class="consultation-workspace-body">
        <AdminMentorOrderManagement ref="mentorOrderManagementRef" :preview="preview" :compact="true" />
      </view>

      <view v-else class="consultation-workspace-body">
        <view class="case-view-tabs" role="tablist" aria-label="咨询争议处理">
          <button
            v-for="item in caseItems"
            :key="item.key"
            class="case-view-tab"
            :class="{ active: activeCaseView === item.key }"
            role="tab"
            :aria-selected="activeCaseView === item.key"
            @tap="selectCaseView(item.key)"
          >
            {{ item.label }}
          </button>
        </view>

        <AdminMentorManagement
          v-if="activeCaseView === 'reports'"
          ref="mentorReportManagementRef"
          :preview="preview"
          :compact="true"
          mailbox="reports"
          :show-mailbox-switch="false"
        />
        <AdminMentorAppealManagement
          v-else
          ref="mentorAppealManagementRef"
          :preview="preview"
          :compact="true"
        />
      </view>
    </view>
  </view>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import AdminMentorAppealManagement from './AdminMentorAppealManagement.vue'
import AdminMentorManagement from './AdminMentorManagement.vue'
import AdminMentorOrderManagement from './AdminMentorOrderManagement.vue'

const props = defineProps({
  preview: Boolean,
  initialView: { type: String, default: 'applications' },
  initialCaseView: { type: String, default: 'reports' }
})

const workspaceItems = [
  { key: 'applications', label: '前辈审核', description: '申请与资质', icon: '/static/ui-icons/tab-profile.svg' },
  { key: 'orders', label: '咨询订单', description: '订单与服务', icon: '/static/ui-icons/mentor-chat-add.svg' },
  { key: 'cases', label: '咨询争议处理', description: '举报与申诉', icon: '/static/ui-icons/report.svg' }
]
const caseItems = [
  { key: 'reports', label: '问题反馈' },
  { key: 'appeals', label: '复核申诉' }
]

const activeView = ref(normalizeWorkspace(props.initialView))
const activeCaseView = ref(normalizeCaseView(props.initialCaseView))
const mentorManagementRef = ref(null)
const mentorOrderManagementRef = ref(null)
const mentorReportManagementRef = ref(null)
const mentorAppealManagementRef = ref(null)

watch(() => props.initialView, (value) => {
  activeView.value = normalizeWorkspace(value)
})

watch(() => props.initialCaseView, (value) => {
  activeCaseView.value = normalizeCaseView(value)
})

async function selectWorkspace(view) {
  const nextView = normalizeWorkspace(view)
  if (activeView.value === nextView) {
    await refresh()
    return
  }
  activeView.value = nextView
  await nextTick()
}

async function selectCaseView(view) {
  const nextView = normalizeCaseView(view)
  if (activeCaseView.value === nextView) {
    await refresh()
    return
  }
  activeCaseView.value = nextView
  await nextTick()
}

async function refresh() {
  await nextTick()
  if (activeView.value === 'applications') {
    await mentorManagementRef.value?.refresh?.()
    return
  }
  if (activeView.value === 'orders') {
    await mentorOrderManagementRef.value?.refresh?.()
    return
  }
  if (activeCaseView.value === 'reports') {
    await mentorReportManagementRef.value?.refresh?.()
    return
  }
  await mentorAppealManagementRef.value?.refresh?.()
}

function normalizeWorkspace(value) {
  return workspaceItems.some((item) => item.key === value) ? value : 'applications'
}

function normalizeCaseView(value) {
  return caseItems.some((item) => item.key === value) ? value : 'reports'
}

defineExpose({ refresh })
</script>

<style scoped>
.consultation-management-page {
  min-height: calc(100vh - 158px);
  color: #31465d;
}

.consultation-view-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.consultation-view-tab {
  min-height: 112px;
  margin: 0;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  border: 1px solid #dfe9eb;
  border-top: 3px solid #9aa9b8;
  border-radius: 8px;
  box-sizing: border-box;
  color: #314a65;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(39, 62, 79, 0.04);
  text-align: left;
}

.consultation-view-tab.active {
  border-color: #94dccc;
  border-top-color: #34b399;
  background: #f2fcf8;
  box-shadow: 0 10px 28px rgba(52, 179, 153, 0.12);
}

.consultation-view-tab::after,
.case-view-tab::after {
  border: 0;
}

.consultation-view-icon {
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
}

.consultation-view-copy {
  min-width: 0;
  flex: 1;
}

.consultation-view-copy strong,
.consultation-view-copy text {
  display: block;
}

.consultation-view-copy strong {
  color: #385069;
  font-size: 15px;
  font-weight: 800;
  line-height: 1.25;
}

.consultation-view-copy text {
  margin-top: 7px;
  color: #8292a1;
  font-size: 11px;
  line-height: 1.25;
}

.consultation-view-arrow {
  color: #90a3ad;
  font-size: 24px;
  line-height: 1;
}

.consultation-view-tab.active .consultation-view-arrow {
  color: #299b84;
}

.consultation-workspace {
  min-height: 0;
  margin-top: 18px;
}

.consultation-workspace-body {
  min-height: 0;
}

.case-view-tabs {
  min-height: 48px;
  padding: 7px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid #dfe9eb;
  border-radius: 8px;
  box-sizing: border-box;
  background: #f7fafb;
}

.case-view-tab {
  min-width: 96px;
  height: 32px;
  margin: 0;
  padding: 0 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 6px;
  box-sizing: border-box;
  color: #718397;
  background: transparent;
  font-size: 11px;
  font-weight: 750;
  line-height: 1;
}

.case-view-tab.active {
  color: #247d6d;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(42, 82, 75, 0.1);
}

.case-view-tabs + .mentor-application-page,
.case-view-tabs + .mentor-appeal-admin-page {
  margin-top: 12px;
}

@media (max-width: 1040px) {
  .consultation-view-tabs {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .consultation-management-page {
    min-height: auto;
  }

  .consultation-view-tab {
    min-height: 90px;
  }
}
</style>
