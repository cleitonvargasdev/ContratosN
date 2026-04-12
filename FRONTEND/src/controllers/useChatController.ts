import { computed, reactive, readonly } from 'vue'

import type { ChatConversation, ChatEventPayload, ChatMessage, ChatUserSummary } from '@/models/chat'
import { useAuthController } from '@/controllers/useAuthController'
import {
  clearChatConversation,
  connectChatEvents,
  deleteChatMessage,
  listChatContacts,
  listChatConversations,
  listChatMessages,
  markChatConversationRead,
  sendChatMessage,
  setChatMuted,
} from '@/services/chatService'
import { getParameters } from '@/services/parameterService'
import { chatMessageToast, playSmsNotificationSound } from '@/services/alertService'

const state = reactive({
  open: false,
  initialized: false,
  loadingConversations: false,
  loadingContacts: false,
  loadingMessages: false,
  sending: false,
  error: '',
  conversations: [] as ChatConversation[],
  contacts: [] as ChatUserSummary[],
  selectedPeerId: null as number | null,
  messagesByPeer: {} as Record<number, ChatMessage[]>,
  draftMessage: '',
})

const auth = useAuthController()
let socket: WebSocket | null = null
let reconnectTimer: number | null = null
let isManualSocketClose = false
let chatNotificationsMuted = false

async function initialize(): Promise<void> {
  await auth.initializeAuth()
  if (!auth.isAuthenticated.value) {
    return
  }

  if (!state.initialized) {
    await Promise.all([fetchConversations(), fetchContacts(), loadNotificationSettings()])
    state.initialized = true
  }

  connectSocket()
}

async function fetchConversations(): Promise<void> {
  state.loadingConversations = true
  state.error = ''
  try {
    state.conversations = await listChatConversations()
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao carregar conversas'
    throw error
  } finally {
    state.loadingConversations = false
  }
}

async function fetchContacts(term?: string): Promise<void> {
  state.loadingContacts = true
  try {
    state.contacts = await listChatContacts(term)
  } finally {
    state.loadingContacts = false
  }
}

async function loadNotificationSettings(): Promise<void> {
  try {
    const parameters = await getParameters()
    chatNotificationsMuted = Boolean(parameters.silenciar_mensagem)
  } catch {
    chatNotificationsMuted = false
  }
}

async function openDrawer(peerUserId?: number): Promise<void> {
  state.open = true
  await initialize()

  if (peerUserId) {
    await selectPeer(peerUserId)
    return
  }

  if (state.selectedPeerId !== null) {
    await loadMessages(state.selectedPeerId)
    await markConversationAsReadIfVisible(state.selectedPeerId)
    return
  }

  const firstPeerId = state.conversations[0]?.peer.id ?? state.contacts[0]?.id
  if (firstPeerId) {
    await selectPeer(firstPeerId)
  }
}

function closeDrawer(): void {
  state.open = false
}

async function toggleDrawer(): Promise<void> {
  if (state.open) {
    closeDrawer()
    return
  }

  await openDrawer()
}

async function selectPeer(peerUserId: number): Promise<void> {
  state.selectedPeerId = peerUserId
  await loadMessages(peerUserId)
  await markConversationAsReadIfVisible(peerUserId)
}

async function loadMessages(peerUserId: number): Promise<void> {
  state.loadingMessages = true
  state.error = ''
  try {
    state.messagesByPeer[peerUserId] = await listChatMessages(peerUserId)
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao carregar mensagens'
    throw error
  } finally {
    state.loadingMessages = false
  }
}

async function sendDraftMessage(): Promise<void> {
  const peerUserId = state.selectedPeerId
  const content = state.draftMessage.trim()
  if (!peerUserId || !content) {
    return
  }

  state.sending = true
  state.error = ''
  try {
    const response = await sendChatMessage(peerUserId, { content })
    upsertConversation(response.conversation)
    upsertMessage(peerUserId, response.message)
    state.draftMessage = ''
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao enviar mensagem'
    throw error
  } finally {
    state.sending = false
  }
}

async function removeMessage(messageId: number): Promise<void> {
  const peerUserId = state.selectedPeerId
  if (!peerUserId) {
    return
  }

  state.error = ''
  try {
    const response = await deleteChatMessage(peerUserId, messageId)
    state.messagesByPeer[peerUserId] = (state.messagesByPeer[peerUserId] ?? []).filter((item) => item.id !== messageId)
    upsertConversation(response.conversation)
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao apagar mensagem'
    throw error
  }
}

