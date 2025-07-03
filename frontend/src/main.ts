import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import { definePreset } from '@primeuix/themes'

import App from './App.vue'
import router from './router'
import './assets/main.css'

const MyPreset = definePreset(Aura, {
  // Override selected settings from the Aura theme:
  // https://github.com/primefaces/primeuix/blob/main/packages/themes/src/presets/aura/base/index.ts
  semantic: {
    // Taken from Tailwind theme:
    // https://github.com/tailwindlabs/tailwindcss/blob/main/packages/tailwindcss/theme.css
    gray: {
      0: '#ffffff',
      50: 'oklch(98.5% 0.002 247.839)',
      100: 'oklch(96.7% 0.003 264.542)',
      200: 'oklch(92.8% 0.006 264.531)',
      300: 'oklch(87.2% 0.01 258.338)',
      400: 'oklch(70.7% 0.022 261.325)',
      500: 'oklch(55.1% 0.027 264.364)',
      600: 'oklch(44.6% 0.03 256.802)',
      700: 'oklch(37.3% 0.034 259.733)',
      800: 'oklch(27.8% 0.033 256.848)',
      900: 'oklch(21% 0.034 264.665)',
      950: 'oklch(13% 0.028 261.692)'
    },
    colorScheme: {
      dark: {
        content: {
          background: '{gray.900}'
        },
        surface: {
          0: '#ffffff',
          50: '{gray.50}',
          100: '{gray.100}',
          200: '{gray.200}',
          300: '{gray.300}',
          400: '{gray.400}',
          500: '{gray.500}',
          600: '{gray.600}',
          700: '{gray.700}',
          800: '{gray.800}',
          900: '{gray.900}',
          950: '{gray.950}'
        }
      }
    }
  }
})

const app = createApp(App)
app.use(PrimeVue, {
  theme: {
    preset: MyPreset
  }
})
app.use(createPinia())
app.use(router)

app.mount('#app')
