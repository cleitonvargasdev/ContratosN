import type {
  Negotiation,
  NegotiationCreatePayload,
  NegotiationListFilters,
  NegotiationListResponse,
  OpenContractForNegotiation,
} from '@/models/negotiation'
import { apiFetch, apiFetchBlob } from '@/services/http'

export async function listNegotiations(filters: NegotiationListFilters): Promise<NegotiationListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))

  if (filters.cliente_nome) params.set('cliente_nome', filters.cliente_nome)
  if (typeof filters.contrato_gerado_id === 'number') params.set('contrato_gerado_id', String(filters.contrato_gerado_id))

  return apiFetch<NegotiationListResponse>(`/negociacoes/?${params.toString()}`)
}

export async function getNegotiationById(negotiationId: number): Promise<Negotiation> {
  return apiFetch<Negotiation>(`/negociacoes/${negotiationId}`)
}

export async function listOpenContracts(clienteId: number): Promise<OpenContractForNegotiation[]> {
  return apiFetch<OpenContractForNegotiation[]>(`/negociacoes/contratos-abertos/${clienteId}`)
}

export async function createNegotiation(payload: NegotiationCreatePayload): Promise<Negotiation> {
  return apiFetch<Negotiation>('/negociacoes/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function printNegotiationPdf(negotiationId: number): Promise<Blob> {
  return apiFetchBlob(`/negociacoes/${negotiationId}/imprimir`)
}
