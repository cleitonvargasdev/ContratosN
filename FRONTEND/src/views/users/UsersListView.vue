<template>
  <UserTable
    :can-create="auth.hasPermission('usuarios', 'create')"
    :can-delete="auth.hasPermission('usuarios', 'delete')"
    :can-update="auth.hasPermission('usuarios', 'update')"
    :error="users.state.error"
    :filters="users.state.filters"
    :loading="users.state.loading"
    :result="users.state.result"
    @apply="handleApply"
    @change-page="handlePage"
    @change-page-size="handlePageSize"
    @edit="handleEdit"
    @delete="handleDelete"
  />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import UserTable from '@/components/users/UserTable.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useUsersController } from '@/controllers/useUsersController'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'
import { connectUsersUpdates, type UserRealtimeEvent } from '@/services/userService'

const users = useUsersController()
const auth = useAuthController()
const router = useRouter()
let reconnectTimer: number | null = null
let updatesSocket: WebSocket | null = null
let isUnmounted = false

onMounted(() => {
  isUnmounted = false
  void users.fetchUsers()
  connectUpdatesSocket()
})

onBeforeUnmount(() => {
  isUnmounted = true
  clearReconnectTimer()
  updatesSocket?.close()
  updatesSocket = null
})

function handleApply(payload: { nome?: string; email?: string; ativo?: boolean }) {
  users.patchFilters({ ...payload, page: 1 })
  void users.fetchUsers()
}

function handlePage(page: number) {
  users.patchFilters({ page })
  void users.fetchUsers()
}

function handlePageSize(pageSize: number) {
  users.patchFilters({ page: 1, page_size: pageSize })
  void users.fetchUsers()
}

function handleEdit(userId: number) {
  void router.push({ name: 'users-edit', params: { id: userId } })
}

async function handleDelete(userId: number) {
  if (!auth.hasPermission('usuarios', 'delete')) {
    return
  }

  if (!(await confirmDeleteAlert())) {
    return
  }

  try {
    await users.removeUser(userId)
    await users.fetchUsers()
    await successAlert('Cadastro excluido com sucesso.', 'delete')
  } catch {
    if (users.state.error) {
      await errorAlert(users.state.error)
    }
    return
  }
}

function connectUpdatesSocket() {
  if (updatesSocket || !auth.isAuthenticated.value) {
    return
  }

  updatesSocket = connectUsersUpdates(handleRealtimeEvent)
  if (!updatesSocket) {
    return
  }

  updatesSocket.addEventListener('close', handleSocketClose)
  updatesSocket.addEventListener('error', () => {
    updatesSocket?.close()
  })
}

function handleRealtimeEvent(event: UserRealtimeEvent) {
  if (event.event === 'connected') {
    return
  }

  void users.fetchUsers()
}

function handleSocketClose() {
  updatesSocket = null

  if (isUnmounted) {
    return
  }

  clearReconnectTimer()
  reconnectTimer = window.setTimeout(() => {
    connectUpdatesSocket()
  }, 3000)
}

function clearReconnectTimer() {
  if (reconnectTimer !== null) {
    window.clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}
</script>
