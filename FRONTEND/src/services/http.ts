import type { RefreshTokenRequest, TokenPair } from '@/models/auth'

const API_URL = import.meta.env.VITE_API_URL
const ACCESS_TOKEN_KEY = 'contratos.accessToken'
const REFRESH_TOKEN_KEY = 'contratos.refreshToken'

let refreshPromise: Promise<string | null> | null = null

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function saveTokens(tokens: TokenPair): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function buildWebSocketUrl(path: string, params: Record<string, string> = {}): string {
  const baseUrl = new URL(API_URL.endsWith('/') ? API_URL : `${API_URL}/`)
  baseUrl.protocol = baseUrl.protocol === 'https:' ? 'wss:' : 'ws:'

  const url = new URL(path.replace(/^\//, ''), baseUrl)
  Object.entries(params).forEach(([key, value]) => {
    url.searchParams.set(key, value)
  })

  return url.toString()
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    clearTokens()
    return null
  }

  if (!refreshPromise) {
    refreshPromise = fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken } satisfies RefreshTokenRequest),
    })
      .then(async (response) => {
        if (!response.ok) {
          clearTokens()
          return null
        }

        const tokens = (await response.json()) as TokenPair
        saveTokens(tokens)
        return tokens.access_token
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

export async function apiFetch<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers)
  const accessToken = getAccessToken()

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
  })

  if (response.status === 401 && retry && getRefreshToken()) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      return apiFetch<T>(path, init, false)
    }
  }

  if (!response.ok) {
    const message = await extractErrorMessage(response)
    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string }
    return data.detail ?? `Erro ${response.status}`
  } catch {
    return `Erro ${response.status}`
  }
}
