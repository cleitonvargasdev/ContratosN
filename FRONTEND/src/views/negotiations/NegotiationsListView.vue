<template>
  <NegotiationTable
    :can-create="auth.hasPermission('contratos', 'create')"
    :error="negotiations.state.error"
    :filters="negotiations.state.filters"
    :loading="negotiations.state.loading"
    :result="negotiations.state.result"
    @apply="handleApply"
    @change-page="handlePage"
    @change-page-size="handlePageSize"
    @view="handleView"
    @print="handlePrint"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import NegotiationTable from '@/components/negotiations/NegotiationTable.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useNegotiationsController } from '@/controllers/useNegotiationsController'
import { errorAlert } from '@/services/alertService'
import { printNegotiationPdf } from '@/services/negotiationService'

const negotiations = useNegotiationsController()
const auth = useAuthController()
const router = useRouter()

onMounted(() => {
  void negotiations.fetchNegotiations()
})

function handleApply(payload: { cliente_nome?: string; contrato_gerado_id?: number }) {
  negotiations.patchFilters({ ...payload, page: 1 })
  void negotiations.fetchNegotiations()
}

function handlePage(page: number) {
  negotiations.patchFilters({ page })
  void negotiations.fetchNegotiations()
}

function handlePageSize(pageSize: number) {
  negotiations.patchFilters({ page: 1, page_size: pageSize })
  void negotiations.fetchNegotiations()
}

function handleView(negotiationId: number) {
  void router.push({ name: 'negotiations-view', params: { id: negotiationId } })
}

async function handlePrint(negotiationId: number) {
  try {
    const blob = await printNegotiationPdf(negotiationId)
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao imprimir negociação')
  }
}
</script>
