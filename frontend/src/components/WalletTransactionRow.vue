<template>
  <view class="wallet-transaction-row" hover-class="wallet-transaction-row-hover" @tap="emit('select', transaction)">
    <view class="wallet-transaction-icon" :class="`tone-${transaction.iconTone || 'blue'}`">
      {{ transaction.iconLabel || '账' }}
    </view>
    <view class="wallet-transaction-main">
      <view class="wallet-transaction-title">{{ transaction.title }}</view>
      <view class="wallet-transaction-description">{{ transaction.description }}</view>
      <view class="wallet-transaction-time">{{ displayTime }}</view>
    </view>
    <view class="wallet-transaction-side">
      <view class="wallet-transaction-amount" :class="amountTone">{{ displayAmount }}</view>
      <view class="wallet-transaction-status" :class="`status-${transaction.status || 'pending'}`">
        {{ statusLabel }}
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { formatWalletAmount, walletStatusLabels } from '../data/walletMock'

const props = defineProps({
  transaction: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['select'])

const displayAmount = computed(() => formatWalletAmount(props.transaction.amount, true))
const amountTone = computed(() => Number(props.transaction.amount || 0) >= 0 ? 'positive' : 'negative')
const statusLabel = computed(() => walletStatusLabels[props.transaction.status] || props.transaction.status || '待处理')
const displayTime = computed(() => {
  const value = String(props.transaction.createdAt || '')
  const match = value.match(/^\d{4}-(\d{2})-(\d{2})\s+(.+)$/)
  if (!match) return value
  return `${Number(match[1])}月${Number(match[2])}日 ${match[3]}`
})
</script>

<style scoped>
.wallet-transaction-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  min-height: 126rpx;
  padding: 22rpx 0;
  border-bottom: 2rpx solid #edf2fb;
  transition: background-color 0.18s ease;
}

.wallet-transaction-row:last-child {
  border-bottom: 0;
}

.wallet-transaction-row-hover {
  background: #f8fbff;
}

.wallet-transaction-icon {
  width: 68rpx;
  height: 68rpx;
  flex: 0 0 68rpx;
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  border-radius: 22rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  font-size: 25rpx;
  line-height: 1;
  font-weight: 900;
}

.wallet-transaction-icon.tone-mint,
.wallet-transaction-icon.tone-cyan {
  border-color: #ccebe5;
  background: #effaf7;
  color: #258c78;
}

.wallet-transaction-icon.tone-warm {
  border-color: #f0ddd0;
  background: #fff7f1;
  color: #b56d49;
}

.wallet-transaction-main {
  min-width: 0;
  flex: 1;
}

.wallet-transaction-title {
  color: #1b2a41;
  overflow: hidden;
  font-size: 25rpx;
  line-height: 1.35;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wallet-transaction-description,
.wallet-transaction-time {
  overflow: hidden;
  color: #7d8da3;
  font-size: 19rpx;
  line-height: 1.4;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wallet-transaction-description {
  margin-top: 7rpx;
}

.wallet-transaction-time {
  margin-top: 4rpx;
  color: #9aa7b8;
}

.wallet-transaction-side {
  min-width: 132rpx;
  flex-shrink: 0;
  text-align: right;
}

.wallet-transaction-amount {
  color: #25364d;
  font-size: 26rpx;
  line-height: 1.25;
  font-weight: 950;
  white-space: nowrap;
}

.wallet-transaction-amount.positive {
  color: #238272;
}

.wallet-transaction-amount.negative {
  color: #4d596b;
}

.wallet-transaction-status {
  margin-top: 10rpx;
  color: #8291a6;
  font-size: 18rpx;
  line-height: 1.25;
  font-weight: 750;
  white-space: nowrap;
}

.wallet-transaction-status.status-settling,
.wallet-transaction-status.status-processing {
  color: #b87832;
}

.wallet-transaction-status.status-failed {
  color: #c36161;
}

.wallet-transaction-status.status-withdrawable,
.wallet-transaction-status.status-success,
.wallet-transaction-status.status-completed {
  color: #5e7fae;
}

@media (max-width: 350px) {
  .wallet-transaction-row {
    gap: 14rpx;
  }

  .wallet-transaction-side {
    min-width: 112rpx;
  }

  .wallet-transaction-description {
    max-width: 260rpx;
  }
}
</style>
