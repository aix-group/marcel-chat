import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ApplicationError {
  title: string
  message: string
  scope: string // TODO: consider constraining these
  retryAction?: () => void
  actionLabel?: string
}

export const useErrorStore = defineStore('errorStore', () => {
  const errors = ref<Array<ApplicationError>>([])

  function clearErrors(scope: string | null) {
    if (scope) {
      errors.value = errors.value.filter((e) => e.scope !== scope)
    } else {
      errors.value = []
    }
  }

  function addError(error: ApplicationError) {
    // Add an error if there is not already one with the same message and scope.
    const index = errors.value.findIndex(
      (e) => e.message === error.message && e.scope === error.scope
    )

    if (index === -1) {
      errors.value.push(error)
    }
  }

  return { errors, clearErrors, addError }
})
