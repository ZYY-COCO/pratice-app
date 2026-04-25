<template>
  <view class="page login-page">
    <view class="auth-hero">
      <view class="hero-badge">账户中心</view>
      <view class="hero-title">{{ heroTitle }}</view>
      <view class="hero-sub">{{ heroSubtitle }}</view>
    </view>

    <view class="segment-wrap">
      <view class="segment">
        <button class="segment-btn" :class="{ active: mode === 'login' }" @tap="switchMode('login')">登录</button>
        <button class="segment-btn" :class="{ active: mode === 'register' }" @tap="switchMode('register')">注册</button>
        <button class="segment-btn" :class="{ active: mode === 'reset' }" @tap="switchMode('reset')">找回密码</button>
      </view>
    </view>

    <view class="login-card">
      <template v-if="mode === 'login'">
        <view class="field">
          <view class="label">邮箱</view>
          <input
            v-model.trim="loginForm.email"
            class="input"
            type="text"
            placeholder="请输入已注册邮箱"
          />
        </view>

        <view class="field">
          <view class="label">密码</view>
          <input
            v-model="loginForm.password"
            class="input"
            password
            type="text"
            placeholder="请输入密码"
          />
        </view>
      </template>

      <template v-else-if="mode === 'register'">
        <view class="field">
          <view class="label">昵称</view>
          <input
            v-model.trim="registerForm.nickname"
            class="input"
            type="text"
            placeholder="请输入昵称（可选）"
          />
        </view>

        <view class="field">
          <view class="label">邮箱</view>
          <input
            v-model.trim="registerForm.email"
            class="input"
            type="text"
            placeholder="请输入可接收验证码的邮箱"
          />
        </view>

        <view class="field">
          <view class="label">验证码</view>
          <view class="code-row">
            <input
              v-model.trim="registerForm.code"
              class="input code-input"
              type="text"
              maxlength="6"
              placeholder="请输入邮箱验证码"
            />
            <button class="code-btn" :disabled="sendingCode.register" @tap="handleSendRegisterCode">
              {{ sendingCode.register ? '发送中...' : '发送验证码' }}
            </button>
          </view>
        </view>

        <view class="field">
          <view class="label">密码</view>
          <input
            v-model="registerForm.password"
            class="input"
            password
            type="text"
            placeholder="请输入至少 6 位密码"
          />
        </view>

        <view class="field">
          <view class="label">确认密码</view>
          <input
            v-model="registerForm.confirmPassword"
            class="input"
            password
            type="text"
            placeholder="请再次输入密码"
          />
        </view>

        <view class="field">
          <view class="label">目标版本</view>
          <picker :range="examLabels" :value="registerExamIndex" @change="onExamChange">
            <view class="picker-box">{{ registerForm.examTarget || '请选择目标版本' }}</view>
          </picker>
        </view>
      </template>

      <template v-else>
        <view class="field">
          <view class="label">邮箱</view>
          <input
            v-model.trim="resetForm.email"
            class="input"
            type="text"
            placeholder="请输入已注册邮箱"
          />
        </view>

        <view class="field">
          <view class="label">验证码</view>
          <view class="code-row">
            <input
              v-model.trim="resetForm.code"
              class="input code-input"
              type="text"
              maxlength="6"
              placeholder="请输入邮箱验证码"
            />
            <button class="code-btn" :disabled="sendingCode.reset" @tap="handleSendResetCode">
              {{ sendingCode.reset ? '发送中...' : '发送验证码' }}
            </button>
          </view>
        </view>

        <view class="field">
          <view class="label">新密码</view>
          <input
            v-model="resetForm.newPassword"
            class="input"
            password
            type="text"
            placeholder="请输入新密码"
          />
        </view>

        <view class="field">
          <view class="label">确认新密码</view>
          <input
            v-model="resetForm.confirmPassword"
            class="input"
            password
            type="text"
            placeholder="请再次输入新密码"
          />
        </view>
      </template>

      <button class="primary-button submit-btn" :disabled="submitting" @tap="submit">
        {{ submitButtonText }}
      </button>

      <button class="ghost-button home-btn" @tap="goBackHome">返回首页</button>
    </view>

    <view v-if="tipText" class="tip-card" :class="{ success: tipType === 'success' }">
      <view class="tip-title">{{ tipType === 'success' ? '操作结果' : '提示信息' }}</view>
      <view class="tip-text">{{ tipText }}</view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  checkBackendHealth,
  loginWithEmail,
  registerWithEmail,
  resetPasswordWithCode,
  sendRegisterCode,
  sendResetCode
} from '../../api/auth'
import { saveAuthSession } from '../../utils/auth'
import { EXAM_OPTIONS } from '../../utils/exam'

