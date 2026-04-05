import { computed, reactive, readonly } from 'vue'

import type { PermissionAction } from '@/models/accessControl'
import type { LoginForm } from '@/models/auth'
import type { AuthenticatedUser } from '@/models/user'
import { loadCurrentUser, loginRequest, logoutRequest } from '@/services/authService'
import { getAccessToken } from '@/services/http'

const state = reactive({
  currentUser: null as AuthenticatedUser | null,
  loading: false,
  initialized: false,
  error: '',
})

async function initializeAuth(): Promise<void> {
  if (state.initialized) return

  if (!getAccessToken()) {
    state.initialized = true
    return
  }

  try {
    state.loading = true
    state.currentUser = await loadCurrentUser()
  } catch {
    logout()
  } finally {
    state.loading = false
    state.initialized = true
  }
}

async function login(credentials: LoginForm): Promise<void> {
  state.error = ''
  state.loading = true

  try {
    await loginRequest(credentials)
    state.currentUser = await loadCurrentUser()
    state.initialized = true
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao realizar login'
    throw error
  } finally {
    state.loading = false
  }
}

function logout(): void {
  logoutRequest()
  state.currentUser = null
  state.error = ''
  state.initialized = true
}

async function reloadUser(): Promise<void> {
  state.currentUser = await loadCurrentUser()
}

function hasPermission(resourceKey: string, action: PermissionAction = 'read'): boolean {
  if (!state.currentUser) {
    return false
  }

  const permission = state.currentUser.permissions.find((item) => item.resource_key === resourceKey)
  if (!permission) {
    return false
  }

  if (action === 'create') return permission.can_create
  if (action === 'update') return permission.can_update
  if (action === 'delete') return permission.can_delete
  return permission.can_read
}

export function useAuthController() {
  return {
    state: readonly(state),
    isAuthenticated: computed(() => Boolean(state.currentUser && getAccessToken())),
    isAdmin: computed(() => state.currentUser?.perfil_nome === 'Administrador'),
    initializeAuth,
    login,
    logout,
    hasPermission,
    reloadUser,
  }
}
