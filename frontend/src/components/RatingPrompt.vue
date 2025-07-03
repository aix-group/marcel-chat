<script setup lang="ts">
import { ref } from 'vue'

const rating = ref(5)
const hasInteracted = ref(false)
const emit = defineEmits(['submit'])

function onRatingChange() {
  hasInteracted.value = true
}
</script>

<template>
  <div id="rating-prompt" class="flex flex-col items-center mt-4 mb-4 space-y-2">
    <label for="rating-input" class="block text-sm font-medium text-gray-900 dark:text-gray-100">
      How useful is the conversation so far?
    </label>
    <input
      id="rating-input"
      v-model="rating"
      @input="onRatingChange"
      type="range"
      min="0"
      max="10"
      class="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-100 dark:bg-gray-800"
    />
    <span class="text-gray-900 dark:text-gray-100">{{ rating }}</span>
    <button
      id="rating-submit"
      @click="emit('submit', rating)"
      :disabled="!hasInteracted"
      :class="[
        'mb-1 px-3 py-1.5 rounded-lg transition text-white',
        hasInteracted
          ? 'focus:ring-blue-400 dark:focus:ring-blue-300 bg-blue-500 hover:bg-blue-600 dark:hover:bg-blue-400'
          : 'bg-gray-400 dark:bg-gray-600 cursor-not-allowed'
      ]"
    >
      Submit
    </button>
  </div>
</template>
