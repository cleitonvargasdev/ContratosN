<template>
  <AccountsReceivableTable
    :can-view-client="auth.hasPermission('clientes', 'update')"
    :can-view-contract="auth.hasPermission('contratos', 'update')"
    :error="accountsReceivable.state.error"
    :filters="accountsReceivable.state.filters"
    :loading="accountsReceivable.state.loading"
    :result="accountsReceivable.state.result"
    @apply="handleApply"
    @change-page="handlePage"
    @change-page-size="handlePageSize"
    @view-client="handleViewClient"
    @view-contract="handleViewContract"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import AccountsReceivableTable from '@/components/accounts-receivable/AccountsReceivableTable.vue'
import { useAccountsReceivableController } from '@/controllers/useAccountsReceivableController'
import { useAuthController } from '@/controllers/useAuthController'

const accountsReceivable = useAccountsReceivableController()
const auth = useAuthController()
const router = useRouter()

onMounted(() => {
  void accountsReceivable.fetchAccountsReceivable()
})

function handleApply(payload: {
  recebida?: boolean
  cliente_query?: string
  data_vencimento_inicial?: string
  data_vencimento_final?: string
}) {
  accountsReceivable.patchFilters({ ...payload, page: 1 })
  void accountsReceivable.fetchAccountsReceivable()
}

function handlePage(page: number) {
  accountsReceivable.patchFilters({ page })
  void accountsReceivable.fetchAccountsReceivable()
}

function handlePageSize(pageSize: number) {
  accountsReceivable.patchFilters({ page: 1, page_size: pageSize })
  void accountsReceivable.fetchAccountsReceivable()
}

function handleViewContract(contractId: number) {
  if (!auth.hasPermission('contratos', 'update')) {
    return
  }

  void router.push({ name: 'contracts-edit', params: { id: contractId } })
}

function handleViewClient(clientId: number) {
  if (!auth.hasPermission('clientes', 'update')) {
    return
  }

  void router.push({ name: 'clients-edit', params: { id: clientId } })
}
</script>