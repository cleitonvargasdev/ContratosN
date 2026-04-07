import type {
  Contract,
  ContractCreateInput,
  ContractInstallment,
  ContractInstallmentGeneratePayload,
  ContractReceipt,
  ContractListFilters,
  ContractListResponse,
  ContractUpdateInput,
  InstallmentPaymentPayload,
  InstallmentSettlePayload,
} from '@/models/contract'
import { apiFetch } from '@/services/http'

export async function listContracts(filters: ContractListFilters): Promise<ContractListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))

  if (typeof filters.contratos_id === 'number') params.set('contratos_id', String(filters.contratos_id))
  if (typeof filters.cliente_id === 'number') params.set('cliente_id', String(filters.cliente_id))
  if (typeof filters.contrato_status === 'number') params.set('contrato_status', String(filters.contrato_status))
  if (typeof filters.quitado === 'boolean') params.set('quitado', String(filters.quitado))

  return apiFetch<ContractListResponse>(`/contratos/?${params.toString()}`)
}

export async function getContractById(contractId: number): Promise<Contract> {
  return apiFetch<Contract>(`/contratos/${contractId}`)
}

export async function createContract(payload: ContractCreateInput): Promise<Contract> {
  return apiFetch<Contract>('/contratos/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateContract(contractId: number, payload: ContractUpdateInput): Promise<Contract> {
  return apiFetch<Contract>(`/contratos/${contractId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteContract(contractId: number): Promise<void> {
  return apiFetch<void>(`/contratos/${contractId}`, { method: 'DELETE' })
}

export async function listContractInstallments(contractId: number): Promise<ContractInstallment[]> {
  return apiFetch<ContractInstallment[]>(`/contratos/${contractId}/parcelas`)
}

export async function generateContractInstallments(contractId: number, payload: ContractInstallmentGeneratePayload): Promise<ContractInstallment[]> {
  return apiFetch<ContractInstallment[]>(`/contratos/${contractId}/parcelas/gerar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function receiveContractInstallment(installmentId: number, payload: InstallmentPaymentPayload): Promise<ContractInstallment> {
  return apiFetch<ContractInstallment>(`/contratos/parcelas/${installmentId}/receber`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function settleContractInstallment(installmentId: number, payload: InstallmentSettlePayload): Promise<ContractInstallment> {
  return apiFetch<ContractInstallment>(`/contratos/parcelas/${installmentId}/quitar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteContractInstallmentPayment(installmentId: number): Promise<ContractInstallment> {
  return apiFetch<ContractInstallment>(`/contratos/parcelas/${installmentId}/pagamento`, { method: 'DELETE' })
}

export async function listInstallmentReceipts(installmentId: number): Promise<ContractReceipt[]> {
  return apiFetch<ContractReceipt[]>(`/contratos/parcelas/${installmentId}/pagamentos`)
}

export async function deleteReceiptPayment(receiptId: number): Promise<ContractInstallment> {
  return apiFetch<ContractInstallment>(`/contratos/pagamentos/${receiptId}`, { method: 'DELETE' })
}