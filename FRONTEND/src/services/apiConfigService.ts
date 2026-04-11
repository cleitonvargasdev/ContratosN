import type { ApiConfig, ApiConfigInput, ApiConfigListFilters, ApiConfigListResponse } from '@/models/apiConfig'
import { apiFetch } from '@/services/http'

export async function listApiConfigs(filters: ApiConfigListFilters): Promise<ApiConfigListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))

  if (filters.nome_api) params.set('nome_api', filters.nome_api)
  if (typeof filters.usuario_id === 'number') params.set('usuario_id', String(filters.usuario_id))

  return apiFetch<ApiConfigListResponse>(`/apis/?${params.toString()}`)
}

export async function getApiConfigById(apiId: number): Promise<ApiConfig> {
  return apiFetch<ApiConfig>(`/apis/${apiId}`)
}

export async function createApiConfig(payload: ApiConfigInput): Promise<ApiConfig> {
  return apiFetch<ApiConfig>('/apis/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateApiConfig(apiId: number, payload: ApiConfigInput): Promise<ApiConfig> {
  return apiFetch<ApiConfig>(`/apis/${apiId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteApiConfig(apiId: number): Promise<void> {
  return apiFetch<void>(`/apis/${apiId}`, { method: 'DELETE' })
}