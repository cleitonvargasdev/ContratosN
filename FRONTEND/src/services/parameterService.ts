import type { Parameter, ParameterAutomationRunResult, ParameterInput } from '@/models/parameter'
import { apiFetch } from '@/services/http'

export async function getParameters(): Promise<Parameter> {
  return apiFetch<Parameter>('/parametros/')
}

export async function updateParameters(payload: ParameterInput): Promise<Parameter> {
  return apiFetch<Parameter>('/parametros/', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function runParameterAutomations(): Promise<ParameterAutomationRunResult> {
  return apiFetch<ParameterAutomationRunResult>('/parametros/executar-rotinas', {
    method: 'POST',
  })
}