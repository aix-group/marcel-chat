<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import assistantImage from '@/assets/assistant.svg'
import { login } from '@/services/admin.ts'
import { APIError } from '@/services/types'
import { useErrorStore } from '@/stores/errorStore'
import ErrorDisplay from '@/components/ErrorDisplay.vue'

const router = useRouter()
const route = useRoute()

const email = ref<string>('')
const password = ref<string>('')
const { addError } = useErrorStore()

async function submit() {
  try {
    const response = await login(email.value, password.value)
    if (response['username']) {
      const redirectUrl = Array.isArray(route.query.redirect)
        ? route.query.redirect[0]
        : route.query.redirect
      router.push(redirectUrl || { name: 'conversations' })
    }
  } catch (err) {
    addError({
      title: 'Whoops!',
      message: err instanceof APIError ? err.message : 'Unexpected error.',
      scope: 'admin-login'
    })
  }
}
</script>

<template>
  <div class="bg-white dark:bg-gray-900 min-h-screen">
    <div class="flex min-h-full flex-1 flex-col justify-center px-6 py-12 lg:px-8">
      <div class="sm:mx-auto sm:w-full sm:max-w-sm">
        <img
          :src="assistantImage"
          class="mx-auto w-auto size-12 rounded-full border-1 border-white/40"
          alt="logo"
          draggable="false"
        />

        <h2
          class="mt-2 text-center text-2xl/9 font-bold tracking-tight text-gray-900 dark:text-gray-100"
        >
          Marcel Login
        </h2>
      </div>

      <div class="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
        <form @submit.prevent="submit" class="space-y-6" action="#" method="POST">
          <div>
            <label for="email" class="block text-sm/6 font-medium text-gray-900 dark:text-white"
              >Email address</label
            >
            <div class="mt-2">
              <input
                name="email"
                id="email"
                autocomplete="email"
                required
                v-model="email"
                class="block w-full rounded-lg px-3 py-1.5 text-base text-gray-900 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-850 dark:text-gray-100 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus-visible:outline-blue-400 dark-visible:focus:outline-blue-300 sm:text-sm/6"
              />
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between">
              <label
                for="password"
                class="block text-sm/6 font-medium text-gray-900 dark:text-gray-100"
                >Password</label
              >
            </div>
            <div class="mt-2">
              <input
                type="password"
                name="password"
                id="password"
                autocomplete="current-password"
                required
                v-model="password"
                class="block w-full rounded-lg px-3 py-1.5 text-base text-gray-900 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-850 dark:text-gray-100 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus-visible:outline-blue-400 dark-visible:focus:outline-blue-300 sm:text-sm/6"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              class="flex w-full justify-center rounded-lg px-3 py-1.5 text-sm/6 font-semibold text-white shadow-xs bg-blue-500 hover:bg-blue-600 dark:hover:bg-blue-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-400 dark-visible:focus:outline-blue-300"
            >
              Sign in
            </button>
          </div>
        </form>
        <ErrorDisplay scope="admin-login" />
      </div>
    </div>
  </div>
</template>
