<template>
  <view class="mentor-response-page" :style="themeInlineStyle">
    <MentorPageHeader :title="pageTitle" @back="goBack" />

    <scroll-view scroll-y class="mentor-response-scroll">
      <view class="mentor-response-content">
        <AppPageLoadingState v-if="loading" message="正在整理处理记录..." />
        <view v-else-if="loadError" class="mentor-response-state error">
          <text>{{ loadError }}</text>
          <button @tap="loadReport">重新加载</button>
        </view>
        <view v-else-if="!report" class="mentor-response-state">
          <strong>未找到这条处理记录</strong>
          <text>请返回“平台处理进度”后重新进入。</text>
        </view>

        <template v-else-if="submitted">
          <view class="mentor-response-success">
            <view class="mentor-response-success-icon">✓</view>
            <strong>{{ successTitle }}</strong>
            <text>{{ successCopy }}</text>
            <button @tap="openSupport">返回处理进度</button>
          </view>
        </template>

        <template v-else>
          <view class="mentor-response-card mentor-response-case">
            <view class="mentor-response-card-title">{{ evidenceOnly ? '本次问题反馈' : '对方反馈' }}</view>
            <view class="mentor-response-meta">
              <text>{{ reporterLabel }}</text>
              <strong>{{ report.issue_type || '咨询问题反馈' }}</strong>
            </view>
            <view class="mentor-response-content-copy">{{ report.content || '对方未填写具体说明。' }}</view>
            <view class="mentor-response-evidence-copy">{{ caseEvidenceCopy }}</view>
          </view>

          <template v-if="evidenceOnly">
            <view v-if="!canUploadEvidence" class="mentor-response-card mentor-response-closed">
              <strong>当前不能继续补充凭证</strong>
              <text>{{ evidenceBlockedCopy }}</text>
            </view>
            <template v-else>
              <view class="mentor-response-card">
                <view class="mentor-response-label"><text>补充凭证</text><strong>最多 3 张</strong></view>
                <view class="mentor-response-proof-copy">你已提交 {{ ownEvidenceCount }} 张；可继续补充与本次反馈直接相关的材料。</view>
                <view class="mentor-response-images">
                  <view v-for="(image, index) in proofImages" :key="image.id" class="mentor-response-image"><image :src="image.path" mode="aspectFill" /><button aria-label="删除图片" :disabled="submitting" @tap="removeImage(index)"><CloseIcon /></button></view>
                  <button v-if="remainingProofCount > 0" class="mentor-response-image-add" :disabled="submitting" @tap="chooseProofImages"><text>＋</text><view>添加凭证</view></button>
                </view>
              </view>
              <view class="mentor-response-notice"><view class="mentor-response-notice-icon">i</view><view>请仅提交与该咨询订单有关的内容，不要上传他人隐私或无关材料。平台会将材料纳入本次处理记录。</view></view>
            </template>
          </template>

          <template v-else-if="!report.can_respond">
            <view class="mentor-response-card mentor-response-closed">
              <strong>{{ responseBlockedTitle }}</strong>
              <text>{{ responseBlockedCopy }}</text>
              <view v-if="report.respondent_content" class="mentor-response-existing"><text>你已提交的说明</text><strong>{{ report.respondent_content }}</strong></view>
            </view>
          </template>

          <template v-else>
            <view class="mentor-response-card mentor-response-description-card">
              <view class="mentor-response-label"><text>我的说明</text><strong>20—500 字</strong></view>
              <textarea
                v-model="responseContent"
                maxlength="500"
                placeholder="请客观说明本次咨询经过、时间和相关情况，平台会结合双方材料和聊天记录核实。"
                placeholder-class="mentor-response-placeholder"
              />
              <view class="mentor-response-count" :class="{ invalid: responseContent.trim().length > 0 && responseContent.trim().length < 20 }">
                {{ responseContent.trim().length }} / 500
              </view>
            </view>

            <view class="mentor-response-card">
              <view class="mentor-response-label"><text>补充凭证</text><strong>选填，最多 3 张</strong></view>
              <view class="mentor-response-proof-copy">你已提交 {{ respondentEvidenceCount }} 张；可补充聊天截图或与本次咨询直接相关的材料。</view>
              <view class="mentor-response-images">
                <view v-for="(image, index) in proofImages" :key="image.id" class="mentor-response-image">
                  <image :src="image.path" mode="aspectFill" />
                  <button aria-label="删除图片" :disabled="submitting" @tap="removeImage(index)"><CloseIcon /></button>
                </view>
                <button v-if="remainingProofCount > 0" class="mentor-response-image-add" :disabled="submitting" @tap="chooseProofImages">
                  <text>＋</text><view>添加凭证</view>
                </button>
              </view>
            </view>

            <view class="mentor-response-notice">
              <view class="mentor-response-notice-icon">i</view>
              <view>请仅提交与该咨询订单有关的内容，不要上传他人隐私或无关材料。平台处理结果会同步给双方。</view>
            </view>
          </template>
        </template>
      </view>
    </scroll-view>

    <view v-if="showSubmitFooter" class="mentor-response-footer">
      <button :loading="submitting" :disabled="!canSubmit" @tap="submitResponse">{{ submitting ? '正在提交' : submitButtonText }}</button>
    </view>
  </view>
