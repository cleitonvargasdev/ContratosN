<template>
  <Teleport to="body">
    <div v-if="chat.state.open" class="chat-overlay" @click.self="chat.closeDrawer()">
      <aside class="chat-drawer">
        <header class="chat-drawer__header">
          <div>
            <p class="eyebrow">Chat interno</p>
            <h2 class="chat-drawer__title">Conversas</h2>
          </div>
          <button class="ghost-button chat-drawer__close" type="button" @click="chat.closeDrawer()">Fechar</button>
        </header>

        <div class="chat-drawer__body">
          <section class="chat-sidebar">
            <input v-model="searchTerm" class="field" type="text" placeholder="Buscar usuário" />

            <div class="chat-sidebar__list">
              <button
                v-for="conversation in filteredConversations"
                :key="`conversation-${conversation.peer.id}`"
                :class="['chat-sidebar__item', { 'chat-sidebar__item--active': chat.state.selectedPeerId === conversation.peer.id }]"
                type="button"
                @click="handleSelectPeer(conversation.peer.id)"
              >
                <div class="chat-sidebar__item-main">
                  <strong>{{ conversation.peer.nome }}</strong>
                  <span :class="['chat-user-status', conversation.peer.online ? 'chat-user-status--online' : 'chat-user-status--offline']">
                    <i class="chat-user-status__dot" aria-hidden="true"></i>
                    {{ conversation.peer.online ? 'Online' : 'Offline' }}
                  </span>
                  <span v-if="conversation.last_message">{{ previewMessage(conversation.last_message.content) }}</span>
                  <span v-else>Nenhuma mensagem ainda.</span>
                </div>
                <div class="chat-sidebar__item-meta">
                  <span v-if="conversation.unread_count" class="chat-sidebar__badge">{{ conversation.unread_count }}</span>
                  <span v-if="conversation.muted" class="chat-sidebar__muted" title="Silenciado">🔕</span>
                </div>
              </button>

              <div v-if="filteredNewContacts.length > 0" class="chat-sidebar__section-label">Iniciar conversa</div>
              <button
                v-for="contact in filteredNewContacts"
                :key="`contact-${contact.id}`"
                :class="['chat-sidebar__item', { 'chat-sidebar__item--active': chat.state.selectedPeerId === contact.id }]"
                type="button"
                @click="handleSelectPeer(contact.id)"
              >
                <div class="chat-sidebar__item-main">
                  <strong>{{ contact.nome }}</strong>
                  <span :class="['chat-user-status', contact.online ? 'chat-user-status--online' : 'chat-user-status--offline']">
                    <i class="chat-user-status__dot" aria-hidden="true"></i>
                    {{ contact.online ? 'Online' : 'Offline' }}
                  </span>
                  <span>{{ contact.login }}</span>
                </div>
              </button>
            </div>
          </section>

          <section class="chat-thread">
            <template v-if="selectedPeer">
              <header class="chat-thread__header">
                <div>
                  <h3>{{ selectedPeer.nome }}</h3>
                  <p>{{ selectedPeer.login }}</p>
                  <span :class="['chat-user-status', selectedPeer.online ? 'chat-user-status--online' : 'chat-user-status--offline']">
                    <i class="chat-user-status__dot" aria-hidden="true"></i>
                    {{ selectedPeer.online ? 'Online' : 'Offline' }}
                  </span>
                </div>
                <div ref="actionsMenuRef" class="chat-thread__header-actions">
                  <button
                    class="ghost-button chat-thread__menu-trigger"
                    type="button"
                    aria-label="Mais ações da conversa"
                    :aria-expanded="actionsMenuOpen"
                    @click.stop="toggleActionsMenu()"
                  >
                    <span></span>
                    <span></span>
                    <span></span>
                  </button>

                  <div v-if="actionsMenuOpen" class="chat-thread__menu" @click.stop>
                    <button class="chat-thread__menu-item" type="button" @click="handleToggleMute(selectedPeer.id)">
                      {{ selectedConversation?.muted ? 'Reativar notificações' : 'Silenciar' }}
                    </button>
                    <button class="chat-thread__menu-item chat-thread__menu-item--danger" type="button" @click="handleClearConversation(selectedPeer.id)">
                      Limpar conversa
                    </button>
                  </div>
                </div>
              </header>

              <div ref="messagesContainerRef" class="chat-thread__messages">
                <p v-if="chat.state.loadingMessages" class="chat-thread__placeholder">Carregando mensagens...</p>
                <p v-else-if="selectedMessages.length === 0" class="chat-thread__placeholder">Nenhuma mensagem enviada ainda.</p>
                <article
                  v-for="message in selectedMessages"
                  :key="message.id"
                  :class="['chat-bubble', message.sender_id === currentUserId ? 'chat-bubble--mine' : 'chat-bubble--theirs']"
                >
                  <div class="chat-bubble__row">
                    <p>{{ message.content }}</p>
                    <button
                      v-if="message.sender_id === currentUserId"
                      class="chat-bubble__delete"
                      type="button"
                      title="Apagar mensagem"
                      aria-label="Apagar mensagem"
                      @click="handleDeleteMessage(message.id)"
                    >
                      ×
                    </button>
                  </div>
                  <div class="chat-bubble__meta">
                    <time>{{ formatTimestamp(message.created_at) }}</time>
                    <span v-if="message.sender_id === currentUserId" :class="['chat-bubble__status', statusClass(message)]">{{ statusIcon(message) }}</span>
                  </div>
                  <div v-if="message.sender_id === currentUserId && message.read_at" class="chat-bubble__read-time">
                    Lido {{ formatReadTimestamp(message.read_at) }}
                  </div>
                </article>
              </div>

              <form class="chat-thread__composer" @submit.prevent="handleSendMessage">
                <input
                  ref="messageInputRef"
                  :value="chat.state.draftMessage"
                  class="field"
                  type="text"
                  placeholder="Digite uma mensagem"
                  :disabled="chat.state.sending"
                  @input="chat.setDraftMessage(($event.target as HTMLInputElement).value)"
                />
                <button class="primary-button primary-button--accent-soft" type="submit" :disabled="chat.state.sending">
                  {{ chat.state.sending ? 'Enviando...' : 'Enviar' }}
                </button>
              </form>
            </template>

            <div v-else class="chat-thread__empty">
              <p>Selecione um usuário para abrir o chat interno.</p>
            </div>
          </section>
        </div>
      </aside>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { useAuthController } from '@/controllers/useAuthController'
