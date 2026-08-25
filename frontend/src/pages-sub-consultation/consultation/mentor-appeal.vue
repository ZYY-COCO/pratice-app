<template>
  <view class="mentor-appeal-page" :style="themeInlineStyle">
    <MentorPageHeader title="申请复核" @back="goBack" />

    <scroll-view scroll-y class="mentor-appeal-scroll">
      <view class="mentor-appeal-content">
        <view v-if="loading" class="mentor-appeal-state">正在读取处理记录…</view>
        <view v-else-if="loadError" class="mentor-appeal-state error">
          <text>{{ loadError }}</text>
          <button @tap="loadReport">重新加载</button>
        </view>
        <view v-else-if="!report" class="mentor-appeal-state">
          <strong>未找到这条处理记录</strong>
          <text>请返回“平台处理进度”后重新进入。</text>
        </view>

        <template v-else-if="submitted">
          <view class="mentor-appeal-success">
            <view class="mentor-appeal-success-icon">✓</view>
            <strong>{{ successTitle }}</strong>
            <text>平台会重新核对双方说明、凭证、订单和聊天记录；处理进度会同步在本页对应的记录中。</text>
            <button @tap="openSupport">返回处理进度</button>
          </view>
        </template>

        <template v-else>
          <view class="mentor-appeal-card mentor-appeal-case">
            <view class="mentor-appeal-card-title">原问题反馈</view>
            <view class="mentor-appeal-meta"><text>{{ reporterLabel }}</text><strong>{{ report.issue_type || '咨询问题反馈' }}</strong></view>
            <view class="mentor-appeal-copy">{{ report.content || '未填写具体说明。' }}</view>
            <view v-if="report.admin_note" class="mentor-appeal-result"><text>原处理说明</text><strong>{{ report.admin_note }}</strong></view>
          </view>

          <template v-if="appeal">
            <view class="mentor-appeal-card">
              <view class="mentor-appeal-label"><text>我的复核申请</text><strong>{{ appealStatusText(appeal.status, appeal.decision) }}</strong></view>
              <view class="mentor-appeal-copy">{{ appeal.content }}</view>
              <view v-if="appeal.admin_note" class="mentor-appeal-result"><text>平台复核说明</text><strong>{{ appeal.admin_note }}</strong></view>
            </view>

            <view v-if="canUploadEvidence" class="mentor-appeal-card">
              <view class="mentor-appeal-label"><text>补充复核凭证</text><strong>最多 3 张</strong></view>
              <view class="mentor-appeal-proof-copy">你已提交 {{ appealEvidenceCount }} 张；可继续补充与本次复核直接相关的材料。</view>
              <view class="mentor-appeal-images">
                <view v-for="(image, index) in proofImages" :key="image.id" class="mentor-appeal-image"><image :src="image.path" mode="aspectFill" /><button aria-label="删除图片" :disabled="submitting" @tap="removeImage(index)"><CloseIcon /></button></view>
                <button v-if="remainingProofCount > 0" class="mentor-appeal-image-add" :disabled="submitting" @tap="chooseProofImages"><text>＋</text><view>添加凭证</view></button>
              </view>
            </view>
            <view v-else-if="appeal.status === 'pending' || appeal.status === 'reviewing'" class="mentor-appeal-card mentor-appeal-closed">
              <strong>复核材料已齐全</strong>
              <text>你已上传 3 张凭证，平台正在处理这次复核申请。</text>
            </view>
          </template>

          <template v-else-if="!report.can_appeal">
            <view class="mentor-appeal-card mentor-appeal-closed">
              <strong>当前暂不支持申请复核</strong>
              <text>仅在平台完成原问题反馈处理后开放一次复核申请；请先在处理进度查看当前状态。</text>
            </view>
          </template>

          <template v-else>
            <view class="mentor-appeal-card mentor-appeal-description-card">
              <view class="mentor-appeal-label"><text>复核说明</text><strong>20—500 字</strong></view>
              <textarea v-model="appealContent" maxlength="500" placeholder="请说明希望平台重新核实的具体事实、时间或原处理结果中的疑问。" placeholder-class="mentor-appeal-placeholder" />
              <view class="mentor-appeal-count" :class="{ invalid: appealContent.trim().length > 0 && appealContent.trim().length < 20 }">{{ appealContent.trim().length }} / 500</view>
            </view>

            <view class="mentor-appeal-card">
              <view class="mentor-appeal-label"><text>补充凭证</text><strong>选填，最多 3 张</strong></view>
              <view class="mentor-appeal-proof-copy">可补充与本次复核直接相关的聊天截图或材料；提交后平台会和原始证据一并核实。</view>
              <view class="mentor-appeal-images">
                <view v-for="(image, index) in proofImages" :key="image.id" class="mentor-appeal-image"><image :src="image.path" mode="aspectFill" /><button aria-label="删除图片" :disabled="submitting" @tap="removeImage(index)"><CloseIcon /></button></view>
                <button v-if="remainingProofCount > 0" class="mentor-appeal-image-add" :disabled="submitting" @tap="chooseProofImages"><text>＋</text><view>添加凭证</view></button>
              </view>
            </view>
          </template>
          <view v-if="showSubmitFooter" class="mentor-appeal-notice"><view>i</view><text>每位参与方对同一问题反馈可申请一次复核。请只提交与咨询有关的真实材料，平台会保留完整处理记录。</text></view>
        </template>
      </view>
    </scroll-view>

    <view v-if="showSubmitFooter" class="mentor-appeal-footer">
      <button :loading="submitting" :disabled="!canSubmit" @tap="submitAppeal">{{ submitting ? '正在提交' : submitButtonText }}</button>
    </view>
  </view>
