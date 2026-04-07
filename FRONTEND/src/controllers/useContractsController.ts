import { reactive, readonly } from 'vue'

import type { Contract, ContractCreateInput, ContractListFilters, ContractListResponse, ContractUpdateInput } from '@/models/contract'
import { createContract, deleteContract, getContractById, listContracts, updateContract } from '@/services/contractService'

const defaultFilters: ContractListFilters = {
  page: 1,
  page_size: 8,
}

export function useContractsController() {
  const state = reactive({
    filters: { ...defaultFilters } as ContractListFilters,
    result: {
      items: [],
      total: 0,
      page: 1,
      page_size: 8,
    } as ContractListResponse,
    loading: false,
    saving: false,
    error: '',
    success: '',
    currentContract: null as Contract | null,
  })

  async function fetchContracts(): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      state.result = await listContracts(state.filters)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar contratos'
    } finally {
      state.loading = false
    }
  }

  async function loadContract(contractId: number): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      state.currentContract = await getContractById(contractId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar contrato'
      throw error
    } finally {
      state.loading = false
    }
  }

  async function submitContract(payload: ContractCreateInput): Promise<Contract> {
    state.saving = true
    state.error = ''
    state.success = ''

    try {
      const created = await createContract(payload)
      state.currentContract = created
      state.success = 'Contrato cadastrado com sucesso.'
      return created
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao cadastrar contrato'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function submitContractUpdate(contractId: number, payload: ContractUpdateInput): Promise<Contract> {
    state.saving = true
    state.error = ''
    state.success = ''

    try {
      const updated = await updateContract(contractId, payload)
      state.currentContract = updated
      state.success = 'Contrato atualizado com sucesso.'
      return updated
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao atualizar contrato'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function removeContract(contractId: number): Promise<void> {
    state.loading = true
    state.error = ''

    try {
      await deleteContract(contractId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao excluir contrato'
      throw error
    } finally {
      state.loading = false
    }
  }

  function patchFilters(partial: Partial<ContractListFilters>): void {
    state.filters = { ...state.filters, ...partial }
  }

  return {
    state: readonly(state),
    fetchContracts,
    loadContract,
    submitContract,
    submitContractUpdate,
    removeContract,
    patchFilters,
  }
}