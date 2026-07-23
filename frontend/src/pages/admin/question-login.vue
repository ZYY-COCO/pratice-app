<template>
  <view></view>
</template>

<script setup>
import { onLoad } from '@dcloudio/uni-app'

onLoad(() => {
  const redirect = encodeURIComponent('/pages/admin/question-desktop')
  uni.reLaunch({ url: `/pages/login/index?portal=1&redirect=${redirect}` })
})
</script>
