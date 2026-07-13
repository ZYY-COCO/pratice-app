<template>
  <view class="favorite-icon" aria-hidden="true"></view>
</template>

<style scoped>
.favorite-icon {
  display: block;
  width: 1em;
  height: 1em;
  flex-shrink: 0;
  background-color: currentColor;
  -webkit-mask: url('/static/ui-icons/favorite.svg') center / contain no-repeat;
  mask: url('/static/ui-icons/favorite.svg') center / contain no-repeat;
}
</style>
