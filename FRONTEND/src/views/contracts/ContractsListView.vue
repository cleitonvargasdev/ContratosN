<template>
  <ContractTable
    :can-create="auth.hasPermission('contratos', 'create')"
    :can-delete="auth.hasPermission('contratos', 'delete')"
    :can-update="auth.hasPermission('contratos', 'update')"
    :error="contracts.state.error"
    :filters="contracts.state.filters"
    :loading="contracts.state.loading"
    :result="contracts.state.result"
    @apply="handleApply"
    @change-page="handlePage"
    @change-page-size="handlePageSize"
    @delete="handleDelete"
    @edit="handleEdit"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import ContractTable from '@/components/contracts/ContractTable.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useContractsController } from '@/controllers/useContractsController'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'

const contracts = useContractsController()
const auth = useAuthController()
const router = useRouter()

onMounted(() => {
  void contracts.fetchContracts()
})

function handleApply(payload: { contratos_id?: number; cliente_id?: number; contrato_status?: number; quitado?: boolean }) {
  contracts.patchFilters({ ...payload, page: 1 })
  void contracts.fetchContracts()
}

function handlePage(page: number) {
  contracts.patchFilters({ page })
  void contracts.fetchContracts()
}

function handlePageSize(pageSize: number) {
  contracts.patchFilters({ page: 1, page_size: pageSize })
  void contracts.fetchContracts()
}

function handleEdit(contractId: number) {
  void router.push({ name: 'contracts-edit', params: { id: contractId } })
}

async function handleDelete(contractId: number) {
  if (!auth.hasPermission('contratos', 'delete')) {
    return
  }

  if (!(await confirmDeleteAlert())) {
    return
  }

  try {
    await contracts.removeContract(contractId)
    await contracts.fetchContracts()
    await successAlert('Contrato excluido com sucesso.', 'delete')
  } catch {
    if (contracts.state.error) {
      await errorAlert(contracts.state.error)
    }
  }
}
</script>