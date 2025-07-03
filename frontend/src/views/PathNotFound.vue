<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <section class="bg-white dark:bg-gray-900" data-testid="pathNotFoundMessage">
    <div class="py-8 px-4 mx-auto max-w-screen-xl lg:py-16 lg:px-6">
      <div class="mx-auto max-w-screen-sm text-center">
        <h1
          class="mb-4 text-7xl tracking-tight font-extrabold lg:text-9xl text-blue-500 dark:text-blue-500"
        >
          404
        </h1>
        <p class="mb-4 text-3xl tracking-tight font-bold text-gray-900 md:text-4xl dark:text-white">
          Something's missing.
        </p>
        <p class="mb-4 text-lg font-light text-gray-500 dark:text-gray-400">
          Sorry, we can't find that page.
        </p>
        <RouterLink
          :to="{ name: 'home' }"
          class="inline-flex text-white bg-blue-500 hover:bg-blue-600 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:focus:ring-blue-900 my-4"
          >Back to Homepage</RouterLink
        >
      </div>
    </div>
  </section>
</template>
