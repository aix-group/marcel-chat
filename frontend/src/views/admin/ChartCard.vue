<script setup lang="ts">
import VueApexCharts from 'vue3-apexcharts'
import { computed } from 'vue'

const props = defineProps<{
  title: string
  time_period: string | null
  series: (number | null)[]
  labels: string[]
}>()

const chartOptions = computed(() => {
  return {
    chart: {
      type: 'bar',
      toolbar: { show: false },
      fontFamily: 'Inter, sans-serif',
      dropShadow: { enabled: false }
    },
    tooltip: {
      enabled: true,
      x: { show: false },
      style: {
        fontSize: '14px',
        fontFamily: 'Inter, sans-serif',
        color: '#1F2937'
      }
    },
    xaxis: {
      categories: props.labels,
      labels: {
        show: true,
        style: {
          colors: '#4B5563',
          fontSize: '12px',
          fontFamily: 'Inter, sans-serif'
        }
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
      crosshairs: {
        fill: {
          type: 'gradient',
          gradient: {
            colorFrom: '#D8E3F0',
            colorTo: '#BED1E6',
            stops: [0, 100],
            opacityFrom: 0.4,
            opacityTo: 0.5
          }
        }
      },
      tooltip: {
        enabled: true
      }
    },
    yaxis: {
      labels: {
        show: true,
        formatter: function (val: number): string | number {
          return Number.isInteger(val) ? val : ''
        }
      }
    },
    plotOptions: {
      bar: {
        borderRadius: 4,
        columnWidth: '50%'
      }
    },
    dataLabels: {
      enabled: false
    },
    grid: {
      show: true,
      strokeDashArray: 4,
      padding: { left: 2, right: 2, top: 0 }
    }
  }
})
</script>

<template>
  <div
    class="w-full bg-white rounded-lg dark:text-gray-800 shadow-sm dark:bg-gray-800 p-2 md:p-6 mb-2"
  >
    <div class="flex justify-between">
      <div>
        <p class="text-base font-normal text-gray-500 dark:text-gray-100">
          {{ title }}
        </p>
        <p class="text-sm text-gray-400 dark:text-gray-100">{{ time_period }}</p>
      </div>
    </div>
    <VueApexCharts
      :options="chartOptions"
      :series="[{ name: title, data: series, color: '#3B82F6' }]"
      type="bar"
      height="300"
    />
  </div>
</template>
