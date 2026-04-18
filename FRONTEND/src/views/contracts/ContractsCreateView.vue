<template>
  <ContractForm
    mode="create"
    :can-delete="false"
    :error="contracts.state.error"
    :initial-contract-draft="initialContractDraft"
    :initial-client-id="initialClientId"
    :saving="contracts.state.saving"
    :success="contracts.state.success"
    @cancel="handleCancel"
    @submit="handleSubmit"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ContractForm from '@/components/contracts/ContractForm.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useContractsController } from '@/controllers/useContractsController'
import type { ContractCreateInput, ContractInstallmentGeneratePayload, ContractUpdateInput } from '@/models/contract'
import type { SolicitationContractDraft } from '@/models/solicitation'
import { errorAlert, successAlert } from '@/services/alertService'
import { generateContractInstallments } from '@/services/contractService'
import { completeSolicitationWithContract, getSolicitationById } from '@/services/solicitationService'

const auth = useAuthController()
const contracts = useContractsController()
const route = useRoute()
const router = useRouter()
const initialContractDraft = ref<SolicitationContractDraft | null>(null)

const initialClientId = computed(() => {
  const raw = route.query.cliente_id
  if (typeof raw !== 'string' || !raw.trim()) {
    return null
  }

  const parsed = Number(raw)
  return Number.isNaN(parsed) ? null : parsed
})

const solicitationId = computed(() => {
  const raw = route.query.solicitacao_id
  if (typeof raw !== 'string' || !raw.trim()) {
    return null
  }

  const parsed = Number(raw)
  return Number.isNaN(parsed) ? null : parsed
})

onMounted(async () => {
  if (!auth.hasPermission('contratos', 'create')) {
    void router.replace({ name: 'contracts-list' })
    return
  }

  if (solicitationId.value && auth.hasPermission('solicitacoes', 'read')) {
    try {
      const detail = await getSolicitationById(solicitationId.value)
      initialContractDraft.value = detail.contrato_sugerido
    } catch {
      initialContractDraft.value = null
    }
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

    if (solicitationId.value && auth.hasPermission('solicitacoes', 'update')) {
      try {
        await completeSolicitationWithContract(solicitationId.value, created.contratos_id)
      } catch (error) {
        await errorAlert(error instanceof Error ? `Contrato salvo, mas falhou ao concluir a solicitação: ${error.message}` : 'Contrato salvo, mas falhou ao concluir a solicitação.')
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
  if (solicitationId.value) {
    void router.push({ name: 'solicitations' })
    return
  }

  void router.push({ name: 'contracts-list' })
}
</script>