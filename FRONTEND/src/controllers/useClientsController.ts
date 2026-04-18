import { reactive, readonly } from 'vue'

import type { Client, ClientInput, ClientListFilters, ClientListResponse } from '@/models/client'
import { createClient, deleteClient, getClientById, listClients, updateClient } from '@/services/clientService'

const defaultFilters: ClientListFilters = {
  page: 1,
  page_size: 8,
}

export function useClientsController() {
  const state = reactive({
    filters: { ...defaultFilters } as ClientListFilters,
    result: {
      items: [],
      total: 0,
      page: 1,
      page_size: 8,
    } as ClientListResponse,
    loading: false,
    saving: false,
    error: '',
    success: '',
    currentClient: null as Client | null,
  })

  async function fetchClients(): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      state.result = await listClients(state.filters)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar clientes'
    } finally {
      state.loading = false
    }
  }

  async function submitClient(payload: ClientInput): Promise<Client> {
    state.saving = true
    state.error = ''
    state.success = ''

    try {
      state.currentClient = await createClient(payload)
      state.success = 'Cliente cadastrado com sucesso.'
      return state.currentClient
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao cadastrar cliente'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function loadClient(clientId: number): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      state.currentClient = await getClientById(clientId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar cliente'
      throw error
    } finally {
      state.loading = false
    }
  }

  async function submitClientUpdate(clientId: number, payload: ClientInput): Promise<void> {
    state.saving = true
    state.error = ''
    state.success = ''

    try {
      state.currentClient = await updateClient(clientId, payload)
      state.success = 'Cliente atualizado com sucesso.'
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao atualizar cliente'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function removeClient(clientId: number): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      await deleteClient(clientId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao excluir cliente'
      throw error
    } finally {
      state.loading = false
    }
  }

  function patchFilters(partial: Partial<ClientListFilters>): void {
    state.filters = { ...state.filters, ...partial }
  }

  return {
    state: readonly(state),
    fetchClients,
    loadClient,
    removeClient,
    submitClient,
    submitClientUpdate,
    patchFilters,
  }
}