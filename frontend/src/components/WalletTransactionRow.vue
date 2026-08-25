<template>
  <view class="wallet-transaction-row" hover-class="wallet-transaction-row-hover" @tap="emit('select', transaction)">
    <view class="wallet-transaction-icon" :class="`tone-${transaction.iconTone || 'blue'}`">
      <view class="wallet-transaction-icon-core">{{ transaction.iconLabel || '账' }}</view>
      <view
        v-if="amountSign"
        class="wallet-transaction-badge"
        :class="amountTone"
      >
        {{ amountSign }}
      </view>
    </view>

    <view class="wallet-transaction-main">
      <view class="wallet-transaction-title">{{ displayTitle }}</view>
      <view class="wallet-transaction-description">{{ transaction.description || '港研通钱包' }}</view>
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
import { formatWalletAmount, walletStatusLabels, walletTypeLabels } from '../data/walletPresentation'

const props = defineProps({
  transaction: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['select'])

const amountValue = computed(() => Number(props.transaction.amount || 0))
const displayTitle = computed(() => (
  props.transaction.title || walletTypeLabels[props.transaction.type] || '钱包交易'
))
const displayAmount = computed(() => {
  if (amountValue.value > 0) return `+${formatWalletAmount(amountValue.value)}`
  if (amountValue.value < 0) return `-${formatWalletAmount(amountValue.value)}`
  return formatWalletAmount(0)
})
const amountTone = computed(() => {
  if (amountValue.value > 0) return 'positive'
  if (amountValue.value < 0) return 'negative'
  return 'neutral'
})
const amountSign = computed(() => {
  if (amountValue.value > 0) return '+'
  if (amountValue.value < 0) return '−'
  return ''
})
const statusLabel = computed(() => walletStatusLabels[props.transaction.status] || props.transaction.status || '待处理')
const displayTime = computed(() => {
  const value = String(props.transaction.createdAt || '')
  const match = value.match(/^\d{4}-(\d{2})-(\d{2})\s+(.+)$/)
  if (match) return `${Number(match[1])}月${Number(match[2])}日 ${match[3]}`
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return `${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
})
</script>

<style scoped>
.wallet-transaction-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  min-height: 132rpx;
  padding: 24rpx 2rpx;
  border-bottom: 2rpx solid #e8ecf3;
  box-sizing: border-box;
  transition: background-color 0.18s ease, transform 0.18s ease;
}

.wallet-transaction-row:last-child {
  border-bottom: 0;
}

.wallet-transaction-row-hover {
  background: rgba(239, 244, 255, 0.66);
  transform: translateX(3rpx);
}

.wallet-transaction-icon {
  position: relative;
  width: 76rpx;
  height: 76rpx;
  flex: 0 0 76rpx;
  border-radius: 50%;
  background: linear-gradient(145deg, #160653, #30119c);
  box-shadow: 0 10rpx 22rpx rgba(33, 14, 105, 0.13);
  display: flex;
  align-items: center;
  justify-content: center;
}

.wallet-transaction-icon.tone-mint {
  background: linear-gradient(145deg, #128e78, #18b890);
  box-shadow: 0 10rpx 22rpx rgba(24, 149, 120, 0.13);
}

.wallet-transaction-icon.tone-cyan {
  background: linear-gradient(145deg, #216cc8, #299cf0);
  box-shadow: 0 10rpx 22rpx rgba(37, 121, 207, 0.13);
}

.wallet-transaction-icon.tone-warm {
  background: linear-gradient(145deg, #9f5e43, #d08a63);
  box-shadow: 0 10rpx 22rpx rgba(160, 96, 67, 0.13);
}

.wallet-transaction-icon-core {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: #ffffff;
  color: #25106c;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  line-height: 1;
  font-weight: 900;
}

.tone-mint .wallet-transaction-icon-core {
  color: #12866f;
}

.tone-cyan .wallet-transaction-icon-core {
  color: #247bc5;
}

.tone-warm .wallet-transaction-icon-core {
  color: #a46649;
}

.wallet-transaction-badge {
  position: absolute;
  left: -7rpx;
  top: -7rpx;
  width: 30rpx;
  height: 30rpx;
  border: 3rpx solid #f9fbff;
  border-radius: 50%;
  background: #64748b;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  font-family: var(--gyt-app-font) !important;
  font-size: 22rpx;
  line-height: 1;
  font-weight: 800;
}

.wallet-transaction-badge.positive {
  background: #12b981;
}

.wallet-transaction-badge.negative {
  background: #6f7890;
}

.wallet-transaction-main {
  min-width: 0;
  flex: 1;
}

.wallet-transaction-title,
.wallet-transaction-description,
.wallet-transaction-time {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wallet-transaction-title {
  color: #171b2b;
  font-size: 25rpx;
  line-height: 1.35;
  font-weight: 900;
}

.wallet-transaction-description {
  margin-top: 7rpx;
  color: #7f8597;
  font-size: 19rpx;
  line-height: 1.4;
  font-weight: 650;
}

.wallet-transaction-time {
  margin-top: 4rpx;
  color: #a0a5b3;
  font-size: 17rpx;
  line-height: 1.35;
  font-weight: 600;
}

.wallet-transaction-side {
  min-width: 144rpx;
  flex-shrink: 0;
  text-align: right;
}

.wallet-transaction-amount {
  color: #34394a;
  font-size: 25rpx;
  line-height: 1.25;
  font-weight: 900;
  white-space: nowrap;
}

.wallet-transaction-amount.positive {
  color: #0ea979;
}

.wallet-transaction-amount.negative {
  color: #34394a;
}

.wallet-transaction-amount.neutral {
  color: #7f8597;
}

.wallet-transaction-status {
  margin-top: 10rpx;
  color: #8990a2;
  font-size: 17rpx;
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
  color: #637fb1;
}

@media (max-width: 350px) {
  .wallet-transaction-row {
    gap: 14rpx;
  }

  .wallet-transaction-icon {
    width: 70rpx;
    height: 70rpx;
    flex-basis: 70rpx;
  }

  .wallet-transaction-side {
    min-width: 122rpx;
  }

  .wallet-transaction-title {
    font-size: 23rpx;
  }

  .wallet-transaction-description {
    max-width: 252rpx;
  }

  .wallet-transaction-amount {
    font-size: 23rpx;
  }
}
</style>
