import type {
  SolicitationDetail,
  SolicitationListFilters,
  SolicitationListResponse,
  SolicitationPendingCount,
} from '@/models/solicitation'
import { apiFetch } from '@/services/http'

export async function listSolicitations(filters: SolicitationListFilters): Promise<SolicitationListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))

  if (filters.status) params.set('status', filters.status)
  if (filters.tipo) params.set('tipo', filters.tipo)
  if (typeof filters.cliente_id === 'number') params.set('cliente_id', String(filters.cliente_id))
  if (filters.termo) params.set('termo', filters.termo)

  return apiFetch<SolicitationListResponse>(`/solicitacoes/?${params.toString()}`)
}

export async function getSolicitationPendingCount(): Promise<SolicitationPendingCount> {
  return apiFetch<SolicitationPendingCount>('/solicitacoes/pendentes/contagem')
}

export async function getSolicitationById(solicitationId: number): Promise<SolicitationDetail> {
  return apiFetch<SolicitationDetail>(`/solicitacoes/${solicitationId}`)
}

export async function linkSolicitationClient(solicitationId: number, clienteId: number) {
  return apiFetch(`/solicitacoes/${solicitationId}/vincular-cliente`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cliente_id: clienteId }),
  })
}

export async function completeSolicitationWithContract(solicitationId: number, contratoId: number, status = 'APROVADO') {
  return apiFetch(`/solicitacoes/${solicitationId}/concluir-contrato`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contrato_id: contratoId, status }),
  })
}

export async function rejectSolicitation(solicitationId: number) {
  return apiFetch(`/solicitacoes/${solicitationId}/rejeitar`, {
    method: 'POST',
  })
}