import { useChatController } from '@/controllers/useChatController'
import { errorAlert } from '@/services/alertService'

const chat = useChatController()
const auth = useAuthController()
const searchTerm = ref('')
const actionsMenuOpen = ref(false)
const actionsMenuRef = ref<HTMLElement | null>(null)
const messagesContainerRef = ref<HTMLElement | null>(null)
const messageInputRef = ref<HTMLInputElement | null>(null)

const filteredConversations = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  if (!term) {
    return chat.state.conversations
  }

  return chat.state.conversations.filter((conversation) => {
    const haystack = `${conversation.peer.nome} ${conversation.peer.login} ${conversation.last_message?.content ?? ''}`.toLowerCase()
    return haystack.includes(term)
  })
})

const filteredNewContacts = computed(() => {
  const usedPeerIds = new Set(chat.state.conversations.map((conversation) => conversation.peer.id))
  const term = searchTerm.value.trim().toLowerCase()

  return chat.state.contacts.filter((contact) => {
    if (usedPeerIds.has(contact.id)) {
      return false
    }
    if (!term) {
      return true
    }
    return `${contact.nome} ${contact.login}`.toLowerCase().includes(term)
  })
})

const selectedConversation = computed(() => chat.selectedConversation.value)
const selectedMessages = computed(() => chat.selectedMessages.value)
const selectedPeer = computed(() => selectedConversation.value?.peer ?? chat.selectedContact.value)
const currentUserId = computed(() => auth.state.currentUser?.id ?? 0)

async function handleSelectPeer(peerUserId: number) {
  try {
    await chat.selectPeer(peerUserId)
  } catch {
    if (chat.state.error) {
      await errorAlert(chat.state.error)
    }
  }
}

async function handleSendMessage() {
  try {
    await chat.sendDraftMessage()
    await nextTick()
    messageInputRef.value?.focus()
  } catch {
    if (chat.state.error) {
      await errorAlert(chat.state.error)
    }
  }
}

