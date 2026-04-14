<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Movimentações</p>
        <h2 class="panel__title">Contratos</h2>
      </div>
      <RouterLink v-if="props.canCreate" class="primary-button primary-button--compact primary-button--accent-soft" to="/contratos/novo">Novo +</RouterLink>
    </header>

    <div class="filters-grid filters-grid--contracts">
      <input v-model="draft.contratos_id" class="field" placeholder="ID contrato" type="number" @input="handleContractIdInput" @keydown.enter.prevent="applyFilters" />
      <input v-model="draft.cliente_nome" class="field" placeholder="Cliente / empresa" type="text" @keydown.enter.prevent="applyFilters" />
      <input v-model="draft.cobrador_nome" class="field" placeholder="Cobrador" type="text" @keydown.enter.prevent="applyFilters" />
      <select v-model="quitadoFilter" class="field" @keydown.enter.prevent="applyFilters">
        <option value="">Todos</option>
        <option value="false">Aberto</option>
        <option value="true">Quitado</option>
      </select>
      <button class="secondary-button" type="button" @click="applyFilters">Aplicar filtros</button>
    </div>

    <div class="summary-row">
      <article class="summary-chip">
        <strong>{{ props.result.total }}</strong>
        <span>Total</span>
      </article>
    </div>

    <p v-if="props.error" class="feedback feedback--error">{{ props.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>Nº</th>
            <th>Data contrato</th>
            <th>Cliente / Empresa</th>
            <th>Valor</th>
            <th>Vl. Parcela</th>
              <th>Aluguel</th>
            <th>Quitado</th>
            <th>Recebido</th>
            <th>Aberto</th>
            <th>Atrasado</th>
            <th class="actions-column contract-actions-column">Ações</th>
            <th class="msg-column contract-msg-column">MSG</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="props.loading">
            <td colspan="12">Carregando contratos...</td>
          </tr>
          <tr v-else-if="props.result.items.length === 0">
            <td colspan="12">Nenhum contrato encontrado.</td>
          </tr>
          <tr v-for="contract in props.result.items" :key="contract.contratos_id" class="data-table__row" @dblclick="handleRowDoubleClick(contract.contratos_id)">
            <td>{{ contract.contratos_id }}</td>
            <td>{{ formatDate(contract.data_contrato) }}</td>
            <td>{{ contract.cliente_nome || '-' }}</td>
            <td>{{ formatCurrency(contract.valor_final) }}</td>
            <td>{{ formatCurrency(contract.valor_parcela) }}</td>
            <td>
              <span :class="['pill', contract.aluguel ? 'pill--warning' : 'pill--default']">
                {{ contract.aluguel ? 'SIM' : 'NAO' }}
              </span>
            </td>
            <td>
              <span :class="['pill', contract.quitado ? 'pill--success' : 'pill--warning']">
                {{ contract.quitado ? 'QUITADO' : 'ABERTO' }}
              </span>
            </td>
            <td>{{ formatCurrency(contract.valor_recebido) }}</td>
            <td>{{ formatCurrency(contract.valor_em_aberto) }}</td>
            <td :class="{ 'contract-table__overdue-value': (contract.valor_em_atraso ?? 0) > 0 }">{{ formatCurrency(contract.valor_em_atraso) }}</td>
            <td class="actions-cell actions-cell--compact contract-actions-cell">
              <div class="actions-cell__content">
                <button v-if="props.canUpdate" class="icon-action" type="button" title="Alterar contrato" aria-label="Alterar contrato" @click="$emit('edit', contract.contratos_id)">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/>
                  </svg>
                </button>
                <button v-if="props.canDelete" class="icon-action icon-action--danger" type="button" title="Excluir contrato" aria-label="Excluir contrato" @click="$emit('delete', contract.contratos_id)">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/>
                  </svg>
                </button>
              </div>
            </td>
            <td class="actions-cell actions-cell--compact contract-actions-cell contract-msg-cell">
              <button
                class="icon-action icon-action--message"
                :disabled="!contract.cliente_telefone || !props.canUpdate"
                type="button"
                title="Enviar contrato PDF no WhatsApp"
                aria-label="Enviar contrato PDF no WhatsApp"
                @click="$emit('sendWhatsappDocument', contract.contratos_id)"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M17.47 14.38c-.27-.13-1.59-.78-1.84-.87-.25-.09-.43-.13-.61.13-.18.27-.7.87-.86 1.05-.16.18-.31.2-.58.07-.27-.13-1.12-.41-2.14-1.3-.79-.7-1.33-1.56-1.48-1.83-.16-.27-.02-.41.11-.54.12-.12.27-.31.4-.47.13-.16.18-.27.27-.45.09-.18.04-.34-.02-.47-.07-.13-.61-1.47-.84-2.02-.22-.53-.44-.46-.61-.47h-.52c-.18 0-.47.07-.72.34-.25.27-.95.93-.95 2.26s.97 2.62 1.11 2.8c.13.18 1.91 2.91 4.62 4.08.65.28 1.15.45 1.54.58.65.2 1.24.17 1.7.1.52-.08 1.59-.65 1.82-1.27.22-.62.22-1.15.16-1.27-.07-.12-.25-.2-.52-.34Z" fill="currentColor"/>
                  <path d="M20.52 3.48A11.8 11.8 0 0 0 12.12 0C5.6 0 .29 5.3.29 11.82c0 2.08.54 4.1 1.57 5.88L0 24l6.48-1.7a11.8 11.8 0 0 0 5.64 1.44h.01c6.52 0 11.82-5.3 11.82-11.82 0-3.16-1.23-6.13-3.43-8.44Zm-8.4 18.26h-.01a9.84 9.84 0 0 1-5.01-1.37l-.36-.21-3.85 1.01 1.03-3.75-.23-.38a9.8 9.8 0 0 1-1.5-5.22c0-5.41 4.4-9.82 9.82-9.82 2.62 0 5.08 1.02 6.93 2.88a9.74 9.74 0 0 1 2.87 6.94c0 5.41-4.41 9.82-9.82 9.82Z" fill="currentColor"/>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer class="pagination-compact">
      <div class="pagination-compact__meta">
        <label class="pagination-compact__label" for="contracts-page-size">Itens por pagina:</label>
        <select id="contracts-page-size" v-model="pageSizeValue" class="pagination-compact__select" @change="changePageSize">
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
import { RouterLink } from 'vue-router'

import type { ContractListResponse } from '@/models/contract'

const props = defineProps<{
  result: ContractListResponse
  loading: boolean
  error: string
  canCreate: boolean
  canUpdate: boolean
  canDelete: boolean
  filters: {
    contratos_id?: number
    cliente_nome?: string
    cobrador_nome?: string
    quitado?: boolean
  }
}>()

const emit = defineEmits<{
  apply: [payload: { contratos_id?: number; cliente_nome?: string; cobrador_nome?: string; quitado?: boolean }]
  'change-page': [page: number]
  'change-page-size': [pageSize: number]
  edit: [contractId: number]
  delete: [contractId: number]
  sendWhatsappDocument: [contractId: number]
}>()

const draft = reactive({
  contratos_id: props.filters.contratos_id ? String(props.filters.contratos_id) : '',
  cliente_nome: props.filters.cliente_nome ?? '',
  cobrador_nome: props.filters.cobrador_nome ?? '',
})

const quitadoFilter = ref('')
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
    draft.contratos_id = typeof filters.contratos_id === 'number' ? String(filters.contratos_id) : ''
    draft.cliente_nome = filters.cliente_nome ?? ''
    draft.cobrador_nome = filters.cobrador_nome ?? ''
    quitadoFilter.value = typeof filters.quitado === 'boolean' ? String(filters.quitado) : ''
  },
  { deep: true, immediate: true },
)

