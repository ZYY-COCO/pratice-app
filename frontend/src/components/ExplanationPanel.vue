<template>
  <view v-if="visible" class="panel">
    <view class="title">【人工精编解析】</view>

    <view class="body">
      <text class="strong">正确答案：{{ correctAnswer }}</text>
      <MathText class="paragraph" :value="explanation" />
    </view>

    <view v-if="autoTag" class="tag">{{ autoTag }}</view>
  </view>
</template>

<script setup>
import MathText from './MathText.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  correctAnswer: {
    type: String,
    default: ''
  },
  explanation: {
    type: String,
    default: ''
  },
  autoTag: {
    type: String,
    default: ''
  }
})

</script>

<style scoped>
.panel {
  padding: 28rpx;
  border-radius: 30rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
}

.title {
  color: #223254;
  font-size: 28rpx;
  font-weight: 800;
}

.body {
  margin-top: 16rpx;
}

.strong {
  display: block;
  color: #172033;
  font-size: 26rpx;
  font-weight: 800;
}

.paragraph {
  display: block;
  margin-top: 14rpx;
  color: #43516d;
  font-size: 25rpx;
  line-height: 1.8;
}

.tag {
  margin-top: 18rpx;
  padding: 18rpx;
  border-radius: 22rpx;
  background: #f8fafc;
  border: 2rpx dashed #d8e0ed;
  color: #6b7280;
  font-size: 22rpx;
  line-height: 1.6;
}
</style>
