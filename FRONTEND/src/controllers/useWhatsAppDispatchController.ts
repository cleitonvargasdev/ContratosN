import { reactive, readonly } from 'vue'

import type { WhatsAppDispatchBatchFilters, WhatsAppDispatchBatchListResponse, WhatsAppDispatchItemListResponse } from '@/models/whatsapp'
import { deleteWhatsAppDispatchBatch, listWhatsAppDispatchBatches, listWhatsAppDispatchItems } from '@/services/whatsappService'

const defaultBatchFilters: WhatsAppDispatchBatchFilters = {
  page: 1,
  page_size: 8,
}

export function useWhatsAppDispatchController() {
  const state = reactive({
    loadingBatches: false,
    loadingItems: false,
    error: '',
    filters: { ...defaultBatchFilters } as WhatsAppDispatchBatchFilters,
    batchResult: {
      items: [],
      total: 0,
      page: 1,
      page_size: 8,
    } as WhatsAppDispatchBatchListResponse,
    itemResult: {
      items: [],
      total: 0,
      page: 1,
      page_size: 8,
    } as WhatsAppDispatchItemListResponse,
    selectedBatchId: null as number | null,
    messageModal: {
      open: false,
      title: '',
      text: '',
    },
  })

  async function loadBatches(): Promise<void> {
    state.loadingBatches = true
    state.error = ''
    try {
      state.batchResult = await listWhatsAppDispatchBatches(state.filters)
      const batchIds = new Set(state.batchResult.items.map((batch) => batch.id))
      if (!state.selectedBatchId || !batchIds.has(state.selectedBatchId)) {
        state.selectedBatchId = null
        state.itemResult = { items: [], total: 0, page: 1, page_size: state.itemResult.page_size }
        return
      }
      await loadItems(state.selectedBatchId, state.itemResult.page, state.itemResult.page_size)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao consultar os envios de WhatsApp'
      throw error
    } finally {
      state.loadingBatches = false
    }
  }

  async function loadItems(batchId: number, page = 1, pageSize = state.itemResult.page_size): Promise<void> {
    state.loadingItems = true
    state.error = ''
    state.selectedBatchId = batchId
    try {
      state.itemResult = await listWhatsAppDispatchItems(batchId, page, pageSize)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao consultar os itens do envio de WhatsApp'
      throw error
    } finally {
      state.loadingItems = false
    }
  }

  async function removeBatch(batchId: number): Promise<void> {
    state.error = ''
    try {
      await deleteWhatsAppDispatchBatch(batchId)
      if (state.selectedBatchId === batchId) {
        clearSelection()
      }
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Falha ao excluir lote de envio de WhatsApp'
      throw error
    }
  }

  function patchFilters(partial: Partial<WhatsAppDispatchBatchFilters>): void {
    state.filters = { ...state.filters, ...partial }
  }

  function clearSelection(): void {
    state.selectedBatchId = null
    state.itemResult = { items: [], total: 0, page: 1, page_size: state.itemResult.page_size }
  }

  function openMessageModal(title: string, text: string): void {
    state.messageModal.open = true
    state.messageModal.title = title
    state.messageModal.text = text
  }

  function closeMessageModal(): void {
    state.messageModal.open = false
    state.messageModal.title = ''
    state.messageModal.text = ''
  }

  return {
    state: readonly(state),
    loadBatches,
    loadItems,
    removeBatch,
    patchFilters,
    clearSelection,
    openMessageModal,
    closeMessageModal,
  }
}