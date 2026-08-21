<template>
  <view class="mentor-info-page">
    <MentorPageHeader title="我的信息" @back="goBack" />

    <scroll-view scroll-y class="mentor-info-scroll">
      <view v-if="mentor" class="mentor-info-content">
        <view class="mentor-info-hero">
          <view class="mentor-info-person-row">
            <view class="mentor-info-avatar" :class="`tone-${mentor.avatarTone || 'blue'}`">
              <image v-if="mentorAvatarUrl" :src="mentorAvatarUrl" mode="aspectFill" />
              <text v-else>{{ mentor.avatar || '前' }}</text>
            </view>
            <view class="mentor-info-person-copy">
              <view class="mentor-info-name-row">
                <text>{{ mentor.maskedName }}</text>
                <text v-if="mentor.verified" class="mentor-info-verified">✓ 平台认证</text>
              </view>
              <view class="mentor-info-school">{{ mentor.school || '未填写院校' }}</view>
              <view class="mentor-info-major">{{ mentor.major || '未填写专业' }}<text v-if="mentor.admissionYear"> · {{ mentor.admissionYear }}级</text></view>
            </view>
          </view>
          <view class="mentor-info-status" :class="{ online: mentor.onlineStatus === 'online' }">
            <view></view>
            <text>{{ mentor.onlineStatus === 'online' ? '在线接单中' : '暂不接即时咨询' }}</text>
          </view>
        </view>

        <view class="mentor-info-section">
          <view class="mentor-info-section-heading">
            <view>
              <strong>我的资料</strong>
              <text>已通过平台认证的信息</text>
            </view>
          </view>
          <view class="mentor-info-facts">
            <view><text>考试类型</text><strong>{{ examTypeLabel }}</strong></view>
            <view><text>初试成绩</text><strong>{{ scoreLabel }}</strong></view>
            <view><text>录取院校</text><strong>{{ mentor.school || '未填写' }}</strong></view>
            <view><text>录取专业</text><strong>{{ mentor.major || '未填写' }}</strong></view>
          </view>
        </view>

        <view v-if="mentor.skills?.length || mentor.bio" class="mentor-info-section">
          <view v-if="mentor.skills?.length" class="mentor-info-detail-block">
            <view class="mentor-info-detail-title">擅长咨询</view>
            <view class="mentor-info-skills">
              <text v-for="skill in mentor.skills" :key="skill">{{ formatSkillLabel(skill) }}</text>
            </view>
          </view>
          <view v-if="mentor.bio" class="mentor-info-detail-block" :class="{ 'has-divider': mentor.skills?.length }">
            <view class="mentor-info-detail-title">个人简介</view>
            <view class="mentor-info-bio">{{ mentor.bio }}</view>
          </view>
        </view>

        <view class="mentor-info-section mentor-info-stats-section">
          <view class="mentor-info-section-heading">
            <view>
              <strong>咨询数据</strong>
              <text>实时同步你的咨询情况</text>
            </view>
          </view>
          <view class="mentor-info-stats-grid">
            <view><text>咨询价格</text><strong>{{ mentor.priceLabel }} / 次</strong></view>
            <view><text>待处理请求</text><strong>{{ pendingOrderCount }} 单</strong></view>
            <view><text>进行中咨询</text><strong>{{ activeOrderCount }} 单</strong></view>
            <view><text>已完成咨询</text><strong>{{ mentor.consultCount || 0 }} 单</strong></view>
          </view>
        </view>

        <view class="mentor-info-bottom-space"></view>
      </view>

      <view v-else-if="infoLoading" class="mentor-info-state">正在加载我的信息…</view>
      <view v-else class="mentor-info-state mentor-info-state-empty">
        <view>前辈资料暂时不可用</view>
        <button @tap="goBack">返回咨询主页</button>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import { fetchMyMentorProfile, fetchMyReceivedMentorOrders } from '../../api/mentorConsultation'
import { normalizeMentorConsultationOrder, normalizeMentorDetailResponse } from '../../data/mentorConsultation'
import { getAuthUser } from '../../utils/auth'

const mentor = ref(null)
const mentorOrders = ref([])
const infoLoading = ref(false)
const ownerUser = ref(getAuthUser() || {})

