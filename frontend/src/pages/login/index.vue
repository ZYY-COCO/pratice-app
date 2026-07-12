<template>
  <view class="page login-page" :style="themeInlineStyle">
    <view class="auth-shell">
      <view class="auth-topbar">
        <button
          v-if="mode !== 'login'"
          class="topbar-back"
          aria-label="返回邮密登录"
          @tap="switchMode('login')"
        >
          <image class="topbar-back-icon" src="/static/ui-icons/auth-back.svg" mode="aspectFit" alt="返回" />
        </button>
        <button class="topbar-help" @tap="openHelp">帮助</button>
      </view>

      <view class="brand" aria-label="港研通">
        <image
          class="brand-image"
          src="/static/gangyantong-home-wordmark-4k.png"
          mode="widthFix"
          alt="港研通"
        />
      </view>

      <view class="login-card">
        <view v-if="mode !== 'login'" class="mode-heading">
          {{ mode === 'register' ? '创建账号' : '找回密码' }}
        </view>

        <template v-if="mode === 'login'">
          <view class="field">
            <input
              v-model.trim="loginForm.email"
              class="input"
              type="text"
              placeholder="请输入已注册邮箱"
            />
          </view>

          <view class="field">
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

        <template v-else-if="mode === 'register'">
          <view class="field">
            <input
              v-model.trim="registerForm.email"
              class="input"
              type="text"
              placeholder="请输入可接收验证码的邮箱"
            />
          </view>

          <view class="field">
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

        <template v-else>
          <view class="field">
            <input
              v-model.trim="resetForm.email"
              class="input"
              type="text"
              placeholder="请输入已注册邮箱"
            />
          </view>

          <view class="field">
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

        <button class="primary-button submit-btn" :disabled="submitting" @tap="submit">
          {{ submitButtonText }}
        </button>

        <button v-if="mode === 'login'" class="wechat-button disabled" @tap="handleWechatLogin">
          <text class="wechat-icon">微</text>
          <text>微信登录 · 即将开放</text>
        </button>

        <view v-if="tipText" class="inline-tip" :class="{ success: tipType === 'success' }">
          {{ tipText }}
        </view>

        <view class="shortcut-divider"></view>

        <view class="shortcut-grid">
          <button v-if="mode !== 'login'" class="shortcut-btn" @tap="switchMode('login')">
            <view class="shortcut-icon login-icon">
              <image
                class="shortcut-image"
                src="/static/ui-icons/email-login.svg"
                mode="aspectFit"
                alt="邮密登录"
              />
            </view>
            <text>邮密登录</text>
          </button>

          <button v-if="mode !== 'register'" class="shortcut-btn" @tap="switchMode('register')">
            <view class="shortcut-icon register-icon">
              <image
                class="shortcut-image"
                src="/static/ui-icons/register.svg"
                mode="aspectFit"
                alt="注册"
              />
            </view>
            <text>注册</text>
          </button>

          <button v-if="mode !== 'reset'" class="shortcut-btn" @tap="switchMode('reset')">
            <view class="shortcut-icon lock-icon">
              <image
                class="shortcut-image"
                src="/static/ui-icons/reset-password.svg"
                mode="aspectFit"
                alt="找回密码"
              />
            </view>
            <text>找回密码</text>
          </button>
        </view>
      </view>
    </view>

    <view v-if="helpVisible" class="help-mask" @tap="closeHelp">
      <view class="help-dialog" role="dialog" aria-modal="true" aria-label="帮助" @tap.stop>
        <view class="help-dialog-header">
          <text class="help-dialog-title">帮助</text>
          <button class="help-close" aria-label="关闭" @tap="closeHelp">×</button>
        </view>
        <button class="help-entry" @tap="openSupportPage">
          <view class="help-entry-copy">
            <text class="help-entry-title">问题与反馈</text>
            <text class="help-entry-subtitle">进入港研通帮助与支持页面</text>
          </view>
          <text class="help-entry-arrow">›</text>
        </button>
      </view>
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
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const mode = ref('login')
const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const supportUrl = 'https://www.gangyantong.com/support.html'
const PHONE_AUTH_ENABLED = false
const WECHAT_AUTH_ENABLED = false
const authMethod = ref('email')
const submitting = ref(false)
const helpVisible = ref(false)
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
  tipText.value = '目前仅支持邮箱注册和邮箱登录。手机号、微信登录正在适配中，登录后可同步错题、收藏和学习记录。'
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

function openHelp() {
  helpVisible.value = true
}

function closeHelp() {
  helpVisible.value = false
}

