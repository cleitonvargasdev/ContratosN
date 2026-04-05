import type { UserApiKeyInfo, UserApiKeySecret } from '@/models/accessControl'
import type { User, UserCreateInput, UserListFilters, UserListResponse, UserUpdateInput } from '@/models/user'
import { apiFetch, buildWebSocketUrl, getAccessToken } from '@/services/http'

export interface UserRealtimeEvent {
  resource: 'usuarios'
  event: 'connected' | 'created' | 'updated' | 'deleted'
  user_id?: number
  changed_fields?: string[]
}

export async function listUsers(filters: UserListFilters): Promise<UserListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))

  if (filters.nome) params.set('nome', filters.nome)
  if (filters.email) params.set('email', filters.email)
  if (typeof filters.ativo === 'boolean') params.set('ativo', String(filters.ativo))

  return apiFetch<UserListResponse>(`/usuarios/?${params.toString()}`)
}

export async function createUser(payload: UserCreateInput): Promise<User> {
  return apiFetch<User>('/usuarios/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function getUserById(userId: number): Promise<User> {
  return apiFetch<User>(`/usuarios/${userId}`)
}

export async function updateUser(userId: number, payload: UserUpdateInput): Promise<User> {
  return apiFetch<User>(`/usuarios/${userId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteUser(userId: number): Promise<void> {
  return apiFetch<void>(`/usuarios/${userId}`, {
    method: 'DELETE',
  })
}

export async function getUserApiKeyInfo(userId: number): Promise<UserApiKeyInfo> {
  return apiFetch<UserApiKeyInfo>(`/usuarios/${userId}/api-key`)
}

export async function rotateUserApiKey(userId: number): Promise<UserApiKeySecret> {
  return apiFetch<UserApiKeySecret>(`/usuarios/${userId}/api-key`, {
    method: 'POST',
  })
}

export function connectUsersUpdates(onEvent: (event: UserRealtimeEvent) => void): WebSocket | null {
  const accessToken = getAccessToken()
  if (!accessToken) {
    return null
  }

  const websocket = new WebSocket(buildWebSocketUrl('/usuarios/ws', { token: accessToken }))
  websocket.addEventListener('message', (message) => {
    const event = JSON.parse(message.data) as UserRealtimeEvent
    onEvent(event)
  })

  return websocket
}
