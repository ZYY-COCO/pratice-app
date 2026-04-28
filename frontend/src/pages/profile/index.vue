<template>
  <view class="page profile-edit-page">
    <view class="profile-edit-head">
      <button class="back-btn" @tap="goBack">‹</button>
      <view>
        <view class="head-title">个人资料</view>
        <view class="head-subtitle">修改昵称、头像样式、性别和绑定邮箱</view>
      </view>
    </view>

    <view class="profile-card">
      <view class="avatar-preview">{{ form.avatar_url || avatarText }}</view>
      <view class="profile-card-copy">
        <view class="profile-name">{{ form.nickname || user.email || '用户' }}</view>
        <view class="profile-email">{{ user.email || '未绑定邮箱' }}</view>
      </view>
    </view>

    <SectionCard title="基础资料" subtitle="保存后会同步到“我的”页面。">
      <view class="field">
        <view class="label">昵称</view>
        <input v-model.trim="form.nickname" class="input" type="text" maxlength="40" placeholder="请输入昵称" />
      </view>

      <view class="field">
        <view class="label">头像样式</view>
        <view class="avatar-grid">
          <button
            v-for="item in avatarOptions"
            :key="item"
            class="avatar-option"
            :class="{ active: form.avatar_url === item }"
            @tap="form.avatar_url = item"
          >
            {{ item }}
          </button>
        </view>
      </view>

      <view class="field">
        <view class="label">性别</view>
        <view class="gender-row">
          <button
            v-for="item in genderOptions"
            :key="item.value"
            class="choice-btn"
            :class="{ active: form.gender === item.value }"
            @tap="form.gender = item.value"
          >
            {{ item.label }}
          </button>
        </view>
      </view>

      <button class="primary-button save-btn" :disabled="savingProfile" @tap="saveProfile">
        {{ savingProfile ? '保存中...' : '保存资料' }}
      </button>
    </SectionCard>

    <SectionCard title="更改绑定 QQ 邮箱" subtitle="验证码会发送到新的邮箱，验证后完成换绑。">
      <view class="current-email">当前邮箱：{{ user.email || '未绑定' }}</view>
      <view class="field">
        <view class="label">新 QQ 邮箱</view>
        <input v-model.trim="emailForm.email" class="input" type="text" placeholder="例如：123456@qq.com" />
      </view>
      <view class="field">
        <view class="label">验证码</view>
        <view class="code-row">
          <input v-model.trim="emailForm.code" class="input code-input" type="text" maxlength="8" placeholder="请输入验证码" />
          <button class="code-btn" :disabled="sendingCode" @tap="sendEmailCode">
            {{ sendingCode ? '发送中...' : '发送验证码' }}
          </button>
        </view>
      </view>
      <button class="ghost-button bind-btn" :disabled="bindingEmail" @tap="bindEmail">
        {{ bindingEmail ? '换绑中...' : '确认换绑' }}
      </button>
    </SectionCard>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import SectionCard from '../../components/SectionCard.vue'
import { changeEmailWithCode, sendChangeEmailCode, updateProfile } from '../../api/auth'
import { getAuthUser, updateAuthUser } from '../../utils/auth'

const avatarOptions = ['测', '学', '研', '文', '英', '数', 'AI', 'Pro']
const genderOptions = [
  { label: '男', value: 'male' },
  { label: '女', value: 'female' }
]

const user = ref(getAuthUser() || {})
const savingProfile = ref(false)
const sendingCode = ref(false)
const bindingEmail = ref(false)
const form = reactive({
  nickname: '',
  avatar_url: '',
  gender: ''
})
const emailForm = reactive({
  email: '',
  code: ''
})

const avatarText = computed(() => (form.nickname || user.value?.email || '用').slice(0, 1))

onShow(() => {
  user.value = getAuthUser() || {}
  form.nickname = user.value.nickname || ''
  form.avatar_url = user.value.avatar_url || ''
  form.gender = user.value.gender || ''
})

