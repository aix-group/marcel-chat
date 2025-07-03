<template>
  <div class="m-auto text-center max-w-md px-2" data-testid="welcome-message">
    <div class="flex justify-center mt-8">
      <div class="flex -space-x-4 mb-1">
        <button>
          <img
            src="@/assets/assistant.svg"
            class="size-12 border-white/40 border-1 rounded-full"
            alt="logo"
            draggable="false"
          />
        </button>
      </div>
    </div>
    <div class="mt-2 mb-5 text-2xl font-semibold text-gray-800 dark:text-gray-200">
      <div class="line-clamp-1">Hello, this is Marcel.</div>
      <div>How can I help you today?</div>
    </div>
  </div>
</template>
