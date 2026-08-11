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
import { confirmActionAlert, confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'
import { syncContractPayable } from '@/services/contractService'

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
    const current = contracts.state.currentContract
    const shouldSuggestPayableUpdate = Boolean(
      current?.conta_pagar_id && (
        current.cliente_id !== payload.contract.cliente_id ||
        Number(current.valor_empretismo || 0) !== Number(payload.contract.valor_empretismo || 0) ||
        current.obs !== payload.contract.obs
      ),
    )
    await contracts.submitContractUpdate(Number(route.params.id), payload.contract as ContractUpdateInput)
    if (shouldSuggestPayableUpdate && await confirmActionAlert(
      'Atualizar conta a pagar?',
      'Este contrato possui uma conta a pagar vinculada. Deseja atualizar o cliente, valor e observações dessa conta?',
      'Atualizar conta',
    )) {
      try {
        await syncContractPayable(Number(route.params.id))
        void successAlert('Conta a pagar atualizada com o contrato.', 'update')
      } catch (error) {
        await errorAlert(error instanceof Error ? `Contrato alterado, mas falhou ao atualizar a conta a pagar: ${error.message}` : 'Contrato alterado, mas falhou ao atualizar a conta a pagar.')
      }
    }
    window.scrollTo({ top: 0, behavior: 'smooth' })
    void successAlert('Contrato alterado com sucesso.', 'update')
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
