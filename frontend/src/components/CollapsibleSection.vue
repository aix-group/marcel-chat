<template>
  <div>
    <span>
      <button class="flex items-center w-full" @click="toggleOpen">
        <svg
          :class="[
            'w-4 h-4 transition-transform duration-200',
            'text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white',
            { 'rotate-90': isOpen }
          ]"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 5l7 7-7 7"
          ></path>
        </svg>
        <span class="ml-1">{{ title }}</span>
      </button>
    </span>
    <div v-show="isOpen">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  title: string
}>()

const isOpen = ref(false)
function toggleOpen() {
  isOpen.value = !isOpen.value
}
</script>
