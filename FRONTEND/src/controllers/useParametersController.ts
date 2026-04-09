import { reactive, readonly } from 'vue'

import type { Parameter, ParameterAutomationRunResult, ParameterInput } from '@/models/parameter'
import { getParameters, runParameterAutomations, updateParameters } from '@/services/parameterService'

export function useParametersController() {
  const state = reactive({
    loading: false,
    saving: false,
    running: false,
    error: '',
    success: '',
    current: null as Parameter | null,
  })

  async function loadParameters(): Promise<void> {
    state.loading = true
    state.error = ''
    try {
      state.current = await getParameters()
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar parametros'
      throw error
    } finally {
      state.loading = false
    }
  }

  async function submitParameters(payload: ParameterInput): Promise<void> {
    state.saving = true
    state.error = ''
    state.success = ''
    try {
      state.current = await updateParameters(payload)
      state.success = 'Parametros atualizados com sucesso.'
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao salvar parametros'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function executeAutomations(): Promise<ParameterAutomationRunResult> {
    state.running = true
    state.error = ''
    try {
      const result = await runParameterAutomations()
      state.current = result.parametros
      return result
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao executar rotinas'
      throw error
    } finally {
      state.running = false
    }
  }

  return {
    state: readonly(state),
    loadParameters,
    submitParameters,
    executeAutomations,
  }
}