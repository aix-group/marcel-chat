<script setup lang="ts">
import AdminNavigation from '@/components/AdminNavigation.vue'
</script>

<template>
  <div class="min-h-screen flex flex-col bg-white dark:bg-gray-900">
    <AdminNavigation />
    <main class="mx-auto w-full max-w-4xl mt-4">
      <router-view />
    </main>
  </div>
</template>
