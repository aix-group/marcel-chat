import { ref } from 'vue'

const notification = ref<{
  message: string
  kind: 'info' | 'danger' | 'success' | 'warning'
} | null>(null)

let timeoutId: ReturnType<typeof setTimeout>

export function useNotification() {
  function notify(
    message: string,
    kind: 'info' | 'danger' | 'success' | 'warning' = 'info',
    duration = 2000
  ) {
    notification.value = { message, kind }

    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      notification.value = null
    }, duration)
  }

  return {
    notification,
    notify
  }
}
