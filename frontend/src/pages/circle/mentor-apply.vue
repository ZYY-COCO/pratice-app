<template>
  <view class="mentor-apply-page">
    <MentorPageHeader :title="pageTitle" @back="goBack" />

    <scroll-view scroll-y class="mentor-apply-scroll">
      <view v-if="pageMode === 'apply'" class="mentor-apply-content">
        <view class="mentor-apply-card">
          <view class="mentor-apply-section-title">认证基本信息</view>
          <view class="mentor-apply-field">
            <view class="mentor-apply-label">真实姓名 <text>后台审核使用</text></view>
            <input v-model="form.realName" placeholder="请输入真实姓名" placeholder-class="mentor-apply-placeholder" />
            <view class="mentor-apply-tip">公开展示时系统会自动进行姓名脱敏。</view>
          </view>
          <view class="mentor-apply-field">
            <view class="mentor-apply-label">录取院校</view>
            <input v-model="schoolKeyword" placeholder="搜索或输入录取院校" placeholder-class="mentor-apply-placeholder" @input="handleSchoolInput" />
            <view v-if="schoolResults.length" class="mentor-apply-search-results">
              <button v-for="school in schoolResults" :key="school" @tap="selectSchool(school)">{{ school }}</button>
            </view>
          </view>
          <view class="mentor-apply-field">
            <view class="mentor-apply-label">录取专业</view>
            <input v-model="form.major" placeholder="支持搜索或直接输入专业" placeholder-class="mentor-apply-placeholder" />
          </view>
          <view class="mentor-apply-two-column">
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">入学年份</view>
              <picker mode="selector" :range="yearOptions" :value="admissionYearIndex" @change="selectAdmissionYear">
                <view class="mentor-apply-picker">{{ form.admissionYear }} <text>⌄</text></view>
              </picker>
            </view>
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">毕业年份</view>
              <picker mode="selector" :range="yearOptions" :value="graduationYearIndex" @change="selectGraduationYear">
                <view class="mentor-apply-picker">{{ form.graduationYear }} <text>⌄</text></view>
              </picker>
            </view>
          </view>
          <view class="mentor-apply-two-column">
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">初试成绩</view>
              <input v-model="form.score" type="number" min="0" max="150" placeholder="例如 110" placeholder-class="mentor-apply-placeholder" @input="handleScoreInput" />
            </view>
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">考试类别</view>
              <view class="mentor-apply-exam-row">
                <button v-for="item in examOptions" :key="item" :class="{ active: form.examType === item }" @tap="form.examType = item">{{ item }}</button>
              </view>
            </view>
          </view>
        </view>

        <view class="mentor-apply-card">
          <view class="mentor-apply-section-title">证明材料</view>
          <view class="mentor-apply-copy">上传录取通知书、学生证或其他录取证明；材料仅用于平台认证审核，不对其他用户公开。</view>
          <view class="mentor-proof-grid">
            <view v-for="(path, index) in proofImages" :key="path" class="mentor-proof-image">
              <image :src="path" mode="aspectFill" />
              <button @tap="removeProof(index)">×</button>
            </view>
            <button v-if="proofImages.length < 3" class="mentor-proof-upload" @tap="chooseProof">
              <text>＋</text><view>上传证明</view>
            </button>
          </view>
        </view>

        <view class="mentor-apply-card">
          <view class="mentor-apply-section-title">擅长咨询领域</view>
          <view class="mentor-apply-copy">最多选择 4 项，方便考生更精准地找到你。</view>
          <view class="mentor-skill-options">
            <button v-for="item in skillOptions" :key="item" :class="{ active: form.skills.includes(item) }" @tap="toggleSkill(item)">{{ item }}</button>
          </view>
        </view>

        <view class="mentor-apply-card">
          <view class="mentor-apply-label"><text>个人简介</text><text>{{ form.bio.length }} / 500</text></view>
          <textarea v-model="form.bio" maxlength="500" placeholder="介绍你的上岸经历、可提供的帮助和擅长方向。" placeholder-class="mentor-apply-placeholder" />
          <view class="mentor-apply-price-field">
            <view><strong>咨询价格</strong><text>单次咨询默认开启 60 分钟咨询窗口。</text></view>
            <view class="mentor-price-input"><text>¥</text><input v-model="form.price" type="number" /><text>/ 次</text></view>
          </view>
        </view>
        <view class="mentor-apply-bottom-space"></view>
      </view>

      <view v-else-if="pageMode === 'pending'" class="mentor-apply-status-content">
        <view class="mentor-apply-status-icon pending">⌛</view>
        <view class="mentor-apply-status-title">认证审核中</view>
        <view class="mentor-apply-status-copy">认证资料已提交，平台将在审核后通知结果。审核期间你可以继续使用考研圈的其他功能。</view>
        <view class="mentor-apply-status-card">
          <view><text>申请院校</text><strong>{{ form.school || '待审核院校' }}</strong></view>
          <view><text>申请专业</text><strong>{{ form.major || '待审核专业' }}</strong></view>
          <view><text>提交状态</text><strong class="green">资料已提交</strong></view>
        </view>
        <view class="mentor-apply-demo-card">
          <strong>本地演示控制</strong><text>用于预览认证完成后的“我的咨询主页”状态。</text>
          <button @tap="approveDemo">模拟认证通过</button>
        </view>
      </view>

      <view v-else class="mentor-apply-center-content">
        <view class="mentor-center-hero">
          <view class="mentor-center-avatar">{{ (form.realName || '前').slice(0, 1) }}</view>
          <view><strong>{{ maskedApplicationName }}</strong><text>✓ 平台认证前辈</text><view>{{ form.school || '我的咨询主页' }} · {{ form.major || '待完善专业' }}</view></view>
        </view>
        <view class="mentor-center-status">
          <view><strong>在线接单</strong><text>允许匹配到的考生发起即时咨询</text></view>
          <switch :checked="isOnline" color="#3478f6" @change="isOnline = $event.detail.value" />
        </view>
        <view class="mentor-center-grid">
          <view><text>咨询价格</text><strong>¥{{ form.price || 39 }} / 次</strong></view>
          <view><text>可预约时间</text><strong>待设置</strong></view>
          <view><text>历史咨询</text><strong>0</strong></view>
          <view><text>用户评价</text><strong>待积累</strong></view>
        </view>
        <view class="mentor-center-reserve">
          <strong>我的咨询主页</strong>
          <text>已为后续接入个人资料、咨询价格、在线状态、可预约时间、历史咨询、收入与用户评价保留页面结构。</text>
        </view>
      </view>
    </scroll-view>

    <view v-if="pageMode === 'apply'" class="mentor-apply-footer"><button @tap="submitApplication">提交认证</button></view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  MENTOR_SKILL_OPTIONS,
  getMentorApplication,
  getMentorVerificationStatus,
  maskMentorName,
  saveMentorApplication,
  searchMentorSchools,
  setMentorVerificationStatus
} from '../../data/mentorConsultation'

