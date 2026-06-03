import { reactive, readonly } from 'vue'

import type { AccountsReceivableListFilters, AccountsReceivableListItem, AccountsReceivableListResponse } from '@/models/contract'
import { listAccountsReceivable } from '@/services/contractService'

const defaultFilters: AccountsReceivableListFilters = {
  page: 1,
  page_size: 8,
}

export function useAccountsReceivableController() {
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
    currentItem: null as AccountsReceivableListItem | null,
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