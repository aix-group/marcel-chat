<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ChartCard from './ChartCard.vue'
import { fetchStatistics, type StatisticsRead, type Agg } from '@/services/admin'

const today = new Date().toISOString().split('T')[0]

const startDate = ref('')
const endDate = ref('')

const time_period = ref<string | null>(null)
const stats = ref<StatisticsRead | null>(null)
const selectedRange = ref<string | null>(null)

const rangeOptions = [
  { label: '7 Days', days: 7 },
  { label: '30 Days', days: 30 },
  { label: '90 Days', days: 90 },
  { label: '180 Days', days: 180 },
  { label: '1 Year', days: 365 }
]
function selectQuickRange(option: { label: string; days: number }) {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - (option.days - 1))

  const format = (d: Date) => d.toISOString().split('T')[0]

  selectedRange.value = option.label
  startDate.value = format(start)
  endDate.value = format(end)

  // Trigger chart update
  loadData()
}

const series = ref({
  users: [] as (number | null)[],
  conversations: [] as (number | null)[],
  messages: [] as (number | null)[],
  ratings: [] as (number | null)[]
})

const labels = ref({
  users: [] as string[],
  conversations: [] as string[],
  messages: [] as string[],
  ratings: [] as string[]
})

const msDay = 86_400_000 // 1 day in ms
const pad = (n: number) => n.toString().padStart(2, '0')
const dm = (d: Date) => `${pad(d.getDate())}.${pad(d.getMonth() + 1)}`
const dmy = (d: Date) => `${dm(d)}.${String(d.getFullYear()).slice(-2)}`

function buildLabels(
  starts: string[],
  agg: Agg,
  queryEndISO: string // inclusive end_date param
): string[] {
  const queryEnd = new Date(queryEndISO)

  return starts.map((iso, i) => {
    const start = new Date(iso)
    const nextStart = i < starts.length - 1 ? new Date(starts[i + 1]) : null
    const end = nextStart
      ? new Date(nextStart.getTime() - msDay) // next bin −1 day
      : queryEnd // last bin → query end

    if (agg === 'day') return start.toLocaleDateString('en-US', { day: '2-digit', month: 'short' })
    if (agg === 'year') return `${dmy(start)}-${dmy(end)}`
    return `${dm(start)}-${dm(end)}`
  })
}

const loadData = async () => {
  const start = new Date(startDate.value)
  const end = new Date(endDate.value)
  const diffDays = Math.trunc((end.getTime() - start.getTime()) / msDay)
  let agg: Agg = 'day'
  if (diffDays > 1000) {
    agg = 'year'
  } else if (diffDays > 180) {
    agg = 'month'
  } else if (diffDays > 30) {
    agg = 'week'
  }

  const data = await fetchStatistics(startDate.value, endDate.value, agg)
  time_period.value = `${startDate.value || ''} to ${endDate.value || ''}`
  stats.value = data

  const extractSeries = (
    items: { value: number | null }[],
    decimals: boolean = false
  ): (number | null)[] =>
    items
      .map((i: { value: number | null }) => i.value)
      .map((n: number | null) => (decimals && n !== null ? Number(n.toFixed(2)) : n))

  const keys = ['users', 'conversations', 'messages', 'ratings'] as const

  for (const key of keys) {
    const startList = data.time_series[key].map((x: { date: string }) => x.date)
    labels.value[key] = buildLabels(startList, agg, endDate.value)

    series.value[key] = extractSeries(data.time_series[key], key === 'ratings')
  }
}

onMounted(() => {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - 29)
  const format = (d: Date) => d.toISOString().split('T')[0]

  startDate.value = format(start)
  endDate.value = format(end)
  loadData()
})
</script>

