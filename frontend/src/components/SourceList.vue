<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Source } from '@/stores/chatStore'
import GlobeIcon from './icons/GlobeIcon.vue'

export interface Props {
  sources: Array<Source>
}

const props = withDefaults(defineProps<Props>(), {
  sources: (): Source[] => []
})

// Validate favicons: the @error handler is called on 404
// We track source index -> visible in the map below.
// If a favicon does not resolve, we show a default icon
const faviconValidMap = ref<Record<number, boolean>>({})
watch(
  () => props.sources,
  (newSources) => {
    faviconValidMap.value = {}
    newSources.forEach((source, index) => {
      faviconValidMap.value[index] = !!source.favicon
    })
  },
  { immediate: true }
)

function onFaviconError(index: number) {
  faviconValidMap.value[index] = false
}
</script>

<template>
  <div
    class="text-gray-900 bg-white border border-gray-200 rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:text-white"
    v-if="sources.length"
  >
    <a
      v-for="(source, index) in sources"
      :key="index"
      :href="source.url"
      target="_blank"
      type="button"
      class="h-8 leading-tight relative inline-flex gap-x-2 items-center w-full px-2 py-2 text-sm focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700 dark:focus:ring-gray-500 dark:focus:text-white hover:bg-gray-100 hover:text-blue-600 dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:text-white"
      :class="{
        'rounded-t-lg border-b': index === 0,
        'border-b': index !== 0 && index !== sources.length - 1,
        'rounded-b-lg': index === sources.length - 1
      }"
    >
      <template v-if="faviconValidMap[index]">
        <img :src="source.favicon" class="w-4 h-4 flex-shrink-0" @error="onFaviconError(index)" />
      </template>
      <template v-else>
        <GlobeIcon class="w-4 h-4 flex-shrink-0" />
      </template>

      <span class="truncate">{{ source.title }}</span>
    </a>
  </div>
</template>
