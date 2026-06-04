import { reactive, readonly } from 'vue'

import type { AccountsReceivableClientGroup, AccountsReceivableListFilters, AccountsReceivableListResponse } from '@/models/contract'
import { listAccountsReceivable } from '@/services/contractService'

function formatDateInput(value: Date) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function createDefaultFilters(): AccountsReceivableListFilters {
  const endDate = new Date()
  const startDate = new Date(endDate)
  startDate.setDate(startDate.getDate() - 30)

  return {
    page: 1,
    page_size: 8,
    recebida: false,
    cliente_ativo: undefined,
    data_vencimento_inicial: formatDateInput(startDate),
    data_vencimento_final: formatDateInput(endDate),
  }
}

export function useAccountsReceivableController() {
  const defaultFilters = createDefaultFilters()
  const state = reactive({
    filters: { ...defaultFilters } as AccountsReceivableListFilters,
    result: {
      items: [],
      total: 0,
      page: 1,
      page_size: 8,
    } as AccountsReceivableListResponse,
    loading: false,
    error: '',
    currentItem: null as AccountsReceivableClientGroup | null,
  })

  async function fetchAccountsReceivable(): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      state.result = await listAccountsReceivable(state.filters)
      state.currentItem = state.result.items[0] ?? null
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar contas a receber'
    } finally {
      state.loading = false
    }
  }

  function patchFilters(partial: Partial<AccountsReceivableListFilters>): void {
    state.filters = { ...state.filters, ...partial }
  }

  return {
    state: readonly(state),
    fetchAccountsReceivable,
    patchFilters,
  }
}