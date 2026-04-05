import { reactive, readonly } from 'vue'

import type { User, UserCreateInput, UserListFilters, UserListResponse, UserUpdateInput } from '@/models/user'
import { createUser, deleteUser, getUserById, listUsers, updateUser } from '@/services/userService'

const defaultFilters: UserListFilters = {
  page: 1,
  page_size: 8,
}

export function useUsersController() {
  const state = reactive({
    filters: { ...defaultFilters } as UserListFilters,
    result: {
      items: [],
      total: 0,
      page: 1,
      page_size: 8,
    } as UserListResponse,
    loading: false,
    saving: false,
    error: '',
    success: '',
    currentUser: null as User | null,
  })

  async function fetchUsers(): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      state.result = await listUsers(state.filters)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar usuarios'
    } finally {
      state.loading = false
    }
  }

  async function submitUser(payload: UserCreateInput): Promise<void> {
    state.saving = true
    state.error = ''
    state.success = ''

    try {
      await createUser(payload)
      state.success = 'Usuario cadastrado com sucesso.'
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao cadastrar usuario'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function loadUser(userId: number): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      state.currentUser = await getUserById(userId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar usuario'
      throw error
    } finally {
      state.loading = false
    }
  }

  async function submitUserUpdate(userId: number, payload: UserUpdateInput): Promise<void> {
    state.saving = true
    state.error = ''
    state.success = ''

    try {
      state.currentUser = await updateUser(userId, payload)
      state.success = 'Usuario atualizado com sucesso.'
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao atualizar usuario'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function removeUser(userId: number): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      await deleteUser(userId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao excluir usuario'
      throw error
    } finally {
      state.loading = false
    }
  }

  function patchFilters(partial: Partial<UserListFilters>): void {
    state.filters = { ...state.filters, ...partial }
  }

  return {
    state: readonly(state),
    fetchUsers,
    loadUser,
    removeUser,
    submitUser,
    submitUserUpdate,
    patchFilters,
  }
}
