<template>
  <view class="portal-login">
    <view class="login-visual">
      <view class="visual-orb orb-one"></view>
      <view class="visual-orb orb-two"></view>
      <view class="brand-lockup">
        <view class="brand-mark"><text>港</text></view>
        <view>
          <view class="brand-name">港研通</view>
          <view class="brand-tagline">QUESTION OPERATIONS</view>
        </view>
      </view>

      <view class="visual-copy">
        <view class="visual-kicker">内部题库工作台</view>
        <view class="visual-title">让题库运营更清晰，<br />让每一次审核都有依据。</view>
        <view class="visual-description">
          集中管理题目、审核队列、批量导入与学习质量数据。
        </view>
        <view class="visual-points">
          <view class="visual-point"><text class="point-dot"></text>数据库白名单访问</view>
          <view class="visual-point"><text class="point-dot"></text>全链路操作留痕</view>
          <view class="visual-point"><text class="point-dot"></text>正式题库与 AI 临时题隔离</view>
        </view>
      </view>

      <view class="visual-foot">港研通内部系统 · 请勿向外部人员分享入口</view>
    </view>

    <view class="login-panel">
      <view class="login-card">
        <view class="mobile-brand">
          <view class="brand-mark small"><text>港</text></view>
          <view class="brand-name">港研通题库中台</view>
        </view>
        <view class="login-eyebrow">INTERNAL ACCESS</view>
        <view class="login-title">欢迎回来</view>
        <view class="login-subtitle">请使用已加入内部权限名单的账号登录</view>

        <view v-if="notice" class="login-notice" :class="noticeTone">
          <view class="notice-dot"></view>
          <text>{{ notice }}</text>
        </view>

        <form class="login-form" @submit="submitLogin">
          <view class="field-group">
            <view class="field-label">邮箱</view>
            <view class="field-shell">
              <text class="field-icon">@</text>
              <input
                v-model.trim="form.email"
                class="field-input"
                type="text"
                autocomplete="username"
                placeholder="name@example.com"
                confirm-type="next"
              />
            </view>
          </view>

          <view class="field-group">
            <view class="field-label">密码</view>
            <view class="field-shell">
              <text class="field-icon">⌁</text>
              <input
                v-model="form.password"
                class="field-input"
                :password="!showPassword"
                autocomplete="current-password"
                placeholder="请输入密码"
                confirm-type="done"
                @confirm="submitLogin"
              />
              <button class="password-toggle" type="button" @tap="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </button>
            </view>
          </view>

          <button class="login-button" form-type="submit" :disabled="submitting">
            <text>{{ submitting ? '正在验证权限…' : '进入题库中台' }}</text>
            <text v-if="!submitting" class="button-arrow">→</text>
          </button>
        </form>

        <view class="permission-tip">
          <view class="tip-icon">i</view>
          <view>
            <view class="tip-title">无法登录？</view>
            <view class="tip-copy">本页面不提供注册或权限申请。新增权限需由系统维护人员直接写入数据库。</view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { loginWithEmail } from '../../api/auth'
import { fetchQuestionAdminPortalMe } from '../../api/admin'
import {
  clearAuthSession,
  isLoggedIn,
  saveAuthSession
} from '../../utils/auth'

const form = reactive({
  email: '',
  password: ''
})
const showPassword = ref(false)
const submitting = ref(false)
const notice = ref('')
const noticeTone = ref('error')

onLoad(async () => {
  if (!isLoggedIn()) return
  submitting.value = true
  try {
    await fetchQuestionAdminPortalMe()
    enterPortal()
  } catch (error) {
    clearAuthSession()
  } finally {
    submitting.value = false
  }
})

async function submitLogin() {
  if (submitting.value) return
  notice.value = ''
  const email = String(form.email || '').trim()
  const password = String(form.password || '')
  if (!email || !password) {
    showNotice('请输入邮箱和密码')
    return
  }

  submitting.value = true
  try {
    const response = await loginWithEmail({ email, password })
    saveAuthSession({
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
      user: response.user
    })
    await fetchQuestionAdminPortalMe()
    noticeTone.value = 'success'
    notice.value = '权限验证通过，正在进入…'
    setTimeout(enterPortal, 180)
  } catch (error) {
    clearAuthSession()
    const detail = typeof error?.detail === 'string' ? error.detail : ''
    if (detail.includes('permission') || detail.includes('权限')) {
      showNotice('账号有效，但尚未加入题库中台权限名单')
    } else if (detail.includes('not configured')) {
      showNotice('权限数据表尚未部署，请联系系统维护人员')
    } else {
      showNotice('邮箱、密码或访问权限验证失败')
    }
  } finally {
    submitting.value = false
  }
}

function showNotice(message) {
  noticeTone.value = 'error'
  notice.value = message
}

function enterPortal() {
  uni.reLaunch({ url: '/pages/admin/question-desktop' })
}
</script>

<style scoped>
page {
  background: #eef3f7;
}

button::after {
  border: 0;
}