async function clearConversation(peerUserId: number): Promise<void> {
  state.error = ''
  try {
    const updatedConversation = await clearChatConversation(peerUserId)
    state.messagesByPeer[peerUserId] = []
    upsertConversation(updatedConversation)
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao limpar conversa'
    throw error
  }
}

async function toggleMute(peerUserId: number): Promise<void> {
  const conversation = state.conversations.find((item) => item.peer.id === peerUserId)
  const muted = !(conversation?.muted ?? false)
  const updatedConversation = await setChatMuted(peerUserId, { muted })
  upsertConversation(updatedConversation)
}

async function markSelectedConversationRead(peerUserId?: number): Promise<void> {
  const targetPeerId = peerUserId ?? state.selectedPeerId
  if (!targetPeerId) {
    return
  }

  try {
    const updatedConversation = await markChatConversationRead(targetPeerId)
    upsertConversation(updatedConversation)
  } catch {
    // Silent to avoid breaking the drawer for stale conversations.
  }
}

async function markConversationAsReadIfVisible(peerUserId: number): Promise<void> {
  if (!state.open || state.selectedPeerId !== peerUserId || document.visibilityState !== 'visible') {
    return
  }

  const conversation = getConversation(peerUserId)
  if (!conversation?.unread_count) {
    return
  }

  await markSelectedConversationRead(peerUserId)
}

function upsertConversation(conversation: ChatConversation): void {
  const currentIndex = state.conversations.findIndex((item) => item.peer.id === conversation.peer.id)
  if (currentIndex >= 0) {
    state.conversations.splice(currentIndex, 1)
  }
  state.conversations.unshift(conversation)
}

function getConversation(peerUserId: number): ChatConversation | undefined {
  return state.conversations.find((item) => item.peer.id === peerUserId)
}

function normalizeIncomingConversation(conversation: ChatConversation, peerUserId: number): ChatConversation {
  const existingConversation = getConversation(peerUserId)
  const shouldIncrementUnread = !state.open || state.selectedPeerId !== peerUserId
  if (!shouldIncrementUnread) {
    return conversation
  }

  return {
    ...conversation,
    unread_count: Math.max(conversation.unread_count, (existingConversation?.unread_count ?? 0) + 1),
  }
}

function updatePeerPresence(userId: number, online: boolean): void {
  state.conversations = state.conversations.map((conversation) => {
    if (conversation.peer.id !== userId) {
      return conversation
    }

    return {
      ...conversation,
      peer: {
        ...conversation.peer,
        online,
      },
    }
  })

  state.contacts = state.contacts.map((contact) => {
    if (contact.id !== userId) {
      return contact
    }

    return {
      ...contact,
      online,
    }
  })
}

function upsertMessage(peerUserId: number, message: ChatMessage): void {
  const current = state.messagesByPeer[peerUserId] ?? []
  const currentIndex = current.findIndex((item) => item.id === message.id)
  if (currentIndex >= 0) {
    const next = [...current]
    next[currentIndex] = { ...next[currentIndex], ...message }
    state.messagesByPeer[peerUserId] = next
    return
  }
  state.messagesByPeer[peerUserId] = [...current, message]
}

function syncConversationLastMessage(peerUserId: number, conversation: ChatConversation): void {
  const lastMessage = conversation.last_message
  if (!lastMessage) {
    return
  }

  upsertMessage(peerUserId, lastMessage)
}

function markPeerMessagesDelivered(peerUserId: number, deliveredAt: string | null): void {
  if (!deliveredAt) {
    return
  }

  const currentUserId = auth.state.currentUser?.id
  if (!currentUserId) {
    return
  }

  const current = state.messagesByPeer[peerUserId] ?? []
  state.messagesByPeer[peerUserId] = current.map((message) => {
    if (message.sender_id !== currentUserId || message.recipient_id !== peerUserId || message.delivered_at) {
      return message
    }
    return { ...message, delivered_at: deliveredAt }
  })
}

function markPeerMessagesRead(peerUserId: number, readAt: string | null): void {
  if (!readAt) {
    return
  }

  const currentUserId = auth.state.currentUser?.id
  if (!currentUserId) {
    return
  }

  const current = state.messagesByPeer[peerUserId] ?? []
  state.messagesByPeer[peerUserId] = current.map((message) => {
    if (message.sender_id !== currentUserId || message.recipient_id !== peerUserId || message.read_at) {
      return message
    }
    return {
      ...message,
      delivered_at: message.delivered_at ?? readAt,
      read_at: readAt,
    }
  })
}