const mode = ref('login')
const submitting = ref(false)
const redirect = ref('/pages/home/index')
const tipText = ref('')
const tipType = ref('warning')
const sendingCode = reactive({
  register: false,
  reset: false
})

const loginForm = reactive({
  email: '',
  password: ''
})

const registerForm = reactive({
  nickname: '',
  email: '',
  code: '',
  password: '',
  confirmPassword: '',
  examTarget: 'Z001'
})

const resetForm = reactive({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

const examLabels = EXAM_OPTIONS.map((item) => item.title)
const registerExamIndex = computed(() =>
  Math.max(0, EXAM_OPTIONS.findIndex((item) => item.code === registerForm.examTarget))
)

const heroTitle = computed(() => {
  if (mode.value === 'register') return '创建你的刷题账号'
  if (mode.value === 'reset') return '通过邮箱找回密码'
  return '欢迎回来，继续刷题'
})

const heroSubtitle = computed(() => {
  if (mode.value === 'register') return '先接收邮箱验证码，再设置密码和目标版本。'
  if (mode.value === 'reset') return '验证邮箱后即可重新设置密码。'
  return '登录后会自动保存会话，错题本和能力报告会同步更新。'
})

const submitButtonText = computed(() => {
  if (submitting.value) {
    if (mode.value === 'login') {
      return '登录中...'
    }
    if (mode.value === 'register') {
      return '注册中...'
    }
    return '重置中...'
  }

  if (mode.value === 'login') {
    return '登录并保存会话'
  }
  if (mode.value === 'register') {
    return '验证并注册'
  }
  return '验证并重置密码'
})

onLoad((options) => {
  if (options?.redirect) {
    redirect.value = decodeURIComponent(options.redirect)
  }

  if (options?.email) {
    const email = decodeURIComponent(options.email)
    loginForm.email = email
    registerForm.email = email
    resetForm.email = email
  }

  if (options?.mode) {
    mode.value = options.mode
  }
})

function switchMode(nextMode) {
  mode.value = nextMode
  tipText.value = ''
}

function onExamChange(event) {
  const index = Number(event.detail.value)
  registerForm.examTarget = EXAM_OPTIONS[index]?.code || 'Z001'
}

function normalizeUiError(error, fallbackText) {
  const detail = error?.detail || ''

  if (!detail) {
    return fallbackText
  }

  if (detail.includes('请求超时')) {
    return '请求超时，请确认后端已启动，或稍后重试'
  }

  if (detail.includes('Failed to fetch') || detail.includes('Network Error') || detail.includes('网络请求失败')) {
    return '网络请求失败，请确认前后端服务都在运行'
  }

  if (detail.includes('Invalid email or password')) {
    return '邮箱或密码错误，请重新检查'
  }

  if (detail.includes('Send register code failed')) {
    return '发送注册验证码失败，请检查邮箱或 SMTP 配置'
  }

  if (detail.includes('Send reset code failed')) {
    return '发送重置验证码失败，请检查邮箱或 SMTP 配置'
  }

  return detail
}

async function ensureBackendAvailable() {
  try {
    await checkBackendHealth()
    return true
  } catch (error) {
    throw {
      detail: normalizeUiError(error, '后端服务不可用，请先启动 backend')
    }
  }
}

async function handleSendRegisterCode() {
  if (!registerForm.email) {
    uni.showToast({ title: '请先填写邮箱', icon: 'none' })
    return
  }

  sendingCode.register = true
  tipText.value = ''

  try {
    await ensureBackendAvailable()
    const response = await sendRegisterCode({ email: registerForm.email })
    tipType.value = 'success'
    tipText.value = response.detail || '验证码已发送，请检查邮箱。'
    uni.showToast({ title: '验证码已发送', icon: 'success' })
  } catch (error) {
    const message = normalizeUiError(error, '发送验证码失败')
    tipType.value = 'warning'
    tipText.value = message
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    sendingCode.register = false
  }
}

async function handleSendResetCode() {
  if (!resetForm.email) {
    uni.showToast({ title: '请先填写邮箱', icon: 'none' })
    return
  }

  sendingCode.reset = true
  tipText.value = ''

  try {
    await ensureBackendAvailable()
    const response = await sendResetCode({ email: resetForm.email })
    tipType.value = 'success'
    tipText.value = response.detail || '验证码已发送，请检查邮箱。'
    uni.showToast({ title: '验证码已发送', icon: 'success' })
  } catch (error) {
    const message = normalizeUiError(error, '发送验证码失败')
    tipType.value = 'warning'
    tipText.value = message
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    sendingCode.reset = false
  }
}

async function submit() {
  if (mode.value === 'login') {
    await submitLogin()
    return
  }

  if (mode.value === 'register') {
    await submitRegister()
    return
  }

  await submitResetPassword()
}

async function submitLogin() {
  if (!loginForm.email || !loginForm.password) {
    uni.showToast({ title: '请先填写邮箱和密码', icon: 'none' })
    return
  }

  submitting.value = true
  tipText.value = ''

  try {
    await ensureBackendAvailable()

    const response = await loginWithEmail({
      email: loginForm.email,
      password: loginForm.password
    })

    saveAuthSession({
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
      user: response.user
    })

    tipType.value = 'success'
    tipText.value = '登录成功，已保存登录状态。'
    uni.showToast({ title: '登录成功', icon: 'success' })

    setTimeout(() => {
      uni.redirectTo({ url: redirect.value })
    }, 200)
  } catch (error) {
    const message = normalizeUiError(error, '登录失败，请检查邮箱和密码')
    tipType.value = 'warning'
    tipText.value = message
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function submitRegister() {
  if (!registerForm.email || !registerForm.code || !registerForm.password) {
    uni.showToast({ title: '请先填写邮箱、验证码和密码', icon: 'none' })
    return
  }

  if (registerForm.password !== registerForm.confirmPassword) {
    uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
    return
  }

  submitting.value = true
  tipText.value = ''

  try {
    await ensureBackendAvailable()

    const response = await registerWithEmail({
      email: registerForm.email,
      password: registerForm.password,
      nickname: registerForm.nickname || null,
      exam_target: registerForm.examTarget,
      verification_code: registerForm.code
    })

    if (response.access_token) {
      saveAuthSession({
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        user: response.user
      })

      tipType.value = 'success'
      tipText.value = '注册成功，并已自动登录。'
      uni.showToast({ title: '注册成功', icon: 'success' })

      setTimeout(() => {
        uni.redirectTo({ url: redirect.value })
      }, 200)
      return
    }

    loginForm.email = registerForm.email
    mode.value = 'login'
    tipType.value = 'success'
    tipText.value = '注册成功，请切换到登录继续登录。'
    uni.showToast({ title: '注册成功', icon: 'success' })
  } catch (error) {
    const message = normalizeUiError(error, '注册失败，请检查验证码和邮箱')
    tipType.value = 'warning'
    tipText.value = message
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function submitResetPassword() {
  if (!resetForm.email || !resetForm.code || !resetForm.newPassword) {
    uni.showToast({ title: '请先填写邮箱、验证码和新密码', icon: 'none' })
    return
  }

  if (resetForm.newPassword !== resetForm.confirmPassword) {
    uni.showToast({ title: '两次输入的新密码不一致', icon: 'none' })
    return
  }

  submitting.value = true
  tipText.value = ''

  try {
    await ensureBackendAvailable()

    const response = await resetPasswordWithCode({
      email: resetForm.email,
      verification_code: resetForm.code,
      new_password: resetForm.newPassword
    })

    loginForm.email = resetForm.email
    mode.value = 'login'
    tipType.value = 'success'
    tipText.value = response.detail || '密码重置成功，请返回登录。'
    uni.showToast({ title: '重置成功', icon: 'success' })
  } catch (error) {
    const message = normalizeUiError(error, '密码重置失败')
    tipType.value = 'warning'
    tipText.value = message
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goBackHome() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index' })
    }
  })
}
</script>

<style scoped>
.login-page {
  padding: calc(var(--status-bar-height) + 28rpx) 24rpx calc(env(safe-area-inset-bottom) + 40rpx);
}

.auth-hero {
  padding: 34rpx 30rpx;
  border-radius: 36rpx;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(238, 244, 255, 0.96)),
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 44%);
  border: 2rpx solid rgba(219, 228, 245, 0.92);
  box-shadow: 0 20rpx 48rpx rgba(20, 31, 66, 0.08);
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: #edf3ff;
  color: #2563eb;
  font-size: 23rpx;
  font-weight: 900;
}

.hero-title {
  margin-top: 18rpx;
  color: #101828;
  font-size: 44rpx;
  line-height: 1.22;
  font-weight: 900;
}

.hero-sub {
  margin-top: 14rpx;
  color: #667085;
  font-size: 25rpx;
  line-height: 1.65;
}

.segment-wrap {
  margin-top: 22rpx;
}

.segment {
  display: flex;
  gap: 10rpx;
  padding: 10rpx;
  border-radius: 32rpx;
  background: rgba(238, 243, 255, 0.94);
  border: 2rpx solid #dbe7ff;
}

.segment-btn {
  flex: 1;
  min-height: 84rpx;
  border: 0;
  border-radius: 26rpx;
  background: transparent;
  color: #667085;
  font-size: 25rpx;
  font-weight: 900;
}

.segment-btn.active {
  background: #ffffff;
  color: #2563eb;
  box-shadow: 0 6rpx 16rpx rgba(37, 99, 235, 0.12);
}

.login-card {
  margin-top: 24rpx;
  padding: 30rpx 26rpx;
  border-radius: 36rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 18rpx 42rpx rgba(20, 31, 66, 0.06);
}

.field + .field {
  margin-top: 24rpx;
}

.label {
  color: #344054;
  font-size: 25rpx;
  font-weight: 900;
}

.input,
.picker-box {
  margin-top: 12rpx;
  min-height: 98rpx;
  padding: 0 26rpx;
  border-radius: 28rpx;
  border: 2rpx solid #dbe3f2;
  background: #fbfcff;
  font-size: 30rpx;
  color: #172033;
  display: flex;
  align-items: center;
}

.code-row {
  display: flex;
  gap: 14rpx;
  align-items: flex-end;
}

.code-input {
  flex: 1;
}

.code-btn {
  min-width: 200rpx;
  min-height: 98rpx;
  border: 0;
  border-radius: 28rpx;
  background: #edf3ff;
  color: #2563eb;
  font-size: 24rpx;
  font-weight: 900;
}

.code-btn[disabled] {
  color: #98a2b3;
}

.submit-btn {
  margin-top: 34rpx;
  min-height: 98rpx;
  border-radius: 30rpx;
  font-size: 30rpx;
}

.home-btn {
  margin-top: 16rpx;
  min-height: 92rpx;
  border-radius: 30rpx;
}

.tip-card {
  margin-top: 22rpx;
  padding: 26rpx;
  border-radius: 32rpx;
  background: #fff8eb;
  border: 2rpx solid #fde7b0;
}

.tip-card.success {
  background: #effcf4;
  border-color: #b7ebc6;
}

.tip-title {
  color: #8a5a13;
  font-size: 25rpx;
  font-weight: 900;
}

.tip-card.success .tip-title,
.tip-card.success .tip-text {
  color: #17663a;
}

.tip-text {
  margin-top: 10rpx;
  color: #8a5a13;
  font-size: 25rpx;
  line-height: 1.7;
}

@media (max-width: 380px) {
  .code-row {
    flex-direction: column;
    align-items: stretch;
  }

  .code-btn {
    width: 100%;
  }
}
</style>
