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
        <button class="method-btn" :class="{ active: authMethod === 'email' }" @tap="switchAuthMethod('email')">
          <text class="method-label">邮箱</text>
        </button>
        <button class="method-btn disabled" @tap="switchAuthMethod('phone')">
          <text class="method-label">手机号</text>
          <text class="soon-badge">即将开放</text>
        </button>
      </view>
      <view class="login-mode-note">目前仅支持邮箱注册登录，新用户注册后自动赠送 1 个月会员。</view>

      <template v-if="mode === 'login'">
        <template v-if="authMethod === 'phone'">
          <view class="field">
            <view class="label">手机号</view>
            <input
              v-model.trim="phoneLoginForm.phone"
              class="input"
              type="text"
              maxlength="15"
              placeholder="请输入手机号（可带区号）"
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
                placeholder="请输入验证码"
              />
              <button class="code-btn" :disabled="sendingCode.phoneLogin" @tap="handleSendPhoneLoginCode">
                {{ sendingCode.phoneLogin ? '发送中...' : '发送验证码' }}
              </button>
            </view>
          </view>

          <view class="auth-note">验证码登录，无需记密码，登录后自动同步错题和报告。</view>
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
            <view class="password-input-wrap">
              <input
                v-model="loginForm.password"
                class="input password-input"
                :password="!passwordVisible.login"
                type="text"
                placeholder="请输入密码"
              />
              <button
                class="eye-toggle"
                :class="{ visible: passwordVisible.login }"
                :aria-label="passwordVisible.login ? '隐藏密码' : '显示密码'"
                @tap="togglePasswordVisibility('login')"
              >
                <text class="eye-icon"></text>
              </button>
            </view>
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
              placeholder="请输入手机号（可带区号）"
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
                placeholder="请输入验证码"
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
            <view class="password-input-wrap">
              <input
                v-model="registerForm.password"
                class="input password-input"
                :password="!passwordVisible.register"
                type="text"
                placeholder="请输入至少 6 位密码"
              />
              <button
                class="eye-toggle"
                :class="{ visible: passwordVisible.register }"
                :aria-label="passwordVisible.register ? '隐藏密码' : '显示密码'"
                @tap="togglePasswordVisibility('register')"
              >
                <text class="eye-icon"></text>
              </button>
            </view>
          </view>

          <view class="field">
            <view class="label">确认密码</view>
            <view class="password-input-wrap">
              <input
                v-model="registerForm.confirmPassword"
                class="input password-input"
                :password="!passwordVisible.registerConfirm"
                type="text"
                placeholder="请再次输入密码"
              />
              <button
                class="eye-toggle"
                :class="{ visible: passwordVisible.registerConfirm }"
                :aria-label="passwordVisible.registerConfirm ? '隐藏密码' : '显示密码'"
                @tap="togglePasswordVisibility('registerConfirm')"
              >
                <text class="eye-icon"></text>
              </button>
            </view>
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
              placeholder="请输入手机号（可带区号）"
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
                placeholder="请输入验证码"
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
            <view class="password-input-wrap">
              <input
                v-model="resetForm.newPassword"
                class="input password-input"
                :password="!passwordVisible.reset"
                type="text"
                placeholder="请输入新密码"
              />
              <button
                class="eye-toggle"
                :class="{ visible: passwordVisible.reset }"
                :aria-label="passwordVisible.reset ? '隐藏密码' : '显示密码'"
                @tap="togglePasswordVisibility('reset')"
              >
                <text class="eye-icon"></text>
              </button>
            </view>
          </view>

          <view class="field">
            <view class="label">确认新密码</view>
            <view class="password-input-wrap">
              <input
                v-model="resetForm.confirmPassword"
                class="input password-input"
                :password="!passwordVisible.resetConfirm"
                type="text"
                placeholder="请再次输入新密码"
              />
              <button
                class="eye-toggle"
                :class="{ visible: passwordVisible.resetConfirm }"
                :aria-label="passwordVisible.resetConfirm ? '隐藏密码' : '显示密码'"
                @tap="togglePasswordVisibility('resetConfirm')"
              >
                <text class="eye-icon"></text>
              </button>
            </view>
          </view>
        </template>
      </template>

      <button class="primary-button submit-btn" :disabled="submitting" @tap="submit">
        {{ submitButtonText }}
      </button>

      <button class="wechat-button disabled" @tap="handleWechatLogin">
        <text class="wechat-icon">微</text>
        <text>微信登录 · 即将开放</text>
      </button>

      <button class="ghost-button home-btn" @tap="goBackHome">返回首页</button>
    </view>

    <view v-if="tipText" class="tip-card" :class="{ success: tipType === 'success' }">
      <view class="tip-title">{{ tipType === 'success' ? '操作结果' : '提示信息' }}</view>
      <view class="tip-text">{{ tipText }}</view>
    </view>

    <!-- #ifdef H5 -->
    <IcpFooter />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import IcpFooter from '../../components/IcpFooter.vue'
