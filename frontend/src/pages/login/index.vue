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
      <view class="method-switch">
        <button class="method-btn" :class="{ active: authMethod === 'phone' }" @tap="switchAuthMethod('phone')">
          手机号
        </button>
        <button class="method-btn" :class="{ active: authMethod === 'email' }" @tap="switchAuthMethod('email')">
          邮箱
        </button>
      </view>

      <template v-if="mode === 'login'">
        <template v-if="authMethod === 'phone'">
          <view class="field">
            <view class="label">手机号</view>
            <input
              v-model.trim="phoneLoginForm.phone"
              class="input"
              type="text"
              maxlength="15"
              placeholder="请输入已注册手机号，港澳台可带区号"
            />
          </view>

          <view class="field">
            <view class="label">验证码</view>
            <view class="code-row">
              <input
                v-model.trim="phoneLoginForm.code"
                class="input code-input"
                type="text"
                maxlength="6"
                placeholder="请输入短信验证码"
              />
              <button class="code-btn" :disabled="sendingCode.phoneLogin" @tap="handleSendPhoneLoginCode">
                {{ sendingCode.phoneLogin ? '发送中...' : '发送验证码' }}
              </button>
            </view>
          </view>

          <view class="auth-note">无需密码，验证码验证后直接进入账号。</view>
        </template>

        <template v-else>
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

        <template v-if="authMethod === 'phone'">
          <view class="field">
            <view class="label">手机号</view>
            <input
              v-model.trim="phoneRegisterForm.phone"
              class="input"
              type="text"
              maxlength="15"
              placeholder="请输入手机号，港澳台可带区号"
            />
          </view>

          <view class="field">
            <view class="label">验证码</view>
            <view class="code-row">
              <input
                v-model.trim="phoneRegisterForm.code"
                class="input code-input"
                type="text"
                maxlength="6"
                placeholder="请输入短信验证码"
              />
              <button class="code-btn" :disabled="sendingCode.phoneRegister" @tap="handleSendPhoneRegisterCode">
                {{ sendingCode.phoneRegister ? '发送中...' : '发送验证码' }}
              </button>
            </view>
          </view>
        </template>

        <template v-else>
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
        </template>

        <view class="field">
          <view class="label">目标版本</view>
          <picker :range="examLabels" :value="registerExamIndex" @change="onExamChange">
            <view class="picker-box">{{ activeRegisterExamTarget || '请选择目标版本' }}</view>
          </picker>
        </view>
      </template>

      <template v-else>
        <template v-if="authMethod === 'phone'">
          <view class="field">
            <view class="label">手机号</view>
            <input
              v-model.trim="phoneResetForm.phone"
              class="input"
              type="text"
              maxlength="15"
              placeholder="请输入已注册手机号，港澳台可带区号"
            />
          </view>

          <view class="field">
            <view class="label">验证码</view>
            <view class="code-row">
              <input
                v-model.trim="phoneResetForm.code"
                class="input code-input"
                type="text"
                maxlength="6"
                placeholder="请输入短信验证码"
              />
              <button class="code-btn" :disabled="sendingCode.phoneReset" @tap="handleSendPhoneResetCode">
                {{ sendingCode.phoneReset ? '发送中...' : '发送验证码' }}
              </button>
            </view>
          </view>

          <view class="auth-note">手机号账号不需要找回密码，验证短信后会直接登录。</view>
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
      </template>

      <button class="primary-button submit-btn" :disabled="submitting" @tap="submit">
        {{ submitButtonText }}
      </button>

      <button class="wechat-button" @tap="handleWechatLogin">
        <text class="wechat-icon">微</text>
        <text>微信一键登录</text>
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
  loginWithPhone,
  loginWithWechat,
  registerWithEmail,
  registerWithPhone,
  resetPasswordWithCode,
  sendPhoneCode,
  sendRegisterCode,
  sendResetCode
} from '../../api/auth'
import { saveAuthSession } from '../../utils/auth'
import { EXAM_OPTIONS } from '../../utils/exam'

