import type {
  AccountsPayable,
  AccountsPayableBaseUpdateInput,
  AccountsPayableInstallment,
  AccountsPayableInstallmentInput,
  AccountsPayableListFilters,
  AccountsPayableListResponse,
  AccountsPayablePaymentInput,
  AccountsPayablePersonOption,
  AccountsPayableInput,
  PaymentMovementListResponse,
} from '@/models/accountsPayable'
import { apiFetch } from '@/services/http'

export async function listAccountsPayable(filters: AccountsPayableListFilters): Promise<AccountsPayableListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))

  if (typeof filters.quitado === 'boolean') params.set('quitado', String(filters.quitado))
  if (filters.pessoa_query) params.set('pessoa_query', filters.pessoa_query)
  if (filters.tipo_pessoa) params.set('tipo_pessoa', filters.tipo_pessoa)
  if (filters.data_vencimento_inicial) params.set('data_vencimento_inicial', filters.data_vencimento_inicial)
  if (filters.data_vencimento_final) params.set('data_vencimento_final', filters.data_vencimento_final)
  if (filters.data_referencia_inicial) params.set('data_referencia_inicial', filters.data_referencia_inicial)
  if (filters.data_referencia_final) params.set('data_referencia_final', filters.data_referencia_final)

  return apiFetch<AccountsPayableListResponse>(`/financeiro/contas-pagar?${params.toString()}`)
}

export async function searchAccountsPayablePeople(query: string): Promise<AccountsPayablePersonOption[]> {
  const params = new URLSearchParams({ query })
  return apiFetch<AccountsPayablePersonOption[]>(`/financeiro/contas-pagar/pessoas?${params.toString()}`)
}

export async function getAccountsPayableById(accountId: number): Promise<AccountsPayable> {
  return apiFetch<AccountsPayable>(`/financeiro/contas-pagar/${accountId}`)
}

export async function createAccountsPayable(payload: AccountsPayableInput): Promise<AccountsPayable> {
  return apiFetch<AccountsPayable>('/financeiro/contas-pagar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateAccountsPayable(accountId: number, payload: AccountsPayableBaseUpdateInput): Promise<AccountsPayable> {
  return apiFetch<AccountsPayable>(`/financeiro/contas-pagar/${accountId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function addAccountsPayableInstallments(accountId: number, parcelas: AccountsPayableInstallmentInput[]): Promise<AccountsPayable> {
  return apiFetch<AccountsPayable>(`/financeiro/contas-pagar/${accountId}/parcelas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ parcelas }),
  })
}

export async function registerAccountsPayablePayment(parcelaId: number, payload: AccountsPayablePaymentInput): Promise<AccountsPayableInstallment> {
  return apiFetch<AccountsPayableInstallment>(`/financeiro/contas-pagar/parcelas/${parcelaId}/pagamentos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteAccountsPayable(accountId: number): Promise<void> {
  return apiFetch<void>(`/financeiro/contas-pagar/${accountId}`, { method: 'DELETE' })
}

export async function listPaymentMovements(filters: { page: number; page_size: number; query?: string; quitado?: boolean; data_vencimento_inicial?: string; data_vencimento_final?: string }): Promise<PaymentMovementListResponse> {
  const params = new URLSearchParams({ page: String(filters.page), page_size: String(filters.page_size) })
  if (filters.query) params.set('query', filters.query)
  if (typeof filters.quitado === 'boolean') params.set('quitado', String(filters.quitado))
  if (filters.data_vencimento_inicial) params.set('data_vencimento_inicial', filters.data_vencimento_inicial)
  if (filters.data_vencimento_final) params.set('data_vencimento_final', filters.data_vencimento_final)
  return apiFetch<PaymentMovementListResponse>(`/financeiro/contas-pagar/movimentacoes?${params}`)
}

export async function removeAccountsPayableInstallmentPayments(parcelaId: number): Promise<AccountsPayableInstallment> {
  return apiFetch<AccountsPayableInstallment>(`/financeiro/contas-pagar/parcelas/${parcelaId}/pagamentos`, { method: 'DELETE' })
}

export async function deleteAccountsPayableInstallment(parcelaId: number): Promise<void> {
  return apiFetch<void>(`/financeiro/contas-pagar/parcelas/${parcelaId}`, { method: 'DELETE' })
}