const pageMode = ref('apply')
const schoolKeyword = ref('')
const proofImages = ref([])
const isOnline = ref(true)
const skillOptions = MENTOR_SKILL_OPTIONS
const examOptions = ['Z001', 'Z002', '申请制']
const yearOptions = ['2028', '2027', '2026', '2025', '2024', '2023', '2022']
const form = ref(createDefaultApplication())

const pageTitle = computed(() => pageMode.value === 'pending' ? '认证审核中' : pageMode.value === 'center' ? '我的咨询主页' : '申请成为前辈')
const schoolResults = computed(() => searchMentorSchools(schoolKeyword.value))
const admissionYearIndex = computed(() => Math.max(0, yearOptions.indexOf(String(form.value.admissionYear))))
const graduationYearIndex = computed(() => Math.max(0, yearOptions.indexOf(String(form.value.graduationYear))))
const maskedApplicationName = computed(() => maskMentorName(form.value.realName || '前辈'))

onLoad((options) => {
  const saved = getMentorApplication()
  if (saved) {
    form.value = { ...createDefaultApplication(), ...saved }
    proofImages.value = Array.isArray(saved.proofImages) ? saved.proofImages : []
  }
  const verificationStatus = getMentorVerificationStatus()
  pageMode.value = verificationStatus === 'verified' ? 'center' : verificationStatus === 'pending' ? 'pending' : (options?.mode === 'pending' ? 'pending' : 'apply')
})

