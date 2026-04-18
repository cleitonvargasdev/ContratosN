<template>
  <ClientForm
    mode="create"
    :error="clients.state.error"
    :initial-draft="initialDraft"
    :saving="clients.state.saving"
    :success="clients.state.success"
    @cancel="handleCancel"
    @submit="handleSubmit"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ClientForm from '@/components/clients/ClientForm.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useClientsController } from '@/controllers/useClientsController'
import type { ClientInput } from '@/models/client'
import type { SolicitationClientDraft } from '@/models/solicitation'
import { confirmActionAlert, errorAlert, successAlert } from '@/services/alertService'
import { getSolicitationById, linkSolicitationClient } from '@/services/solicitationService'

const auth = useAuthController()
const clients = useClientsController()
const route = useRoute()
const router = useRouter()
const initialDraft = ref<SolicitationClientDraft | null>(null)

const solicitationId = computed(() => {
  const raw = route.query.solicitacao_id
  if (typeof raw !== 'string' || !raw.trim()) {
    return null
  }

  const parsed = Number(raw)
  return Number.isNaN(parsed) ? null : parsed
})

const shouldPromptContract = computed(() => route.query.gerar_contrato === '1')

onMounted(async () => {
  if (!auth.hasPermission('clientes', 'create')) {
    void router.replace({ name: 'clients-list' })
    return
  }

  if (solicitationId.value && auth.hasPermission('solicitacoes', 'read')) {
    try {
      const detail = await getSolicitationById(solicitationId.value)
      initialDraft.value = detail.cliente_sugerido
    } catch {
      initialDraft.value = null
    }
  }
})

async function handleSubmit(payload: ClientInput) {
  try {
    const created = await clients.submitClient(payload)

    if (solicitationId.value && auth.hasPermission('solicitacoes', 'update')) {
      await linkSolicitationClient(solicitationId.value, created.clientes_id)
    }

    void successAlert('Novo cadastro salvo com sucesso.', 'create')

    if (solicitationId.value && shouldPromptContract.value) {
      const confirmed = await confirmActionAlert(
        'Gerar contrato agora?',
        'O cliente foi salvo. Deseja abrir a tela do contrato com os dados da solicitação já preenchidos?',
        'Gerar contrato',
      )

      if (confirmed) {
        await router.push({
          name: 'contracts-create',
          query: {
            cliente_id: String(created.clientes_id),
            solicitacao_id: String(solicitationId.value),
          },
        })
        return
      }
    }

    await router.push({ name: 'clients-list' })
  } catch {
    if (clients.state.error) {
      await errorAlert(clients.state.error)
    }
  }
}

function handleCancel() {
  if (solicitationId.value) {
    void router.push({ name: 'solicitations' })
    return
  }

  void router.push({ name: 'clients-list' })
}
</script>