<template>
  <section class="panel whatsapp-panel">
    <header class="panel__header whatsapp-panel__header">
      <div>
        <p class="eyebrow">Integração QuePasa</p>
        <h2 class="panel__title">Conexão com API do WhatsApp</h2>
        <p class="panel__subtitle">Sessão única CONTRATOS vinculada ao Telefone 1 de Parâmetros.</p>
      </div>

      <div class="whatsapp-status-badge" :class="statusBadgeClass">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M16.75 13.96c-.25-.13-1.47-.72-1.69-.8-.23-.08-.39-.12-.56.12-.16.25-.64.8-.78.96-.14.17-.29.19-.54.07-.25-.13-1.05-.39-2-1.23-.74-.66-1.24-1.47-1.38-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.29.37-.43.12-.15.16-.25.25-.42.08-.17.04-.31-.02-.43-.06-.13-.56-1.35-.77-1.85-.2-.48-.4-.41-.56-.42h-.47c-.16 0-.42.06-.64.31-.22.25-.84.82-.84 2s.86 2.31.98 2.47c.12.17 1.69 2.58 4.1 3.62.57.25 1.02.4 1.37.51.57.18 1.08.16 1.49.1.45-.07 1.38-.56 1.57-1.11.2-.55.2-1.03.14-1.12-.06-.1-.22-.16-.46-.28ZM12.04 2C6.52 2 2.04 6.47 2.04 12c0 1.95.56 3.77 1.53 5.31L2 22l4.84-1.51A9.94 9.94 0 0 0 12.04 22C17.56 22 22.04 17.53 22.04 12S17.56 2 12.04 2Z"
            fill="currentColor"
          />
        </svg>
        <span>{{ statusLabel }}</span>
      </div>
    </header>

    <div class="whatsapp-grid">
      <article class="whatsapp-card whatsapp-card--info">
        <h3>Conferência da conta</h3>
        <dl class="whatsapp-summary">
          <div>
            <dt>Sessão</dt>
            <dd>{{ status?.session_key ?? 'CONTRATOS' }}</dd>
          </div>
          <div>
            <dt>Telefone 1</dt>
            <dd>{{ formattedExpectedPhone }}</dd>
          </div>
          <div>
            <dt>Número conectado</dt>
            <dd>{{ formattedConnectedPhone }}</dd>
          </div>
          <div>
            <dt>Status do provedor</dt>
            <dd>{{ status?.provider_status ?? 'Aguardando consulta' }}</dd>
          </div>
        </dl>

        <p class="whatsapp-card__message">{{ statusMessage }}</p>

        <div class="whatsapp-card__actions">
          <button class="primary-button primary-button--success" :disabled="controller.state.connecting" type="button" @click="handleConnect">
            {{ controller.state.connecting ? 'Gerando QR Code...' : 'Conectar' }}
          </button>
          <button class="ghost-button" :disabled="controller.state.loading || controller.state.connecting" type="button" @click="handleRefresh">
            Atualizar status
          </button>
        </div>
      </article>

      <article class="whatsapp-card whatsapp-card--qr">
        <div v-if="controller.state.qrCodeDataUrl" class="whatsapp-qr-box">
          <img class="whatsapp-qr-box__image" :src="controller.state.qrCodeDataUrl" alt="QR Code para conectar o WhatsApp" />
          <div class="whatsapp-qr-box__meta">
            <strong>{{ controller.state.countdown }}s</strong>
            <span>QR Code expira em 15 segundos.</span>
            <span>Tentativa {{ controller.state.attempts }} de 3.</span>
          </div>
        </div>

        <div v-else class="whatsapp-empty-state">
          <div class="whatsapp-empty-state__icon">QR</div>
          <h3>{{ emptyStateTitle }}</h3>
          <p>{{ emptyStateMessage }}</p>
        </div>
      </article>
    </div>

    <section v-if="showConfigurationHint" class="whatsapp-config-hint">
      <h3>Configuração pendente do QuePasa</h3>
      <p>O provedor exige um usuário válido no header X-QUEPASA-USER para gerar o QR Code.</p>
      <p>Defina no backend: QUEPASA_USER=cleitinhojt@gmail.com</p>
      <p>Depois reinicie a API para recarregar as variáveis de ambiente.</p>
    </section>

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
const statusBadgeClass = computed(() => (status.value?.connected ? 'whatsapp-status-badge--connected' : 'whatsapp-status-badge--disconnected'))
const showConfigurationHint = computed(() => isQuePasaUserError(controller.state.error))

