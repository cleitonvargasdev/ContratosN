<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Movimentações</p>
        <h2 class="panel__title">Contas à Receber</h2>
      </div>
    </header>

    <div class="filters-grid filters-grid--accounts-receivable">
      <select v-model="recebidaFilter" class="field" @keydown.enter.prevent="applyFilters">
        <option value="">Todos</option>
        <option value="false">Aberto</option>
        <option value="true">Recebidas</option>
      </select>
      <input
        v-model="draft.cliente_query"
        class="field"
        placeholder="Cliente nome ou CPF/CNPJ"
        type="text"
        @keydown.enter.prevent="applyFilters"
      />
      <input
        v-model="draft.data_vencimento_inicial"
        class="field"
        title="Data inicial do vencimento"
        type="date"
        @keydown.enter.prevent="applyFilters"
      />
      <input
        v-model="draft.data_vencimento_final"
        class="field"
        title="Data final do vencimento"
        type="date"
        @keydown.enter.prevent="applyFilters"
      />
      <button class="secondary-button" type="button" @click="applyFilters">Aplicar filtros</button>
    </div>

    <p v-if="props.error" class="feedback feedback--error">{{ props.error }}</p>

    <div class="summary-row">
      <article class="summary-chip">
        <strong>{{ props.result.total }}</strong>
        <span>Total</span>
      </article>
    </div>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>Contrato</th>
            <th>Parc.</th>
            <th>Cliente</th>
            <th>CPF/CNPJ</th>
            <th>Vencimento</th>
            <th>Valor</th>
            <th>Recebido</th>
            <th>Aberto</th>
            <th>Status</th>
            <th class="actions-column accounts-receivable-actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="props.loading">
            <td colspan="10">Carregando contas a receber...</td>
          </tr>
          <tr v-else-if="props.result.items.length === 0">
            <td colspan="10">Nenhuma parcela encontrada.</td>
          </tr>
          <tr
            v-for="item in props.result.items"
            :key="item.id"
            class="data-table__row"
            @dblclick="handleRowDoubleClick(item.contratos_id)"
          >
            <td>{{ item.contratos_id ?? '-' }}</td>
            <td>{{ formatInstallment(item.parcela_nro) }}</td>
            <td>{{ item.cliente_nome || '-' }}</td>
            <td>{{ item.cliente_cpf_cnpj || '-' }}</td>
            <td>{{ formatDate(item.vencimento) }}</td>
            <td>{{ formatCurrency(item.valor_total) }}</td>
            <td>{{ formatCurrency(item.valor_recebido) }}</td>
            <td>{{ formatCurrency(item.valor_em_aberto) }}</td>
            <td>
              <span :class="['pill', item.quitado ? 'pill--success' : 'pill--warning']">
                {{ item.quitado ? 'RECEBIDA' : 'ABERTO' }}
              </span>
            </td>
            <td class="actions-cell actions-cell--compact accounts-receivable-actions-cell">
              <div class="actions-cell__content">
                <button
                  class="icon-action"
                  :disabled="!item.contratos_id || !props.canViewContract"
                  type="button"
                  title="Ver contrato"
                  aria-label="Ver contrato"
                  @click="emitViewContract(item.contratos_id)"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M6 2h9l5 5v15a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm8 1.5V8h4.5L14 3.5ZM8 12h8v-2H8v2Zm0 4h8v-2H8v2Z" fill="currentColor"/>
                  </svg>
                </button>
                <button
                  class="icon-action"
                  :disabled="!item.cliente_id || !props.canViewClient"
                  type="button"
                  title="Ver cliente"
                  aria-label="Ver cliente"
                  @click="emitViewClient(item.cliente_id)"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M7 4h10a2 2 0 0 1 2 2v12l-4-2-4 2-4-2-4 2V6a2 2 0 0 1 2-2Zm1 3a2 2 0 1 0 4 0 2 2 0 0 0-4 0Zm7 1h2V6h-2v2Zm-7 6h8v-1c0-1.66-3.58-2.5-5-2.5S8 11.34 8 13v1Zm7-2h2v-2h-2v2Z" fill="currentColor"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer class="pagination-compact">
      <div class="pagination-compact__meta">
        <label class="pagination-compact__label" for="accounts-receivable-page-size">Itens por pagina:</label>
        <select id="accounts-receivable-page-size" v-model="pageSizeValue" class="pagination-compact__select" @change="changePageSize">
          <option value="8">8</option>
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="50">50</option>
        </select>
      </div>

      <div class="pagination-compact__status">{{ rangeLabel }}</div>

      <div class="pagination-compact__actions">
        <button class="pagination-compact__button" type="button" :disabled="props.result.page <= 1" @click="$emit('change-page', 1)">&#171;</button>
        <button class="pagination-compact__button" type="button" :disabled="props.result.page <= 1" @click="$emit('change-page', props.result.page - 1)">&#8249;</button>
        <button class="pagination-compact__button" type="button" :disabled="props.result.page >= totalPages" @click="$emit('change-page', props.result.page + 1)">&#8250;</button>
        <button class="pagination-compact__button" type="button" :disabled="props.result.page >= totalPages" @click="$emit('change-page', totalPages)">&#187;</button>
      </div>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

