import type { WhatsAppConnectionStatus, WhatsAppQrCodeResponse } from '@/models/whatsapp'
import { apiFetch } from '@/services/http'

export async function getWhatsAppStatus(): Promise<WhatsAppConnectionStatus> {
  return apiFetch<WhatsAppConnectionStatus>('/whatsapp/status')
}

export async function connectWhatsApp(): Promise<WhatsAppQrCodeResponse> {
  return apiFetch<WhatsAppQrCodeResponse>('/whatsapp/conectar', {
    method: 'POST',
  })
}