</template>

<script setup>
import CloseIcon from '../../components/CloseIcon.vue'
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  createMentorConsultationReportAppeal,
  fetchMyMentorConsultationReports,
  uploadMentorConsultationReportAppealEvidence
} from '../../api/mentorConsultation'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const maxProofCount = 3
const reportId = ref('')
const report = ref(null)
const appeal = ref(null)
const appealContent = ref('')
const proofImages = ref([])
const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const submitted = ref(false)
const resultMode = ref('appeal')
const themeKey = ref(getStoredThemeKey())
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))

const reporterLabel = computed(() => report.value?.reporter_role === 'mentor' ? '认证前辈提交的反馈' : '咨询用户提交的反馈')
const appealEvidenceCount = computed(() => Math.max(0, Number(appeal.value?.evidence_count || 0)))
const appealIsOpen = computed(() => ['pending', 'reviewing'].includes(String(appeal.value?.status || '')))
const remainingProofCount = computed(() => Math.max(0, maxProofCount - appealEvidenceCount.value - proofImages.value.length))
const canUploadEvidence = computed(() => Boolean(appeal.value && appealIsOpen.value && remainingProofCount.value > 0))
const canCreateAppeal = computed(() => Boolean(report.value?.can_appeal && !appeal.value))
const canSubmit = computed(() => Boolean(
  !submitting.value && (appeal.value
    ? canUploadEvidence.value && proofImages.value.length > 0
    : canCreateAppeal.value && appealContent.value.trim().length >= 20 && appealContent.value.trim().length <= 500)
))
const showSubmitFooter = computed(() => Boolean(!submitted.value && (appeal.value ? canUploadEvidence.value : canCreateAppeal.value)))
const submitButtonText = computed(() => appeal.value ? '提交补充凭证' : '提交复核申请')
const successTitle = computed(() => resultMode.value === 'evidence' ? '复核凭证已提交' : '复核申请已提交')

onLoad((options) => {
  reportId.value = String(options?.reportId || '')
  if (!reportId.value) {
    loadError.value = '未找到处理记录，请返回平台处理进度后重新进入。'
    return
  }
  if (!isLoggedIn()) {
    goLogin()
    return
  }
  void loadReport()
})

