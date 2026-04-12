<template>
  <section class="panel whatsapp-panel">
    <header class="panel__header whatsapp-panel__header">
      <div>
        <h2 class="panel__title">Conexão com API do WhatsApp</h2>
        <p class="panel__subtitle">Consulta da conexão do Telefone 1 configurado em Parâmetros.</p>
      </div>
    </header>

    <article class="whatsapp-card whatsapp-card--summary">
      <div class="whatsapp-account-row">
        <div class="whatsapp-account-row__label">
          <span>Telefone 1</span>
          <strong>{{ formattedExpectedPhone }}</strong>
        </div>

        <div class="whatsapp-connection-indicator" :class="statusBadgeClass">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M16.75 13.96c-.25-.13-1.47-.72-1.69-.8-.23-.08-.39-.12-.56.12-.16.25-.64.8-.78.96-.14.17-.29.19-.54.07-.25-.13-1.05-.39-2-1.23-.74-.66-1.24-1.47-1.38-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.29.37-.43.12-.15.16-.25.25-.42.08-.17.04-.31-.02-.43-.06-.13-.56-1.35-.77-1.85-.2-.48-.4-.41-.56-.42h-.47c-.16 0-.42.06-.64.31-.22.25-.84.82-.84 2s.86 2.31.98 2.47c.12.17 1.69 2.58 4.1 3.62.57.25 1.02.4 1.37.51.57.18 1.08.16 1.49.1.45-.07 1.38-.56 1.57-1.11.2-.55.2-1.03.14-1.12-.06-.1-.22-.16-.46-.28ZM12.04 2C6.52 2 2.04 6.47 2.04 12c0 1.95.56 3.77 1.53 5.31L2 22l4.84-1.51A9.94 9.94 0 0 0 12.04 22C17.56 22 22.04 17.53 22.04 12S17.56 2 12.04 2Z"
              fill="currentColor"
            />
          </svg>
          <span>{{ statusLabel }}</span>
        </div>
      </div>

      <dl class="whatsapp-summary">
        <div>
          <dt>Status do serviço da API</dt>
          <dd>{{ serviceStatusLabel }}</dd>
        </div>
        <div>
          <dt>Status do provedor</dt>
          <dd>{{ providerStatusLabel }}</dd>
        </div>
      </dl>

      <p class="whatsapp-card__message">{{ statusMessage }}</p>

      <div class="whatsapp-card__actions">
        <button class="primary-button primary-button--success" :disabled="Boolean(status?.connected) || controller.state.connecting || controller.state.loading" type="button" @click="handleConnect">
          {{ controller.state.connecting ? 'Gerando QR Code...' : 'Conectar' }}
        </button>
        <button class="ghost-button" :disabled="controller.state.loading || controller.state.connecting" type="button" @click="handleRefresh">
          Atualizar status
        </button>
      </div>
    </article>

    <div v-if="controller.state.qrCodeDataUrl" class="whatsapp-qr-modal" role="dialog" aria-modal="true" aria-labelledby="whatsapp-qr-title">
      <div class="whatsapp-qr-modal__backdrop" @click="handleCloseQrPopup"></div>
      <div class="whatsapp-qr-modal__content">
        <h3 id="whatsapp-qr-title">Conectar WhatsApp</h3>
        <img class="whatsapp-qr-box__image" :src="controller.state.qrCodeDataUrl" alt="QR Code para conectar o WhatsApp" />
        <div class="whatsapp-qr-box__meta">
          <strong>{{ controller.state.countdown }}s</strong>
          <span>Escaneie com o Telefone 1.</span>
          <span>Após 15 segundos o popup fecha e o status é consultado novamente.</span>
        </div>
        <button class="ghost-button" type="button" @click="handleCloseQrPopup">Fechar</button>
      </div>
    </div>

    <p v-if="controller.state.error" class="feedback feedback--error">{{ controller.state.error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'

import { useWhatsAppConnectionController } from '@/controllers/useWhatsAppConnectionController'
import { errorAlert } from '@/services/alertService'

const controller = useWhatsAppConnectionController()

const status = computed(() => controller.state.status)
const statusLabel = computed(() => (status.value?.connected ? 'Conectado' : 'Desconectado'))
const serviceStatusLabel = computed(() => (status.value?.connected ? 'Conectado' : 'Desconectado'))
const statusBadgeClass = computed(() => (status.value?.connected ? 'whatsapp-status-badge--connected' : 'whatsapp-status-badge--disconnected'))
const formattedExpectedPhone = computed(() => formatPhone(status.value?.expected_phone ?? null))
const providerStatusLabel = computed(() => translateProviderStatus(status.value?.provider_status))
const statusMessage = computed(() => status.value?.message ?? 'Use Atualizar status para consultar a conexão com a API do WhatsApp.')

onMounted(() => {
  void controller.loadStatus().catch(async () => {
    if (controller.state.error) {
      await errorAlert(controller.state.error)
    }
  })
})

onUnmounted(() => {
  controller.dispose()
})

async function handleRefresh() {
  try {
    await controller.loadStatus()
  } catch {
    if (controller.state.error) {
      await errorAlert(controller.state.error)
    }
  }
}

async function handleConnect() {
  try {
    await controller.startConnectionFlow()
  } catch {
    if (controller.state.error) {
      await errorAlert(controller.state.error)
    }
  }
}

function handleCloseQrPopup() {
  controller.closeQrPopup()
}

function formatPhone(value: string | null): string {
  if (!value) {
    return 'Não informado'
  }

  const digits = value.replace(/\D/g, '')
  if (digits.length === 13) {
    return `+${digits.slice(0, 2)} (${digits.slice(2, 4)}) ${digits.slice(4, 9)}-${digits.slice(9)}`
  }
  if (digits.length === 12) {
    return `+${digits.slice(0, 2)} (${digits.slice(2, 4)}) ${digits.slice(4, 8)}-${digits.slice(8)}`
  }
  if (digits.length === 11) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
  }
  if (digits.length === 10) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`
  }
  return value
}

function translateProviderStatus(value: string | null | undefined): string {
  const normalized = (value ?? '').trim().toLowerCase()
  if (!normalized) {
    return 'Aguardando consulta'
  }
  if (normalized === 'follow server information') {
    return 'Seguindo informações do servidor'
  }
  if (normalized === 'scan') {
    return 'Aguardando leitura do QR Code'
  }
  if (normalized === 'ready') {
    return 'Pronto'
  }
  if (normalized === 'connected' || normalized === 'online' || normalized === '1') {
    return 'Conectado'
  }
  return value ?? 'Aguardando consulta'
}
</script>

<style scoped>
.whatsapp-panel {
  display: grid;
  gap: 1.5rem;
}

.whatsapp-panel__header {
  display: grid;
  gap: 0.45rem;
}

.whatsapp-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(244, 248, 246, 0.98));
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
  padding: 1.5rem;
}

.whatsapp-card--summary {
  display: grid;
  gap: 1.25rem;
}

.whatsapp-account-row {
  align-items: center;
  display: flex;
  gap: 1rem;
  justify-content: space-between;
}

.whatsapp-account-row__label {
  display: grid;
  gap: 0.35rem;
}

.whatsapp-account-row__label span {
  color: #5b6b63;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.whatsapp-account-row__label strong {
  color: #10281f;
  font-size: 1.1rem;
}

.whatsapp-summary {
  display: grid;
  gap: 0.9rem;
  margin: 0;
}

.whatsapp-summary div {
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 0.2rem;
  padding-bottom: 0.75rem;
}

.whatsapp-summary dt {
  color: #5b6b63;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.whatsapp-summary dd {
  color: #10281f;
  font-size: 1rem;
  font-weight: 700;
  margin: 0;
}

.whatsapp-card__message {
  color: #355548;
  line-height: 1.5;
  margin: 0;
}

.whatsapp-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.whatsapp-connection-indicator {
  align-items: center;
  border-radius: 999px;
  display: inline-flex;
  font-weight: 700;
  gap: 0.65rem;
  padding: 0.8rem 1.1rem;
}

.whatsapp-connection-indicator svg {
  height: 1.4rem;
  width: 1.4rem;
}

.whatsapp-status-badge--connected {
  background: rgba(34, 197, 94, 0.14);
  color: #15803d;
}

.whatsapp-status-badge--disconnected {
  background: rgba(220, 38, 38, 0.12);
  color: #b91c1c;
}

.whatsapp-qr-modal {
  inset: 0;
  position: fixed;
  z-index: 80;
}

.whatsapp-qr-modal__backdrop {
  background: rgba(15, 23, 42, 0.54);
  inset: 0;
  position: absolute;
}

.whatsapp-qr-modal__content {
  align-items: center;
  background:
    radial-gradient(circle at top, rgba(34, 197, 94, 0.12), transparent 35%),
    linear-gradient(180deg, rgba(244, 250, 247, 0.98), rgba(234, 243, 238, 0.98));
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.28);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  left: 50%;
  max-width: min(420px, calc(100vw - 2rem));
  padding: 1.5rem;
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
}

.whatsapp-qr-modal__content h3 {
  color: #12372a;
  margin: 0;
}

.whatsapp-qr-box__image {
  background: #ffffff;
  border: 14px solid #ffffff;
  border-radius: 28px;
  box-shadow: 0 20px 45px rgba(7, 94, 84, 0.18);
  max-width: min(320px, 100%);
  width: 100%;
}

.whatsapp-qr-box__meta {
  color: #234034;
  display: grid;
  gap: 0.35rem;
  justify-items: center;
  text-align: center;
}

.whatsapp-qr-box__meta strong {
  color: #0f766e;
  font-size: 2rem;
}

@media (max-width: 720px) {
  .whatsapp-account-row {
    align-items: stretch;
    flex-direction: column;
  }

  .whatsapp-card__actions {
    flex-direction: column;
  }
}
</style>