function applyFilters() {
  const contratosId = toNumberOrUndefined(draft.contratos_id)

  if (typeof contratosId === 'number') {
    emit('apply', {
      contratos_id: contratosId,
      cliente_nome: undefined,
      cobrador_nome: undefined,
      quitado: undefined,
    })
    return
  }

  const quitado = quitadoFilter.value === '' ? undefined : quitadoFilter.value === 'true'
  emit('apply', {
    contratos_id: contratosId,
    cliente_nome: toStringOrUndefined(draft.cliente_nome),
    cobrador_nome: toStringOrUndefined(draft.cobrador_nome),
    quitado,
  })
}

function handleContractIdInput() {
  const contratosId = toNumberOrUndefined(draft.contratos_id)

  if (typeof contratosId === 'number') {
    emit('apply', {
      contratos_id: contratosId,
      cliente_nome: undefined,
      cobrador_nome: undefined,
      quitado: undefined,
    })
    return
  }

  if (!draft.contratos_id.trim()) {
    applyFilters()
  }
}

function changePageSize() {
  emit('change-page-size', Number(pageSizeValue.value))
}

function toNumberOrUndefined(value: string | number | null | undefined) {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : undefined
  }

  const trimmed = String(value ?? '').trim()
  return trimmed ? Number(trimmed) : undefined
}

function toStringOrUndefined(value: string) {
  const trimmed = value.trim()
  return trimmed || undefined
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

function handleRowDoubleClick(contractId: number) {
  if (!props.canUpdate) {
    return
  }

  emit('edit', contractId)
}
</script>