function openSupportPage() {
  closeHelp()

  // #ifdef APP-PLUS
  if (typeof plus !== 'undefined' && plus?.runtime?.openURL) {
    plus.runtime.openURL(supportUrl)
    return
  }
  // #endif

  // #ifdef H5
  if (typeof window !== 'undefined') {
    window.location.href = supportUrl
    return
  }
  // #endif

  uni.setClipboardData({
    data: supportUrl,
    success() {
      uni.showToast({ title: '支持页链接已复制', icon: 'none' })
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  min-height: 100dvh;
  padding: calc(var(--status-bar-height) + 54rpx) 30rpx calc(env(safe-area-inset-bottom) + 36rpx);
  background:
    radial-gradient(circle at 74% 0%, rgba(42, 112, 244, 0.13), transparent 36%),
    linear-gradient(180deg, #f9fbff 0%, #ffffff 58%, #f7faff 100%);
}

.login-page view,
.login-page input,
.login-page button {
  box-sizing: border-box;
}

.login-page button::after {
  border: 0;
}

.auth-shell {
  width: 100%;
  max-width: 690rpx;
  margin: 0 auto;
}

.auth-topbar {
  min-height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.topbar-back,
.topbar-help {
  margin: 0;
  border: 0;
  background: transparent;
}

.topbar-back {
  width: 72rpx;
  height: 72rpx;
  padding: 10rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.topbar-back-icon {
  width: 52rpx;
  height: 52rpx;
}

.topbar-help {
  margin-left: auto;
  min-width: 88rpx;
  min-height: 72rpx;
  padding: 0 8rpx;
  color: #344054;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 72rpx;
}

.brand {
  margin: 28rpx 0 58rpx;
  display: flex;
  justify-content: center;
}

.brand-image {
  display: block;
  width: min(500rpx, 78vw);
  height: auto;
  mix-blend-mode: multiply;
}

.login-card {
  padding: 70rpx 38rpx 54rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid #e5ebf5;
  box-shadow: 0 24rpx 60rpx rgba(29, 57, 116, 0.09);
}

.mode-heading {
  margin: -12rpx 0 34rpx;
  color: #172033;
  font-size: 34rpx;
  line-height: 1.2;
  font-weight: 900;
  text-align: center;
}

.field + .field {
  margin-top: 26rpx;
}

.input {
  width: 100%;
  min-height: 94rpx;
  height: 94rpx;
  padding: 0 28rpx;
  border-radius: 20rpx;
  border: 2rpx solid var(--gyt-primary-border);
  background: #f8faff;
  font-size: 28rpx;
  color: #172033;
  display: flex;
  align-items: center;
}

.password-input-wrap {
  position: relative;
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
  border-radius: 50%;
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
  min-height: 94rpx;
  border: 0;
  border-radius: 20rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 23rpx;
  font-weight: 900;
  line-height: 94rpx;
  padding: 0 10rpx;
}

.code-btn[disabled] {
  color: #98a2b3;
}

.submit-btn {
  margin-top: 32rpx;
  min-height: 96rpx;
  border-radius: 20rpx;
  font-size: 30rpx;
  line-height: 96rpx;
}

.wechat-button {
  margin-top: 20rpx;
  min-height: 88rpx;
  border: 0;
  border-radius: 20rpx;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
}

.wechat-button.disabled {
  background: #f2f4f8;
  color: #7f8ba3;
}

.wechat-button.disabled .wechat-icon {
  background: #cbd5e1;
}

.wechat-icon {
  width: 42rpx;
  height: 42rpx;
  border-radius: 50%;
  background: #c6cfdd;
  color: #ffffff;
  font-size: 22rpx;
  line-height: 42rpx;
  text-align: center;
}

.inline-tip {
  margin-top: 20rpx;
  padding: 18rpx 20rpx;
  border-radius: 16rpx;
  background: #fff8eb;
  border: 2rpx solid #fde7b0;
  color: #8a5a13;
  font-size: 23rpx;
  line-height: 1.55;
}

.inline-tip.success {
  background: #effcf4;
  border-color: #b7ebc6;
  color: #17663a;
}

.shortcut-divider {
  height: 2rpx;
  margin: 48rpx 0 34rpx;
  background: #e7ebf2;
}

.shortcut-grid {
  display: flex;
  justify-content: space-around;
  gap: 24rpx;
}

.shortcut-btn {
  flex: 1;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: #536078;
  font-size: 25rpx;
  font-weight: 700;
  line-height: 1.3;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15rpx;
}

.shortcut-icon {
  position: relative;
  width: 92rpx;
  height: 92rpx;
  border: 2rpx solid #dce4f2;
  border-radius: 50%;
  background: #ffffff;
}

.shortcut-image {
  position: absolute;
  left: 19rpx;
  top: 19rpx;
  width: 54rpx;
  height: 54rpx;
}

.help-mask {
  position: fixed;
  inset: 0;
  z-index: 80;
  padding: 30rpx;
  background: rgba(15, 23, 42, 0.42);
  display: flex;
  align-items: center;
  justify-content: center;
}

.help-dialog {
  width: 100%;
  max-width: 620rpx;
  padding: 28rpx;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 28rpx 70rpx rgba(15, 23, 42, 0.2);
}

.help-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.help-dialog-title {
  color: #172033;
  font-size: 32rpx;
  line-height: 1.3;
  font-weight: 900;
}

.help-close {
  width: 60rpx;
  height: 60rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #f2f4f8;
  color: #667085;
  font-size: 38rpx;
  line-height: 56rpx;
}

.help-entry {
  width: 100%;
  min-height: 110rpx;
  margin: 24rpx 0 0;
  padding: 20rpx 22rpx;
  border: 2rpx solid #e3eaf5;
  border-radius: 16rpx;
  background: #f8faff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  text-align: left;
}

.help-entry-copy {
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8rpx;
}

.help-entry-title {
  color: #172033;
  font-size: 28rpx;
  line-height: 1.25;
  font-weight: 900;
}

.help-entry-subtitle {
  color: #7f8ba3;
  font-size: 22rpx;
  line-height: 1.45;
}

.help-entry-arrow {
  flex-shrink: 0;
  color: var(--gyt-primary);
  font-size: 46rpx;
  line-height: 1;
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

  .brand {
    margin-top: 16rpx;
    margin-bottom: 46rpx;
  }

  .login-card {
    padding-left: 28rpx;
    padding-right: 28rpx;
  }
}
</style>
