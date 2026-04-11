<template>
  <ParameterForm
    :initial-parameters="initialParameters"
    :loading="parameters.state.loading"
    :saving="parameters.state.saving"
    :running-automations="parameters.state.running"
    :error="parameters.state.error"
    :success="parameters.state.success"
    @cancel="handleCancel"
    @run-automations="handleRunAutomations"
    @submit="handleSubmit"
  />
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import ParameterForm from '@/components/parameters/ParameterForm.vue'
import { useParametersController } from '@/controllers/useParametersController'
import type { Parameter, ParameterInput } from '@/models/parameter'
import { errorAlert, successAlert } from '@/services/alertService'

const parameters = useParametersController()
const router = useRouter()
const initialParameters = computed(() => {
  return parameters.state.current as Parameter | null
})

onMounted(() => {
  void parameters.loadParameters().catch(async () => {
    if (parameters.state.error) {
      await errorAlert(parameters.state.error)
    }
  })
})

async function handleSubmit(payload: ParameterInput) {
  try {
    await parameters.submitParameters(payload)
    await successAlert('Parâmetros atualizados com sucesso.', 'update')
  } catch {
    if (parameters.state.error) {
      await errorAlert(parameters.state.error)
    }
  }
}

async function handleRunAutomations() {
  try {
    const result = await parameters.executeAutomations()
    await successAlert(
      `Clientes recalculados: ${result.clientes_recalculados}. Cobranças preparadas: ${result.cobrancas_whatsapp_preparadas}.`,
      'update',
    )
  } catch {
    if (parameters.state.error) {
      await errorAlert(parameters.state.error)
    }
  }
}

function handleCancel() {
  void router.push({ name: 'dashboard' })
}
</script>