<template>
  <view class="chart-shell">
    <view class="title">能力雷达图</view>
    <view class="chart-wrap">
      <svg class="chart" viewBox="0 0 310 250">
        <g transform="translate(155 125)">
          <polygon points="0,-90 85,-28 53,73 -53,73 -85,-28" fill="none" stroke="#d9e3f4" stroke-width="1.2" />
          <polygon points="0,-68 64,-21 40,55 -40,55 -64,-21" fill="none" stroke="#d9e3f4" stroke-width="1.2" />
          <polygon points="0,-46 43,-14 27,37 -27,37 -43,-14" fill="none" stroke="#d9e3f4" stroke-width="1.2" />
          <polygon points="0,-24 22,-7 14,19 -14,19 -22,-7" fill="none" stroke="#d9e3f4" stroke-width="1.2" />
          <line x1="0" y1="0" x2="0" y2="-90" stroke="#d9e3f4" />
          <line x1="0" y1="0" x2="85" y2="-28" stroke="#d9e3f4" />
          <line x1="0" y1="0" x2="53" y2="73" stroke="#d9e3f4" />
          <line x1="0" y1="0" x2="-53" y2="73" stroke="#d9e3f4" />
          <line x1="0" y1="0" x2="-85" y2="-28" stroke="#d9e3f4" />

          <polygon points="0,-58 61,-20 31,42 -24,34 -70,-23" fill="rgba(37,99,235,0.18)" stroke="#2563eb" stroke-width="2.4" />
          <circle cx="0" cy="-58" r="4" fill="#2563eb" />
          <circle cx="61" cy="-20" r="4" fill="#2563eb" />
          <circle cx="31" cy="42" r="4" fill="#2563eb" />
          <circle cx="-24" cy="34" r="4" fill="#2563eb" />
          <circle cx="-70" cy="-23" r="4" fill="#2563eb" />

          <text x="0" y="-103" text-anchor="middle" font-size="12" fill="#41506a">词汇量</text>
          <text x="96" y="-30" text-anchor="start" font-size="12" fill="#41506a">阅读逻辑</text>
          <text x="62" y="89" text-anchor="middle" font-size="12" fill="#41506a">文化常识广度</text>
          <text x="-64" y="89" text-anchor="middle" font-size="12" fill="#41506a">古代典籍深度</text>
          <text x="-102" y="-30" text-anchor="end" font-size="12" fill="#41506a">微积分运算</text>
        </g>
      </svg>
    </view>

    <view class="legend">
      <text class="legend-item">本周综合能力剖面</text>
      <text class="legend-item">凹陷区域即当前短板</text>
    </view>

    <view class="metrics">
      <view v-for="metric in metrics" :key="metric.label" class="metric-row">
        <text class="metric-label">{{ metric.label }}</text>
        <text class="metric-value">{{ metric.value }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  metrics: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.chart-shell {
  padding: 28rpx;
  border-radius: 34rpx;
  background: linear-gradient(180deg, #fbfcff, #f5f8ff);
  border: 2rpx solid #e6ebf5;
}

.title {
  font-size: 28rpx;
  font-weight: 800;
  color: #172033;
}

.chart-wrap {
  display: flex;
  justify-content: center;
  margin-top: 12rpx;
}

.chart {
  width: 100%;
  max-width: 620rpx;
  height: 430rpx;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
  margin-top: 10rpx;
}

.legend-item {
  color: #667085;
  font-size: 22rpx;
}

.metrics {
  margin-top: 16rpx;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  padding: 12rpx 0;
}

.metric-label {
  color: #475467;
  font-size: 23rpx;
}

.metric-value {
  color: #2563eb;
  font-size: 23rpx;
  font-weight: 800;
}
</style>
