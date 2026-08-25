<template>
  <view class="mentor-card" @tap="emit('open')">
    <view class="mentor-card-top">
      <view class="mentor-person">
        <view class="mentor-avatar" :class="`tone-${mentor.avatarTone || 'blue'}`">
          <image v-if="mentor.avatarUrl" :src="mentor.avatarUrl" mode="aspectFill" />
          <text v-else>{{ mentor.avatar || mentor.maskedName?.slice(0, 1) || '研' }}</text>
        </view>
        <view class="mentor-person-copy">
          <view class="mentor-name-row">
            <text class="mentor-name">{{ mentor.maskedName }}</text>
            <text v-if="mentor.verified" class="mentor-verified">✓ 已认证</text>
          </view>
          <view class="mentor-school">{{ mentor.school }}</view>
        </view>
      </view>
      <button
        class="mentor-favorite"
        :class="{ active: favorite }"
        :aria-label="favorite ? '取消收藏前辈' : '收藏前辈'"
        :aria-pressed="favorite"
        @tap.stop="emit('toggle-favorite')"
      >{{ favorite ? '♥' : '♡' }}</button>
    </view>

    <view class="mentor-major-row">
      <text>{{ mentor.major }} · {{ mentor.admissionYear }}级</text>
      <text class="mentor-score">初试 {{ mentor.score }} 分</text>
    </view>

    <view class="mentor-bio">{{ mentor.bio }}</view>

    <view class="mentor-skills">
      <text v-for="skill in mentor.skills?.slice(0, 3)" :key="skill">{{ skill }}</text>
    </view>

    <view class="mentor-service-row">
      <view class="mentor-service-meta">
        <text class="mentor-rating">{{ mentor.ratingCount ? `★ ${Number(mentor.rating || 0).toFixed(1)}` : '暂无评分' }}</text>
        <text>已咨询 {{ mentor.consultCount || 0 }} 人</text>
      </view>
      <view class="mentor-status" :class="{ online: mentor.onlineStatus === 'online' }">
        <view class="mentor-status-dot"></view>
        <text>{{ mentor.availabilityLabel }}</text>
      </view>
    </view>

    <view class="mentor-card-footer">
      <view class="mentor-price">
        <text>{{ mentor.priceLabel }}</text>
        <view>{{ mentor.consultationWindowMinutes || 60 }}分钟咨询窗口</view>
      </view>
      <button class="mentor-consult-button" @tap.stop="emit('consult')">{{ viewOnly ? '查看' : mentor.actionLabel }}</button>
    </view>
  </view>
</template>

