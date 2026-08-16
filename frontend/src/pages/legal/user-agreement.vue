<template>
  <view class="page agreement-page" :style="themeInlineStyle">
    <view class="agreement-card">
      <view class="agreement-title">港研通用户服务协议</view>
      <view class="agreement-date">更新日期：2026年7月17日</view>

      <view class="agreement-intro">
        欢迎使用港研通。请在注册、登录或使用服务前认真阅读本协议。只有在你主动勾选同意后，我们才会继续处理登录或注册请求。
      </view>

      <view v-for="section in sections" :key="section.title" class="agreement-section">
        <view class="section-title">{{ section.title }}</view>
        <view v-for="paragraph in section.paragraphs" :key="paragraph" class="section-text">
          {{ paragraph }}
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())

const sections = [
  {
    title: '一、服务内容',
    paragraphs: [
      '港研通目前以免费内测形式提供科目练习、模拟测试、错题本、收藏夹、练习历史和学习报告等学习辅助功能。',
      '内测期间，部分功能可能根据使用反馈进行调整、暂停或优化。'
    ]
  },
  {
    title: '二、账号注册与使用',
    paragraphs: [
      '你可以使用微信或邮箱账号登录。你应当提供本人有权使用的信息，并妥善保管账号及登录凭证。',
      '不得转让、出租账号，不得利用账号实施违法违规、干扰服务运行或侵害他人权益的行为。'
    ]
  },
  {
    title: '三、学习内容与使用规范',
    paragraphs: [
      '题目、解析和学习报告仅用于学习辅助，不构成考试结果、录取结果或其他专业结论的保证。',
      '未经许可，不得批量抓取、复制、出售、传播小程序中的题目、解析或其他受保护内容。'
    ]
  },
  {
    title: '四、隐私与数据保护',
    paragraphs: [
      '我们按照《用户隐私保护指引》处理登录标识、账号资料和学习记录。具体信息类型、用途和用户权利以该指引为准。',
      '你可以在登录页独立阅读《用户隐私保护指引》，并自行决定是否勾选同意；未勾选不会发起登录或注册请求。'
    ]
  },
  {
    title: '五、账号安全与注销',
    paragraphs: [
      '如发现账号被异常使用，请及时修改密码或联系我们。你可以通过个人资料页申请注销账号；注销后，与该账号关联的数据将按照页面提示处理。'
    ]
  },
  {
    title: '六、服务变更与责任说明',
    paragraphs: [
      '因系统维护、网络故障、第三方服务异常或不可抗力造成服务暂时不可用时，我们会在合理范围内尽快恢复。',
      '我们可能更新本协议；如更新内容对用户权益有重要影响，将通过页面提示等合理方式告知。'
    ]
  },
  {
    title: '七、联系我们',
    paragraphs: [
      '如对本协议或服务有疑问，可发送邮件至 2982326925@qq.com 联系我们。'
    ]
  }
]
</script>

<style scoped>
.agreement-page {
  min-height: 100vh;
  padding: 28rpx 24rpx calc(env(safe-area-inset-bottom) + 36rpx);
  background: var(--gyt-page-bg);
  color: #172033;
}

.agreement-card {
  padding: 36rpx 30rpx;
  border: 2rpx solid #e6ebf5;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 16rpx 36rpx rgba(20, 31, 66, 0.06);
}

.agreement-title {
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1.35;
  text-align: center;
}

.agreement-date {
  margin-top: 12rpx;
  color: #667085;
  font-size: 23rpx;
  text-align: center;
}

.agreement-intro {
  margin-top: 32rpx;
  padding: 22rpx 24rpx;
  border-radius: 20rpx;
  background: var(--gyt-primary-soft);
  color: #344054;
  font-size: 26rpx;
  line-height: 1.8;
}

.agreement-section {
  margin-top: 34rpx;
}

.section-title {
  color: #172033;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.5;
}

.section-text {
  margin-top: 14rpx;
  color: #475467;
  font-size: 25rpx;
  line-height: 1.85;
}
</style>
