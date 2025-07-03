<script setup lang="ts">
import { logout } from '@/services/admin'
import { ref } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'

const route = useRoute()
const router = useRouter()

const links = [
  {
    label: 'Home',
    routeName: 'AdminHome',
    routeAliases: []
  },
  {
    label: 'Conversations',
    routeName: 'conversations',
    routeAliases: ['conversation']
  }
]

async function handleLogout() {
  await logout()
  router.push({ name: 'login' })
}

// only relevant for small screens
const navbarVisible = ref<boolean>(false)
function toggleNavbar() {
  navbarVisible.value = !navbarVisible.value
}
</script>

<template>
  <nav class="bg-white border-gray-200 dark:bg-gray-900">
    <div class="max-w-screen-xl flex flex-wrap items-center justify-between mx-auto p-4">
      <RouterLink
        :to="{ name: 'AdminHome' }"
        :class="'flex items-center space-x-3 rtl:space-x-reverse'"
      >
        <img
          src="@/assets/assistant.svg"
          class="h-8 rounded-full border-1 border-white/40"
          alt="Marcel Logo"
        />
        <span
          class="self-center text-2xl font-semibold whitespace-nowrap text-gray-800 dark:text-white"
          >Marcel Insights</span
        >
      </RouterLink>
      <div class="flex md:order-2 space-x-3 md:space-x-0 rtl:space-x-reverse">
        <button
          @click="handleLogout"
          type="button"
          class="text-white rounded-lg text-sm px-4 py-2 text-center font-medium focus:ring-4 focus:outline-none bg-blue-500 hover:bg-blue-600 focus:ring-blue-400 dark:hover:bg-blue-400 dark:focus:ring-blue-300"
        >
          Logout
        </button>
        <button
          type="button"
          class="inline-flex items-center p-2 w-10 h-10 justify-center text-sm text-gray-500 rounded-lg md:hidden hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200 dark:text-gray-400 dark:hover:bg-gray-700 dark:focus:ring-gray-600"
          aria-controls="navbar-cta"
          aria-expanded="false"
          @click="toggleNavbar"
        >
          <span class="sr-only">Open main menu</span>
          <svg
            class="w-5 h-5"
            aria-hidden="true"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 17 14"
          >
            <path
              stroke="currentColor"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M1 1h15M1 7h15M1 13h15"
            />
          </svg>
        </button>
      </div>
      <div
        class="items-center justify-between w-full md:flex md:w-auto md:order-1"
        :class="[navbarVisible ? '' : 'hidden']"
        id="navbar-cta"
      >
        <ul
          class="flex flex-col font-medium p-4 md:p-0 mt-4 border border-gray-100 rounded-lg bg-gray-50 md:space-x-8 rtl:space-x-reverse md:flex-row md:mt-0 md:border-0 md:bg-white dark:bg-gray-800 md:dark:bg-gray-900 dark:border-gray-700"
        >
          <li :key="link.routeName" v-for="link in links" @click="() => (navbarVisible = false)">
            <RouterLink
              :to="{ name: link.routeName }"
              :class="[
                'block py-2 px-3 md:p-0 rounded-sm',
                link.routeName === route.name || link.routeAliases.includes(String(route.name))
                  ? 'text-white bg-blue-500 md:bg-transparent md:text-blue-600 md:dark:text-blue-400'
                  : 'text-gray-800 rounded-sm hover:bg-gray-100 md:hover:bg-transparent md:hover:text-blue-600 md:dark:hover:text-blue-400 dark:text-white dark:hover:bg-gray-700 dark:hover:text-white md:dark:hover:bg-transparent dark:border-gray-700'
              ]"
              aria-current="page"
              >{{ link.label }}</RouterLink
            >
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>
