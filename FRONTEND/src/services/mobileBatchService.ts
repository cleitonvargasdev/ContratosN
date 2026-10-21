import { apiFetch } from '@/services/http'

export type MobileBatchItem = {
  id: number
  source_item_id: string
  kind: string
  client_id: number | null
  contract_id: number | null
  installment_id: number | null
  amount_units: number | null
  processed: boolean
  blocked: boolean
  block_reason: string | null
}

export type MobileBatch = {
  id: number
  source_id: string
  user_id: number
  status: string
  blocked: boolean
  block_reason: string | null
  items: MobileBatchItem[]
}

export function listBlockedMobileBatches() {
  return apiFetch<MobileBatch[]>('/mobile/lotes/bloqueados')
}

export function unlockMobileBatch(id: number, reason: string) {
  return apiFetch<MobileBatch>(`/mobile/lotes/${id}/desbloquear`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  })
}
