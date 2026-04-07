<template>
  <ContractForm
    mode="create"
    :can-delete="false"
    :error="contracts.state.error"
    :initial-client-id="initialClientId"
    :saving="contracts.state.saving"
    :success="contracts.state.success"
    @cancel="handleCancel"
    @submit="handleSubmit"
  />
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ContractForm from '@/components/contracts/ContractForm.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useContractsController } from '@/controllers/useContractsController'
import type { ContractCreateInput, ContractInstallmentGeneratePayload, ContractUpdateInput } from '@/models/contract'
import { errorAlert, successAlert } from '@/services/alertService'
import { generateContractInstallments } from '@/services/contractService'

const auth = useAuthController()
const contracts = useContractsController()
const route = useRoute()
const router = useRouter()

const initialClientId = computed(() => {
  const raw = route.query.cliente_id
  if (typeof raw !== 'string' || !raw.trim()) {
    return null
  }

  const parsed = Number(raw)
  return Number.isNaN(parsed) ? null : parsed
})

onMounted(() => {
  if (!auth.hasPermission('contratos', 'create')) {
    void router.replace({ name: 'contracts-list' })
  }
})

async function handleSubmit(payload: { contract: ContractCreateInput | ContractUpdateInput; installments: ContractInstallmentGeneratePayload | null }) {
  try {
    const created = await contracts.submitContract(payload.contract as ContractCreateInput)

    if (payload.installments?.parcelas.length) {
      try {
        await generateContractInstallments(created.contratos_id, payload.installments)
      } catch (error) {
        await errorAlert(error instanceof Error ? `Contrato salvo, mas falhou ao salvar parcelas: ${error.message}` : 'Contrato salvo, mas falhou ao salvar parcelas.')
        await router.push({ name: 'contracts-edit', params: { id: created.contratos_id } })
        return
      }
    }

    void successAlert('Novo contrato salvo com sucesso.', 'create')
    await router.push({ name: 'contracts-edit', params: { id: created.contratos_id } })
  } catch {
    if (contracts.state.error) {
      await errorAlert(contracts.state.error)
    }
  }
}

function handleCancel() {
  void router.push({ name: 'contracts-list' })
}
</script>