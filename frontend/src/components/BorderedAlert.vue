<script setup lang="ts">
import InfoIcon from '@/components/icons/InfoIcon.vue'
import { computed } from 'vue'

interface Props {
  title?: string
  kind?: 'info' | 'danger' | 'success' | 'warning' | 'dark'
}

const props = withDefaults(defineProps<Props>(), {
  kind: 'info'
})

const alertClass = computed(() => {
  switch (props.kind) {
    case 'danger':
      return 'text-red-800 border-red-300 bg-red-50 dark:bg-gray-800 dark:text-red-400 dark:border-red-800'
    case 'success':
      return 'text-green-800 border-green-300 bg-green-50 dark:bg-gray-800 dark:text-green-400 dark:border-green-800'
    case 'warning':
      return 'text-yellow-800 border-yellow-300 bg-yellow-50 dark:bg-gray-800 dark:text-yellow-300 dark:border-yellow-800'
    case 'dark':
      return 'text-gray-800 border-gray-300 bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600'
    default: // info
      return 'text-blue-800 border-blue-300 bg-blue-50 dark:bg-gray-800 dark:text-blue-400 dark:border-blue-800'
  }
})
</script>

<template>
  <div
    class="flex items-center p-4 mt-4 text-sm border rounded-lg"
    :class="alertClass"
    role="alert"
  >
    <InfoIcon />
    <span class="sr-only">Info</span>
    <div>
      <span class="font-medium" v-if="title && title.length > 0">{{ title }}</span> <slot />
    </div>
  </div>
</template>