<template>
  <div class="flex gap-4 p-4">
    <!--Date picker -->
    <div class="flex items-end gap-2 p-4">
      <div>
        <label for="start" class="block text-md font-medium text-gray-700 dark:text-gray-300"
          >Start date</label
        >
        <input
          type="date"
          id="start"
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
          :max="today"
          v-model="startDate"
        />
      </div>

      <div>
        <label for="end" class="block text-md font-medium text-gray-700 dark:text-gray-300"
          >End date</label
        >
        <input
          type="date"
          id="end"
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
          :max="today"
          :min="startDate"
          v-model="endDate"
        />
      </div>

      <button
        @click="loadData"
        class="px-4 py-2 mt-6 bg-blue-500 text-white shadow-sm rounded-lg hover:bg-blue-600"
      >
        Apply
      </button>
    </div>
    <!-- Group button -->
    <div class="flex items-end rounded-md p-4" role="group">
      <button
        v-for="option in rangeOptions"
        :key="option.label"
        class="h-[42px] px-3 rounded-xs text-sm shadow-sm font-medium text-gray-900 bg-white border border-gray-200 hover:bg-gray-100 hover:text-blue-500 focus:z-10 focus:ring-2 focus:ring-blue-500 focus:text-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white dark:hover:text-blue-500 dark:hover:bg-gray-700 dark:focus:ring-blue-500 dark:focus:text-blue-500"
        @click="selectQuickRange(option)"
      >
        {{ option.label }}
      </button>
    </div>
  </div>

  <!-- Totals -->
  <div id="totals-wrapper" class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
    <div class="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-white">Total Conversations</h2>
      <p id="total-conversations" class="text-2xl font-bold text-gray-900 dark:text-gray-200">
        {{ stats?.totals.total_conversations.toLocaleString('fr-FR') }}
      </p>
    </div>
    <div class="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-white">Total Users</h2>
      <p id="total-users" class="text-2xl font-bold text-gray-900 dark:text-gray-200">
        {{ stats?.totals.total_users.toLocaleString('fr-FR') }}
      </p>
    </div>
    <div class="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-white">Total Messages</h2>
      <p id="total-messages" class="text-2xl font-bold text-gray-900 dark:text-gray-200">
        {{ stats?.totals.total_messages.toLocaleString('fr-FR') }}
      </p>
    </div>
    <div class="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-white">Average Rating</h2>
      <p id="total-rating" class="text-2xl font-bold text-gray-900 dark:text-gray-200">
        {{
          stats?.totals.total_average_rating != null
            ? stats.totals.total_average_rating.toFixed(2)
            : 'N/A'
        }}
      </p>
    </div>
  </div>
  <!-- Charts -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <template v-if="series.users.some((v) => v)">
      <ChartCard
        title="New Users"
        :series="series.users"
        :labels="labels.users"
        :time_period="time_period"
      />
    </template>
    <template v-else>
      <div class="p-4 bg-white dark:bg-gray-800 rounded shadow text-gray-500 dark:text-gray-100">
        No user data in selected period
      </div>
    </template>

    <template v-if="series.conversations.some((v) => v)">
      <ChartCard
        title="Conversations"
        :series="series.conversations"
        :labels="labels.conversations"
        :time_period="time_period"
      />
    </template>
    <template v-else>
      <div class="p-4 bg-white dark:bg-gray-800 rounded shadow text-gray-500 dark:text-gray-100">
        No conversation data in selected period
      </div>
    </template>

    <template v-if="series.messages.some((v) => v)">
      <ChartCard
        title="Messages"
        :series="series.messages"
        :labels="labels.messages"
        :time_period="time_period"
      />
    </template>
    <template v-else>
      <div class="p-4 bg-white dark:bg-gray-800 rounded shadow text-gray-500 dark:text-gray-100">
        No message data in selected period
      </div>
    </template>

    <template v-if="series.ratings.some((v) => v)">
      <ChartCard
        title="Average Ratings"
        :series="series.ratings"
        :labels="labels.ratings"
        :time_period="time_period"
      />
    </template>
    <template v-else>
      <div class="p-4 bg-white dark:bg-gray-800 rounded shadow text-gray-500 dark:text-gray-100">
        No rating data in selected period
      </div>
    </template>
  </div>
</template>
