import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useJobsStore = defineStore('jobs', () => {
  const jobs = ref([])
  const total = ref(0)
  const loading = ref(false)
  const currentJob = ref(null)

  async function fetchJobs(params = {}) {
    loading.value = true
    try {
      const response = await api.get('/api/jobs', { params })
      jobs.value = response.data.jobs
      total.value = response.data.total
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function getJob(jobUuid) {
    const response = await api.get(`/api/jobs/${jobUuid}`)
    currentJob.value = response.data
    return response.data
  }

  async function createJob(jobData) {
    const response = await api.post('/api/jobs', jobData)
    await fetchJobs()
    return response.data
  }

  async function createBatchJobs(batchData) {
    const response = await api.post('/api/jobs/batch', batchData)
    await fetchJobs()
    return response.data
  }

  async function cancelJob(jobUuid) {
    await api.post(`/api/jobs/${jobUuid}/cancel`)
    await fetchJobs()
  }

  async function deleteJob(jobUuid) {
    await api.delete(`/api/jobs/${jobUuid}`)
    await fetchJobs()
  }

  function getDownloadUrl(jobUuid) {
    return `/api/jobs/${jobUuid}/download`
  }

  async function downloadJob(jobUuid) {
    const response = await api.get(`/api/jobs/${jobUuid}/download`, {
      responseType: 'blob'
    })
    return response
  }

  return {
    jobs,
    total,
    loading,
    currentJob,
    fetchJobs,
    getJob,
    createJob,
    createBatchJobs,
    cancelJob,
    deleteJob,
    getDownloadUrl,
    downloadJob
  }
})