const mentorAvatarUrl = computed(() => getUserAvatarUrl(ownerUser.value) || mentor.value?.avatarUrl || '')
const pendingOrderCount = computed(() => mentorOrders.value.filter((order) => order.orderStatus === 'pending_accept').length)
const activeOrderCount = computed(() => mentorOrders.value.filter((order) => ['accepted', 'in_progress'].includes(order.orderStatus)).length)
const examTypeLabel = computed(() => mentor.value?.examType === 'application' ? '申请制' : (mentor.value?.examType || '未填写'))
const scoreLabel = computed(() => Number.isFinite(Number(mentor.value?.score)) ? `${mentor.value.score} 分` : '未填写')

onLoad(() => {
  void loadMentorInfo()
})

onShow(() => {
  ownerUser.value = getAuthUser() || {}
  void loadMentorInfo({ silent: true })
})

async function loadMentorInfo({ silent = false } = {}) {
  if (infoLoading.value) return
  infoLoading.value = true

  const [profileResult, ordersResult] = await Promise.allSettled([
    fetchMyMentorProfile(),
    fetchMyReceivedMentorOrders({ limit: 50 })
  ])

  if (profileResult.status === 'fulfilled') {
    const profile = normalizeMentorDetailResponse(profileResult.value)
    if (profile) mentor.value = profile
  } else if (!mentor.value && !silent) {
    uni.showToast({ title: profileResult.reason?.detail || '我的信息加载失败', icon: 'none' })
  }

  if (ordersResult.status === 'fulfilled') {
    mentorOrders.value = (Array.isArray(ordersResult.value?.items) ? ordersResult.value.items : [])
      .map((order) => normalizeMentorConsultationOrder(order))
  } else if (!silent && mentor.value) {
    uni.showToast({ title: ordersResult.reason?.detail || '咨询数据加载失败', icon: 'none' })
  }

  infoLoading.value = false
}

function formatSkillLabel(skill) {
  return skill === '初试备考' ? '初试规划' : skill
}

function getUserAvatarUrl(user = {}) {
  const value = String(user?.avatar_url || user?.avatarUrl || '').trim()
  return /^(https?:\/\/|data:image\/)/i.test(value) ? value : ''
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/circle/mentor-apply' })
    }
  })
}
</script>

