<script setup lang="ts">
import { computed } from 'vue'
import InfoIcon from '@/components/icons/InfoIcon.vue'

interface Props {
  message: string
  kind?: 'info' | 'danger' | 'success' | 'warning'
}

const props = withDefaults(defineProps<Props>(), {
  kind: 'info'
})

const notificationClass = computed(() => {
  switch (props.kind) {
    case 'danger':
      return 'dark:text-white text-red-600 bg-red-100 dark:bg-red-700 border-red-600 dark:border-red-400'
    case 'warning':
      return 'dark:text-white text-yellow-600 bg-yellow-100 dark:bg-yellow-700 border-yellow-600 dark:border-yellow-400'
    case 'info':
      return 'dark:text-white text-blue-600 bg-blue-100 dark:bg-blue-700 border-blue-600 dark:border-blue-400'
    default: // success
      return 'dark:text-white text-green-600 bg-green-100 dark:bg-green-700 border-green-600 dark:border-green-400'
  }
})
</script>

<template>
  <div
    class="flex items-center p-4 mb-4 text-sm border rounded-lg min-w-[70vw] absolute bottom-0 left-1/2 transform -translate-x-1/2 z-[1000]"
    :class="notificationClass"
    role="alert"
  >
    <InfoIcon />
    <span class="sr-only">Info</span>
    <div>{{ message }}</div>
  </div>
</template>
