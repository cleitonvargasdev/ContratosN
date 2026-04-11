import { reactive, readonly } from 'vue'

import type { WhatsAppConnectionStatus, WhatsAppQrCodeResponse } from '@/models/whatsapp'
import { connectWhatsApp, getWhatsAppStatus } from '@/services/whatsappService'

const MAX_ATTEMPTS = 3
const STATUS_POLL_INTERVAL_SECONDS = 3

export function useWhatsAppConnectionController() {
  const state = reactive({
    loading: false,
    connecting: false,
    error: '',
    attempts: 0,
    countdown: 0,
    qrCodeDataUrl: '',
    qrMessage: '',
    exhausted: false,
    status: null as WhatsAppConnectionStatus | null,
  })

  let timerId: number | null = null
  let tickBusy = false
  let statusPollCounter = 0

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
    clearTimer()
    state.attempts = 0
    state.exhausted = false
    state.error = ''
    await requestQrCode()
  }

  async function requestQrCode(): Promise<void> {
    if (state.connecting || state.attempts >= MAX_ATTEMPTS) {
      return
    }

    state.connecting = true
    state.error = ''
    try {
      const response = await connectWhatsApp()
      applyQrResponse(response)
      state.attempts += 1
      state.exhausted = false
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

  function applyQrResponse(response: WhatsAppQrCodeResponse): void {
    state.qrCodeDataUrl = response.qr_code_data_url
    state.countdown = response.expires_in_seconds
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
  }

  function startTimer(): void {
    clearTimer()
    statusPollCounter = 0
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

      statusPollCounter += 1
      if (statusPollCounter >= STATUS_POLL_INTERVAL_SECONDS) {
        statusPollCounter = 0
        await refreshStatusDuringFlow()
        if (state.status?.connected) {
          return
        }
      }

      if (state.countdown <= 0) {
        clearTimer()
        await handleQrExpiration()
      }
    } finally {
      tickBusy = false
    }
  }

  async function refreshStatusDuringFlow(): Promise<void> {
    try {
      state.status = await getWhatsAppStatus()
      if (state.status.connected) {
        resetQrState()
      }
    } catch {
      // Mantem o fluxo do QR mesmo quando a consulta intermediaria falha.
    }
  }

  async function handleQrExpiration(): Promise<void> {
    await refreshStatusDuringFlow()
    if (state.status?.connected) {
      return
    }

    if (state.attempts >= MAX_ATTEMPTS) {
      resetQrState()
      state.exhausted = true
      state.qrMessage = 'Limite de 3 tentativas atingido. Clique em Conectar para gerar um novo QR Code.'
      return
    }

    await requestQrCode()
  }

  function resetQrState(): void {
    clearTimer()
    state.qrCodeDataUrl = ''
    state.countdown = 0
    state.qrMessage = ''
    state.exhausted = false
  }

  function clearTimer(): void {
    if (timerId !== null) {
      window.clearInterval(timerId)
      timerId = null
    }
    statusPollCounter = 0
  }

  function dispose(): void {
    clearTimer()
  }

  return {
    state: readonly(state),
    loadStatus,
    startConnectionFlow,
    dispose,
  }
}