import type { PaymentPlanInput, PaymentPlanOption } from '@/models/paymentPlan'
import { apiFetch } from '@/services/http'

export async function listPaymentPlans(descricao?: string): Promise<PaymentPlanOption[]> {
  const params = new URLSearchParams()
  if (descricao) params.set('descricao', descricao)
  return apiFetch<PaymentPlanOption[]>(`/financeiro/planos-pagamentos${params.size ? `?${params.toString()}` : ''}`)
}

export async function getPaymentPlanById(planoId: number): Promise<PaymentPlanOption> {
  return apiFetch<PaymentPlanOption>(`/financeiro/planos-pagamentos/${planoId}`)
}

export async function createPaymentPlan(payload: PaymentPlanInput): Promise<PaymentPlanOption> {
  return apiFetch<PaymentPlanOption>('/financeiro/planos-pagamentos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updatePaymentPlan(planoId: number, payload: PaymentPlanInput): Promise<PaymentPlanOption> {
  return apiFetch<PaymentPlanOption>(`/financeiro/planos-pagamentos/${planoId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deletePaymentPlan(planoId: number): Promise<void> {
  return apiFetch<void>(`/financeiro/planos-pagamentos/${planoId}`, { method: 'DELETE' })
}