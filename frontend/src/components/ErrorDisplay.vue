<script setup lang="ts">
import { useErrorStore } from '@/stores/errorStore'
import BorderedAlert from '@/components/BorderedAlert.vue'
import { storeToRefs } from 'pinia'

export interface Props {
  scope?: string
}

const props = defineProps(['scope'])

const errorStore = useErrorStore()
const { errors } = storeToRefs(errorStore)
</script>

<template>
  <div v-for="error in errors" :key="`error-${error.scope}-${error.message.replace(' ', '')}`">
    <BorderedAlert title="Whoops!" kind="danger" v-if="error.scope === props.scope"
      >{{ error.message }}
      <template v-if="error.retryAction">
        <a @click="error.retryAction" class="font-medium underline cursor-pointer">{{
          error.actionLabel
        }}</a>
      </template>
    </BorderedAlert>
  </div>
</template>
