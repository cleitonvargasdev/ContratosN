<template>
  <ClientForm
    mode="create"
    :error="clients.state.error"
    :saving="clients.state.saving"
    :success="clients.state.success"
    @cancel="handleCancel"
    @submit="handleSubmit"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import ClientForm from '@/components/clients/ClientForm.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useClientsController } from '@/controllers/useClientsController'
import type { ClientInput } from '@/models/client'
import { errorAlert, successAlert } from '@/services/alertService'

const auth = useAuthController()
const clients = useClientsController()
const router = useRouter()

onMounted(() => {
  if (!auth.hasPermission('clientes', 'create')) {
    void router.replace({ name: 'clients-list' })
  }
})

async function handleSubmit(payload: ClientInput) {
  try {
    await clients.submitClient(payload)
    void successAlert('Novo cadastro salvo com sucesso.', 'create')
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