const mode = ref('login')
const authMethod = ref('phone')
const submitting = ref(false)
const redirect = ref('/pages/home/index')
const tipText = ref('')
const tipType = ref('warning')
const sendingCode = reactive({
  register: false,
  reset: false,
  phoneLogin: false,
  phoneRegister: false,
  phoneReset: false
})

const loginForm = reactive({
  email: '',
  password: ''
})

const phoneLoginForm = reactive({
  phone: '',
  code: ''
})

const registerForm = reactive({
  nickname: '',
  email: '',
  code: '',
  password: '',
  confirmPassword: '',
  examTarget: 'Z001'
})

const phoneRegisterForm = reactive({
  nickname: '',
  phone: '',
  code: '',
  examTarget: 'Z001'
})

const resetForm = reactive({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

const phoneResetForm = reactive({
  phone: '',
  code: ''
})

const examLabels = EXAM_OPTIONS.map((item) => item.title)
const registerExamIndex = computed(() =>
  Math.max(0, EXAM_OPTIONS.findIndex((item) => item.code === activeRegisterExamTarget.value))
)
const activeRegisterExamTarget = computed(() =>
  authMethod.value === 'phone' ? phoneRegisterForm.examTarget : registerForm.examTarget
)

const heroTitle = computed(() => {
  if (mode.value === 'register') return authMethod.value === 'phone' ? '手机号注册，开始刷题' : '创建邮箱刷题账号'
  if (mode.value === 'reset') return authMethod.value === 'phone' ? '验证码登录账号' : '通过邮箱找回密码'
  return authMethod.value === 'phone' ? '手机号登录，继续刷题' : '欢迎回来，继续刷题'
})

const heroSubtitle = computed(() => {
  if (mode.value === 'register') {
    return authMethod.value === 'phone'
      ? '接收短信验证码后创建账号，后续无需记密码。'
      : '先接收邮箱验证码，再设置密码和目标版本。'
  }
  if (mode.value === 'reset') {
    return authMethod.value === 'phone'
      ? '手机号账号通过验证码直接登录，不再单独找回密码。'
      : '验证邮箱后即可重新设置密码。'
  }
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
    return authMethod.value === 'phone' ? '验证码登录' : '登录并保存会话'
  }
  if (mode.value === 'register') {
    return authMethod.value === 'phone' ? '验证并创建账号' : '验证并注册'
  }
  return authMethod.value === 'phone' ? '验证并登录' : '验证并重置密码'
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

  if (options?.phone) {
    const phone = decodeURIComponent(options.phone)
    phoneLoginForm.phone = phone
    phoneRegisterForm.phone = phone
    phoneResetForm.phone = phone
  }

  if (options?.mode) {
    mode.value = options.mode
  }

  if (options?.method === 'email' || options?.method === 'phone') {
    authMethod.value = options.method
  }
})

function switchMode(nextMode) {
  mode.value = nextMode
  tipText.value = ''
}

function switchAuthMethod(nextMethod) {
  authMethod.value = nextMethod
  tipText.value = ''
}

function onExamChange(event) {
  const index = Number(event.detail.value)
  const examTarget = EXAM_OPTIONS[index]?.code || 'Z001'
  if (authMethod.value === 'phone') {
    phoneRegisterForm.examTarget = examTarget
    return
  }
  registerForm.examTarget = examTarget
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

  if (detail.includes('Invalid phone number')) {
    return '手机号格式不正确，请检查后重试'
  }

  if (detail.includes('Phone already registered')) {
    return '该手机号已注册，请切换到登录'
  }

  if (detail.includes('Phone not registered')) {
    return '该手机号尚未注册，请先注册'
  }

  if (detail.includes('Invalid verification code')) {
    return '验证码不正确，请重新输入'
  }

  if (detail.includes('Verification code expired')) {
    return '验证码已过期，请重新发送'
  }

  if (detail.includes('SMS provider is not configured')) {
    return '短信通道还没有配置，先在后端配置短信服务后再使用手机号登录'
  }

  if (detail.includes('WeChat login requires')) {
    return '微信登录需要配置正式域名、HTTPS 和微信开放平台参数，当前先保留入口'
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

async function sendPhoneVerificationCode(form, purpose, sendingKey) {
  if (!form.phone) {
    uni.showToast({ title: '请先填写手机号', icon: 'none' })
    return
  }

  sendingCode[sendingKey] = true
  tipText.value = ''

  try {
    await ensureBackendAvailable()
    const response = await sendPhoneCode({
      phone: form.phone,
      purpose
    })
    tipType.value = 'success'
    tipText.value = response.debug_code
      ? `测试验证码：${response.debug_code}`
      : response.detail || '验证码已发送，请查看短信。'
    uni.showToast({ title: '验证码已发送', icon: 'success' })
  } catch (error) {
    const message = normalizeUiError(error, '发送验证码失败')
    tipType.value = 'warning'
    tipText.value = message
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    sendingCode[sendingKey] = false
  }
}

function handleSendPhoneLoginCode() {
  return sendPhoneVerificationCode(phoneLoginForm, 'login', 'phoneLogin')
}

function handleSendPhoneRegisterCode() {
  return sendPhoneVerificationCode(phoneRegisterForm, 'register', 'phoneRegister')
}

function handleSendPhoneResetCode() {
  return sendPhoneVerificationCode(phoneResetForm, 'login', 'phoneReset')
}

async function submit() {
  if (mode.value === 'login') {
    if (authMethod.value === 'phone') {
      await submitPhoneLogin(phoneLoginForm)
      return
    }
    await submitLogin()
    return
  }

  if (mode.value === 'register') {
    if (authMethod.value === 'phone') {
      await submitPhoneRegister()
      return
    }
    await submitRegister()
    return
  }

  if (authMethod.value === 'phone') {
    await submitPhoneLogin(phoneResetForm)
    return
  }
  await submitResetPassword()
}

function saveSessionAndRedirect(response, successText) {
  saveAuthSession({
    accessToken: response.access_token,
    refreshToken: response.refresh_token,
    user: response.user
  })

  tipType.value = 'success'
  tipText.value = successText
  uni.showToast({ title: successText, icon: 'success' })

  setTimeout(() => {
    uni.redirectTo({ url: redirect.value })
  }, 200)
}

async function submitPhoneLogin(form) {
  if (!form.phone || !form.code) {
    uni.showToast({ title: '请先填写手机号和验证码', icon: 'none' })
    return
  }

  submitting.value = true
  tipText.value = ''

  try {
    await ensureBackendAvailable()
    const response = await loginWithPhone({
      phone: form.phone,
      verification_code: form.code
    })
    saveSessionAndRedirect(response, '登录成功')
  } catch (error) {
    const message = normalizeUiError(error, '手机号登录失败')
    tipType.value = 'warning'
    tipText.value = message
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function submitPhoneRegister() {
  if (!phoneRegisterForm.phone || !phoneRegisterForm.code) {
    uni.showToast({ title: '请先填写手机号和验证码', icon: 'none' })
    return
  }

  submitting.value = true
  tipText.value = ''

  try {
    await ensureBackendAvailable()
    const response = await registerWithPhone({
      phone: phoneRegisterForm.phone,
      verification_code: phoneRegisterForm.code,
      nickname: registerForm.nickname || null,
      exam_target: phoneRegisterForm.examTarget
    })
    saveSessionAndRedirect(response, '注册成功')
  } catch (error) {
    const message = normalizeUiError(error, '手机号注册失败')
    tipType.value = 'warning'
    tipText.value = message
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    submitting.value = false
  }
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

async function handleWechatLogin() {
  submitting.value = true
  tipText.value = ''

  try {
    await ensureBackendAvailable()
    const response = await loginWithWechat({})
    saveSessionAndRedirect(response, '微信登录成功')
  } catch (error) {
    const message = normalizeUiError(error, '微信登录暂未开放')
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
  min-height: 100vh;
  min-height: 100dvh;
  padding: calc(var(--status-bar-height) + 22rpx) 30rpx calc(env(safe-area-inset-bottom) + 44rpx);
  background:
    radial-gradient(circle at top right, rgba(22, 119, 255, 0.08), transparent 28%),
    linear-gradient(180deg, #f8fbff 0%, #f2f6fc 100%);
}

.login-page view,
.login-page input,
.login-page button {
  box-sizing: border-box;
}

.login-page button::after {
  border: 0;
}

.auth-hero {
  padding: 34rpx 32rpx 32rpx;
  border-radius: 34rpx;
  background:
    radial-gradient(circle at 88% 18%, rgba(37, 99, 235, 0.13), transparent 32%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(241, 246, 255, 0.98));
  border: 2rpx solid rgba(219, 228, 245, 0.92);
  box-shadow: 0 18rpx 44rpx rgba(20, 31, 66, 0.07);
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 9rpx 16rpx;
  border-radius: 999rpx;
  background: #edf3ff;
  color: #2563eb;
  font-size: 22rpx;
  font-weight: 900;
}

.hero-title {
  margin-top: 18rpx;
  color: #101828;
  font-size: 42rpx;
  line-height: 1.22;
  font-weight: 900;
}

.hero-sub {
  margin-top: 12rpx;
  color: #667085;
  font-size: 25rpx;
  line-height: 1.55;
}

.segment-wrap {
  margin-top: 22rpx;
}

.segment {
  display: flex;
  gap: 8rpx;
  padding: 8rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid #e8eef8;
  box-shadow: 0 10rpx 26rpx rgba(20, 31, 66, 0.05);
}

.segment-btn {
  flex: 1;
  min-height: 72rpx;
  border: 0;
  border-radius: 22rpx;
  background: transparent;
  color: #667085;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 72rpx;
  padding: 0;
}

.segment-btn.active {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #ffffff;
  box-shadow: 0 10rpx 22rpx rgba(37, 99, 235, 0.2);
}

.login-card {
  margin-top: 22rpx;
  padding: 30rpx 28rpx;
  border-radius: 34rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 18rpx 44rpx rgba(20, 31, 66, 0.07);
}

.method-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10rpx;
  margin-bottom: 26rpx;
  padding: 8rpx;
  border-radius: 24rpx;
  background: #f5f8ff;
  border: 2rpx solid #e6ebf5;
}

.method-btn {
  min-height: 68rpx;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #667085;
  font-size: 24rpx;
  line-height: 68rpx;
  font-weight: 900;
  padding: 0;
}

.method-btn.active {
  background: #ffffff;
  color: #2563eb;
  box-shadow: 0 8rpx 20rpx rgba(20, 31, 66, 0.08);
}

.field + .field {
  margin-top: 22rpx;
}

.label {
  color: #344054;
  font-size: 24rpx;
  font-weight: 900;
}

.input,
.picker-box {
  margin-top: 12rpx;
  min-height: 92rpx;
  padding: 0 26rpx;
  border-radius: 24rpx;
  border: 2rpx solid #dbe3f2;
  background: #f8fbff;
  font-size: 28rpx;
  color: #172033;
  display: flex;
  align-items: center;
}

.code-row {
  display: flex;
  gap: 16rpx;
  align-items: stretch;
}

.code-input {
  flex: 1;
}

.code-btn {
  min-width: 190rpx;
  min-height: 92rpx;
  border: 0;
  border-radius: 24rpx;
  background: #eaf2ff;
  color: #1677ff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 92rpx;
  padding: 0 18rpx;
}

.code-btn[disabled] {
  color: #98a2b3;
}

.auth-note {
  margin-top: 18rpx;
  padding: 18rpx 20rpx;
  border-radius: 22rpx;
  background: #f7fbff;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.55;
}

.submit-btn {
  margin-top: 32rpx;
  min-height: 96rpx;
  border-radius: 28rpx;
  font-size: 30rpx;
  line-height: 96rpx;
}

.wechat-button {
  margin-top: 16rpx;
  min-height: 88rpx;
  border: 0;
  border-radius: 26rpx;
  background: #eefbf3;
  color: #138a43;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
}

.wechat-icon {
  width: 42rpx;
  height: 42rpx;
  border-radius: 50%;
  background: #16a34a;
  color: #ffffff;
  font-size: 22rpx;
  line-height: 42rpx;
  text-align: center;
}

.home-btn {
  margin-top: 16rpx;
  min-height: 88rpx;
  border-radius: 26rpx;
  line-height: 88rpx;
}

.tip-card {
  margin-top: 22rpx;
  padding: 26rpx;
  border-radius: 28rpx;
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
