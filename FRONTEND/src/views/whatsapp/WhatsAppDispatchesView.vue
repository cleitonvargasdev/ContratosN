<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <h2 class="panel__title">Envios Agendados</h2>
      </div>
      <button class="secondary-button" :disabled="controller.state.loadingBatches || controller.state.loadingItems" type="button" @click="handleRefresh">
        Atualizar
      </button>
    </header>

    <div class="filters-grid">
      <input v-model="draft.data_inicial" class="field" type="date" />
      <input v-model="draft.data_final" class="field" type="date" />
      <button class="secondary-button" type="button" @click="applyFilters">Aplicar filtros</button>
    </div>

    <div class="summary-row">
      <article class="summary-chip">
        <strong>{{ controller.state.batchResult.total }}</strong>
        <span>Lotes</span>
      </article>
    </div>

    <p v-if="controller.state.error" class="feedback feedback--error">{{ controller.state.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>Status</th>
            <th>Envios</th>
            <th>Erros</th>
            <th>Agendado</th>
            <th>Executado</th>
            <th>Telefone</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="controller.state.loadingBatches">
            <td colspan="7">Carregando lotes...</td>
          </tr>
          <tr v-else-if="controller.state.batchResult.items.length === 0">
            <td colspan="7">Nenhum lote encontrado.</td>
          </tr>
          <tr
            v-for="batch in controller.state.batchResult.items"
            :key="batch.id"
            :class="['data-table__row', 'dispatch-row', { 'dispatch-row--selected': batch.id === controller.state.selectedBatchId }]"
            @click="handleSelectBatch(batch.id)"
          >
            <td><span :class="['pill', batchStatusClass(batch.status)]">{{ formatBatchStatus(batch.status) }}</span></td>
            <td>{{ batch.total_sent }}/{{ batch.total_items }}</td>
            <td>{{ batch.total_errors }}</td>
            <td>{{ formatDateTime(batch.scheduled_for) }}</td>
            <td>{{ formatDateTime(batch.executed_at) }}</td>
            <td>{{ formatPhone(batch.source_phone) }}</td>
            <td class="actions-cell" @click.stop>
              <button class="icon-action icon-action--danger" type="button" title="Excluir lote" aria-label="Excluir lote" @click="handleDeleteBatch(batch.id)">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer class="pagination-compact">
      <div class="pagination-compact__meta">
        <label class="pagination-compact__label" for="batch-page-size">Itens por pagina:</label>
        <select id="batch-page-size" v-model="batchPageSizeValue" class="pagination-compact__select" @change="changeBatchPageSize">
          <option value="8">8</option>
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="50">50</option>
        </select>
      </div>
      <div class="pagination-compact__status">{{ batchRangeLabel }}</div>
      <div class="pagination-compact__actions">
        <button class="pagination-compact__button" type="button" :disabled="controller.state.batchResult.page <= 1" @click="changeBatchPage(1)">&#171;</button>
        <button class="pagination-compact__button" type="button" :disabled="controller.state.batchResult.page <= 1" @click="changeBatchPage(controller.state.batchResult.page - 1)">&#8249;</button>
        <button class="pagination-compact__button" type="button" :disabled="controller.state.batchResult.page >= batchTotalPages" @click="changeBatchPage(controller.state.batchResult.page + 1)">&#8250;</button>
        <button class="pagination-compact__button" type="button" :disabled="controller.state.batchResult.page >= batchTotalPages" @click="changeBatchPage(batchTotalPages)">&#187;</button>
      </div>
    </footer>

    <section class="dispatch-detail-card">
      <header class="panel__header panel__header--stacked">
        <div>
          <p class="eyebrow">Detalhamento do lote</p>
          <h3 class="panel__title panel__title--small">Itens do lote</h3>
        </div>
      </header>

      <div class="table-wrap">
        <table class="data-table data-table--cadastro">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Contrato</th>
              <th>Parcela</th>
              <th>Valor</th>
              <th>Mensagem</th>
              <th>Horário</th>
              <th>Sit.</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!controller.state.selectedBatchId">
              <td colspan="7">Selecione um lote para carregar os envios.</td>
            </tr>
            <tr v-else-if="controller.state.loadingItems">
              <td colspan="7">Carregando itens do lote...</td>
            </tr>
            <tr v-else-if="controller.state.itemResult.items.length === 0">
              <td colspan="7">Nenhum envio encontrado para o lote selecionado.</td>
            </tr>
            <tr v-for="item in controller.state.itemResult.items" :key="item.id" class="data-table__row dispatch-item-row">
              <td>{{ item.client_name || '-' }}</td>
              <td>{{ item.contratos_id ?? '-' }}</td>
              <td>{{ item.parcela_nro ?? '-' }}</td>
              <td>{{ formatCurrency(item.amount) }}</td>
              <td>
                <button class="message-preview-button" type="button" @click="openMessage(item)">
                  {{ messagePreview(item.message_payload.text) }}
                </button>
              </td>
              <td>{{ formatDateTime(item.sent_at ?? item.due_at) }}</td>
              <td>
                <span class="dispatch-status-whatsapp" :class="item.status === 'sent' ? 'dispatch-status-whatsapp--success' : 'dispatch-status-whatsapp--error'">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12.04 2C6.52 2 2.04 6.47 2.04 12c0 1.95.56 3.77 1.53 5.31L2 22l4.84-1.51A9.94 9.94 0 0 0 12.04 22C17.56 22 22.04 17.53 22.04 12S17.56 2 12.04 2Zm0 18a8.07 8.07 0 0 1-4.12-1.13l-.29-.18-2.87.89.92-2.79-.19-.3A8.03 8.03 0 1 1 12.04 20Zm4.71-5.85c-.25-.13-1.47-.72-1.69-.8-.23-.08-.39-.12-.56.12-.16.25-.64.8-.78.96-.14.17-.29.19-.54.07-.25-.13-1.05-.39-2-1.23-.74-.66-1.24-1.47-1.38-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.29.37-.43.12-.15.16-.25.25-.42.08-.17.04-.31-.02-.43-.06-.13-.56-1.35-.77-1.85-.2-.48-.4-.41-.56-.42h-.47c-.16 0-.42.06-.64.31-.22.25-.84.82-.84 2s.86 2.31.98 2.47c.12.17 1.69 2.58 4.1 3.62.57.25 1.02.4 1.37.51.57.18 1.08.16 1.49.1.45-.07 1.38-.56 1.57-1.11.2-.55.2-1.03.14-1.12-.06-.1-.22-.16-.46-.28Z" fill="currentColor" />
                  </svg>
                </span>
                <p v-if="item.error_message" class="dispatch-status-error">{{ item.error_message }}</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="pagination-compact">
        <div class="pagination-compact__meta">
          <label class="pagination-compact__label" for="item-page-size">Itens por pagina:</label>
          <select id="item-page-size" v-model="itemPageSizeValue" class="pagination-compact__select" :disabled="!controller.state.selectedBatchId" @change="changeItemPageSize">
            <option value="8">8</option>
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
          </select>
        </div>
        <div class="pagination-compact__status">{{ itemRangeLabel }}</div>
        <div class="pagination-compact__actions">
          <button class="pagination-compact__button" type="button" :disabled="!controller.state.selectedBatchId || controller.state.itemResult.page <= 1" @click="changeItemPage(1)">&#171;</button>
          <button class="pagination-compact__button" type="button" :disabled="!controller.state.selectedBatchId || controller.state.itemResult.page <= 1" @click="changeItemPage(controller.state.itemResult.page - 1)">&#8249;</button>
          <button class="pagination-compact__button" type="button" :disabled="!controller.state.selectedBatchId || controller.state.itemResult.page >= itemTotalPages" @click="changeItemPage(controller.state.itemResult.page + 1)">&#8250;</button>
          <button class="pagination-compact__button" type="button" :disabled="!controller.state.selectedBatchId || controller.state.itemResult.page >= itemTotalPages" @click="changeItemPage(itemTotalPages)">&#187;</button>
        </div>
      </footer>
    </section>

    <Teleport to="body">
      <div v-if="controller.state.messageModal.open" class="modal-backdrop" @click.self="controller.closeMessageModal()">
        <section class="modal-card modal-card--compact dispatch-message-modal">
          <header class="panel__header panel__header--stacked">
            <div>
              <p class="eyebrow">Mensagem enviada</p>
              <h3 class="panel__title panel__title--small">{{ controller.state.messageModal.title }}</h3>
            </div>
          </header>
          <div class="dispatch-message-modal__body">
            <p>{{ controller.state.messageModal.text }}</p>
          </div>
          <footer class="form-actions">
            <button class="ghost-button" type="button" @click="controller.closeMessageModal()">Fechar</button>
          </footer>
        </section>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import type { WhatsAppDispatchItem } from '@/models/whatsapp'
import { useWhatsAppDispatchController } from '@/controllers/useWhatsAppDispatchController'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'

const controller = useWhatsAppDispatchController()
const draft = reactive({
  data_inicial: '',
  data_final: '',
})
const batchPageSizeValue = ref(String(controller.state.batchResult.page_size))
const itemPageSizeValue = ref(String(controller.state.itemResult.page_size))

const batchTotalPages = computed(() => Math.max(1, Math.ceil(controller.state.batchResult.total / controller.state.batchResult.page_size)))
const itemTotalPages = computed(() => Math.max(1, Math.ceil(controller.state.itemResult.total / controller.state.itemResult.page_size)))
const batchRangeLabel = computed(() => buildRangeLabel(controller.state.batchResult.total, controller.state.batchResult.page, controller.state.batchResult.page_size))
const itemRangeLabel = computed(() => {
  if (!controller.state.selectedBatchId) {
    return '0-0 de 0'
  }
  return buildRangeLabel(controller.state.itemResult.total, controller.state.itemResult.page, controller.state.itemResult.page_size)
})

watch(
  () => controller.state.batchResult.page_size,
  (pageSize) => {
    batchPageSizeValue.value = String(pageSize)
  },
  { immediate: true },
)

watch(
  () => controller.state.itemResult.page_size,
  (pageSize) => {
    itemPageSizeValue.value = String(pageSize)
  },
  { immediate: true },
)

onMounted(() => {
  controller.clearSelection()
  void controller.loadBatches().catch(async () => {
    if (controller.state.error) {
      await errorAlert(controller.state.error)
    }
  })
})

async function handleRefresh() {
  try {
    await controller.loadBatches()
  } catch {
    if (controller.state.error) {
      await errorAlert(controller.state.error)
    }
  }
}

async function applyFilters() {
  controller.patchFilters({
    page: 1,
    data_inicial: draft.data_inicial || undefined,
    data_final: draft.data_final || undefined,
  })
  controller.clearSelection()
  await handleRefresh()
}

async function handleSelectBatch(batchId: number) {
  try {
    await controller.loadItems(batchId, 1, controller.state.itemResult.page_size)
  } catch {
    if (controller.state.error) {
      await errorAlert(controller.state.error)
    }
  }
}

async function handleDeleteBatch(batchId: number) {
  if (!(await confirmDeleteAlert())) {
    return
  }

  try {
    await controller.removeBatch(batchId)
    await controller.loadBatches()
    await successAlert('Lote excluido com sucesso.', 'delete')
  } catch {
    if (controller.state.error) {
      await errorAlert(controller.state.error)
    }
  }
}

async function changeBatchPage(page: number) {
  controller.patchFilters({ page })
  await handleRefresh()
}

async function changeBatchPageSize() {
  controller.patchFilters({ page: 1, page_size: Number(batchPageSizeValue.value) })
  controller.clearSelection()
  await handleRefresh()
}

async function changeItemPage(page: number) {
  if (!controller.state.selectedBatchId) {
    return
  }
  try {
    await controller.loadItems(controller.state.selectedBatchId, page, controller.state.itemResult.page_size)
  } catch {
    if (controller.state.error) {
      await errorAlert(controller.state.error)
    }
  }
}

async function changeItemPageSize() {
  if (!controller.state.selectedBatchId) {
    return
  }
  try {
    await controller.loadItems(controller.state.selectedBatchId, 1, Number(itemPageSizeValue.value))
  } catch {
    if (controller.state.error) {
      await errorAlert(controller.state.error)
    }
  }
}

function openMessage(item: WhatsAppDispatchItem) {
  controller.openMessageModal(`Contrato ${item.contratos_id ?? '-'} • Parcela ${item.parcela_nro ?? '-'}`, String(item.message_payload.text || '-'))
}

function messagePreview(text: string | undefined): string {
  if (!text?.trim()) {
    return '-'
  }
  return 'Olá!...'
}

function buildRangeLabel(total: number, page: number, pageSize: number): string {
  if (total === 0) {
    return '0-0 de 0'
  }
  const start = (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, total)
  return `${start}-${end} de ${total}`
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('pt-BR')
}

function formatCurrency(value: number | null): string {
  if (typeof value !== 'number') {
    return '-'
  }
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

function formatPhone(value: string | null): string {
  if (!value) {
    return '-'
  }
  const digits = value.replace(/\D/g, '')
  if (digits.length === 11) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
  }
  return value
}

function formatBatchStatus(value: string): string {
  if (value === 'success') return 'Sucesso'
  if (value === 'partial') return 'Parcial'
  if (value === 'error') return 'Erro'
  if (value === 'empty') return 'Sem envios'
  if (value === 'processing') return 'Processando'
  return value
}

function batchStatusClass(value: string): string {
  if (value === 'success') return 'pill--success'
  if (value === 'partial') return 'pill--warning'
  if (value === 'error') return 'pill--danger'
  return 'pill--neutral'
}
</script>

<style scoped>
.dispatch-detail-card {
  display: grid;
  gap: 1rem;
}

.dispatch-row {
  cursor: pointer;
}

.dispatch-row td,
.dispatch-item-row td {
  transition: background-color 0.16s ease, color 0.16s ease;
}

.dispatch-row:hover td,
.dispatch-item-row:hover td {
  background: rgba(15, 118, 110, 0.06);
}

.dispatch-row td:first-child,
.dispatch-item-row td:first-child {
  border-radius: 3px 0 0 3px;
}

.dispatch-row td:last-child,
.dispatch-item-row td:last-child {
  border-radius: 0 3px 3px 0;
}

.dispatch-row--selected td {
  background: rgba(22, 163, 74, 0.12);
}

.dispatch-status-whatsapp {
  align-items: center;
  display: inline-flex;
  font-weight: 700;
  gap: 0.45rem;
}

.dispatch-status-whatsapp svg {
  height: 1rem;
  width: 1rem;
}

.dispatch-status-whatsapp--success {
  color: #15803d;
}

.dispatch-status-whatsapp--error {
  color: #b91c1c;
}

.dispatch-status-error {
  color: #b91c1c;
  margin: 0.35rem 0 0;
}

.message-preview-button {
  background: transparent;
  border: 0;
  color: #0f766e;
  cursor: pointer;
  font: inherit;
  padding: 0;
  text-decoration: underline;
}

.dispatch-message-modal {
  max-width: 680px;
  width: min(680px, calc(100vw - 2rem));
}

.dispatch-message-modal__body {
  color: #10281f;
  line-height: 1.6;
  white-space: pre-wrap;
}

.pill--warning {
  background: rgba(245, 158, 11, 0.16);
  color: #b45309;
}

.pill--neutral {
  background: rgba(100, 116, 139, 0.12);
  color: #475569;
}
</style>