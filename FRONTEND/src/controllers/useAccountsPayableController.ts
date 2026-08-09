import { reactive, readonly } from 'vue'

import type {
  AccountsPayable,
  AccountsPayableBaseUpdateInput,
  AccountsPayableInstallment,
  AccountsPayableInstallmentInput,
  AccountsPayableListFilters,
  AccountsPayableListResponse,
  AccountsPayablePaymentInput,
  AccountsPayablePersonOption,
  AccountsPayableInput,
} from '@/models/accountsPayable'
import {
  addAccountsPayableInstallments,
  createAccountsPayable,
  deleteAccountsPayable,
  deleteAccountsPayableInstallment,
  getAccountsPayableById,
  listAccountsPayable,
  registerAccountsPayablePayment,
  removeAccountsPayableInstallmentPayments,
  searchAccountsPayablePeople,
  updateAccountsPayable,
} from '@/services/accountsPayableService'

function formatDateInput(value: Date) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function createDefaultFilters(): AccountsPayableListFilters {
  const endDate = new Date()
  const startDate = new Date(endDate)
  startDate.setMonth(startDate.getMonth() - 2)

  return {
    page: 1,
    page_size: 8,
    quitado: false,
    data_vencimento_inicial: formatDateInput(startDate),
    data_vencimento_final: formatDateInput(endDate),
  }
}

export function useAccountsPayableController() {
  const defaultFilters = createDefaultFilters()
  const state = reactive({
    filters: { ...defaultFilters } as AccountsPayableListFilters,
    result: {
      items: [],
      total: 0,
      page: 1,
      page_size: 8,
    } as AccountsPayableListResponse,
    currentAccount: null as AccountsPayable | null,
    peopleOptions: [] as AccountsPayablePersonOption[],
    loading: false,
    saving: false,
    peopleLoading: false,
    error: '',
    success: '',
  })

  async function fetchAccountsPayable(): Promise<void> {
    state.loading = true
    state.error = ''
    try {
      state.result = await listAccountsPayable(state.filters)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar contas a pagar'
    } finally {
      state.loading = false
    }
  }

  async function loadAccount(accountId: number): Promise<void> {
    state.loading = true
    state.error = ''
    try {
      state.currentAccount = await getAccountsPayableById(accountId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar conta a pagar'
      throw error
    } finally {
      state.loading = false
    }
  }

  async function submitAccount(payload: AccountsPayableInput): Promise<AccountsPayable> {
    state.saving = true
    state.error = ''
    state.success = ''
    try {
      state.currentAccount = await createAccountsPayable(payload)
      state.success = 'Conta a pagar cadastrada com sucesso.'
      return state.currentAccount
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao cadastrar conta a pagar'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function submitAccountUpdate(accountId: number, payload: AccountsPayableBaseUpdateInput): Promise<AccountsPayable> {
    state.saving = true
    state.error = ''
    state.success = ''
    try {
      state.currentAccount = await updateAccountsPayable(accountId, payload)
      state.success = 'Conta a pagar atualizada com sucesso.'
      return state.currentAccount
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao atualizar conta a pagar'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function appendInstallments(accountId: number, parcelas: AccountsPayableInstallmentInput[]): Promise<AccountsPayable> {
    state.saving = true
    state.error = ''
    try {
      state.currentAccount = await addAccountsPayableInstallments(accountId, parcelas)
      return state.currentAccount
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao adicionar parcelas'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function settleInstallment(parcelaId: number, payload: AccountsPayablePaymentInput): Promise<AccountsPayableInstallment> {
    state.saving = true
    state.error = ''
    try {
      return await registerAccountsPayablePayment(parcelaId, payload)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao registrar pagamento'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function removeAccount(accountId: number): Promise<void> {
    state.loading = true
    state.error = ''
    try {
      await deleteAccountsPayable(accountId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao excluir conta a pagar'
      throw error
    } finally {
      state.loading = false
    }
  }

  async function removeInstallmentPayments(parcelaId: number): Promise<void> {
    state.saving = true
    state.error = ''
    try {
      await removeAccountsPayableInstallmentPayments(parcelaId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao remover pagamentos'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function removeInstallment(parcelaId: number): Promise<void> {
    state.saving = true
    state.error = ''
    try {
      await deleteAccountsPayableInstallment(parcelaId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao excluir parcela'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function fetchPeopleOptions(query: string): Promise<void> {
    state.peopleLoading = true
    state.error = ''
    try {
      state.peopleOptions = await searchAccountsPayablePeople(query)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao pesquisar pessoas'
      throw error
    } finally {
      state.peopleLoading = false
    }
  }

  function clearPeopleOptions(): void {
    state.peopleOptions = []
  }

  function patchFilters(partial: Partial<AccountsPayableListFilters>): void {
    state.filters = { ...state.filters, ...partial }
  }

  return {
    state: readonly(state),
    fetchAccountsPayable,
    loadAccount,
    submitAccount,
    submitAccountUpdate,
    appendInstallments,
    settleInstallment,
    removeAccount,
    removeInstallmentPayments,
    removeInstallment,
    fetchPeopleOptions,
    clearPeopleOptions,
    patchFilters,
  }
}
