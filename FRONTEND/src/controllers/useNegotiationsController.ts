import { reactive, readonly } from 'vue'

import type { Negotiation, NegotiationCreatePayload, NegotiationListFilters, NegotiationListResponse } from '@/models/negotiation'
import { createNegotiation, listNegotiations } from '@/services/negotiationService'

const defaultFilters: NegotiationListFilters = {
  page: 1,
  page_size: 8,
}

export function useNegotiationsController() {
  const state = reactive({
    filters: { ...defaultFilters } as NegotiationListFilters,
    result: {
      items: [],
      total: 0,
      page: 1,
      page_size: 8,
    } as NegotiationListResponse,
    loading: false,
    saving: false,
    error: '',
    success: '',
  })

  async function fetchNegotiations(): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      state.result = await listNegotiations(state.filters)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar negociacoes'
    } finally {
      state.loading = false
    }
  }

  async function submitNegotiation(payload: NegotiationCreatePayload): Promise<Negotiation> {
    state.saving = true
    state.error = ''
    state.success = ''

    try {
      const created = await createNegotiation(payload)
      state.success = 'Negociacao criada com sucesso.'
      return created
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao criar negociacao'
      throw error
    } finally {
      state.saving = false
    }
  }

  function patchFilters(partial: Partial<NegotiationListFilters>): void {
    state.filters = { ...state.filters, ...partial }
  }

  return {
    state: readonly(state),
    fetchNegotiations,
    submitNegotiation,
    patchFilters,
  }
}
