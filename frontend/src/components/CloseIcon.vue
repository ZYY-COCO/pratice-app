<template>
  <image class="close-icon-image" :src="iconSrc" mode="aspectFit" alt="关闭" />
</template>

<script setup>
import { computed } from 'vue'
import { getOriginalIconSrc, getToneIconSrc } from '../utils/iconAssets'

const cancelIconSource = '/static/ui-icons/png/original/cancel.png'

const props = defineProps({
  tone: {
    type: String,
    default: 'original'
  }
})

const iconSrc = computed(() => (
  props.tone === 'original'
    ? getOriginalIconSrc(cancelIconSource)
    : getToneIconSrc(cancelIconSource, props.tone)
))
</script>

<style scoped>
.close-icon-image {
  display: block;
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
}
</style>
