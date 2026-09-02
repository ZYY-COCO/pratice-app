<template>
  <view class="mentor-report-page" :style="themeInlineStyle">
    <MentorPageHeader title="举报咨询" @back="goBack" />

    <scroll-view scroll-y class="mentor-report-scroll">
      <view v-if="submitted" class="mentor-report-success">
        <view class="mentor-report-success-icon">✓</view>
        <view class="mentor-report-success-title">举报信息已提交</view>
        <view class="mentor-report-success-copy">{{ successCopy }}</view>
        <view class="mentor-report-success-number">举报编号：{{ reportNumber }}</view>
        <button @tap="openSupport">查看处理进度</button>
        <button class="mentor-report-return" @tap="goBack">返回聊天</button>
      </view>

      <view v-else class="mentor-report-content">
        <view class="mentor-report-card mentor-report-target-card">
          <view class="mentor-report-card-title">举报对象</view>
          <view class="mentor-report-target">
            <view class="mentor-report-avatar" :class="targetRole === 'mentor' ? `tone-${mentor?.avatarTone || 'blue'}` : 'tone-mint'">
              {{ targetRole === 'mentor' ? mentor?.avatar || '前' : '同' }}
            </view>
            <view>
              <strong>{{ targetName }}</strong>
              <text>{{ targetDescription }}</text>
            </view>
          </view>
        </view>

        <view class="mentor-report-card">
          <view class="mentor-report-label"><text>问题类型</text><strong>必填</strong></view>
          <picker mode="selector" :range="issueOptions" range-key="label" :value="issueTypeIndex" @change="selectIssueType">
            <view class="mentor-report-picker" :class="{ placeholder: !selectedIssueType }">
              <text>{{ selectedIssueType || '请选择问题类型' }}</text><view class="mentor-report-picker-arrow" aria-hidden="true"></view>
            </view>
          </picker>
        </view>

        <view class="mentor-report-card mentor-report-description-card">
          <view class="mentor-report-label"><text>举报说明</text><strong>20—500 字</strong></view>
          <textarea
            v-model="reportContent"
            maxlength="500"
            placeholder="请描述具体经过、时间和相关情况，便于平台核实。"
            placeholder-class="mentor-report-placeholder"
          />
          <view class="mentor-report-count" :class="{ invalid: reportContent.trim().length > 0 && reportContent.trim().length < 20 }">
            {{ reportContent.trim().length }} / 500
          </view>
        </view>

        <view class="mentor-report-card">
          <view class="mentor-report-label"><text>相关凭证</text><strong>选填，最多 3 张</strong></view>
          <view class="mentor-report-proof-copy">可补充聊天截图或其他与本次咨询相关的凭证。</view>
          <view class="mentor-report-images">
            <view v-for="(image, index) in proofImages" :key="image.id" class="mentor-report-image">
              <image :src="image.path" mode="aspectFill" />
              <button aria-label="删除图片" :disabled="submitting" @tap="removeImage(index)"><CloseIcon /></button>
            </view>
            <button v-if="proofImages.length < maxProofCount" class="mentor-report-image-add" :disabled="submitting" @tap="chooseProofImages">
              <text>＋</text><view>添加凭证</view>
            </button>
          </view>
        </view>

        <view class="mentor-report-notice">
          <view class="mentor-report-notice-icon">i</view>
          <view>请勿提交与本次咨询无关的内容或他人的隐私信息。</view>
        </view>
        <view class="mentor-report-bottom-space"></view>
      </view>
    </scroll-view>

    <view v-if="!submitted" class="mentor-report-footer">
      <button :loading="submitting" :disabled="!canSubmit" @tap="submitReport">{{ submitting ? '正在提交' : '提交举报' }}</button>
    </view>
  </view>
</template>

<script setup>
import CloseIcon from '../../components/CloseIcon.vue'
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  createMentorConsultationReport,
  fetchMentorProfile,
  uploadMentorConsultationReportEvidence
} from '../../api/mentorConsultation'
import { cacheMentors, getMentorById, normalizeMentorDetailResponse } from '../../data/mentorConsultation'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const maxProofCount = 3
const mentor = ref(null)
const orderId = ref('')
const mentorId = ref('')
const targetRole = ref('mentor')
const selectedIssueType = ref('')
const reportContent = ref('')
const proofImages = ref([])
const submitted = ref(false)
const reportNumber = ref('')
const submitting = ref(false)
const failedEvidenceCount = ref(0)
const themeKey = ref(getStoredThemeKey())
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))