<script setup>
defineProps({
  mentor: {
    type: Object,
    required: true
  },
  favorite: {
    type: Boolean,
    default: false
  },
  viewOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['open', 'consult', 'toggle-favorite'])
</script>

<style scoped>
.mentor-card {
  position: relative;
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  padding: 26rpx;
  border: 2rpx solid rgba(229, 226, 224, 0.94);
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 10rpx 28rpx rgba(48, 42, 38, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.mentor-card:active {
  transform: scale(0.985);
  box-shadow: 0 10rpx 24rpx rgba(52, 120, 246, 0.1);
}

.mentor-card-top,
.mentor-person,
.mentor-name-row,
.mentor-major-row,
.mentor-service-row,
.mentor-card-footer {
  display: flex;
  align-items: center;
}

.mentor-card-top,
.mentor-major-row,
.mentor-service-row,
.mentor-card-footer {
  justify-content: space-between;
  gap: 10rpx;
}

.mentor-person {
  min-width: 0;
  flex: 1;
  gap: 14rpx;
}

.mentor-avatar {
  width: 82rpx;
  height: 82rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.84);
  border-radius: 50%;
  color: #3478f6;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  font-size: 29rpx;
  line-height: 1;
  font-weight: 900;
  flex-shrink: 0;
  box-shadow: 0 6rpx 16rpx rgba(35, 76, 139, 0.1);
}

.mentor-avatar image {
  width: 100%;
  height: 100%;
  border-radius: inherit;
}

.mentor-avatar.tone-blue {
  background: #e6efff;
  color: #3478f6;
}

.mentor-avatar.tone-mint {
  background: #e2f4ef;
  color: #198777;
}

.mentor-avatar.tone-violet {
  background: #eeeafe;
  color: #7162bd;
}

.mentor-avatar.tone-warm {
  background: #f9eee1;
  color: #b66c32;
}

.mentor-person-copy {
  min-width: 0;
  flex: 1;
}

.mentor-name-row {
  min-width: 0;
  gap: 8rpx;
}

.mentor-name {
  min-width: 0;
  color: #172033;
  overflow: hidden;
  font-size: 29rpx;
  line-height: 1.2;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mentor-verified {
  padding: 5rpx 9rpx;
  border-radius: 999rpx;
  background: #eaf2ff;
  color: #3478f6;
  font-size: 17rpx;
  line-height: 1.2;
  font-weight: 800;
  flex-shrink: 0;
}

.mentor-school {
  margin-top: 7rpx;
  color: #5f6f85;
  overflow: hidden;
  font-size: 22rpx;
  line-height: 1.25;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mentor-favorite {
  width: 54rpx;
  height: 54rpx;
  min-width: 54rpx;
  min-height: 54rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(237, 244, 255, 0.86);
  color: #7890ae;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  line-height: 1;
  transition: transform 180ms ease, color 180ms ease, background-color 180ms ease;
}

.mentor-favorite::after,
.mentor-consult-button::after {
  border: 0;
}

.mentor-favorite.active {
  background: #edf4ff;
  color: #3478f6;
}

.mentor-favorite:active,
.mentor-consult-button:active {
  transform: scale(0.96);
}

.mentor-major-row {
  margin-top: 20rpx;
  padding: 16rpx 18rpx;
  border-radius: 18rpx;
  background: var(--gyt-primary-tint, #f4f8ff);
  color: #354b68;
  font-size: 23rpx;
  line-height: 1.35;
  font-weight: 800;
}

.mentor-major-row > text:first-child {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mentor-score {
  color: #3478f6;
  font-size: 21rpx;
  font-weight: 900;
  white-space: nowrap;
}

.mentor-bio {
  margin-top: 16rpx;
  color: #56667d;
  font-size: 22rpx;
  line-height: 1.6;
  font-weight: 560;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.mentor-skills {
  min-height: 46rpx;
  margin-top: 14rpx;
  overflow: hidden;
  display: flex;
  flex-wrap: wrap;
  gap: 9rpx;
}

.mentor-skills text {
  padding: 8rpx 13rpx;
  border-radius: 999rpx;
  background: rgba(237, 244, 255, 0.92);
  color: #4b6fa8;
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 800;
}

.mentor-service-row {
  margin-top: 18rpx;
  padding-top: 16rpx;
  border-top: 2rpx solid rgba(78, 113, 151, 0.1);
}

.mentor-service-meta {
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6rpx 12rpx;
  color: #728198;
  font-size: 20rpx;
  line-height: 1.3;
  font-weight: 700;
}

.mentor-rating {
  color: #e49a31;
  font-weight: 900;
}

.mentor-status {
  padding: 7rpx 11rpx;
  border-radius: 999rpx;
  background: #f3f5f8;
  color: #718197;
  display: inline-flex;
  align-items: center;
  gap: 5rpx;
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 800;
  white-space: nowrap;
  flex-shrink: 0;
}

.mentor-status.online {
  background: #e5f6ec;
  color: #218653;
}

.mentor-status-dot {
  width: 9rpx;
  height: 9rpx;
  border-radius: 50%;
  background: #a5b0bf;
}

.mentor-status.online .mentor-status-dot {
  background: #2caf68;
  box-shadow: 0 0 0 4rpx rgba(44, 175, 104, 0.12);
}

.mentor-card-footer {
  margin-top: 18rpx;
}

.mentor-price text {
  color: #172033;
  font-size: 29rpx;
  line-height: 1.1;
  font-weight: 900;
}

.mentor-price view {
  margin-top: 6rpx;
  color: #8694a8;
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 650;
}

.mentor-consult-button {
  min-width: 168rpx;
  min-height: 70rpx;
  margin: 0;
  padding: 0 22rpx;
  border: 0;
  border-radius: 20rpx;
  background: var(--gyt-primary, #3478f6);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 900;
  box-shadow: 0 10rpx 22rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.18));
  transition: transform 180ms ease;
  flex-shrink: 0;
}

@media (max-width: 350px) {
  .mentor-card {
    padding: 22rpx;
  }

  .mentor-verified {
    padding-right: 7rpx;
    padding-left: 7rpx;
    font-size: 15rpx;
  }

  .mentor-consult-button {
    min-width: 148rpx;
    padding-right: 16rpx;
    padding-left: 16rpx;
    font-size: 20rpx;
  }
}
</style>
