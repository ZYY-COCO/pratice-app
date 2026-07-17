<template>
  <view class="page profile-edit-page" :style="themeInlineStyle">
    <view class="profile-card">
      <image
        v-if="isImageAvatar(form.avatar_url)"
        class="avatar-preview avatar-preview-image"
        :src="form.avatar_url"
        mode="aspectFill"
        alt="用户头像"
      />
      <view v-else class="avatar-preview">{{ avatarText }}</view>
      <view class="profile-card-copy">
        <view class="profile-name">{{ profileName }}</view>
        <view class="profile-email">{{ profileContact }}</view>
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
            @tap="selectAvatarOption(item)"
          >
            {{ item }}
          </button>
          <button
            class="avatar-option upload-avatar-option"
            :class="{ active: isImageAvatar(form.avatar_url) }"
            :disabled="uploadingAvatar"
            aria-label="从相册选择头像"
            @tap="chooseAvatarImage"
          >
            <text class="avatar-upload-plus">{{ uploadingAvatar ? '…' : '+' }}</text>
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

      <view class="save-hint">{{ hasProfileChanges ? '保存后会自动返回“我的”页面。' : '当前资料已同步。' }}</view>
      <button class="primary-button save-btn" :disabled="savingProfile || !canSaveProfile" @tap="saveProfile">
        {{ savingProfile ? '保存中...' : hasProfileChanges ? '保存资料' : '暂无修改' }}
      </button>
    </SectionCard>

    <SectionCard title="绑定 / 更改 QQ 邮箱" :subtitle="emailSectionSubtitle">
      <view class="current-email">当前邮箱：{{ currentEmailText }}</view>
      <!-- #ifdef MP-WEIXIN -->
      <view v-if="isWechatBindingFlow" class="binding-rule">
        未注册邮箱可直接绑定；已注册邮箱需要确认合并，并选择保留微信或邮箱账号资料。
      </view>
      <!-- #endif -->
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
        {{ bindingEmail ? (isWechatBindingFlow ? '处理中...' : '换绑中...') : isWechatBindingFlow ? '确认绑定 / 检查合并' : '确认换绑' }}
      </button>

      <!-- #ifdef MP-WEIXIN -->
      <view v-if="canUnbindWechat" class="unbind-panel">
        <view class="unbind-title">解除微信绑定</view>
        <view class="unbind-copy">
          解绑后将不能再用当前微信进入此邮箱账号，请先确认可以通过邮箱找回密码。
        </view>
        <view class="code-row">
          <input
            v-model.trim="unbindForm.code"
            class="input code-input"
            type="text"
            maxlength="8"
            placeholder="当前邮箱验证码"
          />
          <button class="code-btn" :disabled="sendingUnbindCode" @tap="sendWechatUnbindCode">
            {{ sendingUnbindCode ? '发送中...' : '发送解绑码' }}
          </button>
        </view>
        <button class="unbind-button" :disabled="unbindingWechat" @tap="confirmWechatUnbind">
          {{ unbindingWechat ? '解绑中...' : '解除当前微信绑定' }}
        </button>
      </view>
      <!-- #endif -->
    </SectionCard>

    <SectionCard title="账号安全" subtitle="删除账号后将无法恢复当前学习数据。">
      <view class="danger-copy">
        删除账号会清除登录身份，并删除与该账号关联的刷题记录、错题、收藏和学习统计。
      </view>
      <button class="danger-button" :disabled="deletingAccount" @tap="confirmDeleteAccount">
        {{ deletingAccount ? '删除中...' : '删除账号' }}
      </button>
    </SectionCard>

    <!-- #ifdef H5 -->
    <IcpFooter />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import IcpFooter from '../../components/IcpFooter.vue'
import SectionCard from '../../components/SectionCard.vue'
import {
  bindWechatEmail,
  changeEmailWithCode,
  deleteAccount,
  sendBindEmailCode,
  sendChangeEmailCode,
  sendUnbindWechatCode,
  unbindWechat,
  updateProfile,
  uploadAvatar
} from '../../api/auth'
import { clearAuthSession, getAuthUser, saveAuthSession, updateAuthUser } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'
import { getPublicEmail, getUserContactLabel, getUserDisplayName } from '../../utils/userDisplay'
import { requireWechatPrivacyAuthorization } from '../../utils/wechatPrivacy'

const avatarOptions = ['测', '学', '研', '文', '英', '数', 'AI']
const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const genderOptions = [
  { label: '男', value: 'male' },
  { label: '女', value: 'female' }
]