onShow(() => { themeKey.value = getStoredThemeKey() })

async function loadReport() {
  if (!reportId.value || loading.value) return
  loading.value = true
  loadError.value = ''
  try {
    const response = await fetchMyMentorConsultationReports({ limit: 200 })
    const current = (Array.isArray(response?.items) ? response.items : []).find((item) => String(item?.id || '') === reportId.value)
    if (!current) {
      loadError.value = '未找到该处理记录，可能已无查看权限。'
      return
    }
    report.value = current
    appeal.value = current.appeal_id
      ? {
          id: current.appeal_id,
          content: current.appeal_content || '',
          status: current.appeal_status || 'pending',
          decision: current.appeal_decision || 'none',
          admin_note: current.appeal_admin_note || null,
          evidence_count: Number(current.appeal_evidence_count || 0)
        }
      : null
  } catch (error) {
    loadError.value = error?.detail || '处理记录读取失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function chooseProofImages() {
  const count = remainingProofCount.value
  if (count <= 0 || submitting.value) return
  uni.chooseImage({
    count,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success(result) {
      const tempFiles = Array.isArray(result.tempFiles) ? result.tempFiles : []
      const tempFilePaths = Array.isArray(result.tempFilePaths) ? result.tempFilePaths : []
      const images = tempFilePaths.map((path, index) => {
        const tempFile = tempFiles[index]
        const fileCandidate = tempFile?.file || tempFile?.fileObject || tempFile
        const file = typeof Blob !== 'undefined' && fileCandidate instanceof Blob ? fileCandidate : null
        return {
          id: `appeal-proof-${Date.now()}-${index}-${Math.random().toString(36).slice(2, 8)}`,
          path: path || tempFile?.path || tempFile?.tempFilePath || '',
          file,
          fileName: tempFile?.name || file?.name || `appeal-evidence-${index + 1}`
        }
      }).filter((image) => image.path)
      proofImages.value = [...proofImages.value, ...images].slice(0, Math.max(0, maxProofCount - appealEvidenceCount.value))
    },
    fail(error) {
      if (!String(error?.errMsg || '').includes('cancel')) uni.showToast({ title: '图片选择失败，请重试', icon: 'none' })
    }
  })
}

function removeImage(index) {
  if (!submitting.value) proofImages.value.splice(index, 1)
}

async function submitAppeal() {
  if (!canSubmit.value || !report.value?.id) return
  submitting.value = true
  try {
    let createdThisTime = false
    if (!appeal.value) {
      appeal.value = await createMentorConsultationReportAppeal(report.value.id, { content: appealContent.value.trim() })
      report.value = {
        ...report.value,
        can_appeal: false,
        appeal_id: appeal.value.id,
        appeal_status: appeal.value.status,
        appeal_content: appeal.value.content,
        appeal_admin_note: appeal.value.admin_note || null,
        appeal_evidence_count: 0
      }
      createdThisTime = true
    }
    const evidenceBeforeUpload = appealEvidenceCount.value
    const failures = []
    let uploadedCount = 0
    for (const image of proofImages.value) {
      try {
        await uploadMentorConsultationReportAppealEvidence(appeal.value.id, { filePath: image.path, file: image.file, fileName: image.fileName })
        uploadedCount += 1
      } catch (error) {
        failures.push(image)
      }
    }
    appeal.value = { ...appeal.value, evidence_count: evidenceBeforeUpload + uploadedCount }
    report.value = { ...report.value, appeal_evidence_count: evidenceBeforeUpload + uploadedCount }
    proofImages.value = failures
    if (failures.length) {
      uni.showToast({ title: uploadedCount > 0 ? '部分凭证上传失败，请重试' : '凭证上传失败，请重试', icon: 'none' })
      return
    }
    resultMode.value = createdThisTime ? 'appeal' : 'evidence'
    submitted.value = true
  } catch (error) {
    uni.showToast({ title: error?.detail || '复核申请提交失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function appealStatusText(status, decision) {
  if (status === 'resolved' && decision === 'reopen') return '已受理，原案复核中'
  return { pending: '待受理', reviewing: '复核中', resolved: '复核已完成', dismissed: '维持原结论' }[status] || '待受理'
}

function goLogin() {
  const target = `/pages-sub-consultation/consultation/mentor-appeal?reportId=${encodeURIComponent(reportId.value)}`
  uni.reLaunch({ url: `/pages/login/index?redirect=${encodeURIComponent(target)}` })
}

function goBack() {
  uni.navigateBack({ fail() { uni.reLaunch({ url: '/pages-sub-consultation/consultation/mentor-support' }) } })
}

function openSupport() {
  uni.redirectTo({ url: '/pages-sub-consultation/consultation/mentor-support' })
}
</script>

<style scoped>
.mentor-appeal-page{height:100vh;height:100dvh;overflow:hidden;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f4f8ff);color:#2d405d}.mentor-appeal-scroll{min-height:0;flex:1}.mentor-appeal-content{padding:24rpx 24rpx calc(150rpx + env(safe-area-inset-bottom))}.mentor-appeal-card,.mentor-appeal-state,.mentor-appeal-success{padding:28rpx;border:2rpx solid var(--gyt-primary-border,#d9e7fc);border-radius:28rpx;background:var(--gyt-panel-bg,#fff);box-shadow:0 14rpx 34rpx var(--gyt-primary-shadow,rgba(52,120,246,.06))}.mentor-appeal-card+.mentor-appeal-card{margin-top:18rpx}.mentor-appeal-state{margin-top:18rpx;color:#8292a8;text-align:center;font-size:22rpx;line-height:1.6}.mentor-appeal-state strong,.mentor-appeal-state text{display:block}.mentor-appeal-state.error{color:#bd655c}.mentor-appeal-state button{margin-top:14rpx;border:0;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-size:20rpx}.mentor-appeal-state button::after{border:0}.mentor-appeal-card-title{color:#2d405d;font-size:27rpx;font-weight:900}.mentor-appeal-meta{display:flex;align-items:center;justify-content:space-between;gap:16rpx;margin-top:18rpx}.mentor-appeal-meta text{color:var(--gyt-primary,#3478f6);font-size:19rpx;font-weight:800}.mentor-appeal-meta strong{max-width:54%;overflow:hidden;color:#52667f;font-size:20rpx;text-align:right;text-overflow:ellipsis;white-space:nowrap}.mentor-appeal-copy{margin-top:15rpx;color:#63758d;font-size:22rpx;line-height:1.65;font-weight:650;white-space:pre-wrap}.mentor-appeal-result{margin-top:16rpx;padding:16rpx;border-radius:17rpx;background:var(--gyt-primary-tint,#f7faff)}.mentor-appeal-result text,.mentor-appeal-result strong{display:block}.mentor-appeal-result text{color:#8a9aaf;font-size:18rpx}.mentor-appeal-result strong{margin-top:7rpx;color:#5d7088;font-size:20rpx;line-height:1.55;font-weight:650;white-space:pre-wrap}.mentor-appeal-label{display:flex;align-items:center;justify-content:space-between;gap:14rpx;color:#40546e;font-size:23rpx;font-weight:850}.mentor-appeal-label strong{color:#9aabc1;font-size:18rpx;font-weight:700}.mentor-appeal-description-card textarea{box-sizing:border-box;width:100%;min-height:230rpx;margin-top:16rpx;padding:18rpx;border:2rpx solid var(--gyt-primary-border,#e0eafa);border-radius:18rpx;background:var(--gyt-primary-tint,#fbfdff);color:#2d405d;font-size:22rpx;line-height:1.55;font-weight:600}.mentor-appeal-placeholder{color:#a7b3c4;font-weight:500}.mentor-appeal-count{margin-top:10rpx;color:#9aa9bb;text-align:right;font-size:19rpx;font-weight:650}.mentor-appeal-count.invalid{color:#e58a51}.mentor-appeal-proof-copy{margin-top:14rpx;color:#8796aa;font-size:20rpx;line-height:1.5;font-weight:650}.mentor-appeal-images{display:flex;flex-wrap:wrap;gap:14rpx;margin-top:18rpx}.mentor-appeal-image,.mentor-appeal-image-add{width:144rpx;height:144rpx;border-radius:18rpx;overflow:hidden;position:relative}.mentor-appeal-image{border:2rpx solid var(--gyt-primary-border,#d8e6fa);background:var(--gyt-primary-tint,#f3f7fd)}.mentor-appeal-image image{width:100%;height:100%}.mentor-appeal-image button{position:absolute;top:6rpx;right:6rpx;width:36rpx;height:36rpx;min-height:36rpx;margin:0;padding:0;border:0;border-radius:50%;background:rgba(28,43,66,.65);color:#fff;font-size:27rpx;line-height:1}.mentor-appeal-image-add{margin:0;border:2rpx dashed var(--gyt-primary-border,#bed4f7);background:var(--gyt-primary-tint,#f7faff);color:var(--gyt-primary,#6180b4);display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:18rpx;font-weight:750}.mentor-appeal-image-add>text{font-size:42rpx;line-height:1}.mentor-appeal-image-add view{margin-top:7rpx}.mentor-appeal-closed strong,.mentor-appeal-closed text{display:block}.mentor-appeal-closed>strong{color:#53677e;font-size:24rpx}.mentor-appeal-closed>text{margin-top:10rpx;color:#8393a8;font-size:20rpx;line-height:1.55;font-weight:650}.mentor-appeal-notice{display:flex;align-items:flex-start;gap:12rpx;margin:20rpx 4rpx 0;color:#8292a8;font-size:19rpx;line-height:1.55;font-weight:650}.mentor-appeal-notice>view{width:28rpx;height:28rpx;margin-top:1rpx;border-radius:50%;background:var(--gyt-primary-soft,#dbe9fc);color:var(--gyt-primary,#5d82bd);display:flex;align-items:center;justify-content:center;font-size:18rpx;font-weight:900;flex-shrink:0}.mentor-appeal-footer{padding:16rpx 24rpx calc(20rpx + env(safe-area-inset-bottom));border-top:2rpx solid var(--gyt-primary-border,#dbe7f8);background:var(--gyt-panel-bg,#fff)}.mentor-appeal-footer button,.mentor-appeal-success button{width:100%;min-height:76rpx;margin:0;padding:0 16rpx;border:0;border-radius:20rpx;background:var(--gyt-primary-gradient,#3478f6);color:#fff;display:flex;align-items:center;justify-content:center;font-size:24rpx;line-height:1;font-weight:900;box-shadow:0 10rpx 22rpx var(--gyt-primary-shadow,rgba(52,120,246,.2))}.mentor-appeal-footer button[disabled]{background:#bfcce0;box-shadow:none}.mentor-appeal-footer button::after,.mentor-appeal-success button::after,.mentor-appeal-image button::after,.mentor-appeal-image-add::after{border:0}.mentor-appeal-success{margin-top:100rpx;text-align:center}.mentor-appeal-success-icon{width:112rpx;height:112rpx;margin:0 auto;border-radius:50%;background:#e5f5ee;color:#24a575;display:flex;align-items:center;justify-content:center;font-size:62rpx;font-weight:900}.mentor-appeal-success strong,.mentor-appeal-success text{display:block}.mentor-appeal-success strong{margin-top:26rpx;color:#273953;font-size:31rpx;font-weight:900}.mentor-appeal-success text{margin-top:12rpx;color:#7c8da4;font-size:21rpx;line-height:1.65;font-weight:650}.mentor-appeal-success button{margin-top:32rpx}
</style>
