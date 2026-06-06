import type { Supplier, SupplierInput, SupplierListFilters, SupplierListResponse } from '@/models/supplier'
import { apiFetch } from '@/services/http'

export async function listSuppliers(filters: SupplierListFilters): Promise<SupplierListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))

  if (filters.nome) params.set('nome', filters.nome)
  if (filters.cpf_cnpj) params.set('cpf_cnpj', filters.cpf_cnpj)
  if (typeof filters.ativo === 'boolean') params.set('ativo', String(filters.ativo))

  return apiFetch<SupplierListResponse>(`/fornecedores/?${params.toString()}`)
}

export async function getSupplierById(supplierId: number): Promise<Supplier> {
  return apiFetch<Supplier>(`/fornecedores/${supplierId}`)
}

export async function createSupplier(payload: SupplierInput): Promise<Supplier> {
  return apiFetch<Supplier>('/fornecedores/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateSupplier(supplierId: number, payload: SupplierInput): Promise<Supplier> {
  return apiFetch<Supplier>(`/fornecedores/${supplierId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteSupplier(supplierId: number): Promise<void> {
  return apiFetch<void>(`/fornecedores/${supplierId}`, { method: 'DELETE' })
}