import type {
  AccountsReceivableListFilters,
  AccountsReceivableListResponse,
  BatchInstallmentReceiveConfirmResult,
  BatchInstallmentReceivePayload,
  BatchInstallmentReceivePreview,
  Contract,
  ContractComodato,
  ContractComodatoInput,
  ContractCreateInput,
  ContractInstallment,
  ContractInstallmentGeneratePayload,
  ContractReceipt,
  ContractListFilters,
  ContractListResponse,
  InstallmentCreatePayload,
  ContractUpdateInput,
  InstallmentPaymentPayload,
  InstallmentSettlePayload,
  InstallmentUpdatePayload,
} from '@/models/contract'
import { apiFetch, apiFetchBlob } from '@/services/http'

export async function listAccountsReceivable(filters: AccountsReceivableListFilters): Promise<AccountsReceivableListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))

  if (typeof filters.recebida === 'boolean') params.set('recebida', String(filters.recebida))
  if (filters.cliente_query) params.set('cliente_query', filters.cliente_query)
  if (filters.data_vencimento_inicial) params.set('data_vencimento_inicial', filters.data_vencimento_inicial)
  if (filters.data_vencimento_final) params.set('data_vencimento_final', filters.data_vencimento_final)

  return apiFetch<AccountsReceivableListResponse>(`/contratos/parcelas?${params.toString()}`)
}

export async function listContracts(filters: ContractListFilters): Promise<ContractListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))

  if (typeof filters.contratos_id === 'number') params.set('contratos_id', String(filters.contratos_id))
  if (filters.cliente_nome) params.set('cliente_nome', filters.cliente_nome)
  if (filters.cobrador_nome) params.set('cobrador_nome', filters.cobrador_nome)
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

export async function createContractInstallment(contractId: number, payload: InstallmentCreatePayload): Promise<ContractInstallment> {
  return apiFetch<ContractInstallment>(`/contratos/${contractId}/parcelas`, {
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

export async function previewBatchContractReceive(contractId: number, payload: BatchInstallmentReceivePayload): Promise<BatchInstallmentReceivePreview> {
  return apiFetch<BatchInstallmentReceivePreview>(`/contratos/${contractId}/parcelas/recebimento-lote/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function confirmBatchContractReceive(contractId: number, payload: BatchInstallmentReceivePayload): Promise<BatchInstallmentReceiveConfirmResult> {
  return apiFetch<BatchInstallmentReceiveConfirmResult>(`/contratos/${contractId}/parcelas/recebimento-lote/confirmar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateContractInstallment(installmentId: number, payload: InstallmentUpdatePayload): Promise<ContractInstallment> {
  return apiFetch<ContractInstallment>(`/contratos/parcelas/${installmentId}`, {
    method: 'PUT',
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

export async function settleOpenContractInstallments(contractId: number, payload: InstallmentSettlePayload): Promise<ContractInstallment[]> {
  return apiFetch<ContractInstallment[]>(`/contratos/${contractId}/parcelas/quitar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function reopenContractInstallment(installmentId: number): Promise<ContractInstallment> {
  return apiFetch<ContractInstallment>(`/contratos/parcelas/${installmentId}/reabrir`, {
    method: 'POST',
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

export async function sendInstallmentWhatsAppMessage(installmentId: number): Promise<{ success: boolean; message: string; chatid: string; installment_id: number }> {
  return apiFetch<{ success: boolean; message: string; chatid: string; installment_id: number }>(`/contratos/parcelas/${installmentId}/whatsapp`, {
    method: 'POST',
  })
}

export async function printContractPdf(contractId: number): Promise<Blob> {
  return apiFetchBlob(`/contratos/${contractId}/imprimir`)
}

export async function printContractComodatoPdf(contractId: number): Promise<Blob> {
  return apiFetchBlob(`/contratos/${contractId}/comodato/imprimir`)
}

export async function sendContractWhatsAppDocument(contractId: number): Promise<{ success: boolean; message: string; chatid: string; contract_id: number; document_url: string }> {
  return apiFetch<{ success: boolean; message: string; chatid: string; contract_id: number; document_url: string }>(`/contratos/${contractId}/whatsapp-documento`, {
    method: 'POST',
  })
}

export async function getContractComodato(contractId: number): Promise<ContractComodato> {
  return apiFetch<ContractComodato>(`/contratos/${contractId}/comodato`)
}

export async function saveContractComodato(contractId: number, payload: ContractComodatoInput): Promise<ContractComodato> {
  return apiFetch<ContractComodato>(`/contratos/${contractId}/comodato`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteContractComodato(contractId: number): Promise<void> {
  return apiFetch<void>(`/contratos/${contractId}/comodato`, { method: 'DELETE' })
}