function goBack() {
  uni.navigateBack()
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

async function saveProfile() {
  if (!form.nickname) {
    uni.showToast({ title: '请填写昵称', icon: 'none' })
    return
  }

  savingProfile.value = true
  try {
    const nextUser = await updateProfile({
      nickname: form.nickname,
      avatar_url: form.avatar_url || null,
      gender: form.gender || null
    })
    updateAuthUser(nextUser)
    user.value = getAuthUser() || nextUser
    uni.showToast({ title: '资料已保存', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '保存失败，请稍后重试', icon: 'none' })
  } finally {
    savingProfile.value = false
  }
}

async function sendEmailCode() {
  if (!emailForm.email || !isValidEmail(emailForm.email)) {
    uni.showToast({ title: '请填写正确的新邮箱', icon: 'none' })
    return
  }
  if (emailForm.email === user.value.email) {
    uni.showToast({ title: '新邮箱不能与当前邮箱相同', icon: 'none' })
    return
  }

  sendingCode.value = true
  try {
    await sendChangeEmailCode({ email: emailForm.email })
    uni.showToast({ title: '验证码已发送', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '验证码发送失败', icon: 'none' })
  } finally {
    sendingCode.value = false
  }
}

async function bindEmail() {
  if (!emailForm.email || !emailForm.code) {
    uni.showToast({ title: '请填写邮箱和验证码', icon: 'none' })
    return
  }

  bindingEmail.value = true
  try {
    const nextUser = await changeEmailWithCode({
      email: emailForm.email,
      verification_code: emailForm.code
    })
    updateAuthUser(nextUser)
    user.value = getAuthUser() || nextUser
    emailForm.email = ''
    emailForm.code = ''
    uni.showToast({ title: '绑定邮箱已更新', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '换绑失败，请检查验证码', icon: 'none' })
  } finally {
    bindingEmail.value = false
  }
}
</script>

<style scoped>
.profile-edit-page {
  padding-bottom: calc(env(safe-area-inset-bottom) + 44rpx);
}

.profile-edit-head {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-bottom: 22rpx;
}

.back-btn {
  width: 72rpx;
  height: 72rpx;
  flex: 0 0 72rpx;
  margin: 0;
  border: 0;
  border-radius: 24rpx;
  background: #ffffff;
  color: #172033;
  font-size: 42rpx;
  line-height: 72rpx;
  box-shadow: 0 10rpx 26rpx rgba(20, 31, 66, 0.06);
}

.head-title {
  color: #101828;
  font-size: 38rpx;
  line-height: 1.25;
  font-weight: 950;
}

.head-subtitle {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.45;
  font-weight: 650;
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 22rpx;
  padding: 28rpx;
  margin-bottom: 20rpx;
  border-radius: 34rpx;
  background: #ffffff;
  border: 2rpx solid #e8effc;
  box-shadow: 0 16rpx 42rpx rgba(25, 48, 89, 0.08);
}

.avatar-preview {
  width: 112rpx;
  height: 112rpx;
  flex: 0 0 112rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #4f7dff, #87aaff);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38rpx;
  font-weight: 950;
  box-shadow: 0 14rpx 26rpx rgba(37, 99, 235, 0.22);
}

.profile-card-copy {
  flex: 1;
  min-width: 0;
}

.profile-name {
  color: #101828;
  font-size: 34rpx;
  line-height: 1.3;
  font-weight: 950;
}

.profile-email,
.current-email {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.45;
  font-weight: 650;
}

.field {
  margin-top: 22rpx;
}

.label {
  color: #344054;
  font-size: 24rpx;
  line-height: 1.35;
  font-weight: 850;
}

.input {
  margin-top: 14rpx;
  width: 100%;
  min-height: 92rpx;
  padding: 0 24rpx;
  border: 2rpx solid #dbe3f2;
  border-radius: 24rpx;
  background: #f8fbff;
  color: #172033;
  font-size: 26rpx;
  box-sizing: border-box;
}

.avatar-grid,
.gender-row {
  margin-top: 14rpx;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14rpx;
}

.gender-row {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.avatar-option,
.choice-btn {
  min-height: 80rpx;
  margin: 0;
  border: 2rpx solid #dbe4f5;
  border-radius: 22rpx;
  background: #ffffff;
  color: #475467;
  font-size: 25rpx;
  line-height: 80rpx;
  font-weight: 900;
}

.avatar-option.active,
.choice-btn.active {
  border-color: #2563eb;
  background: #edf3ff;
  color: #2563eb;
  box-shadow: 0 8rpx 18rpx rgba(37, 99, 235, 0.12);
}

.save-btn,
.bind-btn {
  margin-top: 26rpx;
}

.code-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.code-input {
  flex: 1;
  min-width: 0;
}

.code-btn {
  width: 190rpx;
  min-height: 92rpx;
  margin: 14rpx 0 0;
  border: 0;
  border-radius: 24rpx;
  background: #edf3ff;
  color: #2563eb;
  font-size: 24rpx;
  line-height: 92rpx;
  font-weight: 900;
}

.code-btn:disabled {
  background: #eef2f7;
  color: #98a2b3;
}
</style>