.portal-login {
  --ink: #17243a;
  --muted: #728096;
  --line: #dce5eb;
  --mint: #4fd1b5;
  --mint-dark: #22aa90;
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(420px, 1.05fr) minmax(480px, 0.95fr);
  background: #f7fafc;
  color: var(--ink);
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.login-visual {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 54px 7.5vw 42px;
  box-sizing: border-box;
  background:
    radial-gradient(circle at 82% 18%, rgba(115, 231, 204, 0.2), transparent 34%),
    radial-gradient(circle at 8% 78%, rgba(87, 132, 174, 0.18), transparent 36%),
    linear-gradient(145deg, #1c304a 0%, #263d58 52%, #344f69 100%);
  color: #fff;
}

.brand-lockup,
.mobile-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  z-index: 2;
}

.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #163b3c;
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(145deg, #7ce4cf, #46cdb0);
  box-shadow: 0 14px 34px rgba(60, 211, 179, 0.24);
}

.brand-mark.small {
  width: 42px;
  height: 42px;
  border-radius: 13px;
}

.brand-name {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.brand-tagline {
  margin-top: 3px;
  color: rgba(255, 255, 255, 0.52);
  font-size: 10px;
  letter-spacing: 0.18em;
}

.visual-copy {
  position: relative;
  z-index: 2;
  margin: auto 0;
  max-width: 650px;
}

.visual-kicker,
.login-eyebrow {
  color: #70e0c7;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
}

.visual-title {
  margin-top: 22px;
  font-size: clamp(36px, 3.4vw, 58px);
  line-height: 1.28;
  font-weight: 650;
  letter-spacing: -0.035em;
}

.visual-description {
  margin-top: 24px;
  max-width: 520px;
  color: rgba(255, 255, 255, 0.65);
  font-size: 16px;
  line-height: 1.8;
}

.visual-points {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 26px;
  margin-top: 38px;
}

.visual-point {
  display: flex;
  align-items: center;
  gap: 9px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}

.point-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #5dd7ba;
  box-shadow: 0 0 0 5px rgba(93, 215, 186, 0.1);
}

.visual-foot {
  position: relative;
  z-index: 2;
  color: rgba(255, 255, 255, 0.36);
  font-size: 12px;
}

.visual-orb {
  position: absolute;
  border: 1px solid rgba(111, 224, 199, 0.1);
  border-radius: 50%;
}

.orb-one {
  width: 520px;
  height: 520px;
  right: -260px;
  top: 8%;
}

.orb-two {
  width: 340px;
  height: 340px;
  left: -190px;
  bottom: 4%;
}

.login-panel {
  min-height: 100vh;
  padding: 70px 8vw;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  background:
    radial-gradient(circle at 100% 0%, rgba(79, 209, 181, 0.1), transparent 28%),
    #f8fafc;
}

.login-card {
  width: min(440px, 100%);
}

.mobile-brand {
  display: none;
  margin-bottom: 48px;
}

.login-title {
  margin-top: 14px;
  font-size: 36px;
  line-height: 1.25;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.login-subtitle {
  margin-top: 11px;
  color: var(--muted);
  font-size: 14px;
}

.login-notice {
  margin-top: 24px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #ffd7d7;
  border-radius: 10px;
  color: #b64646;
  background: #fff6f6;
  font-size: 13px;
}

.login-notice.success {
  color: #15836e;
  border-color: #c6eee4;
  background: #f1fbf8;
}

.notice-dot {
  width: 7px;
  height: 7px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: currentColor;
}

.login-form {
  margin-top: 32px;
}

.field-group + .field-group {
  margin-top: 21px;
}

.field-label {
  margin-bottom: 9px;
  color: #3f4c5f;
  font-size: 13px;
  font-weight: 600;
}

.field-shell {
  height: 52px;
  display: flex;
  align-items: center;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: 11px;
  box-sizing: border-box;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.field-shell:focus-within {
  border-color: #54cdb4;
  box-shadow: 0 0 0 4px rgba(79, 209, 181, 0.1);
}

.field-icon {
  width: 26px;
  color: #95a2b2;
  font-size: 16px;
  font-weight: 600;
}

.field-input {
  min-width: 0;
  height: 50px;
  flex: 1;
  color: var(--ink);
  font-size: 14px;
}

.password-toggle {
  width: auto;
  margin: 0;
  padding: 7px 4px 7px 12px;
  color: #738196;
  background: transparent;
  font-size: 12px;
  line-height: 1;
}

.login-button {
  height: 54px;
  margin: 30px 0 0;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-radius: 11px;
  color: #123c3a;
  background: linear-gradient(135deg, #68ddc4, #45c8aa);
  box-shadow: 0 14px 30px rgba(50, 187, 157, 0.2);
  font-size: 15px;
  font-weight: 700;
}

.login-button[disabled] {
  opacity: 0.62;
}

.button-arrow {
  font-size: 20px;
  line-height: 1;
}

.permission-tip {
  margin-top: 32px;
  padding: 17px;
  display: flex;
  gap: 12px;
  border: 1px solid #e4ebef;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.62);
}

.tip-icon {
  width: 22px;
  height: 22px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #238e79;
  background: #dff6f0;
  font-size: 12px;
  font-weight: 700;
}

.tip-title {
  color: #455266;
  font-size: 12px;
  font-weight: 700;
}

.tip-copy {
  margin-top: 5px;
  color: #8793a3;
  font-size: 12px;
  line-height: 1.65;
}

@media (max-width: 900px) {
  .portal-login {
    display: block;
  }

  .login-visual {
    display: none;
  }

  .login-panel {
    padding: 48px 24px;
  }

  .mobile-brand {
    display: flex;
  }
}
</style>
