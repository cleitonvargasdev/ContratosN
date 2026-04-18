<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Movimentações</p>
        <h2 class="panel__title">Negociações</h2>
      </div>
      <RouterLink v-if="props.canCreate" class="primary-button primary-button--compact primary-button--accent-soft" to="/negociacoes/novo">+ Negociação</RouterLink>
    </header>

    <div class="filters-grid filters-grid--contracts">
      <input v-model="draft.contrato_gerado_id" class="field" placeholder="ID contrato gerado" type="number" @keydown.enter.prevent="applyFilters" />
      <input v-model="draft.cliente_nome" class="field" placeholder="Cliente / empresa" type="text" @keydown.enter.prevent="applyFilters" />
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
            <th>Cliente</th>
            <th>Data</th>
            <th>Valor em Aberto</th>
            <th>Contrato Gerado</th>
            <th>Situação</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="props.loading">
            <td colspan="7">Carregando negociações...</td>
          </tr>
          <tr v-else-if="props.result.items.length === 0">
            <td colspan="7">Nenhuma negociação encontrada.</td>
          </tr>
          <tr v-for="neg in props.result.items" :key="neg.negociacao_id" class="data-table__row">
            <td>{{ neg.negociacao_id }}</td>
            <td>{{ neg.cliente_nome || '-' }}</td>
            <td>{{ formatDate(neg.data_negociacao) }}</td>
            <td>{{ formatCurrency(neg.valor_total_aberto) }}</td>
            <td>{{ neg.contrato_gerado_id || '-' }}</td>
            <td>
              <span :class="['pill', neg.contrato_quitado ? 'pill--success' : 'pill--warning']">
                {{ neg.contrato_quitado ? 'QUITADO' : 'PENDENTE' }}
              </span>
            </td>
            <td class="actions-cell actions-cell--compact">
              <div class="actions-cell__content">
                <button class="icon-action" type="button" title="Ver negociação" aria-label="Ver negociação" @click="$emit('view', neg.negociacao_id)">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5ZM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5Zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3Z" fill="currentColor"/>
                  </svg>
                </button>
                <button class="icon-action" type="button" title="Imprimir negociação" aria-label="Imprimir negociação" @click="$emit('print', neg.negociacao_id)">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3Zm-3 11H8v-5h8v5Zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1Zm-1-9H6v4h12V3Z" fill="currentColor"/>
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
        <label class="pagination-compact__label" for="negotiations-page-size">Itens por pagina:</label>
        <select id="negotiations-page-size" v-model="pageSizeValue" class="pagination-compact__select" @change="changePageSize">
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

import type { NegotiationListResponse } from '@/models/negotiation'

const props = defineProps<{
  result: NegotiationListResponse
  loading: boolean
  error: string
  canCreate: boolean
  filters: {
    cliente_nome?: string
    contrato_gerado_id?: number
  }
}>()

const emit = defineEmits<{
  apply: [payload: { cliente_nome?: string; contrato_gerado_id?: number }]
  'change-page': [page: number]
  'change-page-size': [pageSize: number]
  view: [negotiationId: number]
  print: [negotiationId: number]
}>()

const draft = reactive({
  contrato_gerado_id: '',
  cliente_nome: props.filters.cliente_nome ?? '',
})

const pageSizeValue = ref(String(props.result.page_size))

const totalPages = computed(() => Math.max(1, Math.ceil(props.result.total / props.result.page_size)))

const rangeLabel = computed(() => {
  if (props.result.total === 0) return '0-0 de 0'
  const start = (props.result.page - 1) * props.result.page_size + 1
  const end = Math.min(props.result.page * props.result.page_size, props.result.total)
  return `${start}-${end} de ${props.result.total}`
})

watch(() => props.result.page_size, (ps) => { pageSizeValue.value = String(ps) }, { immediate: true })
watch(() => props.filters, (f) => {
  draft.contrato_gerado_id = typeof f.contrato_gerado_id === 'number' ? String(f.contrato_gerado_id) : ''
  draft.cliente_nome = f.cliente_nome ?? ''
}, { deep: true, immediate: true })

function applyFilters() {
  const contratoId = draft.contrato_gerado_id.trim() ? Number(draft.contrato_gerado_id) : undefined
  emit('apply', {
    contrato_gerado_id: Number.isFinite(contratoId) ? contratoId : undefined,
    cliente_nome: draft.cliente_nome.trim() || undefined,
  })
}

function changePageSize() {
  emit('change-page-size', Number(pageSizeValue.value))
}

function formatDate(value: string | null) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('pt-BR').format(new Date(value))
}

function formatCurrency(value: number | null | undefined) {
  if (typeof value !== 'number') return '-'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}
</script>
