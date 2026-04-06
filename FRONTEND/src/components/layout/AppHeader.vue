<template>
  <header class="topbar">
    <div class="topbar__logout-card">
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
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthController } from '@/controllers/useAuthController'
import { useChatController } from '@/controllers/useChatController'
import ChatDrawer from '@/components/layout/ChatDrawer.vue'

const auth = useAuthController()
const chat = useChatController()
const router = useRouter()

onMounted(() => {
  void chat.initialize()
})

async function handleToggleChat() {
  await chat.toggleDrawer()
}

function handleLogout() {
  chat.resetChat()
  auth.logout()
  void router.push({ name: 'login' })
}
</script>