const mentorIssueOptions = [
  '服务态度问题',
  '虚假经历或信息',
  '收费或诱导私下交易',
  '爽约或未提供服务',
  '骚扰、辱骂或不当言行',
  '泄露隐私',
  '其他问题'
]
const applicantIssueOptions = [
  '骚扰、辱骂或不当言行',
  '虚假身份或材料',
  '诱导私下交易',
  '恶意占用时段或爽约',
  '侵犯隐私',
  '发布不当内容',
  '恶意评价或失实反馈',
  '其他问题'
]

const issueOptions = computed(() => (targetRole.value === 'mentor' ? mentorIssueOptions : applicantIssueOptions)
  .map((label) => ({ label })))
const issueTypeIndex = computed(() => Math.max(0, issueOptions.value.findIndex((item) => item.label === selectedIssueType.value)))
const targetName = computed(() => targetRole.value === 'mentor' ? (mentor.value?.maskedName || '认证前辈') : '咨询用户')
const targetDescription = computed(() => targetRole.value === 'mentor'
  ? (mentor.value ? `${mentor.value.school || ''}${mentor.value.school && mentor.value.major ? ' · ' : ''}${mentor.value.major || ''}` : '本次咨询的认证前辈')
  : '本次咨询的咨询用户')
const canSubmit = computed(() => Boolean(
  !submitting.value
  && orderId.value
  && selectedIssueType.value
  && reportContent.value.trim().length >= 20
  && reportContent.value.trim().length <= 500
))
const successCopy = computed(() => failedEvidenceCount.value > 0
  ? `举报已提交，但有 ${failedEvidenceCount.value} 张凭证未上传成功。请在“查看处理进度”中补充，平台仍会关联本次咨询订单和聊天记录进行核实。`
  : '感谢你的反馈。平台会关联本次咨询订单和聊天记录，以便后续核实。')

onLoad((options) => {
  orderId.value = String(options?.orderId || '')
  mentorId.value = String(options?.mentorId || '')
  targetRole.value = options?.targetRole === 'applicant' ? 'applicant' : 'mentor'
  mentor.value = getMentorById(mentorId.value)
  if (!orderId.value) {
    uni.showToast({ title: '未找到咨询订单，请返回聊天页重新进入', icon: 'none' })
    return
  }
  if (targetRole.value === 'mentor') void loadMentor()
})

onShow(() => {
  themeKey.value = getStoredThemeKey()
})

async function loadMentor() {
  if (!mentorId.value) return
  try {
    const profile = normalizeMentorDetailResponse(await fetchMentorProfile(mentorId.value))
    if (!profile) return
    mentor.value = profile
    cacheMentors([profile])
  } catch (error) {
    // 本地目录缓存可以保证网络短暂波动时仍显示举报对象。
  }
}

function selectIssueType(event) {
  selectedIssueType.value = issueOptions.value[Number(event?.detail?.value)]?.label || ''
}

function chooseProofImages() {
  const remainingCount = maxProofCount - proofImages.value.length
  if (remainingCount <= 0 || submitting.value) return
  uni.chooseImage({
    count: remainingCount,
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
          id: `report-proof-${Date.now()}-${index}-${Math.random().toString(36).slice(2, 8)}`,
          path: path || tempFile?.path || tempFile?.tempFilePath || '',
          file,
          fileName: tempFile?.name || file?.name || `report-evidence-${index + 1}`
        }
      }).filter((image) => image.path)
      proofImages.value = [...proofImages.value, ...images].slice(0, maxProofCount)
    },
    fail(error) {
      if (!String(error?.errMsg || '').includes('cancel')) {
        uni.showToast({ title: '图片选择失败，请重试', icon: 'none' })
      }
    }
  })
}

function removeImage(index) {
  if (submitting.value) return
  proofImages.value.splice(index, 1)
}