</template>

<script setup>
import CloseIcon from '../../components/CloseIcon.vue'
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import {
  fetchMyMentorConsultationReports,
  respondToMentorConsultationReport,
  uploadMentorConsultationReportEvidence
} from '../../api/mentorConsultation'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const maxProofCount = 3
const reportId = ref('')
const report = ref(null)
const evidenceOnly = ref(false)
const responseContent = ref('')
const proofImages = ref([])
const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const submitted = ref(false)
const failedEvidenceCount = ref(0)
const themeKey = ref(getStoredThemeKey())
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))

const reporterLabel = computed(() => report.value?.reporter_role === 'mentor' ? '认证前辈提交的反馈' : '咨询用户提交的反馈')
const reporterEvidenceCount = computed(() => Math.max(0, Number(report.value?.reporter_evidence_count || 0)))
const respondentEvidenceCount = computed(() => Math.max(0, Number(report.value?.respondent_evidence_count || 0)))
const ownEvidenceCount = computed(() => report.value?.participation_role === 'respondent' ? respondentEvidenceCount.value : reporterEvidenceCount.value)
const caseEvidenceCopy = computed(() => evidenceOnly.value
  ? `你已提交 ${ownEvidenceCount.value} 张相关凭证`
  : `对方已提交 ${reporterEvidenceCount.value} 张相关凭证`)
const reportIsOpen = computed(() => ['pending', 'reviewing'].includes(String(report.value?.status || '')))
const remainingProofCount = computed(() => Math.max(0, maxProofCount - ownEvidenceCount.value - proofImages.value.length))
const canUploadEvidence = computed(() => Boolean(report.value && reportIsOpen.value && remainingProofCount.value > 0))
const canSubmit = computed(() => Boolean(
  !submitting.value
  && (evidenceOnly.value
    ? canUploadEvidence.value && proofImages.value.length > 0
    : report.value?.can_respond
      && responseContent.value.trim().length >= 20
      && responseContent.value.trim().length <= 500)
))
const showSubmitFooter = computed(() => Boolean(
  report.value
  && !submitted.value
  && (evidenceOnly.value ? canUploadEvidence.value : report.value?.can_respond)
))
const pageTitle = computed(() => evidenceOnly.value ? '补充处理凭证' : '提交处理说明')
const responseButtonText = computed(() => report.value?.respondent_content ? '更新说明并提交凭证' : '提交说明并补充凭证')
const submitButtonText = computed(() => evidenceOnly.value ? '提交补充凭证' : responseButtonText.value)
const successTitle = computed(() => evidenceOnly.value ? '补充凭证已提交' : '说明已提交')
const successCopy = computed(() => failedEvidenceCount.value > 0
  ? `${evidenceOnly.value ? '补充凭证已保存' : '说明已保存'}，但有 ${failedEvidenceCount.value} 张凭证未上传成功。你可以返回处理进度后再次补充。`
  : evidenceOnly.value
    ? '平台已收到补充凭证，会将其纳入订单、聊天和双方材料的核实记录。'
    : '平台会结合双方说明、凭证、订单和聊天记录继续核实，处理结果会同步给双方。')
