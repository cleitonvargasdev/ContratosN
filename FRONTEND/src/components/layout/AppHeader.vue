<template>
  <header class="topbar">
    <div class="topbar__logout-card">
      <div
        class="topbar__action-button topbar__whatsapp-status"
        :class="whatsAppStatus.connected ? 'topbar__whatsapp-status--connected' : 'topbar__whatsapp-status--disconnected'"
        :title="whatsAppStatus.message"
        :aria-label="whatsAppStatus.message"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M17.47 14.38c-.27-.13-1.58-.78-1.82-.87-.25-.09-.43-.13-.61.14-.18.27-.7.87-.86 1.05-.16.18-.31.2-.58.07-.27-.13-1.12-.41-2.13-1.31-.79-.7-1.32-1.57-1.47-1.84-.16-.27-.02-.42.12-.55.12-.12.27-.31.4-.47.14-.16.18-.27.27-.45.09-.18.04-.34-.02-.47-.07-.13-.61-1.48-.84-2.03-.22-.53-.44-.46-.61-.47l-.52-.01c-.18 0-.47.07-.72.34-.25.27-.95.93-.95 2.27s.97 2.64 1.11 2.82c.13.18 1.9 2.89 4.6 4.05.64.28 1.15.44 1.54.56.65.21 1.24.18 1.71.11.52-.08 1.58-.65 1.8-1.27.22-.63.22-1.17.15-1.28-.06-.11-.24-.18-.51-.31Z"
            fill="currentColor"
          />
          <path
            d="M20.52 3.48A11.86 11.86 0 0 0 12.06 0C5.5 0 .16 5.34.16 11.9c0 2.1.55 4.16 1.6 5.98L0 24l6.28-1.65a11.9 11.9 0 0 0 5.78 1.48h.01c6.56 0 11.9-5.34 11.9-11.9 0-3.18-1.24-6.16-3.45-8.45ZM12.07 21.8h-.01a9.88 9.88 0 0 1-5.03-1.37l-.36-.21-3.73.98 1-3.63-.24-.37a9.88 9.88 0 0 1-1.51-5.3c0-5.47 4.45-9.92 9.92-9.92 2.65 0 5.14 1.03 7.01 2.91a9.86 9.86 0 0 1 2.89 7.02c0 5.47-4.45 9.92-9.92 9.92Z"
            fill="currentColor"
          />
        </svg>
      </div>
      <button
        class="topbar__action-button"
        type="button"
        title="Notificações e chat interno"
        aria-label="Notificações e chat interno"
        @click="handleToggleChat"
      >
        <span v-if="chat.unreadCount.value" class="topbar__action-badge">{{ chat.unreadCount.value }}</span>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 3a6 6 0 0 1 6 6v2.79c0 .53.21 1.04.59 1.41l1 1A1 1 0 0 1 18.88 16H5.12a1 1 0 0 1-.71-1.71l1-1A1.99 1.99 0 0 0 6 11.79V9a6 6 0 0 1 6-6Zm0 19a3 3 0 0 0 2.82-2H9.18A3 3 0 0 0 12 22Z" />
        </svg>
      </button>
      <button
        class="topbar__logout-button"
        type="button"
        title="Sair do sistema"
        aria-label="Sair do sistema"
        @click="handleLogout"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M12 3a1 1 0 0 1 1 1v7a1 1 0 1 1-2 0V4a1 1 0 0 1 1-1Zm0 18a8 8 0 0 1-5.657-13.657 1 1 0 1 1 1.414 1.414A6 6 0 1 0 16.243 8.757a1 1 0 0 1 1.414-1.414A8 8 0 0 1 12 21Z"
          />
        </svg>
      </button>
    </div>
  </header>

  <ChatDrawer />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthController } from '@/controllers/useAuthController'
import { useChatController } from '@/controllers/useChatController'
import ChatDrawer from '@/components/layout/ChatDrawer.vue'
import { getWhatsAppStatus } from '@/services/whatsappService'

const auth = useAuthController()
const chat = useChatController()
const router = useRouter()
const whatsAppStatus = reactive({
  connected: false,
  message: 'WhatsApp desconectado.',
})

let statusPollTimer: number | null = null

onMounted(() => {
  void chat.initialize()
  void loadWhatsAppStatus()
  statusPollTimer = window.setInterval(() => {
    void loadWhatsAppStatus()
  }, 15000)
})

onBeforeUnmount(() => {
  if (statusPollTimer !== null) {
    window.clearInterval(statusPollTimer)
    statusPollTimer = null
  }
})

async function loadWhatsAppStatus() {
  try {
    const status = await getWhatsAppStatus()
    whatsAppStatus.connected = status.connected
    whatsAppStatus.message = status.message ?? (status.connected ? 'WhatsApp conectado.' : 'WhatsApp desconectado.')
  } catch {
    whatsAppStatus.connected = false
    whatsAppStatus.message = 'WhatsApp desconectado.'
  }
}

async function handleToggleChat() {
  await chat.toggleDrawer()
}

function handleLogout() {
  chat.resetChat()
  auth.logout()
  void router.push({ name: 'login' })
}
</script>

<style scoped>
.topbar__whatsapp-status {
  cursor: default;
}

.topbar__whatsapp-status svg {
  fill: currentColor;
}

.topbar__whatsapp-status--connected {
  color: #15803d;
  border-color: rgba(22, 163, 74, 0.22);
  background: rgba(22, 163, 74, 0.12);
}

.topbar__whatsapp-status--disconnected {
  color: #b91c1c;
  border-color: rgba(220, 38, 38, 0.18);
  background: rgba(220, 38, 38, 0.1);
}
</style>
