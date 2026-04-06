<template>
  <ClientTable
    :can-create="auth.hasPermission('clientes', 'create')"
    :can-delete="auth.hasPermission('clientes', 'delete')"
    :can-update="auth.hasPermission('clientes', 'update')"
    :error="clients.state.error"
    :filters="clients.state.filters"
    :loading="clients.state.loading"
    :result="clients.state.result"
    @apply="handleApply"
    @change-page="handlePage"
    @change-page-size="handlePageSize"
    @contract="handleContract"
    @delete="handleDelete"
    @edit="handleEdit"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import ClientTable from '@/components/clients/ClientTable.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useClientsController } from '@/controllers/useClientsController'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'

const clients = useClientsController()
const auth = useAuthController()
const router = useRouter()

onMounted(() => {
  void clients.fetchClients()
})

function handleApply(payload: { nome?: string; cpf_cnpj?: string; ativo?: boolean }) {
  clients.patchFilters({ ...payload, page: 1 })
  void clients.fetchClients()
}

function handlePage(page: number) {
  clients.patchFilters({ page })
  void clients.fetchClients()
}

function handlePageSize(pageSize: number) {
  clients.patchFilters({ page: 1, page_size: pageSize })
  void clients.fetchClients()
}

function handleEdit(clientId: number) {
  void router.push({ name: 'clients-edit', params: { id: clientId } })
}

function handleContract(clientId: number) {
  void router.push({
    name: 'module-placeholder',
    params: { group: 'financeiro', slug: 'contratos' },
    query: {
      grupo: 'Financeiro',
      titulo: `Novo contrato para cliente ${clientId}`,
      cliente_id: String(clientId),
    },
  })
}

async function handleDelete(clientId: number) {
  if (!auth.hasPermission('clientes', 'delete')) {
    return
  }

  if (!(await confirmDeleteAlert())) {
    return
  }

  try {
    await clients.removeClient(clientId)
    await clients.fetchClients()
    await successAlert('Cadastro excluido com sucesso.', 'delete')
  } catch {
    if (clients.state.error) {
      await errorAlert(clients.state.error)
    }
  }
}
</script>