import type { AccountsReceivableListResponse } from '@/models/contract'

const props = defineProps<{
  result: AccountsReceivableListResponse
  loading: boolean
  error: string
  canViewContract: boolean
  canViewClient: boolean
  filters: {
    recebida?: boolean
    cliente_query?: string
    data_vencimento_inicial?: string
    data_vencimento_final?: string
  }
}>()

const emit = defineEmits<{
  apply: [payload: { recebida?: boolean; cliente_query?: string; data_vencimento_inicial?: string; data_vencimento_final?: string }]
  'change-page': [page: number]
  'change-page-size': [pageSize: number]
  'view-contract': [contractId: number]
  'view-client': [clientId: number]
}>()

const draft = reactive({
  cliente_query: props.filters.cliente_query ?? '',
  data_vencimento_inicial: props.filters.data_vencimento_inicial ?? '',
  data_vencimento_final: props.filters.data_vencimento_final ?? '',
})

const recebidaFilter = ref('')
const pageSizeValue = ref(String(props.result.page_size))

const totalPages = computed(() => Math.max(1, Math.ceil(props.result.total / props.result.page_size)))

const rangeLabel = computed(() => {
  if (props.result.total === 0) {
    return '0-0 de 0'
  }

  const start = (props.result.page - 1) * props.result.page_size + 1
  const end = Math.min(props.result.page * props.result.page_size, props.result.total)
  return `${start}-${end} de ${props.result.total}`
})

watch(
  () => props.result.page_size,
  (pageSize) => {
    pageSizeValue.value = String(pageSize)
  },
  { immediate: true },
)

watch(
  () => props.filters,
  (filters) => {
    draft.cliente_query = filters.cliente_query ?? ''
    draft.data_vencimento_inicial = filters.data_vencimento_inicial ?? ''
    draft.data_vencimento_final = filters.data_vencimento_final ?? ''
    recebidaFilter.value = typeof filters.recebida === 'boolean' ? String(filters.recebida) : ''
  },
  { deep: true, immediate: true },
)

function applyFilters() {
  const recebida = recebidaFilter.value === '' ? undefined : recebidaFilter.value === 'true'
  emit('apply', {
    recebida,
    cliente_query: toStringOrUndefined(draft.cliente_query),
    data_vencimento_inicial: toStringOrUndefined(draft.data_vencimento_inicial),
    data_vencimento_final: toStringOrUndefined(draft.data_vencimento_final),
  })
}

function changePageSize() {
  emit('change-page-size', Number(pageSizeValue.value))
}

function toStringOrUndefined(value: string) {
  const trimmed = value.trim()
  return trimmed || undefined
}

function formatInstallment(value: number | null) {
  if (typeof value !== 'number') {
    return '-'
  }

  return String(value).padStart(2, '0')
}

function formatDate(value: string | null) {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('pt-BR').format(new Date(value))
}

function formatCurrency(value: number | null | undefined) {
  if (typeof value !== 'number') {
    return '-'
  }

  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

function handleRowDoubleClick(contractId: number | null) {
  if (!props.canViewContract || !contractId) {
    return
  }

  emit('view-contract', contractId)
}

function emitViewContract(contractId: number | null) {
  if (!contractId) {
    return
  }

  emit('view-contract', contractId)
}

function emitViewClient(clientId: number | null) {
  if (!clientId) {
    return
  }

  emit('view-client', clientId)
}
</script>

<style scoped>
.filters-grid--accounts-receivable {
  grid-template-columns: minmax(10rem, 0.9fr) minmax(16rem, 1.6fr) minmax(11rem, 1fr) minmax(11rem, 1fr) auto;
  align-items: center;
}

.accounts-receivable-actions-column {
  width: 8rem;
}

.accounts-receivable-actions-cell {
  min-width: 7.5rem;
}

@media (max-width: 1180px) {
  .filters-grid--accounts-receivable {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .filters-grid--accounts-receivable {
    grid-template-columns: 1fr;
  }
}
</style>