const user = ref(getAuthUser() || {})
let IS_MP_WEIXIN = false
// #ifdef MP-WEIXIN
IS_MP_WEIXIN = true
// #endif
const savingProfile = ref(false)
const sendingCode = ref(false)
const bindingEmail = ref(false)
const sendingUnbindCode = ref(false)
const unbindingWechat = ref(false)
const deletingAccount = ref(false)
const uploadingAvatar = ref(false)
const form = reactive({
  nickname: '',
  avatar_url: '',
  gender: ''
})
const emailForm = reactive({
  email: '',
  code: ''
})
const unbindForm = reactive({
  code: ''
})

const profileName = computed(() => form.nickname || getUserDisplayName(user.value, '用户'))
const profileContact = computed(() => getUserContactLabel(user.value, '未绑定账号'))
const currentPublicEmail = computed(() => getPublicEmail(user.value) || '')
const currentEmailText = computed(() => currentPublicEmail.value || '未绑定')
const isWechatBindingFlow = computed(() => Boolean(IS_MP_WEIXIN && user.value?.wechat_openid))
const canUnbindWechat = computed(() => Boolean(isWechatBindingFlow.value && currentPublicEmail.value))
const emailSectionSubtitle = computed(() => (
  isWechatBindingFlow.value
    ? '微信用户验证邮箱后可直接绑定，或安全合并已有邮箱账号。'
    : '手机号账号也可以额外绑定邮箱，验证码验证后生效。'
))
const avatarText = computed(() => (form.avatar_url || profileName.value || '用').slice(0, 1))
const initialProfile = ref({
  nickname: '',
  avatar_url: '',
  gender: ''
})
const hasProfileChanges = computed(() =>
  form.nickname !== initialProfile.value.nickname ||
  form.avatar_url !== initialProfile.value.avatar_url ||
  form.gender !== initialProfile.value.gender
)
const canSaveProfile = computed(() => Boolean(form.nickname && hasProfileChanges.value))

onShow(() => {
  user.value = getAuthUser() || {}
  form.nickname = user.value.nickname || ''
  form.avatar_url = user.value.avatar_url || ''
  form.gender = user.value.gender || ''
  initialProfile.value = {
    nickname: form.nickname,
    avatar_url: form.avatar_url,
    gender: form.gender
  }
})

function isImageAvatar(value) {
  const avatar = String(value || '')
  return avatar.startsWith('http://') || avatar.startsWith('https://') || avatar.startsWith('data:image')
}

function selectAvatarOption(item) {
  form.avatar_url = item
}

async function chooseAvatarImage() {
  if (uploadingAvatar.value) return

  try {
    await requireWechatPrivacyAuthorization()
  } catch (error) {
    uni.showToast({ title: error?.detail || '需要同意隐私保护指引后才能选择头像', icon: 'none' })
    return
  }

  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album'],
    success(result) {
      const selected = result.tempFiles?.[0]
      const filePath = result.tempFilePaths?.[0] || selected?.path || ''
      const browserFile =
        selected?.file ||
        (typeof File !== 'undefined' && selected instanceof File ? selected : null)

      if (!filePath && !browserFile) {
        uni.showToast({ title: '未读取到所选图片', icon: 'none' })
        return
      }

      uploadSelectedAvatar({
        filePath,
        file: browserFile,
        fileName: selected?.name || browserFile?.name || 'avatar'
      })
    },
    fail(error) {
      const message = error?.errMsg || ''
      if (message.toLowerCase().includes('cancel')) return
      uni.showModal({
        title: '无法访问相册',
        content: '请在系统设置中允许港研通访问照片，然后重新选择头像。',
        showCancel: false,
        confirmText: '我知道了'
      })
    }
  })
}

