import type { AddressLookupResponse, BairroInput, BairroOption, CidadeInput, CidadeOption, FeriadoInput, FeriadoOption, UFInput, UFOption } from '@/models/location'
import { apiFetch } from '@/services/http'

export async function listUfs(term?: string): Promise<UFOption[]> {
  const params = new URLSearchParams()
  if (term) params.set('term', term)
  return apiFetch<UFOption[]>(`/localidades/ufs${params.size ? `?${params.toString()}` : ''}`)
}

export async function listCitiesByUf(uf: string): Promise<CidadeOption[]> {
  const params = new URLSearchParams({ uf })
  return apiFetch<CidadeOption[]>(`/localidades/cidades?${params.toString()}`)
}

export async function listCities(filters: { uf?: string; nome?: string } = {}): Promise<CidadeOption[]> {
  const params = new URLSearchParams()
  if (filters.uf) params.set('uf', filters.uf)
  if (filters.nome) params.set('nome', filters.nome)
  return apiFetch<CidadeOption[]>(`/localidades/cidades${params.size ? `?${params.toString()}` : ''}`)
}

export async function listBairrosByCidade(cidadeId: number): Promise<BairroOption[]> {
  const params = new URLSearchParams({ cidade_id: String(cidadeId) })
  return apiFetch<BairroOption[]>(`/localidades/bairros?${params.toString()}`)
}

export async function listBairros(filters: { cidade_id?: number; nome?: string } = {}): Promise<BairroOption[]> {
  const params = new URLSearchParams()
  if (typeof filters.cidade_id === 'number') params.set('cidade_id', String(filters.cidade_id))
  if (filters.nome) params.set('nome', filters.nome)
  return apiFetch<BairroOption[]>(`/localidades/bairros${params.size ? `?${params.toString()}` : ''}`)
}

export async function getUfById(ufId: number): Promise<UFOption> {
  return apiFetch<UFOption>(`/localidades/ufs/${ufId}`)
}

export async function createUf(payload: UFInput): Promise<UFOption> {
  return apiFetch<UFOption>('/localidades/ufs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateUf(ufId: number, payload: UFInput): Promise<UFOption> {
  return apiFetch<UFOption>(`/localidades/ufs/${ufId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteUf(ufId: number): Promise<void> {
  return apiFetch<void>(`/localidades/ufs/${ufId}`, { method: 'DELETE' })
}

export async function getCidadeById(cidadeId: number): Promise<CidadeOption> {
  return apiFetch<CidadeOption>(`/localidades/cidades/${cidadeId}`)
}

export async function createCidade(payload: CidadeInput): Promise<CidadeOption> {
  return apiFetch<CidadeOption>('/localidades/cidades', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateCidade(cidadeId: number, payload: CidadeInput): Promise<CidadeOption> {
  return apiFetch<CidadeOption>(`/localidades/cidades/${cidadeId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteCidade(cidadeId: number): Promise<void> {
  return apiFetch<void>(`/localidades/cidades/${cidadeId}`, { method: 'DELETE' })
}

export async function getBairroById(bairroId: number): Promise<BairroOption> {
  return apiFetch<BairroOption>(`/localidades/bairros/${bairroId}`)
}

export async function createBairro(payload: BairroInput): Promise<BairroOption> {
  return apiFetch<BairroOption>('/localidades/bairros', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateBairro(bairroId: number, payload: BairroInput): Promise<BairroOption> {
  return apiFetch<BairroOption>(`/localidades/bairros/${bairroId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteBairro(bairroId: number): Promise<void> {
  return apiFetch<void>(`/localidades/bairros/${bairroId}`, { method: 'DELETE' })
}

export async function listFeriados(filters: { nivel?: number; uf?: string; cidade_id?: number; descricao?: string } = {}): Promise<FeriadoOption[]> {
  const params = new URLSearchParams()
  if (typeof filters.nivel === 'number') params.set('nivel', String(filters.nivel))
  if (filters.uf) params.set('uf', filters.uf)
  if (typeof filters.cidade_id === 'number') params.set('cidade_id', String(filters.cidade_id))
  if (filters.descricao) params.set('descricao', filters.descricao)
  return apiFetch<FeriadoOption[]>(`/localidades/feriados${params.size ? `?${params.toString()}` : ''}`)
}

export async function getFeriadoById(feriadoId: number): Promise<FeriadoOption> {
  return apiFetch<FeriadoOption>(`/localidades/feriados/${feriadoId}`)
}

export async function createFeriado(payload: FeriadoInput): Promise<FeriadoOption> {
  return apiFetch<FeriadoOption>('/localidades/feriados', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateFeriado(feriadoId: number, payload: FeriadoInput): Promise<FeriadoOption> {
  return apiFetch<FeriadoOption>(`/localidades/feriados/${feriadoId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteFeriado(feriadoId: number): Promise<void> {
  return apiFetch<void>(`/localidades/feriados/${feriadoId}`, { method: 'DELETE' })
}

export async function lookupAddressByCep(cep: string): Promise<AddressLookupResponse> {
  return apiFetch<AddressLookupResponse>(`/localidades/consulta-cep/${encodeURIComponent(cep)}`)
}

export async function lookupCepByAddress(payload: {
  uf: string
  cidade: string
  logradouro: string
  bairro?: string
}): Promise<AddressLookupResponse> {
  const params = new URLSearchParams({
    uf: payload.uf,
    cidade: payload.cidade,
    logradouro: payload.logradouro,
  })

  if (payload.bairro) {
    params.set('bairro', payload.bairro)
  }

  return apiFetch<AddressLookupResponse>(`/localidades/consulta-endereco?${params.toString()}`)
}