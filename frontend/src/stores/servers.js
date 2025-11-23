import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useServersStore = defineStore('servers', () => {
  const servers = ref([])
  const activeServers = ref([])
  const currentServer = ref(null)
  const loading = ref(false)

  async function fetchServers() {
    loading.value = true
    try {
      const response = await api.get('/api/servers')
      servers.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchActiveServers() {
    loading.value = true
    try {
      const response = await api.get('/api/servers/active')
      activeServers.value = response.data
      // Set default server if not set
      if (!currentServer.value && activeServers.value.length > 0) {
        const defaultServer = activeServers.value.find(s => s.is_default) || activeServers.value[0]
        currentServer.value = defaultServer
      }
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function createServer(serverData) {
    const response = await api.post('/api/servers', serverData)
    await fetchServers()
    return response.data
  }

  async function updateServer(serverId, serverData) {
    const response = await api.put(`/api/servers/${serverId}`, serverData)
    await fetchServers()
    return response.data
  }

  async function deleteServer(serverId) {
    await api.delete(`/api/servers/${serverId}`)
    await fetchServers()
  }

  async function testConnection(serverId) {
    const response = await api.post(`/api/servers/${serverId}/test`)
    return response.data
  }

  function setCurrentServer(server) {
    currentServer.value = server
  }

  return {
    servers,
    activeServers,
    currentServer,
    loading,
    fetchServers,
    fetchActiveServers,
    createServer,
    updateServer,
    deleteServer,
    testConnection,
    setCurrentServer
  }
})
