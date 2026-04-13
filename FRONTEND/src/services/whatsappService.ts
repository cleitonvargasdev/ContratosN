import type {
  WhatsAppConnectionStatus,
  WhatsAppDispatchBatchFilters,
  WhatsAppDispatchBatchListResponse,
  WhatsAppDispatchItemListResponse,
  WhatsAppQrCodeResponse,
} from '@/models/whatsapp'
import { apiFetch } from '@/services/http'

export async function getWhatsAppStatus(): Promise<WhatsAppConnectionStatus> {
  return apiFetch<WhatsAppConnectionStatus>('/whatsapp/status')
}

export async function connectWhatsApp(): Promise<WhatsAppQrCodeResponse> {
  return apiFetch<WhatsAppQrCodeResponse>('/whatsapp/conectar', {
    method: 'POST',
  })
}

export async function listWhatsAppDispatchBatches(filters: WhatsAppDispatchBatchFilters): Promise<WhatsAppDispatchBatchListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))
  if (filters.data_inicial) params.set('data_inicial', filters.data_inicial)
  if (filters.data_final) params.set('data_final', filters.data_final)
  return apiFetch<WhatsAppDispatchBatchListResponse>(`/whatsapp/envios?${params.toString()}`)
}

export async function listWhatsAppDispatchItems(batchId: number, page: number, pageSize: number): Promise<WhatsAppDispatchItemListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(page))
  params.set('page_size', String(pageSize))
  return apiFetch<WhatsAppDispatchItemListResponse>(`/whatsapp/envios/${batchId}/itens?${params.toString()}`)
}

export async function deleteWhatsAppDispatchBatch(batchId: number): Promise<void> {
  return apiFetch<void>(`/whatsapp/envios/${batchId}`, {
    method: 'DELETE',
  })
}