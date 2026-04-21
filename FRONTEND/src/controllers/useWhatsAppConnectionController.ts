import { reactive, readonly } from 'vue'

import type { WhatsAppConnectionStatus } from '@/models/whatsapp'
import { connectWhatsApp, getWhatsAppStatus } from '@/services/whatsappService'

export function useWhatsAppConnectionController() {
  const state = reactive({
    loading: false,
    connecting: false,
    error: '',
    qrCodeDataUrl: '',
    qrMessage: '',
    status: null as WhatsAppConnectionStatus | null,
  })

  let timerId: number | null = null
  let statusRequestBusy = false

  async function loadStatus(): Promise<void> {
    state.loading = true
    state.error = ''
    try {
      state.status = await getWhatsAppStatus()
      if (state.status.connected) {
        resetQrState()
      }
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao consultar o status do WhatsApp'
      throw error
    } finally {
      state.loading = false
    }
  }

  async function startConnectionFlow(): Promise<void> {
    if (state.status?.connected || state.connecting) {
      return
    }

    clearTimer()
    state.error = ''
    state.connecting = true
    try {
      const response = await connectWhatsApp()
      state.qrCodeDataUrl = response.qr_code_data_url
      state.qrMessage = response.message ?? ''
      if (state.status) {
        state.status = {
          ...state.status,
          expected_phone: response.expected_phone,
          provider_status: response.provider_status,
          message: response.message ?? state.status.message,
          connected: false,
        }
      }
      scheduleStatusPoll()
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao gerar o QR Code do WhatsApp'
      state.qrCodeDataUrl = ''
      state.qrMessage = state.error
      throw error
    } finally {
      state.connecting = false
    }
  }

  function scheduleStatusPoll(): void {
    clearTimer()
    if (!state.qrCodeDataUrl) {
      return
    }
    timerId = window.setTimeout(() => {
      void pollConnectionStatus()
    }, 3000)
  }

  async function pollConnectionStatus(): Promise<void> {
    if (statusRequestBusy || !state.qrCodeDataUrl) {
      return
    }
    statusRequestBusy = true
    try {
      await loadStatus()
    } finally {
      statusRequestBusy = false
      if (state.qrCodeDataUrl && !state.status?.connected) {
        scheduleStatusPoll()
      }
    }
  }

  function resetQrState(): void {
    clearTimer()
    state.qrCodeDataUrl = ''
    state.qrMessage = ''
  }

  function clearTimer(): void {
    if (timerId !== null) {
      window.clearTimeout(timerId)
      timerId = null
    }
  }

  function closeQrPopup(): void {
    resetQrState()
  }

  function dispose(): void {
    resetQrState()
  }

  return {
    state: readonly(state),
    loadStatus,
    startConnectionFlow,
    closeQrPopup,
    dispose,
  }
}