async function uploadSelectedAvatar(fileInfo) {
  uploadingAvatar.value = true
  try {
    const nextUser = await uploadAvatar(fileInfo)
    updateAuthUser(nextUser)
    user.value = getAuthUser() || nextUser
    form.avatar_url = nextUser.avatar_url || ''
    initialProfile.value.avatar_url = form.avatar_url
    uni.showToast({ title: '头像已更换', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '头像上传失败，请稍后重试', icon: 'none' })
  } finally {
    uploadingAvatar.value = false
  }
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

async function saveProfile() {
  if (!hasProfileChanges.value) {
    uni.showToast({ title: '暂无修改', icon: 'none' })
    return
  }
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
    initialProfile.value = {
      nickname: form.nickname,
      avatar_url: form.avatar_url,
      gender: form.gender
    }
    uni.navigateBack({
      success() {
        setTimeout(() => {
          uni.showToast({ title: '保存成功', icon: 'success' })
        }, 180)
      },
      fail() {
        uni.reLaunch({
          url: '/pages/home/index',
          success() {
            setTimeout(() => {
              uni.showToast({ title: '保存成功', icon: 'success' })
            }, 180)
          }
        })
      }
    })
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
  if (emailForm.email === getPublicEmail(user.value)) {
    uni.showToast({ title: '新邮箱不能与当前邮箱相同', icon: 'none' })
    return
  }

  sendingCode.value = true
  try {
    if (isWechatBindingFlow.value) {
      await sendBindEmailCode({ email: emailForm.email })
    } else {
      await sendChangeEmailCode({ email: emailForm.email })
    }
    uni.showToast({ title: '验证码已发送', icon: 'none' })
  } catch (error) {
    showEmailBindingError(error, '验证码发送失败')
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
    if (isWechatBindingFlow.value) {
      let result = await bindWechatEmail({
        email: emailForm.email,
        verification_code: emailForm.code
      })

      if (result?.status === 'merge_required') {
        const profileSource = await chooseMergeProfileSource(result)
        if (!profileSource) {
          uni.showToast({ title: '已取消账号合并', icon: 'none' })
          return
        }
        result = await bindWechatEmail({
          email: emailForm.email,
          verification_code: emailForm.code,
          profile_source: profileSource
        })
      }

      applyAuthResult(result?.auth)
      uni.showToast({ title: result?.detail || '邮箱绑定成功', icon: 'success' })
    } else {
      const nextUser = await changeEmailWithCode({
        email: emailForm.email,
        verification_code: emailForm.code
      })
      updateAuthUser(nextUser)
      user.value = getAuthUser() || nextUser
      uni.showToast({ title: '绑定邮箱已更新', icon: 'none' })
    }

    emailForm.email = ''
    emailForm.code = ''
  } catch (error) {
    showEmailBindingError(error, '绑定失败，请检查验证码')
  } finally {
    bindingEmail.value = false
  }
}

function applyAuthResult(auth) {
  if (!auth?.access_token || !auth?.user) {
    throw { detail: '账号会话更新失败，请重新登录' }
  }
  saveAuthSession({
    accessToken: auth.access_token,
    refreshToken: auth.refresh_token,
    user: auth.user
  })
  user.value = auth.user
  form.nickname = auth.user.nickname || ''
  form.avatar_url = auth.user.avatar_url || ''
  form.gender = auth.user.gender || ''
  initialProfile.value = {
    nickname: form.nickname,
    avatar_url: form.avatar_url,
    gender: form.gender
  }
}

function chooseMergeProfileSource(result) {
  const emailNickname = result?.email_account?.nickname || '邮箱账号'
  const wechatNickname = result?.wechat_account?.nickname || '微信账号'
  const maskedEmail = result?.email_account?.email_masked || emailForm.email

  return new Promise((resolve) => {
    uni.showModal({
      title: '发现已注册邮箱账号',
      content: `${maskedEmail} 已注册。合并后两边的作答、错题、收藏和统计都会保留，是否继续？`,
      confirmText: '继续合并',
      cancelText: '暂不合并',
      success(modalResult) {
        if (!modalResult.confirm) {
          resolve(null)
          return
        }
        uni.showActionSheet({
          title: '选择合并后使用的账号资料',
          itemList: [
            `保留微信资料（${wechatNickname}）`,
            `保留邮箱资料（${emailNickname}）`
          ],
          success(actionResult) {
            resolve(actionResult.tapIndex === 0 ? 'wechat' : 'email')
          },
          fail() {
            resolve(null)
          }
        })
      },
      fail() {
        resolve(null)
      }
    })
  })
}

function showEmailBindingError(error, fallback) {
  const message = error?.detail || fallback
  if (message.includes('已绑定其他微信账号')) {
    uni.showModal({
      title: '该邮箱已被绑定',
      content: '该邮箱已经绑定其他微信账号，请先登录原账号，在个人资料中解除微信绑定。',
      showCancel: false,
      confirmText: '我知道了'
    })
    return
  }
  uni.showToast({ title: message, icon: 'none' })
}

async function sendWechatUnbindCode() {
  sendingUnbindCode.value = true
  try {
    await sendUnbindWechatCode()
    uni.showToast({ title: '解绑验证码已发送', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '解绑验证码发送失败', icon: 'none' })
  } finally {
    sendingUnbindCode.value = false
  }
}

function confirmWechatUnbind() {
  if (!unbindForm.code) {
    uni.showToast({ title: '请填写当前邮箱收到的验证码', icon: 'none' })
    return
  }

  uni.showModal({
    title: '确认解除微信绑定？',
    content: '解绑后不能再使用当前微信进入此邮箱账号。请确认你可以通过邮箱登录或找回密码。',
    confirmText: '确认解绑',
    cancelText: '取消',
    success(result) {
      if (result.confirm) {
        unbindCurrentWechat()
      }
    }
  })
}

async function unbindCurrentWechat() {
  unbindingWechat.value = true
  try {
    const nextUser = await unbindWechat({ verification_code: unbindForm.code })
    updateAuthUser(nextUser)
    user.value = getAuthUser() || nextUser
    unbindForm.code = ''
    uni.showToast({ title: '微信绑定已解除', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '解除微信绑定失败', icon: 'none' })
  } finally {
    unbindingWechat.value = false
  }
}

function confirmDeleteAccount() {
  if (deletingAccount.value) return
  uni.showModal({
    title: '确认删除账号？',
    content: '删除后将无法登录该账号，也无法恢复刷题记录、错题、收藏和学习统计。',
    confirmText: '删除账号',
    cancelText: '取消',
    confirmColor: '#ef4444',
    success(result) {
      if (result.confirm) {
        deleteCurrentAccount()
      }
    }
  })
}

async function deleteCurrentAccount() {
  deletingAccount.value = true
  try {
    await deleteAccount()
    clearAuthSession()
    user.value = {}
    uni.reLaunch({
      url: '/pages/home/index',
      success() {
        setTimeout(() => {
          uni.showToast({ title: '账号已删除', icon: 'none' })
        }, 180)
      }
    })
  } catch (error) {
    uni.showToast({ title: error?.detail || '删除失败，请稍后重试', icon: 'none' })
  } finally {
    deletingAccount.value = false
  }
}
</script>

<style scoped>
.profile-edit-page {
  padding-bottom: calc(env(safe-area-inset-bottom) + 44rpx);
  background:
    linear-gradient(180deg, rgba(232, 240, 255, 0.86), rgba(246, 248, 252, 0.98) 34%, #f6f8fc 100%);
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 22rpx;
  padding: 30rpx;
  margin-bottom: 22rpx;
  border-radius: 34rpx;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 255, 0.96));
  border: 2rpx solid #e8effc;
  box-shadow: 0 16rpx 42rpx rgba(25, 48, 89, 0.08);
}

