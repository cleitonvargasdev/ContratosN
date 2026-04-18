import type { LoginForm, TokenPair } from '@/models/auth'
import type { AuthenticatedUser } from '@/models/user'
import { apiFetch, clearTokens, saveTokens } from '@/services/http'

const API_URL = (import.meta.env.VITE_API_URL?.trim() || 'http://127.0.0.1:8007/api/v1').replace(/\/$/, '')

export async function loginRequest(credentials: LoginForm): Promise<TokenPair> {
  const body = new URLSearchParams({
    username: credentials.username,
    password: credentials.password,
  })

  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })

  if (!response.ok) {
    clearTokens()
    const data = (await response.json()) as { detail?: string }
    throw new Error(data.detail ?? 'Falha ao autenticar')
  }

  const tokens = (await response.json()) as TokenPair
  saveTokens(tokens)
  return tokens
}

export async function loadCurrentUser(): Promise<AuthenticatedUser> {
  return apiFetch<AuthenticatedUser>('/auth/me')
}

export function logoutRequest(): void {
  clearTokens()
}