const responseBlockedTitle = computed(() => report.value?.respondent_content ? '该记录已结束处理' : '当前不能继续补充说明')
const responseBlockedCopy = computed(() => report.value?.status === 'resolved' || report.value?.status === 'dismissed'
  ? '平台已完成本次处理；你可在平台处理进度查看结论和退款结果。'
  : '请稍后刷新处理进度，或等待平台将状态更新为可补充。')
const evidenceBlockedCopy = computed(() => report.value?.status === 'resolved' || report.value?.status === 'dismissed'
  ? '平台已完成本次处理，不能再补充凭证。'
  : ownEvidenceCount.value >= maxProofCount
    ? '你已上传 3 张凭证。如需补充其他情况，请在平台处理说明中说明。'
    : '当前处理记录暂不支持继续补充凭证，请稍后刷新。')

onLoad((options) => {
  reportId.value = String(options?.reportId || '')
  evidenceOnly.value = options?.mode === 'evidence'
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

onShow(() => {
  themeKey.value = getStoredThemeKey()
})

async function loadReport() {
  if (!reportId.value || loading.value) return
  loading.value = true
  loadError.value = ''
  try {
    const response = await fetchMyMentorConsultationReports({ limit: 200 })
    const items = Array.isArray(response?.items) ? response.items : []
    const current = items.find((item) => String(item?.id || '') === reportId.value)
    if (!current) {
      loadError.value = '未找到该处理记录，可能已无查看权限。'
      return
    }
    report.value = current
    if (!evidenceOnly.value) responseContent.value = current.respondent_content || ''
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
          id: `response-proof-${Date.now()}-${index}-${Math.random().toString(36).slice(2, 8)}`,
          path: path || tempFile?.path || tempFile?.tempFilePath || '',
          file,
          fileName: tempFile?.name || file?.name || `response-evidence-${index + 1}`
        }
      }).filter((image) => image.path)
      proofImages.value = [...proofImages.value, ...images].slice(0, Math.max(0, maxProofCount - ownEvidenceCount.value))
    },
    fail(error) {
      if (!String(error?.errMsg || '').includes('cancel')) {
        uni.showToast({ title: '图片选择失败，请重试', icon: 'none' })
      }
    }
  })
}

function removeImage(index) {
  if (!submitting.value) proofImages.value.splice(index, 1)
}

async function submitResponse() {
  if (!canSubmit.value || !report.value?.id) return
  submitting.value = true
  try {
    const evidenceCountBeforeUpload = ownEvidenceCount.value
    let updated = report.value
    if (!evidenceOnly.value) {
      const content = responseContent.value.trim()
      if (content !== String(report.value.respondent_content || '').trim()) {
        updated = await respondToMentorConsultationReport(report.value.id, { content })
      }
    }

    const failures = []
    let uploadedCount = 0
    for (const image of proofImages.value) {
      try {
        await uploadMentorConsultationReportEvidence(report.value.id, {
          filePath: image.path,
          file: image.file,
          fileName: image.fileName
        })
        uploadedCount += 1
      } catch (error) {
        failures.push(image)
      }
    }
    const evidenceCountField = report.value.participation_role === 'respondent'
      ? 'respondent_evidence_count'
      : 'reporter_evidence_count'
    report.value = {
      ...report.value,
      ...updated,
      [evidenceCountField]: evidenceCountBeforeUpload + uploadedCount
    }
    failedEvidenceCount.value = failures.length
    proofImages.value = failures
    if (failures.length) {
      uni.showToast({
        title: uploadedCount > 0 ? '部分凭证上传失败，请重试' : '凭证上传失败，请重试',
        icon: 'none'
      })
      return
    }
    submitted.value = true
  } catch (error) {
    uni.showToast({
      title: error?.detail || (evidenceOnly.value ? '凭证上传失败，请稍后重试' : '说明提交失败，请稍后重试'),
      icon: 'none'
    })
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  const target = `/pages-sub-consultation/consultation/mentor-response?reportId=${encodeURIComponent(reportId.value)}${evidenceOnly.value ? '&mode=evidence' : ''}`
  uni.reLaunch({ url: `/pages/login/index?redirect=${encodeURIComponent(target)}` })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages-sub-consultation/consultation/mentor-support' })
    }
  })
}

