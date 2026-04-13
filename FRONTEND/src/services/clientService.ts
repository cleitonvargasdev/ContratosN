import type { CobradorOption, Client, ClientInput, ClientListFilters, ClientListResponse, ClientScoreLog, RegraComissaoOption, RegraJurosOption } from '@/models/client'
import { apiFetch } from '@/services/http'

export async function listClients(filters: ClientListFilters): Promise<ClientListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))

  if (filters.nome) params.set('nome', filters.nome)
  if (filters.cpf_cnpj) params.set('cpf_cnpj', filters.cpf_cnpj.replace(/\D/g, ''))
  if (typeof filters.ativo === 'boolean') params.set('ativo', String(filters.ativo))

  return apiFetch<ClientListResponse>(`/clientes/?${params.toString()}`)
}

export async function createClient(payload: ClientInput): Promise<Client> {
  return apiFetch<Client>('/clientes/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function getClientById(clientId: number): Promise<Client> {
  return apiFetch<Client>(`/clientes/${clientId}`)
}

export async function listClientScoreLogs(clientId: number): Promise<ClientScoreLog[]> {
  return apiFetch<ClientScoreLog[]>(`/clientes/${clientId}/score-log`)
}

export async function updateClient(clientId: number, payload: ClientInput): Promise<Client> {
  return apiFetch<Client>(`/clientes/${clientId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteClient(clientId: number): Promise<void> {
  return apiFetch<void>(`/clientes/${clientId}`, { method: 'DELETE' })
}

export async function listRegraJurosOptions(): Promise<RegraJurosOption[]> {
  return apiFetch<RegraJurosOption[]>('/clientes/opcoes/regras-juros')
}

export async function listRegraComissaoOptions(): Promise<RegraComissaoOption[]> {
  return apiFetch<RegraComissaoOption[]>('/clientes/opcoes/regras-comissao')
}

export async function listCobradorOptions(): Promise<CobradorOption[]> {
  return apiFetch<CobradorOption[]>('/clientes/opcoes/cobradores')
}