async function submitReport() {
  if (submitting.value) return
  if (!orderId.value) {
    uni.showToast({ title: '未找到咨询订单，请返回聊天页重新进入', icon: 'none' })
    return
  }
  if (!selectedIssueType.value) {
    uni.showToast({ title: '请选择问题类型', icon: 'none' })
    return
  }
  if (reportContent.value.trim().length < 20) {
    uni.showToast({ title: '举报说明请至少填写 20 个字', icon: 'none' })
    return
  }

  submitting.value = true
  try {
    const report = await createMentorConsultationReport(orderId.value, {
      issue_type: selectedIssueType.value,
      content: reportContent.value.trim()
    })
    const failures = []
    for (const image of proofImages.value) {
      try {
        await uploadMentorConsultationReportEvidence(report.id, {
          filePath: image.path,
          file: image.file,
          fileName: image.fileName
        })
      } catch (error) {
        failures.push(image)
      }
    }
    failedEvidenceCount.value = failures.length
    reportNumber.value = `RP${String(report.id || Date.now()).replace(/-/g, '').slice(-8).toUpperCase()}`
    submitted.value = true
    if (failures.length) {
      uni.showToast({ title: '举报已提交，部分凭证未上传', icon: 'none' })
    }
  } catch (error) {
    uni.showToast({ title: error?.detail || '举报提交失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=circle&section=community&communityTab=mentor' })
    }
  })
}

function openSupport() {
  uni.redirectTo({ url: '/pages-sub-consultation/consultation/mentor-support' })
}
</script>