function connectSocket(): void {
  if (socket || !auth.isAuthenticated.value) {
    return
  }

  socket = connectChatEvents(handleSocketEvent)
  if (!socket) {
    return
  }

  socket.addEventListener('close', handleSocketClose)
  socket.addEventListener('error', () => {
    socket?.close()
  })
}

function handleSocketClose(): void {
  socket = null
  if (isManualSocketClose) {
    isManualSocketClose = false
    return
  }

  if (!auth.isAuthenticated.value) {
    return
  }

  clearReconnectTimer()
  reconnectTimer = window.setTimeout(() => {
    connectSocket()
  }, 3000)
}

function clearReconnectTimer(): void {
  if (reconnectTimer !== null) {
    window.clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

function handleSocketEvent(event: ChatEventPayload): void {
  if (event.event === 'connected') {
    return
  }

  if (event.event === 'presence' && event.user_id) {
    updatePeerPresence(event.user_id, Boolean(event.online))
    return
  }

  if (!event.conversation) {
    return
  }

  const peerUserId = event.conversation.peer.id
  const currentUserId = auth.state.currentUser?.id
  const isIncomingMessage = Boolean(event.event === 'message' && event.message && currentUserId && event.message.recipient_id === currentUserId)
  const nextConversation = isIncomingMessage ? normalizeIncomingConversation(event.conversation, peerUserId) : event.conversation

  upsertConversation(nextConversation)
  syncConversationLastMessage(peerUserId, nextConversation)

  if (event.event === 'cleared') {
    state.messagesByPeer[peerUserId] = []
    return
  }

  if (event.event === 'deleted' && event.deleted_message_id) {
    state.messagesByPeer[peerUserId] = (state.messagesByPeer[peerUserId] ?? []).filter((item) => item.id !== event.deleted_message_id)
    return
  }

  if (event.message) {
    upsertMessage(peerUserId, event.message)
  }

  if (event.event === 'delivered') {
    markPeerMessagesDelivered(peerUserId, nextConversation.last_message?.delivered_at ?? null)
    return
  }

  if (event.event === 'read') {
    markPeerMessagesRead(peerUserId, nextConversation.last_message?.read_at ?? null)
    return
  }

  if (state.open && isIncomingMessage) {
    if (state.selectedPeerId === peerUserId) {
      void markConversationAsReadIfVisible(peerUserId)
    }
    return
  }

  if (isIncomingMessage && event.message && !nextConversation.muted) {
    if (!chatNotificationsMuted) {
      playSmsNotificationSound()
    }
    void chatMessageToast(nextConversation.peer.nome, event.message.content)
  }
}

function resetChat(): void {
  clearReconnectTimer()
  if (socket) {
    isManualSocketClose = true
    socket.close()
  }
  socket = null
  chatNotificationsMuted = false
  state.open = false
  state.initialized = false
  state.loadingConversations = false
  state.loadingContacts = false
  state.loadingMessages = false
  state.sending = false
  state.error = ''
  state.conversations = []
  state.contacts = []
  state.selectedPeerId = null
  state.messagesByPeer = {}
  state.draftMessage = ''
}

function setDraftMessage(value: string): void {
  state.draftMessage = value
}

export function useChatController() {
  const selectedConversation = computed(() => state.conversations.find((item) => item.peer.id === state.selectedPeerId) ?? null)
  const selectedContact = computed(() => state.contacts.find((item) => item.id === state.selectedPeerId) ?? null)
  const selectedMessages = computed(() => (state.selectedPeerId ? state.messagesByPeer[state.selectedPeerId] ?? [] : []))
  const unreadCount = computed(() => state.conversations.reduce((total, conversation) => total + conversation.unread_count, 0))

  return {
    state: readonly(state),
    selectedConversation,
    selectedContact,
    selectedMessages,
    unreadCount,
    initialize,
    fetchContacts,
    fetchConversations,
    openDrawer,
    closeDrawer,
    toggleDrawer,
    selectPeer,
    sendDraftMessage,
    removeMessage,
    clearConversation,
    toggleMute,
    markSelectedConversationRead,
    setDraftMessage,
    resetChat,
  }
}