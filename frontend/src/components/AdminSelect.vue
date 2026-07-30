<template>
  <view
    ref="rootRef"
    class="admin-select"
    :class="[{ open, disabled }, `align-${menuAlign}`]"
  >
    <button
      class="admin-select__trigger"
      type="button"
      :disabled="disabled"
      :aria-label="ariaLabel || currentLabel"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @tap.stop="toggleSelect"
      @keydown.esc.stop.prevent="closeSelect"
    >
      <text class="admin-select__label">
        <text v-if="prefix" class="admin-select__prefix">{{ prefix }}</text>{{ currentLabel }}
      </text>
      <text class="admin-select__arrow" :class="{ open }">⌄</text>
    </button>

    <view v-if="open" class="admin-select__menu" role="listbox" @tap.stop>
      <button
        v-for="(option, index) in options"
        :key="optionKey(option, index)"
        class="admin-select__option"
        :class="{ selected: index === normalizedIndex }"
        type="button"
        role="option"
        :aria-selected="index === normalizedIndex"
        @tap.stop="chooseOption(index)"
      >
        <text class="admin-select__option-label">{{ optionLabel(option) }}</text>
        <text class="admin-select__check" :class="{ visible: index === normalizedIndex }">✓</text>
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  options: {
    type: Array,
    default: () => []
  },
  valueIndex: {
    type: [Number, String],
    default: 0
  },
  prefix: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请选择'
  },
  ariaLabel: {
    type: String,
    default: ''
  },
  menuAlign: {
    type: String,
    default: 'left'
  },
  disabled: Boolean
})

const emit = defineEmits(['change'])
const rootRef = ref(null)
const open = ref(false)
const selectId = `admin-select-${Math.random().toString(36).slice(2)}`

const normalizedIndex = computed(() => {
  const index = Number(props.valueIndex)
  if (!Number.isInteger(index) || index < 0 || index >= props.options.length) return 0
  return index
})

const currentLabel = computed(() => {
  const option = props.options[normalizedIndex.value]
  return option == null ? props.placeholder : optionLabel(option)
})

function optionLabel(option) {
  if (option && typeof option === 'object') return String(option.label ?? option.value ?? '')
  return String(option ?? '')
}

function optionKey(option, index) {
  if (option && typeof option === 'object') return `${option.value ?? option.label ?? index}-${index}`
  return `${String(option)}-${index}`
}

function toggleSelect() {
  if (props.disabled) return
  if (!open.value && typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('admin-select-open', { detail: selectId }))
  }
  open.value = !open.value
}

function closeSelect() {
  open.value = false
}

function chooseOption(index) {
  closeSelect()
  if (index === normalizedIndex.value) return
  emit('change', {
    detail: { value: String(index) },
    target: { value: String(index) }
  })
}

function handleOtherSelectOpen(event) {
  if (event?.detail !== selectId) closeSelect()
}

function handleDocumentPointerDown(event) {
  if (!open.value) return
  const element = rootRef.value?.$el || rootRef.value
  const path = typeof event.composedPath === 'function' ? event.composedPath() : []
  if (element && (path.includes(element) || element.contains?.(event.target))) return
  closeSelect()
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('admin-select-open', handleOtherSelectOpen)
  }
  if (typeof document !== 'undefined') {
    document.addEventListener('pointerdown', handleDocumentPointerDown, true)
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('admin-select-open', handleOtherSelectOpen)
  }
  if (typeof document !== 'undefined') {
    document.removeEventListener('pointerdown', handleDocumentPointerDown, true)
  }
})
</script>

<style scoped>
.admin-select {
  --admin-select-height: 38px;
  --admin-select-radius: 8px;
  --admin-select-font-size: 11px;
  --admin-select-font-weight: 650;
  --admin-select-padding-x: 11px;
  --admin-select-menu-min-width: 100%;
  position: relative;
  width: 100%;
  min-width: 0;
  color: #536277;
  z-index: 1;
}

.admin-select.open {
  z-index: 3200;
}

.admin-select__trigger {
  width: 100%;
  height: var(--admin-select-height);
  min-height: var(--admin-select-height);
  margin: 0;
  padding: 0 var(--admin-select-padding-x);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 9px;
  border: 1px solid #dbe4e8;
  border-radius: var(--admin-select-radius);
  box-sizing: border-box;
  color: inherit;
  background: #ffffff;
  cursor: pointer;
  font-size: var(--admin-select-font-size);
  font-weight: var(--admin-select-font-weight);
  line-height: 1;
  text-align: left;
  transition: border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
}

.admin-select__trigger::after,
.admin-select__option::after {
  border: 0;
}

.admin-select__trigger:hover,
.admin-select.open .admin-select__trigger {
  border-color: #8edecd;
  color: #315e58;
  background: #fbfefd;
  box-shadow: 0 0 0 3px rgba(80, 208, 180, 0.09);
}

.admin-select.disabled {
  opacity: 0.58;
}

.admin-select__label,
.admin-select__option-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-select__prefix {
  color: #30445c;
  font-weight: 800;
}

.admin-select__arrow {
  flex: 0 0 auto;
  color: #9aa5b1;
  font-size: 12px;
  transform-origin: center;
  transition: color 0.16s ease, transform 0.16s ease;
}

.admin-select__arrow.open {
  color: #2aaa90;
  transform: rotate(180deg);
}

.admin-select__menu {
  width: 100%;
  min-width: var(--admin-select-menu-min-width);
  max-height: 248px;
  padding: 6px;
  position: absolute;
  top: calc(100% + 7px);
  left: 0;
  overflow-y: auto;
  border: 1px solid #dce7e8;
  border-radius: 10px;
  box-sizing: border-box;
  background: #ffffff;
  box-shadow: 0 16px 38px rgba(35, 55, 74, 0.16), 0 3px 10px rgba(35, 55, 74, 0.07);
  transform-origin: top left;
  animation: admin-select-in 0.15s ease-out;
}

.admin-select.align-right .admin-select__menu {
  right: 0;
  left: auto;
  transform-origin: top right;
}

.admin-select__option {
  width: 100%;
  min-height: 40px;
  margin: 0;
  padding: 0 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border-radius: 7px;
  box-sizing: border-box;
  color: #506075;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  font-weight: 550;
  line-height: 1.35;
  text-align: left;
  transition: color 0.14s ease, background 0.14s ease;
}

.admin-select__option + .admin-select__option {
  margin-top: 2px;
}

.admin-select__option:hover {
  color: #294c49;
  background: #f1f6f7;
}

.admin-select__option.selected {
  color: #16826e;
  background: #eaf9f5;
  font-weight: 750;
}

.admin-select__check {
  flex: 0 0 auto;
  color: #22aa8f;
  font-size: 12px;
  font-weight: 900;
  opacity: 0;
}

.admin-select__check.visible {
  opacity: 1;
}

@keyframes admin-select-in {
  from {
    opacity: 0;
    transform: translateY(-4px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (max-width: 899px) {
  .admin-select {
    --admin-select-height: 42px;
    --admin-select-font-size: 13px;
    --admin-select-menu-min-width: 100%;
  }

  .admin-select__option {
    min-height: 42px;
    font-size: 13px;
  }
}
</style>