<style scoped>
.mentor-report-page{height:100vh;height:100dvh;overflow:hidden;background:#f4f8ff;display:flex;flex-direction:column}.mentor-report-scroll{min-height:0;flex:1}.mentor-report-content{padding:24rpx 24rpx 0}.mentor-report-card{margin-top:18rpx;padding:28rpx;border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-report-target-card{margin-top:0}.mentor-report-card-title{color:#273953;font-size:28rpx;line-height:1.25;font-weight:900}.mentor-report-target{display:flex;align-items:center;gap:16rpx;margin-top:20rpx}.mentor-report-avatar{width:68rpx;height:68rpx;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:25rpx;font-weight:900;flex-shrink:0}.mentor-report-avatar.tone-blue{background:#e6efff;color:#3478f6}.mentor-report-avatar.tone-mint{background:#e2f4ef;color:#198777}.mentor-report-avatar.tone-violet{background:#eeeafe;color:#7162bd}.mentor-report-avatar.tone-warm{background:#f9eee1;color:#b66c32}.mentor-report-target strong,.mentor-report-target text{display:block}.mentor-report-target strong{color:#2d405d;font-size:25rpx;line-height:1.25;font-weight:900}.mentor-report-target text{margin-top:6rpx;color:#8494aa;font-size:20rpx;line-height:1.35;font-weight:650}.mentor-report-label{display:flex;align-items:center;justify-content:space-between;gap:16rpx;margin-bottom:14rpx;color:#40546e;font-size:23rpx;line-height:1.25;font-weight:850}.mentor-report-label strong{color:#9aabc1;font-size:18rpx;font-weight:700}.mentor-report-picker{box-sizing:border-box;width:100%;height:76rpx;padding:0 18rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#fbfdff;color:#2d405d;display:flex;align-items:center;justify-content:space-between;gap:16rpx;font-size:22rpx;font-weight:650}.mentor-report-picker.placeholder{color:#a7b3c4;font-weight:500}.mentor-report-picker-arrow{color:#8293aa;font-size:26rpx}.mentor-report-description-card textarea{box-sizing:border-box;width:100%;min-height:230rpx;padding:18rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#fbfdff;color:#2d405d;font-size:22rpx;line-height:1.55;font-weight:600}.mentor-report-placeholder{color:#a7b3c4;font-weight:500}.mentor-report-count{margin-top:10rpx;color:#9aa9bb;text-align:right;font-size:19rpx;font-weight:650}.mentor-report-count.invalid{color:#e58a51}.mentor-report-proof-copy{color:#8796aa;font-size:20rpx;line-height:1.5;font-weight:650}.mentor-report-images{display:flex;flex-wrap:wrap;gap:14rpx;margin-top:18rpx}.mentor-report-image,.mentor-report-image-add{width:144rpx;height:144rpx;border-radius:18rpx;overflow:hidden;position:relative}.mentor-report-image{border:2rpx solid #d8e6fa;background:#f3f7fd}.mentor-report-image image{width:100%;height:100%}.mentor-report-image button{box-sizing:border-box;position:absolute;top:6rpx;right:6rpx;width:36rpx;height:36rpx;min-height:36rpx;margin:0;padding:0;border:0;border-radius:50%;background:rgba(28,43,66,.65);color:#fff;display:flex;align-items:center;justify-content:center;font-size:27rpx;line-height:1}.mentor-report-image-add{box-sizing:border-box;margin:0;border:2rpx dashed #bed4f7;background:#f7faff;color:#6180b4;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-size:18rpx;font-weight:750}.mentor-report-image-add>text{font-size:42rpx;line-height:1}.mentor-report-image-add view{margin-top:7rpx}.mentor-report-image button::after,.mentor-report-image-add::after,.mentor-report-footer button::after,.mentor-report-success button::after{border:0}.mentor-report-notice{display:flex;align-items:flex-start;gap:12rpx;margin:20rpx 4rpx 0;color:#8292a8;font-size:19rpx;line-height:1.5;font-weight:650}.mentor-report-notice-icon{width:28rpx;height:28rpx;margin-top:1rpx;border-radius:50%;background:#dbe9fc;color:#5d82bd;display:flex;align-items:center;justify-content:center;font-size:18rpx;font-weight:900;flex-shrink:0}.mentor-report-bottom-space{height:calc(132rpx + env(safe-area-inset-bottom))}.mentor-report-footer{padding:16rpx 24rpx calc(20rpx + env(safe-area-inset-bottom));border-top:2rpx solid #dbe7f8;background:rgba(255,255,255,.97)}.mentor-report-footer button,.mentor-report-success button{box-sizing:border-box;width:100%;height:76rpx;min-height:76rpx;margin:0;padding:0 16rpx;border:0;border-radius:20rpx;background:#3478f6;color:#fff;display:flex;align-items:center;justify-content:center;text-align:center;font-size:24rpx;line-height:1;font-weight:900;box-shadow:0 10rpx 22rpx rgba(52,120,246,.2)}.mentor-report-footer button[disabled]{background:#bfcce0;box-shadow:none}.mentor-report-success{padding:128rpx 50rpx 70rpx;text-align:center}.mentor-report-success-icon{width:112rpx;height:112rpx;margin:0 auto;border-radius:50%;background:#e5f5ee;color:#24a575;display:flex;align-items:center;justify-content:center;font-size:62rpx;font-weight:900}.mentor-report-success-title{margin-top:26rpx;color:#273953;font-size:31rpx;line-height:1.3;font-weight:900}.mentor-report-success-copy{margin-top:12rpx;color:#7c8da4;font-size:21rpx;line-height:1.65;font-weight:650}.mentor-report-success-number{margin:24rpx 0 34rpx;padding:16rpx;border-radius:16rpx;background:#edf4ff;color:#5272a3;font-size:20rpx;font-weight:750}
.mentor-report-page { background: var(--gyt-page-bg); }
.mentor-report-card { border-color: var(--gyt-primary-border, #d9e7fc); background: var(--gyt-panel-bg, #ffffff); box-shadow: 0 14rpx 34rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.06)); }
.mentor-report-avatar.tone-blue,.mentor-report-notice-icon,.mentor-report-success-number { background: var(--gyt-primary-soft, #edf4ff); color: var(--gyt-primary, #3478f6); }
.mentor-report-picker,.mentor-report-description-card textarea { border-color: var(--gyt-primary-border, #e0eafa); background: var(--gyt-primary-tint, #fbfdff); }
.mentor-report-image { border-color: var(--gyt-primary-border, #d8e6fa); background: var(--gyt-primary-tint, #f3f7fd); }
.mentor-report-image-add { border-color: var(--gyt-primary-border, #bed4f7); background: var(--gyt-primary-tint, #f7faff); color: var(--gyt-primary, #3478f6); }
.mentor-report-footer { border-color: var(--gyt-primary-border, #dbe7f8); background: var(--gyt-primary-tint, #ffffff); }
.mentor-report-footer button,.mentor-report-success button { background: var(--gyt-primary-gradient, #3478f6); box-shadow: 0 10rpx 22rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.2)); }
.mentor-report-image,.mentor-report-image-add { box-sizing: border-box; width: 148rpx; height: 148rpx; }
.mentor-report-footer button { position: relative; }
.mentor-report-footer button[disabled] { height: 76rpx; min-height: 76rpx; padding-top: 0; padding-bottom: 0; }
.mentor-report-footer button[loading]::before { position: absolute; top: 0; bottom: 0; left: 18rpx; width: 26rpx; height: 26rpx; margin: auto 0; }
.mentor-report-picker-arrow{width:14rpx;height:14rpx;margin:0 4rpx 7rpx 12rpx;border-right:3rpx solid currentColor;border-bottom:3rpx solid currentColor;color:#8293aa;transform:rotate(45deg);flex:none}
</style>
