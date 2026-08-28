<template><image class="app-refresh-icon" :src="iconSrc" mode="aspectFit" aria-hidden="true" /></template>

<script setup>
import { getThemeIconSrc } from '../../utils/iconAssets'
import { getStoredThemeKey } from '../../utils/theme'

const iconSrc = getThemeIconSrc('/static/ui-icons/png/original/refresh.png', getStoredThemeKey())
</script>

<style scoped>
.app-refresh-icon {
  display: block;
  width: 34rpx;
  height: 34rpx;
  flex: none;
}
</style>
