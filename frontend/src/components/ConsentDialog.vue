<script setup lang="ts">
import assistantImage from '@/assets/assistant.svg'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { ref } from 'vue'
import { useConsentStore } from '@/stores/consentStore'
import BorderedAlert from './BorderedAlert.vue'
import { putUserConsent } from '@/services/session'
import { APIError } from '@/services/types'
import { useErrorStore } from '@/stores/errorStore'
import ErrorDisplay from './ErrorDisplay.vue'

const { addError, clearErrors } = useErrorStore()
const consentStore = useConsentStore()
const showSuccess = ref<boolean>(false)
const showDeclinedWarning = ref<boolean>(false)

function convertMarkupToHtml(markup: string): string {
  return DOMPurify.sanitize(marked(markup, { async: false }))
}

const disclaimer = `Hello, this is Marcel! I can help you with **enrolment-related questions** for the **Master Data Science** at Marburg University. I am still learning and may not always provide perfect answers. Please verify important information and use discretion when following suggestions.

To improve this service, we are collecting anonymous usage statistics. You can find more about it in our [privacy terms](/privacy). Do you agree with that?`

const declinedMessage = `Sorry to hear that. If you don't want to use this service, please close the page.`

async function onSubmit() {
  try {
    await putUserConsent()
    showSuccess.value = true
    consentStore.setConsent(true)
  } catch (err) {
    addError({
      title: 'Whoops!',
      message: err instanceof APIError ? err.message : 'Unexpected error.',
      scope: 'consent-dialog',
      retryAction: async () => {
        clearErrors('consent-dialog')
        await onSubmit()
      },
      actionLabel: 'Retry.'
    })
  }
}

async function onDecline() {
  showDeclinedWarning.value = true
}
</script>

<template>
  <div class="flex flex-col mt-4 mb-3 space-y-3">
    <div class="grid lg:grid-cols-[28px_auto] grid-cols-1">
      <div class="col-span-2 flex items-center">
        <img class="mr-4 max-w-[28px] max-h-[28px]" :src="assistantImage" />
        <div>
          <span class="font-bold capitalize dark:text-white">Marcel</span>
        </div>
      </div>

      <div class="col-span-2 grid grid-cols-subgrid mt-2">
        <div class="col-start-1 lg:col-start-2 lg:ml-4">
          <!-- eslint-disable-next-line vue/no-v-html -->
          <span
            data-testid="consent-dialog"
            class="mt-3 prose dark:prose-invert"
            v-html="convertMarkupToHtml(disclaimer)"
          ></span>

          <template v-if="showSuccess">
            <div data-testid="consent-success">
              <BorderedAlert kind="success" title="Thank you!">Let's get started.</BorderedAlert>
            </div>
          </template>
          <template v-else>
            <div v-if="showDeclinedWarning" data-testid="consent-declined">
              <BorderedAlert kind="info" title="">{{ declinedMessage }}</BorderedAlert>
            </div>
            <div class="flex gap-x-2 mt-3">
              <button
                data-testid="consent-submit-button"
                @click="onSubmit"
                class="mb-1 px-3 py-1.5 rounded-lg transition text-white focus:ring-blue-400 dark:focus:ring-blue-300 bg-blue-500 hover:bg-blue-600 dark:hover:bg-blue-400"
              >
                Yes
              </button>
              <button
                data-testid="consent-decline-button"
                @click="onDecline"
                class="mb-1 px-3 py-1.5 rounded-lg transition text-white focus:ring-blue-400 dark:focus:ring-blue-300 bg-blue-500 hover:bg-blue-600 dark:hover:bg-blue-400"
              >
                No
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <ErrorDisplay scope="consent-dialog" />
  </div>
</template>
