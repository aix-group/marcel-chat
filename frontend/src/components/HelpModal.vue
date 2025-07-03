<script setup lang="ts">
import { ref } from 'vue'
import CloseIcon from '@/components/icons/CloseIcon.vue'

const showModal = ref(false)

const version = __APP_VERSION__
const commit = __GIT_COMMIT__
</script>

<template>
  <!-- Help icon -->
  <div class="lg:flex fixed lg:bottom-0 xs:top-0 right-0 px-3 py-3 z-10">
    <div aria-label="Help" class="flex">
      <button
        id="show-shortcuts-button"
        class="w-6 h-6 flex items-center justify-center text-xs rounded-full text-gray-600 bg-gray-300/20 dark:text-gray-100 dark:bg-gray-50/30"
        @click="showModal = true"
      >
        ?
      </button>
    </div>
  </div>

  <div
    v-if="showModal"
    class="fixed inset-0 flex items-center justify-center z-20 bg-black/50"
    @click.self="showModal = false"
  >
    <div class="w-2xl m-6 px-5 py-4 rounded-lg bg-white">
      <div class="flex items-center">
        <span class="text-gray-800 text-lg">About Marcel</span>
        <button
          type="button"
          class="ml-auto rounded-lg text-sm p-1.5 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-100 bg-transparent"
          @click="showModal = false"
        >
          <CloseIcon class="w-5 h-5" />
          <span class="sr-only">Close modal</span>
        </button>
      </div>

      <hr class="h-px my-2 bg-gray-200 border-0" />

      <div class="text-gray-800">
        <p>
          Marcel is a chatbot developed at Marburg University. Marcel is a prototype and is
          constantly being improved. By using Marcel you agree that we can use anonymous
          conversation data to improve the chatbot. Marcel will not ask you for personal information
          (name, student ID) and you should not proactively provide it in conversations. For more
          details please refer to our
          <RouterLink class="font-medium underline hover:no-underline" :to="{ name: 'privacy' }"
            >privacy policy</RouterLink
          >
          and
          <a
            href="https://www.mathematik.uni-marburg.de/legal/datenschutz.html#english"
            class="font-medium underline hover:no-underline"
            >legal notice</a
          >.
        </p>
      </div>

      <div class="my-4 flex flex-row items-center gap-6 max-w-full overflow-hidden">
        <img
          src="@/assets/umr.svg"
          alt="Marburg University Logo"
          class="h-20 w-auto flex-grow flex-shrink min-w-0 object-contain"
        />
        <img
          src="@/assets/tagline.svg"
          alt="Marcel Marburg Study Support Chatbot Logo"
          class="h-20 w-auto flex-grow flex-shrink min-w-0 object-contain"
        />
      </div>

      <hr class="h-px my-2 bg-gray-200 border-0" />

      <div class="text-gray-400">
        <p>Version: {{ version }} ({{ commit }})</p>
      </div>
    </div>
  </div>
</template>
