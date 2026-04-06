export interface ChatUserSummary {
  id: number
  nome: string
  login: string
  online: boolean
}

export interface ChatMessage {
  id: number
  thread_id: number
  sender_id: number
  recipient_id: number
  content: string
  created_at: string
  delivered_at: string | null
  read_at: string | null
}

export interface ChatConversation {
  peer: ChatUserSummary
  last_message: ChatMessage | null
  unread_count: number
  muted: boolean
}

export interface ChatSendMessageInput {
  content: string
}

export interface ChatSendMessageResponse {
  conversation: ChatConversation
  message: ChatMessage
}

export interface ChatMessageDeleteResponse {
  conversation: ChatConversation
  deleted_message_id: number
}

export interface ChatMuteUpdate {
  muted: boolean
}

export interface ChatEventPayload {
  resource: 'chat'
  event: 'connected' | 'presence' | 'message' | 'delivered' | 'read' | 'deleted' | 'cleared'
  conversation?: ChatConversation
  message?: ChatMessage | null
  deleted_message_id?: number
  user_id?: number
  online?: boolean
}