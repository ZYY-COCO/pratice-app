<template>
  <view class="circle-resource-section" :class="`is-${resourceType}`">
    <view v-if="loading" class="circle-resource-state">正在整理{{ sectionLabel }}…</view>
    <view v-else-if="loadError" class="circle-resource-state">
      <view class="circle-resource-state-mark">{{ resourceType === 'material' ? '资' : '课' }}</view>
      <strong>{{ resourceType === 'material' ? '推荐资料正在整理' : '课程正在筹备' }}</strong>
      <button type="button" @tap="loadResources">重新加载</button>
    </view>
    <view v-else-if="!items.length" class="circle-resource-state">
      <view class="circle-resource-state-mark">{{ resourceType === 'material' ? '资' : '课' }}</view>
      <strong>{{ resourceType === 'material' ? '暂未上架推荐资料' : '课程正在筹备' }}</strong>
    </view>
    <view v-else class="circle-resource-grid">
      <view v-for="item in items" :key="item.id" class="circle-resource-card">
        <image v-if="item.cover_url" class="circle-resource-cover" :src="item.cover_url" mode="aspectFill" />
        <view class="circle-resource-card-body">
          <view class="circle-resource-card-topline">
            <text v-if="item.subject" class="circle-resource-subject">{{ item.subject }}</text>
            <text v-if="resourceType === 'course'" class="circle-resource-price">{{ formatCoursePrice(item.course_price) }}</text>
          </view>
          <view class="circle-resource-name">{{ item.title }}</view>
          <view v-if="item.summary" class="circle-resource-summary">{{ item.summary }}</view>
          <view v-if="item.tags?.length" class="circle-resource-tags">
            <text v-for="tag in item.tags.slice(0, 3)" :key="`${item.id}-${tag}`">{{ tag }}</text>
          </view>
          <view v-if="resourceType === 'material'" class="circle-resource-material-action">
            <text v-if="item.access_code">提取码：{{ item.access_code }}</text>
            <button type="button" @tap="copyMaterialLink(item)">复制链接</button>
          </view>
          <view v-else class="circle-resource-course-meta">
            <text>{{ item.instructor_name || '港研通教研组' }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchCircleResources } from '../api/circleResources'

const props = defineProps({
  resourceType: {
    type: String,
    default: 'material',
    validator: (value) => ['material', 'course'].includes(value)
  }
})

const items = ref([])
const loading = ref(true)
const loadError = ref(false)
const sectionLabel = computed(() => (props.resourceType === 'material' ? '推荐资料' : '精选课程'))

onMounted(() => {
  void loadResources()
})

async function loadResources() {
  loading.value = true
  loadError.value = false
  try {
    const response = await fetchCircleResources(props.resourceType)
    items.value = Array.isArray(response?.items) ? response.items : []
  } catch (error) {
    items.value = []
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function formatCoursePrice(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '即将上线'
  if (number === 0) return '免费'
  return `¥${Number.isInteger(number) ? number : number.toFixed(2)}`
}

function copyMaterialLink(item) {
  const shareUrl = String(item?.share_url || '').trim()
  if (!shareUrl) {
    uni.showToast({ title: '链接正在补充中', icon: 'none' })
    return
  }
  const text = [
    `百度网盘链接：${shareUrl}`,
    item?.access_code ? `提取码：${item.access_code}` : ''
  ].filter(Boolean).join('\n')
  uni.setClipboardData({
    data: text,
    success: () => uni.showToast({ title: '链接已复制', icon: 'success' }),
    fail: () => uni.showToast({ title: '复制失败，请稍后重试', icon: 'none' })
  })
}
</script>

<style scoped>
.circle-resource-section{width:100%;box-sizing:border-box;padding:4rpx 20rpx 72rpx}.circle-resource-state{min-height:580rpx;padding:42rpx 30rpx;display:flex;align-items:center;flex-direction:column;justify-content:center;text-align:center}.circle-resource-state-mark{width:104rpx;height:104rpx;display:grid;place-items:center;border-radius:24rpx;background:#e7f7f2;color:#2d9a82;font-size:38rpx;font-weight:850}.circle-resource-state strong{margin-top:26rpx;color:#495b70;font-size:30rpx;font-weight:850}.circle-resource-state button{height:62rpx;margin:24rpx 0 0;padding:0 28rpx;display:inline-flex;align-items:center;justify-content:center;border:1rpx solid #dbe8e7;border-radius:12rpx;background:#fff;color:#398c7b;font-size:24rpx;font-weight:750;line-height:1}.circle-resource-state button::after,.circle-resource-material-action button::after{border:0}.circle-resource-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20rpx}.circle-resource-card{min-width:0;overflow:hidden;border:1rpx solid rgba(220,230,234,.92);border-radius:16rpx;background:rgba(255,255,255,.94);box-shadow:0 10rpx 28rpx rgba(47,65,84,.05)}.circle-resource-cover{width:100%;height:188rpx;display:block;background:#edf3f3}.circle-resource-card-body{padding:19rpx 18rpx 18rpx}.circle-resource-card-topline{min-height:30rpx;display:flex;align-items:center;justify-content:space-between;gap:10rpx}.circle-resource-subject{min-width:0;overflow:hidden;color:#338f7c;font-size:20rpx;font-weight:750;text-overflow:ellipsis;white-space:nowrap}.circle-resource-price{flex:0 0 auto;color:#cf7650;font-size:22rpx;font-weight:850}.circle-resource-name{margin-top:8rpx;overflow:hidden;color:#33465c;font-size:27rpx;font-weight:850;line-height:1.42;text-overflow:ellipsis;white-space:nowrap}.circle-resource-summary{min-height:58rpx;margin-top:9rpx;display:-webkit-box;overflow:hidden;color:#8291a0;font-size:21rpx;line-height:1.5;-webkit-box-orient:vertical;-webkit-line-clamp:2}.circle-resource-tags{min-height:34rpx;margin-top:12rpx;display:flex;align-items:center;gap:7rpx;overflow:hidden}.circle-resource-tags text{max-width:122rpx;padding:5rpx 9rpx;overflow:hidden;border-radius:99rpx;background:#eef6f5;color:#66827f;font-size:18rpx;font-weight:650;text-overflow:ellipsis;white-space:nowrap}.circle-resource-material-action,.circle-resource-course-meta{min-height:52rpx;margin-top:13rpx;padding-top:12rpx;display:flex;align-items:center;justify-content:space-between;gap:10rpx;border-top:1rpx solid #edf1f2}.circle-resource-material-action>text,.circle-resource-course-meta text{min-width:0;overflow:hidden;color:#93a0aa;font-size:19rpx;text-overflow:ellipsis;white-space:nowrap}.circle-resource-material-action button{height:44rpx;flex:0 0 auto;margin:0;padding:0 14rpx;display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:9rpx;background:#e4f6f1;color:#268b75;font-size:20rpx;font-weight:800;line-height:1}@media(max-width:360px){.circle-resource-grid{grid-template-columns:1fr}.circle-resource-cover{height:220rpx}}
</style>