function createDefaultApplication() {
  return {
    realName: '', school: '', major: '', admissionYear: '2025', graduationYear: '2027', score: '', examType: 'Z001', skills: [], bio: '', price: '39'
  }
}

function handleSchoolInput(event) {
  form.value.school = event?.detail?.value || schoolKeyword.value
  schoolKeyword.value = form.value.school
}

function selectSchool(school) {
  form.value.school = school
  schoolKeyword.value = school
}

function selectAdmissionYear(event) { form.value.admissionYear = yearOptions[Number(event?.detail?.value)] || yearOptions[0] }
function selectGraduationYear(event) { form.value.graduationYear = yearOptions[Number(event?.detail?.value)] || yearOptions[0] }

function handleScoreInput(event) {
  const rawValue = String(event?.detail?.value ?? '')
  if (!rawValue) {
    form.value.score = ''
    return
  }
  const score = Number(rawValue)
  form.value.score = Number.isFinite(score) ? String(Math.min(150, Math.max(0, Math.trunc(score)))) : ''
}

function toggleSkill(skill) {
  if (form.value.skills.includes(skill)) {
    form.value.skills = form.value.skills.filter((item) => item !== skill)
    return
  }
  if (form.value.skills.length >= 4) {
    uni.showToast({ title: '最多选择 4 个擅长领域', icon: 'none' })
    return
  }
  form.value.skills = [...form.value.skills, skill]
}

function chooseProof() {
  uni.chooseImage({
    count: Math.max(1, 3 - proofImages.value.length),
    sizeType: ['compressed'],
    success(result) {
      proofImages.value = [...proofImages.value, ...(result.tempFilePaths || [])].slice(0, 3)
    },
    fail() {
      uni.showToast({ title: '未选择证明材料', icon: 'none' })
    }
  })
}

function removeProof(index) { proofImages.value = proofImages.value.filter((_, itemIndex) => itemIndex !== index) }

function submitApplication() {
  if (!form.value.realName.trim() || !form.value.school.trim() || !form.value.major.trim() || !String(form.value.score).trim()) {
    uni.showToast({ title: '请补充真实姓名、录取院校、专业和初试成绩', icon: 'none' })
    return
  }
  const score = Number(form.value.score)
  if (!Number.isInteger(score) || score < 0 || score > 150) {
    uni.showToast({ title: '初试成绩请填写 0–150 分', icon: 'none' })
    return
  }
  saveMentorApplication({ ...form.value, proofImages: proofImages.value })
  setMentorVerificationStatus('pending')
  pageMode.value = 'pending'
}

function approveDemo() {
  setMentorVerificationStatus('verified')
  pageMode.value = 'center'
  uni.showToast({ title: '已切换为认证通过（演示）', icon: 'none' })
}

function goBack() {
  uni.navigateBack({ fail() { uni.reLaunch({ url: '/pages/home/index?tab=circle&section=community&communityTab=mentor' }) } })
}
</script>

