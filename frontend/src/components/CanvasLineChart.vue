<template>
  <view class="canvas-line-chart" aria-hidden="true">
    <canvas
      :id="canvasId"
      :canvas-id="canvasId"
      class="canvas-line-chart__surface"
    />
    <view v-if="interactive" class="canvas-line-chart__hit-layer">
      <view
        v-for="(point, index) in normalizedPoints"
        :key="`${point.x}-${point.y}-${index}`"
        class="canvas-line-chart__hit-point"
        :style="getPointHitStyle(point)"
        @touchstart.stop="emit('pointTouchStart', index)"
        @touchmove.stop="emit('pointTouchMove', index)"
        @touchend.stop="emit('pointTouchEnd', index)"
        @touchcancel.stop="emit('pointTouchEnd', index)"
        @tap.stop="emit('pointTap', index)"
      />
    </view>
  </view>
</template>

<script setup>
import { computed, getCurrentInstance, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'

const props = defineProps({
  canvasId: {
    type: String,
    required: true
  },
  points: {
    type: Array,
    default: () => []
  },
  gridY: {
    type: Array,
    default: () => []
  },
  viewWidth: {
    type: Number,
    default: 300
  },
  viewHeight: {
    type: Number,
    default: 112
  },
  lineColor: {
    type: String,
    default: '#16786f'
  },
  gridColor: {
    type: String,
    default: 'rgba(49, 76, 84, 0.12)'
  },
  pointFill: {
    type: String,
    default: '#ffffff'
  },
  pointStroke: {
    type: String,
    default: ''
  },
  fillColor: {
    type: String,
    default: ''
  },
  areaBaseline: {
    type: Number,
    default: 112
  },
  lineWidth: {
    type: Number,
    default: 3
  },
  gridLineWidth: {
    type: Number,
    default: 1
  },
  pointRadius: {
    type: Number,
    default: 4.5
  },
  activeIndex: {
    type: Number,
    default: -1
  },
  interactive: {
    type: Boolean,
    default: false
  },
  hitRadius: {
    type: Number,
    default: 13
  }
})

const emit = defineEmits([
  'pointTap',
  'pointTouchStart',
  'pointTouchMove',
  'pointTouchEnd'
])

const instance = getCurrentInstance()
let redrawTimer = null

const normalizedPoints = computed(() => (
  props.points
    .map((point) => ({
      x: Number(point?.x),
      y: Number(point?.y)
    }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y))
))

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function getPointHitStyle(point) {
  const width = Math.max(1, Number(props.viewWidth) || 300)
  const height = Math.max(1, Number(props.viewHeight) || 112)
  const radius = Math.max(8, Number(props.hitRadius) || 13)

  return {
    left: `${clamp((point.x / width) * 100, 0, 100)}%`,
    top: `${clamp((point.y / height) * 100, 0, 100)}%`,
    width: `${(radius * 2 / width) * 100}%`,
    height: `${(radius * 2 / height) * 100}%`
  }
}

function scheduleDraw(delay = 16) {
  if (redrawTimer !== null) {
    clearTimeout(redrawTimer)
  }
  redrawTimer = setTimeout(() => {
    redrawTimer = null
    drawChart()
  }, delay)
}

async function drawChart() {
  await nextTick()
  const component = instance?.proxy
  if (!component || typeof uni === 'undefined') return

  const query = uni.createSelectorQuery().in(component)
  query.select('.canvas-line-chart').boundingClientRect((rect) => {
    const width = Number(rect?.width || 0)
    const height = Number(rect?.height || 0)
    if (!width || !height) return

    const designWidth = Math.max(1, Number(props.viewWidth) || 300)
    const designHeight = Math.max(1, Number(props.viewHeight) || 112)
    const scaleX = width / designWidth
    const scaleY = height / designHeight
    const scaleLine = Math.max(0.75, Math.min(scaleX, scaleY))
    const points = normalizedPoints.value
    const context = uni.createCanvasContext(props.canvasId, component)

    context.clearRect(0, 0, width, height)
    context.setLineCap('round')
    context.setLineJoin('round')

    context.setStrokeStyle(props.gridColor)
    context.setLineWidth(Math.max(1, Number(props.gridLineWidth) * scaleLine))
    props.gridY.forEach((gridValue) => {
      const y = Number(gridValue)
      if (!Number.isFinite(y)) return
      context.beginPath()
      context.moveTo(0, y * scaleY)
      context.lineTo(width, y * scaleY)
      context.stroke()
    })

    if (points.length && props.fillColor) {
      const baseline = clamp(Number(props.areaBaseline) || designHeight, 0, designHeight) * scaleY
      context.beginPath()
      context.moveTo(points[0].x * scaleX, baseline)
      points.forEach((point) => context.lineTo(point.x * scaleX, point.y * scaleY))
      context.lineTo(points[points.length - 1].x * scaleX, baseline)
      context.closePath()
      context.setFillStyle(props.fillColor)
      context.fill()
    }

    if (points.length > 1) {
      context.beginPath()
      points.forEach((point, index) => {
        const x = point.x * scaleX
        const y = point.y * scaleY
        if (index === 0) context.moveTo(x, y)
        else context.lineTo(x, y)
      })
      context.setStrokeStyle(props.lineColor)
      context.setLineWidth(Math.max(1, Number(props.lineWidth) * scaleLine))
      context.stroke()
    }

    const pointStroke = props.pointStroke || props.lineColor
    points.forEach((point, index) => {
      const radius = Number(props.pointRadius) + (index === props.activeIndex ? 1 : 0)
      context.beginPath()
      context.arc(point.x * scaleX, point.y * scaleY, Math.max(2, radius * scaleLine), 0, Math.PI * 2)
      context.setFillStyle(props.pointFill)
      context.fill()
      context.setStrokeStyle(pointStroke)
      context.setLineWidth(Math.max(1, (index === props.activeIndex ? 4 : 3) * scaleLine))
      context.stroke()
    })

    context.draw()
  }).exec()
}

watch(
  () => [
    props.points,
    props.gridY,
    props.lineColor,
    props.gridColor,
    props.pointFill,
    props.pointStroke,
    props.fillColor,
    props.activeIndex
  ],
  () => scheduleDraw(),
  { deep: true, flush: 'post' }
)

onMounted(() => scheduleDraw(50))

onBeforeUnmount(() => {
  if (redrawTimer !== null) {
    clearTimeout(redrawTimer)
    redrawTimer = null
  }
})
</script>

<style scoped>
.canvas-line-chart,
.canvas-line-chart__surface,
.canvas-line-chart__hit-layer {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
}

.canvas-line-chart {
  position: relative;
  display: block;
}

.canvas-line-chart__surface,
.canvas-line-chart__hit-layer {
  position: absolute;
  inset: 0;
}

.canvas-line-chart__hit-layer {
  z-index: 2;
  pointer-events: none;
}

.canvas-line-chart__hit-point {
  position: absolute;
  min-width: 24px;
  min-height: 24px;
  transform: translate(-50%, -50%);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.001);
  pointer-events: auto;
}
</style>
