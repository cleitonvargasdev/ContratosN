<template>
  <ClientForm
    mode="edit"
    :error="clients.state.error"
    :initial-client="clients.state.currentClient"
    :saving="clients.state.saving"
    :success="clients.state.success"
    @cancel="handleCancel"
    @submit="handleSubmit"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ClientForm from '@/components/clients/ClientForm.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useClientsController } from '@/controllers/useClientsController'
import type { ClientInput } from '@/models/client'
import { errorAlert, successAlert } from '@/services/alertService'

const auth = useAuthController()
const clients = useClientsController()
const route = useRoute()
const router = useRouter()

onMounted(async () => {
  if (!auth.hasPermission('clientes', 'update')) {
    await router.replace({ name: 'clients-list' })
    return
  }

  try {
    await clients.loadClient(Number(route.params.id))
  } catch {
    await router.replace({ name: 'clients-list' })
  }
})

async function handleSubmit(payload: ClientInput) {
  try {
    await clients.submitClientUpdate(Number(route.params.id), payload)
    void successAlert('Cadastro alterado com sucesso.', 'update')
    await new Promise((resolve) => window.setTimeout(resolve, 1000))
    await router.push({ name: 'clients-list' })
  } catch {
    if (clients.state.error) {
      await errorAlert(clients.state.error)
    }
  }
}

function handleCancel() {
  void router.push({ name: 'clients-list' })
}
</script>