import {
  checkBackendHealth,
  fetchWechatAuthUrl,
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
import { redirectIfAlreadyAuthed } from '../../utils/routeGuard'
import { EXAM_OPTIONS } from '../../utils/exam'

const mode = ref('login')
const PHONE_AUTH_ENABLED = false
const WECHAT_AUTH_ENABLED = false
const authMethod = ref('email')
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
const passwordVisible = reactive({
  login: false,
  register: false,
  registerConfirm: false,
  reset: false,
  resetConfirm: false
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

function togglePasswordVisibility(key) {
  passwordVisible[key] = !passwordVisible[key]
}

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

  if (options?.method === 'email') {
    authMethod.value = 'email'
  }

  if (options?.method === 'phone') {
    showAuthMethodUnavailable()
  }

  const wechatParams = getWechatOAuthParams(options)
  if (wechatParams.code) {
    mode.value = 'login'
    handleWechatCodeLogin(wechatParams)
    return
  }

  redirectIfAlreadyAuthed(redirect.value)
})

function switchMode(nextMode) {
  mode.value = nextMode
  tipText.value = ''
}

function switchAuthMethod(nextMethod) {
  if (nextMethod === 'phone' && !PHONE_AUTH_ENABLED) {
    showAuthMethodUnavailable()
    return
  }
  authMethod.value = nextMethod
  tipText.value = ''
}

function showAuthMethodUnavailable() {
  authMethod.value = 'email'
  tipType.value = 'warning'
  tipText.value = '目前仅支持邮箱注册和邮箱登录。手机号、微信登录正在适配中，新用户用邮箱注册后会自动赠送 1 个月会员。'
  uni.showToast({ title: '请先使用邮箱登录', icon: 'none' })
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

  if (detail.includes('WeChat login is not configured')) {
    return '微信登录还没有配置 AppID 和 AppSecret，请先完成微信开放平台配置'
  }

  if (detail.includes('Invalid WeChat state') || detail.includes('WeChat state expired')) {
    return '微信授权状态已失效，请重新点击微信登录'
  }

  if (detail.includes('WeChat token exchange failed')) {
    return '微信授权失败，请重新尝试'
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
    uni.reLaunch({ url: redirect.value })
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
      uni.reLaunch({ url: redirect.value })
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
        uni.reLaunch({ url: redirect.value })
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
  if (!WECHAT_AUTH_ENABLED) {
    showAuthMethodUnavailable()
    return
  }

  submitting.value = true
  tipText.value = ''

  try {
    await ensureBackendAvailable()
    const redirectUri = getWechatRedirectUri()
    if (!redirectUri) {
      throw { detail: '当前环境暂不支持微信网页授权' }
    }
    const response = await fetchWechatAuthUrl({ redirect_uri: redirectUri })
    if (!response?.auth_url) {
      throw { detail: '微信授权地址生成失败' }
    }
    window.location.href = response.auth_url
  } catch (error) {
    const message = normalizeUiError(error, '微信登录暂未开放')
    tipType.value = 'warning'
    tipText.value = message
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function handleWechatCodeLogin(params) {
  if (!params.code) return
  submitting.value = true
  tipText.value = ''
  try {
    await ensureBackendAvailable()
    const response = await loginWithWechat({
      code: params.code,
      state: params.state || null
    })
    cleanupWechatUrl()
    saveSessionAndRedirect(response, '微信登录成功')
  } catch (error) {
    cleanupWechatUrl()
    const message = normalizeUiError(error, '微信登录失败')
    tipType.value = 'warning'
    tipText.value = message
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function getWechatRedirectUri() {
  if (typeof window === 'undefined') return ''
  const url = new URL(window.location.href)
  url.searchParams.delete('code')
  url.searchParams.delete('state')
  const hashIndex = url.hash.indexOf('?')
  if (hashIndex >= 0) {
    const hashPath = url.hash.slice(0, hashIndex)
    const hashQuery = new URLSearchParams(url.hash.slice(hashIndex + 1))
    hashQuery.delete('code')
    hashQuery.delete('state')
    const nextHash = hashQuery.toString()
    url.hash = nextHash ? `${hashPath}?${nextHash}` : hashPath
  }
  return url.toString()
}

function getWechatOAuthParams(options = {}) {
  const params = {
    code: options?.code || '',
    state: options?.state || ''
  }
  if (params.code || typeof window === 'undefined') {
    return params
  }

  const url = new URL(window.location.href)
  params.code = url.searchParams.get('code') || ''
  params.state = url.searchParams.get('state') || ''
  if (params.code) return params

  const hashIndex = url.hash.indexOf('?')
  if (hashIndex >= 0) {
    const hashQuery = new URLSearchParams(url.hash.slice(hashIndex + 1))
    params.code = hashQuery.get('code') || ''
    params.state = hashQuery.get('state') || ''
  }
  return params
}

function cleanupWechatUrl() {
  if (typeof window === 'undefined' || !window.history?.replaceState) return
  const url = new URL(window.location.href)
  url.searchParams.delete('code')
  url.searchParams.delete('state')
  const hashIndex = url.hash.indexOf('?')
  if (hashIndex >= 0) {
    const hashPath = url.hash.slice(0, hashIndex)
    const hashQuery = new URLSearchParams(url.hash.slice(hashIndex + 1))
    hashQuery.delete('code')
    hashQuery.delete('state')
    const nextHash = hashQuery.toString()
    url.hash = nextHash ? `${hashPath}?${nextHash}` : hashPath
  }
  window.history.replaceState({}, document.title, url.toString())
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
  padding: calc(var(--status-bar-height) + 14rpx) 30rpx calc(env(safe-area-inset-bottom) + 40rpx);
  background:
    radial-gradient(circle at top right, var(--gyt-primary-shadow), transparent 28%),
    var(--gyt-page-bg);
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
  padding: 26rpx 30rpx 28rpx;
  border-radius: 30rpx;
  background:
    radial-gradient(circle at 88% 18%, var(--gyt-primary-shadow), transparent 32%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(241, 246, 255, 0.98));
  border: 2rpx solid rgba(219, 228, 245, 0.92);
  box-shadow: 0 14rpx 34rpx rgba(20, 31, 66, 0.06);
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 8rpx 15rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 22rpx;
  font-weight: 900;
}

.hero-title {
  margin-top: 14rpx;
  color: #101828;
  font-size: 38rpx;
  line-height: 1.22;
  font-weight: 900;
}

.hero-sub {
  margin-top: 10rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.45;
}

.segment-wrap {
  margin-top: 18rpx;
}

.segment {
  display: flex;
  gap: 6rpx;
  padding: 7rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid #e8eef8;
  box-shadow: 0 8rpx 22rpx rgba(20, 31, 66, 0.045);
}

.segment-btn {
  flex: 1;
  width: 0;
  min-height: 68rpx;
  margin: 0;
  border: 0;
  border-radius: 20rpx;
  background: transparent;
  color: #667085;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.segment-btn.active {
  background: var(--gyt-primary-gradient);
  color: #ffffff;
  box-shadow: 0 10rpx 22rpx var(--gyt-primary-shadow);
}

.login-card {
  margin-top: 18rpx;
  padding: 24rpx 26rpx 26rpx;
  border-radius: 30rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 14rpx 34rpx rgba(20, 31, 66, 0.06);
}

.method-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10rpx;
  margin-bottom: 24rpx;
  padding: 8rpx;
  border-radius: 24rpx;
  background: var(--gyt-primary-tint);
  border: 2rpx solid #e8edf7;
}

.method-btn {
  width: 100%;
  min-height: 70rpx;
  margin: 0;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #667085;
  font-size: 24rpx;
  line-height: 1;
  font-weight: 900;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.method-btn.active {
  background: linear-gradient(180deg, #ffffff 0%, #f9fbff 100%);
  color: var(--gyt-primary);
  box-shadow: 0 8rpx 18rpx rgba(20, 31, 66, 0.075);
}

.method-btn.disabled {
  color: #98a2b3;
}

.method-label {
  line-height: 1;
}

.soon-badge {
  padding: 6rpx 10rpx;
  border-radius: 999rpx;
  background: #eef2f7;
  color: #667085;
  font-size: 18rpx;
  line-height: 1;
  font-weight: 900;
}

.login-mode-note {
  margin: -8rpx 0 22rpx;
  padding: 16rpx 20rpx;
  border-radius: 20rpx;
  background: #fff8eb;
  border: 2rpx solid #fde7b0;
  color: #8a5a13;
  font-size: 23rpx;
  line-height: 1.55;
}

.field + .field {
  margin-top: 20rpx;
}

.label {
  color: #344054;
  font-size: 24rpx;
  font-weight: 900;
}

.input,
.picker-box {
  margin-top: 10rpx;
  min-height: 86rpx;
  padding: 0 24rpx;
  border-radius: 22rpx;
  border: 2rpx solid var(--gyt-primary-border);
  background: var(--gyt-primary-tint);
  font-size: 28rpx;
  color: #172033;
  display: flex;
  align-items: center;
}

.password-input-wrap {
  position: relative;
  margin-top: 10rpx;
}

.password-input-wrap .input {
  margin-top: 0;
}

.password-input {
  padding-right: 92rpx;
}

.eye-toggle {
  position: absolute;
  right: 14rpx;
  top: 50%;
  width: 64rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 20rpx;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transform: translateY(-50%);
}

.eye-toggle::after {
  border: 0;
}

.eye-icon {
  position: relative;
  width: 36rpx;
  height: 24rpx;
  border: 4rpx solid #98a2b3;
  border-radius: 50%;
}

.eye-icon::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: #98a2b3;
  transform: translate(-50%, -50%);
}

.eye-icon::after {
  content: '';
  position: absolute;
  left: -8rpx;
  top: 50%;
  width: 52rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: #98a2b3;
  transform: translateY(-50%) rotate(-38deg);
  transform-origin: center;
}

.eye-toggle.visible .eye-icon {
  border-color: var(--gyt-primary);
}

.eye-toggle.visible .eye-icon::before {
  background: var(--gyt-primary);
}

.eye-toggle.visible .eye-icon::after {
  opacity: 0;
}

.code-row {
  display: flex;
  gap: 12rpx;
  align-items: stretch;
}

.code-input {
  flex: 1;
}

.code-btn {
  width: 184rpx;
  min-height: 86rpx;
  border: 0;
  border-radius: 22rpx;
  background: linear-gradient(180deg, var(--gyt-primary-soft) 0%, var(--gyt-primary-soft) 100%);
  color: var(--gyt-primary);
  font-size: 23rpx;
  font-weight: 900;
  line-height: 86rpx;
  padding: 0 10rpx;
}

.code-btn[disabled] {
  color: #98a2b3;
}

.auth-note {
  margin-top: 16rpx;
  padding: 16rpx 20rpx;
  border-radius: 20rpx;
  background: linear-gradient(180deg, var(--gyt-primary-tint) 0%, var(--gyt-primary-tint) 100%);
  color: #667085;
  font-size: 23rpx;
  line-height: 1.55;
}

.submit-btn {
  margin-top: 28rpx;
  min-height: 92rpx;
  border-radius: 26rpx;
  font-size: 30rpx;
  line-height: 92rpx;
}

.wechat-button {
  margin-top: 14rpx;
  min-height: 84rpx;
  border: 0;
  border-radius: 24rpx;
  background: #f1fbf5;
  color: #138a43;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 84rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
}

.wechat-button.disabled {
  background: #f4f6fa;
  color: #98a2b3;
}

.wechat-button.disabled .wechat-icon {
  background: #cbd5e1;
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
  margin-top: 14rpx;
  min-height: 84rpx;
  border-radius: 24rpx;
  line-height: 84rpx;
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
  .login-page {
    padding-left: 24rpx;
    padding-right: 24rpx;
  }

  .code-row {
    flex-direction: column;
    align-items: stretch;
  }

  .code-btn {
    width: 100%;
  }
}
</style>