<style scoped>
.mentor-info-page{height:100vh;overflow:hidden;background:#f4f8ff;display:flex;flex-direction:column}.mentor-info-scroll{min-height:0;flex:1}.mentor-info-content{padding:24rpx 24rpx 0}.mentor-info-hero,.mentor-info-section{border:2rpx solid #d9e7fc;border-radius:30rpx;background:rgba(255,255,255,.94);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-info-hero{padding:30rpx}.mentor-info-person-row{display:flex;align-items:center;gap:18rpx}.mentor-info-avatar{width:94rpx;height:94rpx;overflow:hidden;border:3rpx solid #fff;border-radius:50%;background:#e6efff;color:#3478f6;display:flex;align-items:center;justify-content:center;font-size:34rpx;font-weight:900;flex-shrink:0}.mentor-info-avatar image{width:100%;height:100%}.mentor-info-avatar.tone-mint{background:#e2f4ef;color:#198777}.mentor-info-avatar.tone-violet{background:#eeeafe;color:#7162bd}.mentor-info-avatar.tone-warm{background:#f9eee1;color:#b66c32}.mentor-info-person-copy{min-width:0;flex:1}.mentor-info-name-row{display:flex;align-items:center;gap:10rpx;min-width:0}.mentor-info-name-row>text:first-child{min-width:0;overflow:hidden;color:#263a57;font-size:30rpx;line-height:1.2;font-weight:900;text-overflow:ellipsis;white-space:nowrap}.mentor-info-verified{padding:6rpx 10rpx;border-radius:999rpx;background:#edf4ff;color:#3478f6;font-size:18rpx;line-height:1.2;font-weight:800;white-space:nowrap}.mentor-info-school{margin-top:12rpx;color:#506580;font-size:23rpx;line-height:1.3;font-weight:800}.mentor-info-major{margin-top:7rpx;color:#8292a8;font-size:20rpx;line-height:1.35;font-weight:650}.mentor-info-major text{color:inherit;font:inherit}.mentor-info-status{display:inline-flex;align-items:center;gap:8rpx;margin-top:22rpx;padding:9rpx 13rpx;border-radius:999rpx;background:#eef3fb;color:#7f8ea2;font-size:19rpx;line-height:1.2;font-weight:800}.mentor-info-status>view{width:12rpx;height:12rpx;border-radius:50%;background:#aeb9c8}.mentor-info-status.online{background:#e7f7ed;color:#258656}.mentor-info-status.online>view{background:#25b970;box-shadow:0 0 0 5rpx rgba(37,185,112,.12)}.mentor-info-section{margin-top:18rpx;padding:26rpx}.mentor-info-section-heading strong,.mentor-info-section-heading text{display:block}.mentor-info-section-heading strong{color:#40546e;font-size:25rpx;line-height:1.25;font-weight:900}.mentor-info-section-heading text{margin-top:6rpx;color:#8796a9;font-size:19rpx;line-height:1.4;font-weight:650}.mentor-info-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2rpx;margin:22rpx -26rpx -26rpx;overflow:hidden;border-top:2rpx solid #edf2f8}.mentor-info-facts>view{min-width:0;padding:22rpx 26rpx;border-top:1rpx solid #edf2f8}.mentor-info-facts>view:nth-child(-n+2){border-top:0}.mentor-info-facts>view:nth-child(odd){border-right:1rpx solid #edf2f8}.mentor-info-facts text,.mentor-info-facts strong{display:block}.mentor-info-facts text{color:#8a98ab;font-size:19rpx;font-weight:650}.mentor-info-facts strong{margin-top:9rpx;overflow:hidden;color:#41546e;font-size:22rpx;line-height:1.35;font-weight:900;text-overflow:ellipsis;white-space:nowrap}.mentor-info-detail-block+.mentor-info-detail-block{margin-top:22rpx}.mentor-info-detail-block.has-divider{padding-top:22rpx;border-top:2rpx solid #edf2f8}.mentor-info-detail-title{color:#40546e;font-size:23rpx;font-weight:900}.mentor-info-skills{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:16rpx}.mentor-info-skills text{padding:9rpx 13rpx;border-radius:999rpx;background:#edf4ff;color:#4f76ad;font-size:19rpx;line-height:1.2;font-weight:750}.mentor-info-bio{margin-top:12rpx;color:#6d7f97;font-size:21rpx;line-height:1.65;font-weight:600}.mentor-info-stats-section{padding-bottom:0;overflow:hidden}.mentor-info-stats-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2rpx;margin:22rpx -26rpx 0;overflow:hidden;border-top:2rpx solid #edf2f8}.mentor-info-stats-grid>view{padding:26rpx;border-top:1rpx solid #edf2f8}.mentor-info-stats-grid>view:nth-child(-n+2){border-top:0}.mentor-info-stats-grid>view:nth-child(odd){border-right:1rpx solid #edf2f8}.mentor-info-stats-grid text,.mentor-info-stats-grid strong{display:block}.mentor-info-stats-grid text{color:#8a98ab;font-size:19rpx;font-weight:650}.mentor-info-stats-grid strong{margin-top:9rpx;color:#41546e;font-size:23rpx;line-height:1.35;font-weight:900}.mentor-info-bottom-space{height:calc(44rpx + env(safe-area-inset-bottom))}.mentor-info-state{padding:110rpx 38rpx;color:#7d8ea6;text-align:center;font-size:23rpx;font-weight:700}.mentor-info-state-empty button{min-height:60rpx;margin:28rpx auto 0;padding:0 24rpx;border:0;border-radius:18rpx;background:#3478f6;color:#fff;font-size:21rpx;font-weight:850}.mentor-info-state-empty button::after{border:0}@media(max-width:350px){.mentor-info-content{padding-right:18rpx;padding-left:18rpx}.mentor-info-hero,.mentor-info-section{padding-right:22rpx;padding-left:22rpx}.mentor-info-facts,.mentor-info-stats-grid{margin-right:-22rpx;margin-left:-22rpx}.mentor-info-facts>view,.mentor-info-stats-grid>view{padding-right:22rpx;padding-left:22rpx}.mentor-info-name-row{gap:7rpx}.mentor-info-verified{padding-right:8rpx;padding-left:8rpx;font-size:17rpx}}
</style>
