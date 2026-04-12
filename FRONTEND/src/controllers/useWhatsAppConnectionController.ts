import { reactive, readonly } from 'vue'

import type { WhatsAppConnectionStatus } from '@/models/whatsapp'
import { connectWhatsApp, getWhatsAppStatus } from '@/services/whatsappService'

export function useWhatsAppConnectionController() {
  const state = reactive({
    loading: false,
    connecting: false,
    error: '',
    countdown: 0,
    qrCodeDataUrl: '',
    qrMessage: '',
    status: null as WhatsAppConnectionStatus | null,
  })

  let timerId: number | null = null
  let tickBusy = false

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
      state.countdown = 15
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
      startTimer()
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao gerar o QR Code do WhatsApp'
      state.qrCodeDataUrl = ''
      state.countdown = 0
      state.qrMessage = state.error
      throw error
    } finally {
      state.connecting = false
    }
  }

  function startTimer(): void {
    clearTimer()
    timerId = window.setInterval(() => {
      void tick()
    }, 1000)
  }

  async function tick(): Promise<void> {
    if (tickBusy) {
      return
    }
    tickBusy = true
    try {
      if (state.countdown > 0) {
        state.countdown -= 1
      }

      if (state.countdown <= 0) {
        clearTimer()
        await finalizeConnectionFlow()
      }
    } finally {
      tickBusy = false
    }
  }

  async function finalizeConnectionFlow(): Promise<void> {
    try {
      state.status = await getWhatsAppStatus()
    } catch {
      // Mantem o fechamento do popup mesmo quando a consulta final falha.
    }
    resetQrState()
  }

  function resetQrState(): void {
    clearTimer()
    state.qrCodeDataUrl = ''
    state.countdown = 0
    state.qrMessage = ''
  }

  function clearTimer(): void {
    if (timerId !== null) {
      window.clearInterval(timerId)
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