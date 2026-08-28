<template>
  <view class="app-empty-state" :class="{ compact }" role="status" :aria-label="label">
    <image
      class="app-empty-state-image"
      src="/static/ui-icons/png/original/empty-favorites.png"
      mode="aspectFit"
      :alt="label"
    />
    <view v-if="hasCopy" class="app-empty-state-copy">
      <strong v-if="title">{{ title }}</strong>
      <text v-if="description">{{ description }}</text>
      <slot />
    </view>
  </view>
</template>

<script setup>
import { computed, useSlots } from 'vue'

const props = defineProps({
  label: {
    type: String,
    default: '暂无内容'
  },
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const slots = useSlots()
const hasCopy = computed(() => Boolean(props.title || props.description || slots.default))
</script>

<style scoped>
.app-empty-state {
  width: 100%;
  min-height: 320rpx;
  flex: 1 1 320rpx;
  box-sizing: border-box;
  padding: 36rpx 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.app-empty-state-image {
  width: 240rpx;
  height: 240rpx;
  max-width: 150px;
  max-height: 150px;
  display: block;
  opacity: 0.92;
}

.app-empty-state.compact {
  min-height: 250rpx;
  padding-top: 22rpx;
  padding-bottom: 22rpx;
  flex: 0 0 auto;
}

.app-empty-state.compact .app-empty-state-image {
  width: 176rpx;
  height: 176rpx;
}

.app-empty-state-copy {
  max-width: 540rpx;
  margin-top: 12rpx;
  color: #8490a3;
  font-size: 22rpx;
  line-height: 1.55;
}

.app-empty-state-copy strong,
.app-empty-state-copy text {
  display: block;
}

.app-empty-state-copy strong {
  color: #536176;
  font-size: 25rpx;
  font-weight: 650;
}

.app-empty-state-copy text {
  margin-top: 7rpx;
}

.app-empty-state-copy :deep(button) {
  min-height: 58rpx;
  margin: 20rpx auto 0;
  padding: 0 24rpx;
  border: 0;
  border-radius: 18rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 21rpx;
  line-height: 58rpx;
  font-weight: 700;
}

.app-empty-state-copy :deep(button)::after {
  border: 0;
}
</style>
