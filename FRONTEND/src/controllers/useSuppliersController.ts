import { reactive, readonly } from 'vue'

import type { Supplier, SupplierInput, SupplierListFilters, SupplierListResponse } from '@/models/supplier'
import { createSupplier, deleteSupplier, getSupplierById, listSuppliers, updateSupplier } from '@/services/supplierService'

const defaultFilters: SupplierListFilters = {
  page: 1,
  page_size: 8,
}

export function useSuppliersController() {
  const state = reactive({
    filters: { ...defaultFilters } as SupplierListFilters,
    result: {
      items: [],
      total: 0,
      page: 1,
      page_size: 8,
    } as SupplierListResponse,
    loading: false,
    saving: false,
    error: '',
    success: '',
    currentSupplier: null as Supplier | null,
  })

  async function fetchSuppliers(): Promise<void> {
    state.loading = true
    state.error = ''
    try {
      state.result = await listSuppliers(state.filters)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar fornecedores'
    } finally {
      state.loading = false
    }
  }

  async function loadSupplier(supplierId: number): Promise<void> {
    state.loading = true
    state.error = ''
    try {
      state.currentSupplier = await getSupplierById(supplierId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao carregar fornecedor'
      throw error
    } finally {
      state.loading = false
    }
  }

  async function submitSupplier(payload: SupplierInput): Promise<Supplier> {
    state.saving = true
    state.error = ''
    state.success = ''
    try {
      state.currentSupplier = await createSupplier(payload)
      state.success = 'Fornecedor cadastrado com sucesso.'
      return state.currentSupplier
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao cadastrar fornecedor'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function submitSupplierUpdate(supplierId: number, payload: SupplierInput): Promise<void> {
    state.saving = true
    state.error = ''
    state.success = ''
    try {
      state.currentSupplier = await updateSupplier(supplierId, payload)
      state.success = 'Fornecedor atualizado com sucesso.'
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao atualizar fornecedor'
      throw error
    } finally {
      state.saving = false
    }
  }

  async function removeSupplier(supplierId: number): Promise<void> {
    state.loading = true
    state.error = ''
    try {
      await deleteSupplier(supplierId)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao excluir fornecedor'
      throw error
    } finally {
      state.loading = false
    }
  }

  function patchFilters(partial: Partial<SupplierListFilters>): void {
    state.filters = { ...state.filters, ...partial }
  }

  return {
    state: readonly(state),
    fetchSuppliers,
    loadSupplier,
    submitSupplier,
    submitSupplierUpdate,
    removeSupplier,
    patchFilters,
  }
}