.avatar-preview {
  width: 112rpx;
  height: 112rpx;
  flex: 0 0 112rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--gyt-primary), var(--gyt-primary));
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38rpx;
  font-weight: 950;
  box-shadow: 0 14rpx 26rpx var(--gyt-primary-shadow);
}

.avatar-preview-image {
  display: block;
  object-fit: cover;
  background: #ffffff;
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

.binding-rule {
  margin-top: 16rpx;
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: var(--gyt-primary-tint);
  color: #667085;
  font-size: 22rpx;
  line-height: 1.55;
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
  border: 2rpx solid var(--gyt-primary-border);
  border-radius: 24rpx;
  background: var(--gyt-primary-tint);
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
  border: 2rpx solid var(--gyt-primary-border);
  border-radius: 22rpx;
  background: #ffffff;
  color: #475467;
  font-size: 25rpx;
  line-height: 80rpx;
  font-weight: 900;
}

.avatar-option.active,
.choice-btn.active {
  border-color: var(--gyt-primary);
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  box-shadow: 0 8rpx 18rpx var(--gyt-primary-shadow);
}

.upload-avatar-option {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.upload-avatar-option[disabled] {
  opacity: 0.6;
}

.avatar-upload-plus {
  color: var(--gyt-primary);
  font-size: 46rpx;
  line-height: 1;
  font-weight: 500;
}

.save-hint {
  margin-top: 24rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.45;
  font-weight: 650;
}

.save-btn,
.bind-btn {
  margin-top: 18rpx;
}

.unbind-panel {
  margin-top: 28rpx;
  padding-top: 26rpx;
  border-top: 2rpx solid #edf1f7;
}

.unbind-title {
  color: #344054;
  font-size: 25rpx;
  line-height: 1.4;
  font-weight: 900;
}

.unbind-copy {
  margin-top: 8rpx;
  color: #7f8ba3;
  font-size: 22rpx;
  line-height: 1.55;
  font-weight: 650;
}

.unbind-button {
  width: 100%;
  min-height: 82rpx;
  margin-top: 16rpx;
  border: 2rpx solid #fecaca;
  border-radius: 24rpx;
  background: #fff7f7;
  color: #b42318;
  font-size: 25rpx;
  line-height: 82rpx;
  font-weight: 900;
}

.unbind-button[disabled] {
  opacity: 0.6;
}
.save-btn:disabled {
  background: #d9e2f1;
  color: #8a95a8;
  box-shadow: none;
}

.danger-copy {
  color: #667085;
  font-size: 24rpx;
  line-height: 1.65;
  font-weight: 650;
}

.danger-button {
  margin-top: 22rpx;
  width: 100%;
  min-height: 92rpx;
  border: 2rpx solid #fecaca;
  border-radius: 28rpx;
  background: #fff1f2;
  color: #b42318;
  font-size: 28rpx;
  line-height: 92rpx;
  font-weight: 900;
}

.danger-button[disabled] {
  opacity: 0.6;
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
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 24rpx;
  line-height: 92rpx;
  font-weight: 900;
}

.code-btn:disabled {
  background: #eef2f7;
  color: #98a2b3;
}
</style>
