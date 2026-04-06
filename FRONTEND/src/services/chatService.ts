import type {
  ChatConversation,
  ChatEventPayload,
  ChatMessage,
  ChatMessageDeleteResponse,
  ChatMuteUpdate,
  ChatSendMessageInput,
  ChatSendMessageResponse,
  ChatUserSummary,
} from '@/models/chat'
import { apiFetch, buildWebSocketUrl, getAccessToken } from '@/services/http'

export async function listChatContacts(term?: string): Promise<ChatUserSummary[]> {
  const params = new URLSearchParams()
  if (term) {
    params.set('term', term)
  }
  return apiFetch<ChatUserSummary[]>(`/chat/contatos${params.size ? `?${params.toString()}` : ''}`)
}

export async function listChatConversations(): Promise<ChatConversation[]> {
  return apiFetch<ChatConversation[]>('/chat/conversas')
}

export async function listChatMessages(peerUserId: number): Promise<ChatMessage[]> {
  return apiFetch<ChatMessage[]>(`/chat/conversas/${peerUserId}/mensagens`)
}

export async function sendChatMessage(peerUserId: number, payload: ChatSendMessageInput): Promise<ChatSendMessageResponse> {
  return apiFetch<ChatSendMessageResponse>(`/chat/conversas/${peerUserId}/mensagens`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function setChatMuted(peerUserId: number, payload: ChatMuteUpdate): Promise<ChatConversation> {
  return apiFetch<ChatConversation>(`/chat/conversas/${peerUserId}/silenciar`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function markChatConversationRead(peerUserId: number): Promise<ChatConversation> {
  return apiFetch<ChatConversation>(`/chat/conversas/${peerUserId}/lidas`, {
    method: 'POST',
  })
}

export async function deleteChatMessage(peerUserId: number, messageId: number): Promise<ChatMessageDeleteResponse> {
  return apiFetch<ChatMessageDeleteResponse>(`/chat/conversas/${peerUserId}/mensagens/${messageId}`, {
    method: 'DELETE',
  })
}

export async function clearChatConversation(peerUserId: number): Promise<ChatConversation> {
  return apiFetch<ChatConversation>(`/chat/conversas/${peerUserId}`, {
    method: 'DELETE',
  })
}

export function connectChatEvents(onEvent: (event: ChatEventPayload) => void): WebSocket | null {
  const accessToken = getAccessToken()
  if (!accessToken) {
    return null
  }

  const websocket = new WebSocket(buildWebSocketUrl('/chat/ws', { token: accessToken }))
  websocket.addEventListener('message', (message) => {
    onEvent(JSON.parse(message.data) as ChatEventPayload)
  })
  return websocket
}