function openSupport() {
  uni.redirectTo({ url: '/pages-sub-consultation/consultation/mentor-support' })
}
</script>

<style scoped>
.mentor-response-page{height:100vh;height:100dvh;overflow:hidden;display:flex;flex-direction:column;background:var(--gyt-page-bg,#f4f8ff);color:#2d405d}.mentor-response-scroll{min-height:0;flex:1}.mentor-response-content{padding:24rpx 24rpx calc(150rpx + env(safe-area-inset-bottom))}.mentor-response-card,.mentor-response-state,.mentor-response-success{padding:28rpx;border:2rpx solid var(--gyt-primary-border,#d9e7fc);border-radius:28rpx;background:var(--gyt-panel-bg,#fff);box-shadow:0 14rpx 34rpx var(--gyt-primary-shadow,rgba(52,120,246,.06))}.mentor-response-card+.mentor-response-card{margin-top:18rpx}.mentor-response-state{margin-top:18rpx;color:#8292a8;text-align:center;font-size:22rpx;line-height:1.6}.mentor-response-state strong,.mentor-response-state text{display:block}.mentor-response-state.error{color:#bd655c}.mentor-response-state button{box-sizing:border-box;height:56rpx;min-height:56rpx;margin:14rpx auto 0;padding:0 20rpx;border:0;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);display:flex;align-items:center;justify-content:center;text-align:center;font-size:20rpx;line-height:1;font-weight:800}.mentor-response-state button::after{border:0}.mentor-response-card-title{color:#2d405d;font-size:27rpx;font-weight:900}.mentor-response-meta{display:flex;align-items:center;justify-content:space-between;gap:16rpx;margin-top:18rpx}.mentor-response-meta text{color:var(--gyt-primary,#3478f6);font-size:19rpx;font-weight:800}.mentor-response-meta strong{max-width:54%;overflow:hidden;color:#52667f;font-size:20rpx;text-align:right;text-overflow:ellipsis;white-space:nowrap}.mentor-response-content-copy{margin-top:15rpx;color:#63758d;font-size:22rpx;line-height:1.65;font-weight:650;white-space:pre-wrap}.mentor-response-evidence-copy{margin-top:14rpx;color:#8797aa;font-size:19rpx;font-weight:700}.mentor-response-label{display:flex;align-items:center;justify-content:space-between;gap:14rpx;color:#40546e;font-size:23rpx;font-weight:850}.mentor-response-label strong{color:#9aabc1;font-size:18rpx;font-weight:700}.mentor-response-description-card textarea{box-sizing:border-box;width:100%;min-height:230rpx;margin-top:16rpx;padding:18rpx;border:2rpx solid var(--gyt-primary-border,#e0eafa);border-radius:18rpx;background:var(--gyt-primary-tint,#fbfdff);color:#2d405d;font-size:22rpx;line-height:1.55;font-weight:600}.mentor-response-placeholder{color:#a7b3c4;font-weight:500}.mentor-response-count{margin-top:10rpx;color:#9aa9bb;text-align:right;font-size:19rpx;font-weight:650}.mentor-response-count.invalid{color:#e58a51}.mentor-response-proof-copy{margin-top:14rpx;color:#8796aa;font-size:20rpx;line-height:1.5;font-weight:650}.mentor-response-images{display:flex;flex-wrap:wrap;gap:14rpx;margin-top:18rpx}.mentor-response-image,.mentor-response-image-add{box-sizing:border-box;width:148rpx;height:148rpx;border-radius:18rpx;overflow:hidden;position:relative}.mentor-response-image{border:2rpx solid var(--gyt-primary-border,#d8e6fa);background:var(--gyt-primary-tint,#f3f7fd)}.mentor-response-image image{width:100%;height:100%}.mentor-response-image button{box-sizing:border-box;position:absolute;top:6rpx;right:6rpx;width:36rpx;height:36rpx;min-height:36rpx;margin:0;padding:0;border:0;border-radius:50%;background:rgba(28,43,66,.65);color:#fff;display:flex;align-items:center;justify-content:center;font-size:27rpx;line-height:1}.mentor-response-image-add{margin:0;border:2rpx dashed var(--gyt-primary-border,#bed4f7);background:var(--gyt-primary-tint,#f7faff);color:var(--gyt-primary,#6180b4);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-size:18rpx;font-weight:750}.mentor-response-image-add>text{font-size:42rpx;line-height:1}.mentor-response-image-add view{margin-top:7rpx}.mentor-response-notice{display:flex;align-items:flex-start;gap:12rpx;margin:20rpx 4rpx 0;color:#8292a8;font-size:19rpx;line-height:1.55;font-weight:650}.mentor-response-notice-icon{width:28rpx;height:28rpx;margin-top:1rpx;border-radius:50%;background:var(--gyt-primary-soft,#dbe9fc);color:var(--gyt-primary,#5d82bd);display:flex;align-items:center;justify-content:center;font-size:18rpx;font-weight:900;flex-shrink:0}.mentor-response-closed strong,.mentor-response-closed text{display:block}.mentor-response-closed>strong{color:#53677e;font-size:24rpx}.mentor-response-closed>text{margin-top:10rpx;color:#8393a8;font-size:20rpx;line-height:1.55;font-weight:650}.mentor-response-existing{margin-top:18rpx;padding:16rpx;border-radius:17rpx;background:var(--gyt-primary-tint,#f7faff)}.mentor-response-existing text,.mentor-response-existing strong{display:block}.mentor-response-existing text{color:#8a9aaf;font-size:18rpx}.mentor-response-existing strong{margin-top:7rpx;color:#5d7088;font-size:20rpx;line-height:1.55;font-weight:650;white-space:pre-wrap}.mentor-response-footer{padding:16rpx 24rpx calc(20rpx + env(safe-area-inset-bottom));border-top:2rpx solid var(--gyt-primary-border,#dbe7f8);background:var(--gyt-panel-bg,#fff)}.mentor-response-footer button,.mentor-response-success button{position:relative;box-sizing:border-box;width:100%;height:76rpx;min-height:76rpx;margin:0;padding:0 16rpx;border:0;border-radius:20rpx;background:var(--gyt-primary-gradient,#3478f6);color:#fff;display:flex;align-items:center;justify-content:center;text-align:center;font-size:24rpx;line-height:1;font-weight:900;box-shadow:0 10rpx 22rpx var(--gyt-primary-shadow,rgba(52,120,246,.2))}.mentor-response-footer button[disabled]{height:76rpx;min-height:76rpx;padding-top:0;padding-bottom:0;background:#bfcce0;box-shadow:none}.mentor-response-footer button[loading]::before{position:absolute;top:0;bottom:0;left:18rpx;width:26rpx;height:26rpx;margin:auto 0}.mentor-response-footer button::after,.mentor-response-success button::after,.mentor-response-image button::after,.mentor-response-image-add::after{border:0}.mentor-response-success{margin-top:100rpx;text-align:center}.mentor-response-success-icon{width:112rpx;height:112rpx;margin:0 auto;border-radius:50%;background:#e5f5ee;color:#24a575;display:flex;align-items:center;justify-content:center;font-size:62rpx;font-weight:900}.mentor-response-success strong,.mentor-response-success text{display:block}.mentor-response-success strong{margin-top:26rpx;color:#273953;font-size:31rpx;font-weight:900}.mentor-response-success text{margin-top:12rpx;color:#7c8da4;font-size:21rpx;line-height:1.65;font-weight:650}.mentor-response-success button{margin-top:32rpx}
</style>