async function handleDeleteMessage(messageId: number) {
  try {
    await chat.removeMessage(messageId)
  } catch {
    if (chat.state.error) {
      await errorAlert(chat.state.error)
    }
  }
}

async function handleToggleMute(peerUserId: number) {
  closeActionsMenu()
  try {
    await chat.toggleMute(peerUserId)
  } catch {
    if (chat.state.error) {
      await errorAlert(chat.state.error)
    }
  }
}

async function handleClearConversation(peerUserId: number) {
  closeActionsMenu()
  try {
    await chat.clearConversation(peerUserId)
  } catch {
    if (chat.state.error) {
      await errorAlert(chat.state.error)
    }
  }
}

function toggleActionsMenu(): void {
  actionsMenuOpen.value = !actionsMenuOpen.value
}

function closeActionsMenu(): void {
  actionsMenuOpen.value = false
}

async function scrollMessagesToBottom(): Promise<void> {
  await nextTick()
  const container = messagesContainerRef.value
  if (!container || !chat.state.open) {
    return
  }

  container.scrollTop = container.scrollHeight
}

function handleDocumentClick(event: MouseEvent): void {
  if (!actionsMenuRef.value) {
    return
  }

  const target = event.target
  if (target instanceof Node && !actionsMenuRef.value.contains(target)) {
    closeActionsMenu()
  }
}

function previewMessage(content: string): string {
  return content.length > 42 ? `${content.slice(0, 42)}...` : content
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit',
  }).format(new Date(value))
}

function formatReadTimestamp(value: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function statusIcon(message: { delivered_at: string | null; read_at: string | null }): string {
  if (message.read_at) {
    return '✓✓'
  }
  if (message.delivered_at) {
    return '✓✓'
  }
  return '✓'
}

function statusClass(message: { delivered_at: string | null; read_at: string | null }): string {
  if (message.read_at) {
    return 'chat-bubble__status--read'
  }
  if (message.delivered_at) {
    return 'chat-bubble__status--delivered'
  }
  return 'chat-bubble__status--sent'
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})

watch(
  () => [chat.state.open, chat.state.selectedPeerId, selectedMessages.value.length],
  async ([isOpen]) => {
    if (!isOpen) {
      return
    }

    await scrollMessagesToBottom()
  },
)
</script>

<style scoped>
.chat-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.16);
  z-index: 70;
}

.chat-drawer {
  position: absolute;
  top: 18px;
  right: 22px;
  width: min(920px, calc(100vw - 32px));
  height: min(78vh, 720px);
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(36, 48, 59, 0.08);
  border-radius: 14px;
  box-shadow: 0 28px 54px rgba(15, 23, 42, 0.16);
  display: grid;
  grid-template-rows: auto 1fr;
  overflow: hidden;
}

.chat-drawer__header {
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(36, 48, 59, 0.08);
}

.chat-drawer__title,
.chat-thread__header h3 {
  margin: 0;
}

.chat-drawer__body {
  display: grid;
  grid-template-columns: 290px minmax(0, 1fr);
  min-height: 0;
}

.chat-sidebar {
  padding: 12px;
  border-right: 1px solid rgba(36, 48, 59, 0.08);
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 10px;
  min-height: 0;
}

.chat-sidebar__list {
  min-height: 0;
  overflow-y: auto;
  display: grid;
  gap: 8px;
}

.chat-sidebar__section-label {
  margin-top: 6px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(36, 48, 59, 0.5);
}

.chat-sidebar__item {
  padding: 10px 12px;
  border: 1px solid rgba(36, 48, 59, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  justify-content: space-between;
  gap: 10px;
  cursor: pointer;
  text-align: left;
}

.chat-sidebar__item--active {
  border-color: rgba(249, 115, 22, 0.22);
  background: rgba(249, 115, 22, 0.08);
}

.chat-sidebar__item-main {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.chat-sidebar__item-main strong,
.chat-sidebar__item-main span,
.chat-thread__header p,
.chat-bubble p,
.chat-bubble time,
.chat-thread__placeholder,
.chat-thread__empty p {
  margin: 0;
}

.chat-sidebar__item-main span {
  color: rgba(36, 48, 59, 0.58);
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-user-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  white-space: nowrap;
}

.chat-user-status__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
  box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.08);
}