<style scoped>
.mentor-apply-page{height:100vh;overflow:hidden;background:#f4f8ff;display:flex;flex-direction:column}.mentor-apply-scroll{min-height:0;flex:1}.mentor-apply-content{padding:24rpx 24rpx 0}
.mentor-apply-card{margin-top:18rpx;padding:28rpx;border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-apply-section-title{color:#273953;font-size:28rpx;font-weight:900}.mentor-apply-field{margin-top:23rpx}.mentor-apply-label{display:flex;align-items:center;justify-content:space-between;gap:10rpx;margin-bottom:12rpx;color:#40546e;font-size:23rpx;line-height:1.25;font-weight:850}.mentor-apply-label>text:last-child{color:#98a9c0;font-size:18rpx;font-weight:650}.mentor-apply-label>text:first-child{color:inherit;font-size:inherit;font-weight:inherit}.mentor-apply-label>text{color:inherit;display:inline;font-weight:inherit}.mentor-apply-label>text+text{color:#98a9c0;font-size:18rpx}.mentor-apply-label > text:last-child{font-weight:650}
.mentor-apply-field input,.mentor-apply-picker{box-sizing:border-box;width:100%;height:72rpx;padding:0 18rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#fbfdff;color:#2d405d;font-size:23rpx;line-height:68rpx;font-weight:650}.mentor-apply-placeholder{color:#a7b3c4;font-weight:500}.mentor-apply-tip{margin-top:8rpx;color:#91a0b4;font-size:18rpx;line-height:1.4;font-weight:600}.mentor-apply-search-results{display:flex;flex-wrap:wrap;gap:9rpx;margin-top:11rpx}.mentor-apply-search-results button,.mentor-apply-exam-row button,.mentor-skill-options button{min-height:48rpx;margin:0;padding:0 14rpx;border:2rpx solid #dce7f8;border-radius:14rpx;background:#fbfdff;color:#708199;font-size:20rpx;font-weight:750}.mentor-apply-search-results button::after,.mentor-apply-exam-row button::after,.mentor-skill-options button::after,.mentor-proof-image button::after,.mentor-proof-upload::after,.mentor-apply-footer button::after,.mentor-apply-demo-card button::after{border:0}.mentor-apply-two-column{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16rpx}.mentor-apply-picker{display:flex;align-items:center;justify-content:space-between;line-height:1.2}.mentor-apply-picker text{color:#8494a9;font-size:24rpx}.mentor-apply-exam-row{display:flex;flex-wrap:wrap;gap:8rpx}.mentor-apply-exam-row button{min-width:70rpx}.mentor-apply-exam-row button.active,.mentor-skill-options button.active{border-color:#b9d2ff;background:#edf4ff;color:#3478f6}.mentor-apply-copy{margin-top:10rpx;color:#7e8ea4;font-size:20rpx;line-height:1.55;font-weight:650}.mentor-proof-grid{display:flex;flex-wrap:wrap;gap:12rpx;margin-top:20rpx}.mentor-proof-image,.mentor-proof-upload{width:140rpx;height:140rpx;border-radius:18rpx;overflow:hidden;position:relative}.mentor-proof-image{border:2rpx solid #d8e6fa}.mentor-proof-image image{width:100%;height:100%}.mentor-proof-image button{position:absolute;top:6rpx;right:6rpx;width:34rpx;height:34rpx;min-height:34rpx;margin:0;padding:0;border:0;border-radius:50%;background:rgba(27,42,66,.62);color:#fff;font-size:26rpx;line-height:1}.mentor-proof-upload{margin:0;border:2rpx dashed #bed4f7;background:#f7faff;color:#6180b4;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:20rpx;font-weight:750}.mentor-proof-upload>text{font-size:42rpx;line-height:1}.mentor-proof-upload view{margin-top:7rpx;font-size:18rpx}.mentor-skill-options{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:18rpx}.mentor-apply-card textarea{box-sizing:border-box;width:100%;min-height:178rpx;padding:16rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#fbfdff;color:#3a4f6e;font-size:22rpx;line-height:1.5}.mentor-apply-price-field{margin-top:24rpx;padding-top:20rpx;border-top:2rpx solid #edf1f8;display:flex;align-items:center;justify-content:space-between;gap:18rpx}.mentor-apply-price-field strong,.mentor-apply-price-field text{display:block}.mentor-apply-price-field strong{color:#40546e;font-size:23rpx;font-weight:900}.mentor-apply-price-field text{margin-top:6rpx;color:#8d9bb0;font-size:18rpx;line-height:1.35;font-weight:650}.mentor-price-input{display:flex;align-items:center;gap:5rpx;border:2rpx solid #d9e7fa;border-radius:16rpx;background:#fbfdff;color:#3478f6;padding:0 12rpx;flex-shrink:0}.mentor-price-input input{width:58rpx;height:58rpx;padding:0;border:0;background:transparent;color:#2d405d;text-align:center;font-size:25rpx;font-weight:900}.mentor-price-input text{margin:0;color:#5e78a3;font-size:20rpx;font-weight:800}.mentor-apply-bottom-space{height:calc(136rpx + env(safe-area-inset-bottom))}.mentor-apply-footer{padding:16rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));border-top:2rpx solid #dbe7f8;background:rgba(255,255,255,.97)}.mentor-apply-footer button{width:100%;min-height:76rpx;margin:0;border:0;border-radius:20rpx;background:#3478f6;color:#fff;font-size:24rpx;font-weight:900;box-shadow:0 10rpx 22rpx rgba(52,120,246,.2)}
.mentor-apply-status-content,.mentor-apply-center-content{padding:84rpx 24rpx 50rpx;text-align:center}.mentor-apply-status-icon{width:100rpx;height:100rpx;margin:0 auto;border-radius:50%;background:#edf4ff;color:#3478f6;display:flex;align-items:center;justify-content:center;font-size:45rpx;font-weight:900}.mentor-apply-status-title{margin-top:22rpx;color:#283b56;font-size:32rpx;font-weight:900}.mentor-apply-status-copy{max-width:560rpx;margin:14rpx auto 0;color:#7d8ea6;font-size:22rpx;line-height:1.6;font-weight:650}.mentor-apply-status-card,.mentor-apply-demo-card{margin-top:32rpx;padding:26rpx;border:2rpx solid #d9e7fc;border-radius:26rpx;background:rgba(255,255,255,.93);text-align:left;box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-apply-status-card>view{display:flex;align-items:center;justify-content:space-between;gap:20rpx;color:#8796a9;font-size:21rpx;font-weight:650}.mentor-apply-status-card>view+view{margin-top:18rpx}.mentor-apply-status-card strong{color:#40546d;font-weight:850}.mentor-apply-status-card strong.green{color:#278d58}.mentor-apply-demo-card strong,.mentor-apply-demo-card text{display:block}.mentor-apply-demo-card strong{color:#48648e;font-size:24rpx;font-weight:900}.mentor-apply-demo-card text{margin-top:8rpx;color:#8291a5;font-size:20rpx;line-height:1.5;font-weight:650}.mentor-apply-demo-card button{min-height:60rpx;margin:18rpx 0 0;padding:0 20rpx;border:0;border-radius:17rpx;background:#3478f6;color:#fff;font-size:21rpx;font-weight:850}
.mentor-center-hero,.mentor-center-status,.mentor-center-grid,.mentor-center-reserve{border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-center-hero{padding:28rpx;display:flex;align-items:center;gap:16rpx;text-align:left}.mentor-center-avatar{width:78rpx;height:78rpx;border-radius:50%;background:#e6efff;color:#3478f6;display:flex;align-items:center;justify-content:center;font-size:30rpx;font-weight:900;flex-shrink:0}.mentor-center-hero strong,.mentor-center-hero text,.mentor-center-hero view{display:block}.mentor-center-hero strong{color:#273a55;font-size:28rpx;font-weight:900}.mentor-center-hero text{margin-top:6rpx;color:#3478f6;font-size:19rpx;font-weight:800}.mentor-center-hero view{margin-top:6rpx;color:#7c8ca2;font-size:20rpx;font-weight:650}.mentor-center-status{margin-top:18rpx;padding:25rpx;display:flex;align-items:center;justify-content:space-between;gap:20rpx;text-align:left}.mentor-center-status strong,.mentor-center-status text{display:block}.mentor-center-status strong{color:#40546e;font-size:24rpx;font-weight:900}.mentor-center-status text{margin-top:6rpx;color:#8391a6;font-size:19rpx;line-height:1.4;font-weight:650}.mentor-center-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2rpx;margin-top:18rpx;overflow:hidden}.mentor-center-grid>view{padding:26rpx;border:1rpx solid #edf2f8;text-align:left}.mentor-center-grid text,.mentor-center-grid strong{display:block}.mentor-center-grid text{color:#8a98ab;font-size:19rpx;font-weight:650}.mentor-center-grid strong{margin-top:9rpx;color:#41546e;font-size:23rpx;font-weight:900}.mentor-center-reserve{margin-top:18rpx;padding:26rpx;text-align:left}.mentor-center-reserve strong,.mentor-center-reserve text{display:block}.mentor-center-reserve strong{color:#46618c;font-size:24rpx;font-weight:900}.mentor-center-reserve text{margin-top:9rpx;color:#8090a6;font-size:20rpx;line-height:1.55;font-weight:650}
.mentor-apply-exam-row{flex-wrap:nowrap}.mentor-apply-exam-row button{flex:1;min-width:0;min-height:72rpx;height:72rpx;padding:0;border-radius:18rpx;font-size:23rpx;line-height:68rpx;white-space:nowrap}
@media(max-width:350px){.mentor-apply-content{padding-right:18rpx;padding-left:18rpx}.mentor-apply-card{padding:23rpx}.mentor-proof-image,.mentor-proof-upload{width:126rpx;height:126rpx}}
</style>
