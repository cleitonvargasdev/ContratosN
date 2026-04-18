import { reactive, readonly } from 'vue'

import type { SolicitationDetail, SolicitationListFilters, SolicitationListResponse } from '@/models/solicitation'
import { getSolicitationById, getSolicitationPendingCount, listSolicitations } from '@/services/solicitationService'

const defaultFilters: SolicitationListFilters = {
  page: 1,
  page_size: 10,
  status: 'PENDENTE',
}

export function useSolicitationsController() {
  const state = reactive({
    filters: { ...defaultFilters } as SolicitationListFilters,
    result: {
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    } as SolicitationListResponse,
    loading: false,
    detailLoading: false,
    error: '',
    detail: null as SolicitationDetail | null,
    pendingCount: 0,
  })

  async function fetchSolicitations(): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      state.result = await listSolicitations(state.filters)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar solicitacoes'
      throw error
    } finally {
      state.loading = false
    }
  }

  async function loadSolicitationDetail(solicitationId: number): Promise<void> {
    state.detailLoading = true
    state.error = ''

    try {
      state.detail = await getSolicitationById(solicitationId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar solicitacao'
      throw error
    } finally {
      state.detailLoading = false
    }
  }

  async function fetchPendingCount(): Promise<void> {
    try {
      const response = await getSolicitationPendingCount()
      state.pendingCount = response.pendentes
    } catch {
      state.pendingCount = 0
    }
  }

  function patchFilters(partial: Partial<SolicitationListFilters>): void {
    state.filters = { ...state.filters, ...partial }
  }

  function clearDetail(): void {
    state.detail = null
  }

  return {
    state: readonly(state),
    fetchSolicitations,
    loadSolicitationDetail,
    fetchPendingCount,
    patchFilters,
    clearDetail,
  }
}
