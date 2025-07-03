import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

export const useConsentStore = defineStore('consent', () => {
  const key = 'consentGiven'

  const consentGiven = ref<boolean>(localStorage.getItem(key) === 'true')
  // transient state for UI: after submitting the consent, we show it until users start a new conversation
  const pendingDismiss = ref<boolean>(false)

  watch(consentGiven, (newValue) => {
    localStorage.setItem(key, String(newValue))
  })

  function setConsent(value: boolean) {
    consentGiven.value = value
    if (value === true) {
      pendingDismiss.value = true
    }
  }

  function dismissConsentDialog() {
    pendingDismiss.value = false
  }

  const showConsentDialog = computed(() => {
    return !consentGiven.value || pendingDismiss.value
  })

  return {
    consentGiven,
    showConsentDialog,
    setConsent,
    dismissConsentDialog
  }
})