const formattedExpectedPhone = computed(() => formatPhone(status.value?.expected_phone ?? null))
const formattedConnectedPhone = computed(() => formatPhone(status.value?.connected_phone ?? null))
const statusMessage = computed(() => status.value?.message ?? 'Verifique a conexão e gere um QR Code quando necessário.')

const emptyStateTitle = computed(() => {
  if (controller.state.exhausted) {
    return 'QR Code pausado'
  }
  if (status.value?.connected) {
    return 'Conta conectada'
  }
  return 'Pronto para conectar'
})

const emptyStateMessage = computed(() => {
  if (controller.state.exhausted) {
    return controller.state.qrMessage || 'O limite de 3 tentativas foi atingido. Gere um novo QR Code manualmente.'
  }
  if (status.value?.connected) {
    return 'A sessão CONTRATOS já está conectada. Nenhum QR Code é necessário neste momento.'
  }
  return controller.state.qrMessage || 'Clique em Conectar para gerar o QR Code da sessão CONTRATOS.'
})

onMounted(() => {
  void controller.loadStatus().catch(async () => {
    if (controller.state.error && !isQuePasaUserError(controller.state.error)) {
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
    if (controller.state.error && !isQuePasaUserError(controller.state.error)) {
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

function isQuePasaUserError(message: string): boolean {
  const normalized = message.toLowerCase()
  return normalized.includes('quepasa_user') || normalized.includes('usuario do quepasa') || normalized.includes('missing user name parameter')
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
</script>

<style scoped>
.whatsapp-panel {
  display: grid;
  gap: 1.5rem;
}

.whatsapp-panel__header {
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.whatsapp-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: minmax(280px, 380px) minmax(0, 1fr);
}

.whatsapp-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(244, 248, 246, 0.98));
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
  padding: 1.5rem;
}

.whatsapp-card h3 {
  color: #12372a;
  font-size: 1.05rem;
  margin: 0 0 1rem;
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
  margin: 1rem 0 0;
}

.whatsapp-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.whatsapp-status-badge {
  align-items: center;
  border-radius: 999px;
  display: inline-flex;
  font-weight: 700;
  gap: 0.65rem;
  padding: 0.8rem 1.1rem;
}

.whatsapp-status-badge svg {
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

.whatsapp-card--qr {
  align-items: center;
  background:
    radial-gradient(circle at top, rgba(34, 197, 94, 0.12), transparent 35%),
    linear-gradient(180deg, rgba(244, 250, 247, 0.96), rgba(234, 243, 238, 0.98));
  display: flex;
  justify-content: center;
  min-height: 420px;
}

.whatsapp-config-hint {
  background: linear-gradient(180deg, rgba(255, 247, 237, 0.96), rgba(255, 251, 235, 0.98));
  border: 1px solid rgba(194, 120, 3, 0.22);
  border-radius: 20px;
  color: #8a4b08;
  display: grid;
  gap: 0.45rem;
  padding: 1rem 1.2rem;
}

.whatsapp-config-hint h3 {
  color: #9a3412;
  margin: 0;
}

.whatsapp-config-hint p {
  margin: 0;
}

.whatsapp-qr-box {
  align-items: center;
  display: grid;
  gap: 1.25rem;
  justify-items: center;
  width: 100%;
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

.whatsapp-empty-state {
  align-items: center;
  color: #264438;
  display: grid;
  gap: 0.9rem;
  justify-items: center;
  max-width: 340px;
  text-align: center;
}

.whatsapp-empty-state h3 {
  margin: 0;
}

.whatsapp-empty-state p {
  line-height: 1.6;
  margin: 0;
}

.whatsapp-empty-state__icon {
  align-items: center;
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  border-radius: 24px;
  color: #15803d;
  display: inline-flex;
  font-size: 1.4rem;
  font-weight: 800;
  height: 84px;
  justify-content: center;
  letter-spacing: 0.12em;
  width: 84px;
}

@media (max-width: 960px) {
  .whatsapp-panel__header {
    flex-direction: column;
  }

  .whatsapp-grid {
    grid-template-columns: 1fr;
  }

  .whatsapp-card--qr {
    min-height: 360px;
  }
}
</style>