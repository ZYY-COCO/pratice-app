<template>
  <AppPageHeader :title="title" :subtitle="subtitle" @back="emit('back')">
    <template #right><slot name="right" /></template>
  </AppPageHeader>
</template>

<script setup>
import AppPageHeader from './ui/AppPageHeader.vue'

defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['back'])
</script>