.chat-user-status--online {
  color: #1f9d68 !important;
}

.chat-user-status--offline {
  color: rgba(109, 125, 141, 0.86) !important;
}

.chat-sidebar__item-meta {
  display: grid;
  justify-items: end;
  align-content: start;
  gap: 4px;
}

.chat-sidebar__badge {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(249, 115, 22, 0.16);
  color: rgba(216, 90, 4, 0.92);
  font-size: 11px;
  font-weight: 800;
}

.chat-sidebar__muted {
  font-size: 12px;
}

.chat-thread {
  min-height: 0;
  display: grid;
  grid-template-rows: auto 1fr auto;
}

.chat-thread__header {
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(36, 48, 59, 0.08);
}

.chat-thread__header-actions {
  position: relative;
  display: flex;
  justify-content: flex-end;
}

.chat-thread__header p {
  color: rgba(36, 48, 59, 0.56);
  font-size: 12px;
}

.chat-thread__header .chat-user-status {
  margin-top: 4px;
}

.chat-thread__mute,
.chat-drawer__close {
  min-height: 30px;
}

.chat-thread__menu-trigger {
  width: 34px;
  min-height: 34px;
  padding: 0;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
}

.chat-thread__menu-trigger span {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: currentColor;
}

.chat-thread__menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 210px;
  padding: 8px;
  border: 1px solid rgba(36, 48, 59, 0.08);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.12);
  display: grid;
  gap: 4px;
  z-index: 3;
}

.chat-thread__menu-item {
  width: 100%;
  padding: 10px 12px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #24303b;
  text-align: left;
  cursor: pointer;
  transition: background 160ms ease, color 160ms ease;
}

.chat-thread__menu-item:hover {
  background: rgba(249, 115, 22, 0.08);
  color: rgba(216, 90, 4, 0.92);
}

.chat-thread__menu-item--danger:hover {
  background: rgba(216, 75, 98, 0.08);
  color: rgba(182, 63, 82, 0.95);
}

.chat-thread__messages {
  padding: 16px;
  overflow-y: auto;
  display: grid;
  align-content: start;
  gap: 10px;
  background: linear-gradient(180deg, rgba(249, 115, 22, 0.04), rgba(255, 255, 255, 0.86));
}

.chat-bubble {
  max-width: min(72%, 420px);
  padding: 10px 12px;
  border-radius: 10px;
  display: grid;
  gap: 6px;
}

.chat-bubble__row,
.chat-bubble__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.chat-bubble__delete {
  border: 0;
  background: transparent;
  color: rgba(36, 48, 59, 0.45);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0;
}

.chat-bubble__delete:hover {
  color: rgba(216, 75, 98, 0.8);
}

.chat-bubble__status {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: -0.08em;
}

.chat-bubble__status--sent {
  color: rgba(36, 48, 59, 0.48);
}

.chat-bubble__status--delivered {
  color: rgba(36, 48, 59, 0.62);
}

.chat-bubble__status--read {
  color: #2684ff;
}

.chat-bubble__read-time {
  font-size: 10px;
  color: rgba(36, 48, 59, 0.52);
  text-align: right;
}

.chat-bubble--mine {
  justify-self: end;
  background: rgba(249, 115, 22, 0.14);
  color: #7a3a0a;
}

.chat-bubble--theirs {
  justify-self: start;
  background: rgba(36, 48, 59, 0.08);
}

.chat-bubble time {
  font-size: 10px;
  color: rgba(36, 48, 59, 0.56);
}

.chat-thread__composer {
  padding: 14px 16px;
  border-top: 1px solid rgba(36, 48, 59, 0.08);
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.chat-thread__placeholder,
.chat-thread__empty {
  color: rgba(36, 48, 59, 0.56);
}

.chat-thread__empty {
  display: grid;
  place-items: center;
  padding: 16px;
}

@media (max-width: 980px) {
  .chat-drawer {
    top: 10px;
    right: 10px;
    left: 10px;
    width: auto;
    height: calc(100vh - 20px);
  }

  .chat-drawer__body {
    grid-template-columns: 1fr;
    grid-template-rows: 220px 1fr;
  }

  .chat-sidebar {
    border-right: 0;
    border-bottom: 1px solid rgba(36, 48, 59, 0.08);
  }
}
</style>