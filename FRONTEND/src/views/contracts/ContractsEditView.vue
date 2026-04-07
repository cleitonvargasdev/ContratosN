<template>
  <ContractForm
    mode="edit"
    :can-delete="auth.hasPermission('contratos', 'delete')"
    :error="contracts.state.error"
    :initial-contract="contracts.state.currentContract"
    :saving="contracts.state.saving"
    :success="contracts.state.success"
    @cancel="handleCancel"
    @delete="handleDelete"
    @new="handleNew"
    @submit="handleSubmit"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ContractForm from '@/components/contracts/ContractForm.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useContractsController } from '@/controllers/useContractsController'
import type { ContractCreateInput, ContractInstallmentGeneratePayload, ContractUpdateInput } from '@/models/contract'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'

const auth = useAuthController()
const contracts = useContractsController()
const route = useRoute()
const router = useRouter()

onMounted(async () => {
  if (!auth.hasPermission('contratos', 'update')) {
    await router.replace({ name: 'contracts-list' })
    return
  }

  try {
    await contracts.loadContract(Number(route.params.id))
  } catch {
    await router.replace({ name: 'contracts-list' })
  }
})

async function handleSubmit(payload: { contract: ContractCreateInput | ContractUpdateInput; installments: ContractInstallmentGeneratePayload | null }) {
  try {
    await contracts.submitContractUpdate(Number(route.params.id), payload.contract as ContractUpdateInput)
    void successAlert('Contrato alterado com sucesso.', 'update')
    await new Promise((resolve) => window.setTimeout(resolve, 1000))
    await router.push({ name: 'contracts-list' })
  } catch {
    if (contracts.state.error) {
      await errorAlert(contracts.state.error)
    }
  }
}

async function handleDelete() {
  if (!auth.hasPermission('contratos', 'delete')) {
    return
  }

  if (!(await confirmDeleteAlert())) {
    return
  }

  try {
    await contracts.removeContract(Number(route.params.id))
    await successAlert('Contrato excluido com sucesso.', 'delete')
    await router.push({ name: 'contracts-list' })
  } catch {
    if (contracts.state.error) {
      await errorAlert(contracts.state.error)
    }
  }
}

function handleCancel() {
  void router.push({ name: 'contracts-list' })
}

function handleNew() {
  void router.push({ name: 'contracts-create' })
}
</script>