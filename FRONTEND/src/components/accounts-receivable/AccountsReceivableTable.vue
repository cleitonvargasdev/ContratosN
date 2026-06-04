<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Movimentações</p>
        <h2 class="panel__title">Contas à Receber</h2>
      </div>
    </header>

    <div class="filters-grid filters-grid--accounts-receivable">
      <div class="accounts-receivable-status-toggle" role="group" aria-label="Filtro de status">
        <button
          class="accounts-receivable-status-toggle__option"
          :class="!recebidaFilter ? 'accounts-receivable-status-toggle__option--active' : ''"
          type="button"
          @click="selectRecebida(false)"
        >
          Aberto
        </button>
        <button
          class="accounts-receivable-status-toggle__option accounts-receivable-status-toggle__option--quitado"
          :class="recebidaFilter ? 'accounts-receivable-status-toggle__option--active' : ''"
          type="button"
          @click="selectRecebida(true)"
        >
          Quitado
        </button>
      </div>
      <input
        v-model="draft.cliente_query"
        class="field"
        placeholder="Cliente nome ou CPF/CNPJ"
        type="text"
        @keydown.enter.prevent="applyFilters"
      />
      <select v-model="clienteAtivoValue" class="field" @change="applyFilters">
        <option value="">Cliente: todos</option>
        <option value="true">Cliente ativo</option>
        <option value="false">Cliente inativo</option>
      </select>
      <label class="accounts-receivable-date-field">
        <span>Data venc. inicial</span>
        <input
          v-model="draft.data_vencimento_inicial"
          class="field"
          title="Data inicial do vencimento"
          type="date"
          @keydown.enter.prevent="applyFilters"
        />
      </label>
      <label class="accounts-receivable-date-field">
        <span>Data venc. final</span>
        <input
          v-model="draft.data_vencimento_final"
          class="field"
          title="Data final do vencimento"
          type="date"
          @keydown.enter.prevent="applyFilters"
        />
      </label>
      <button class="secondary-button accounts-receivable-filter-button" type="button" @click="applyFilters">Filtrar</button>
    </div>

    <p v-if="props.error" class="feedback feedback--error">{{ props.error }}</p>

    <div class="summary-row">
      <article class="summary-chip">
        <strong>{{ props.result.total }}</strong>
        <span>Clientes</span>
      </article>
    </div>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>Parc.</th>
            <th>Venc.</th>
            <th>Juros</th>
            <th>Vlr Total</th>
            <th>Dias</th>
            <th>Status</th>
            <th class="actions-column accounts-receivable-actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="props.loading">
            <td colspan="7">Carregando contas a receber...</td>
          </tr>
          <tr v-else-if="props.result.items.length === 0">
            <td colspan="7">Nenhuma parcela encontrada.</td>
          </tr>
          <template v-for="clientGroup in props.result.items" :key="clientGroup.client_key">
            <tr class="payment-plan-group-row accounts-receivable-group-row accounts-receivable-group-row--client">
              <td colspan="7">
                <button
                  class="payment-plan-group-button accounts-receivable-group-button accounts-receivable-group-button--client"
                  type="button"
                  @click="toggleClientGroup(clientGroup.client_key)"
                >
                  <span class="payment-plan-group-button__icon">{{ isClientGroupOpen(clientGroup.client_key) ? '-' : '+' }}</span>
                  <strong>{{ clientGroup.cliente_nome || 'Cliente não informado' }}</strong>
                  <span class="accounts-receivable-group-button__field"><b>CPF:</b> {{ clientGroup.cliente_cpf_cnpj || '-' }}</span>
                  <span class="accounts-receivable-group-button__field"><b>Saldo Devedor:</b> {{ formatCurrency(clientGroup.cliente_valor_em_aberto) }}</span>
                  <span class="payment-plan-group-button__meta">{{ clientGroup.installment_count }} {{ clientGroup.installment_count === 1 ? 'parcela' : 'parcelas' }}</span>
                </button>
              </td>
            </tr>

            <template v-if="isClientGroupOpen(clientGroup.client_key)">
              <template v-for="contractGroup in clientGroup.contracts" :key="contractGroup.contract_key">
                <tr class="payment-plan-group-row accounts-receivable-group-row accounts-receivable-group-row--contract">
                  <td colspan="7">
                    <button
                      class="payment-plan-group-button accounts-receivable-group-button accounts-receivable-group-button--contract"
                      type="button"
                      @click="toggleContractGroup(contractGroup.contract_key)"
                    >
                      <span class="payment-plan-group-button__icon">{{ isContractGroupOpen(contractGroup.contract_key) ? '-' : '+' }}</span>
                      <span class="accounts-receivable-group-button__field"><b>Nº Contrato:</b> {{ contractGroup.contratos_id ?? '-' }}</span>
                      <span class="accounts-receivable-group-button__field"><b>Vlr Parc.:</b> {{ formatCurrency(contractGroup.valor_parcela) }}</span>
                      <span class="accounts-receivable-group-button__field"><b>Vlr Contrato:</b> {{ formatCurrency(contractGroup.valor_total) }}</span>
                      <span class="accounts-receivable-group-button__field"><b>Recebido:</b> {{ formatCurrency(contractGroup.valor_recebido) }}</span>
                      <span class="accounts-receivable-group-button__field"><b>Aberto:</b> {{ formatCurrency(contractGroup.valor_em_aberto) }}</span>
                      <span class="accounts-receivable-group-button__field"><b>Últ. Rec.:</b> {{ formatDate(contractGroup.ultimo_recebimento) }}</span>
                      <span class="accounts-receivable-group-button__field"><b>Em atraso:</b> {{ formatCurrency(contractGroup.valor_em_atraso) }}</span>
                      <span :class="['pill', resolveContractStatus(contractGroup).className]">{{ resolveContractStatus(contractGroup).label }}</span>
                    </button>
                  </td>
                </tr>

                <tr
                  v-for="item in visibleContractItems(contractGroup)"
                  :key="item.id"
                  class="data-table__row"
                  @dblclick="handleRowDoubleClick(item.contratos_id)"
                >
                  <td class="payment-plan-grouped-cell accounts-receivable-installment-cell">{{ formatInstallment(item.parcela_nro) }}</td>
                  <td>{{ formatDate(item.vencimento) }}</td>
                  <td>{{ formatCurrency(item.valor_juros) }}</td>
                  <td>{{ formatCurrency(item.valor_total) }}</td>
                  <td>{{ formatOverdueDays(item) }}</td>
                  <td>
                    <span :class="['pill', resolveInstallmentStatus(item).className]">
                      {{ resolveInstallmentStatus(item).label }}
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
                          <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm0 2c-4.42 0-8 2.24-8 5v1h16v-1c0-2.76-3.58-5-8-5Zm0-12a10 10 0 1 1-10 10A10 10 0 0 1 12 2Zm0 18a8 8 0 1 0-8-8 8 8 0 0 0 8 8Z" fill="currentColor"/>
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </template>
            </template>
          </template>
        </tbody>
      </table>
    </div>

    <footer class="pagination-compact">
      <div class="pagination-compact__meta">
        <label class="pagination-compact__label" for="accounts-receivable-page-size">Clientes por pagina:</label>
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

import type {
  AccountsReceivableContractGroup,
  AccountsReceivableListItem,
  AccountsReceivableListResponse,
} from '@/models/contract'

type InstallmentRow = AccountsReceivableListItem
type ContractGroup = AccountsReceivableContractGroup

const props = defineProps<{
  result: AccountsReceivableListResponse
  loading: boolean
  error: string
  canViewContract: boolean
  canViewClient: boolean
  filters: {
    recebida: boolean
    cliente_ativo?: boolean
    cliente_query?: string
    data_vencimento_inicial?: string
    data_vencimento_final?: string
  }
}>()

const emit = defineEmits<{
  apply: [payload: { recebida: boolean; cliente_ativo?: boolean; cliente_query?: string; data_vencimento_inicial?: string; data_vencimento_final?: string }]
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

const recebidaFilter = ref(Boolean(props.filters.recebida))
const clienteAtivoValue = ref(booleanFilterToString(props.filters.cliente_ativo))
const pageSizeValue = ref(String(props.result.page_size))
const openedClientGroups = reactive<Record<string, boolean>>({})
const openedContractGroups = reactive<Record<string, boolean>>({})

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
    recebidaFilter.value = Boolean(filters.recebida)
    clienteAtivoValue.value = booleanFilterToString(filters.cliente_ativo)
  },
  { deep: true, immediate: true },
)

watch(
  () => props.result.items,
  (groups) => {
    const validClientKeys = new Set(groups.map((group) => group.client_key))
    const validContractKeys = new Set(groups.flatMap((group) => group.contracts.map((contract) => contract.contract_key)))

    for (const group of groups) {
      if (!(group.client_key in openedClientGroups)) {
        openedClientGroups[group.client_key] = false
      }

      for (const contract of group.contracts) {
        if (!(contract.contract_key in openedContractGroups)) {
          openedContractGroups[contract.contract_key] = false
        }
      }
    }

    for (const key of Object.keys(openedClientGroups)) {
      if (!validClientKeys.has(key)) {
        delete openedClientGroups[key]
      }
    }

    for (const key of Object.keys(openedContractGroups)) {
      if (!validContractKeys.has(key)) {
        delete openedContractGroups[key]
      }
    }
  },
  { immediate: true },
)

function applyFilters() {
  emit('apply', {
    recebida: recebidaFilter.value,
    cliente_ativo: parseBooleanFilter(clienteAtivoValue.value),
    cliente_query: toStringOrUndefined(draft.cliente_query),
    data_vencimento_inicial: toStringOrUndefined(draft.data_vencimento_inicial),
    data_vencimento_final: toStringOrUndefined(draft.data_vencimento_final),
  })
}

function selectRecebida(value: boolean) {
  if (recebidaFilter.value === value) {
    return
  }

  recebidaFilter.value = value
  applyFilters()
}

function changePageSize() {
  emit('change-page-size', Number(pageSizeValue.value))
}

function toStringOrUndefined(value: string) {
  const trimmed = value.trim()
  return trimmed || undefined
}

function parseBooleanFilter(value: string) {
  if (value === 'true') {
    return true
  }

  if (value === 'false') {
    return false
  }

  return undefined
}

function booleanFilterToString(value: boolean | undefined) {
  if (typeof value !== 'boolean') {
    return ''
  }

  return String(value)
}

function formatInstallment(value: number | null) {
  if (typeof value !== 'number') {
    return '-'
  }

  return String(value).padStart(2, '0')
}

function formatOverdueDays(item: InstallmentRow) {
  const overdueDays = getOverdueDays(item)
  return overdueDays > 0 ? String(overdueDays) : '-'
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

function toggleClientGroup(key: string) {
  openedClientGroups[key] = !(openedClientGroups[key] ?? false)
}

function toggleContractGroup(key: string) {
  openedContractGroups[key] = !(openedContractGroups[key] ?? false)
}

function isClientGroupOpen(key: string) {
  return openedClientGroups[key] ?? false
}

function isContractGroupOpen(key: string) {
  return openedContractGroups[key] ?? false
}

function visibleContractItems(group: ContractGroup) {
  return isContractGroupOpen(group.contract_key) ? group.items : []
}

function getOverdueDays(item: InstallmentRow) {
  if (item.quitado || !item.vencimento) {
    return 0
  }

  const dueDate = new Date(item.vencimento)
  if (Number.isNaN(dueDate.getTime())) {
    return 0
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  dueDate.setHours(0, 0, 0, 0)

  const diffMs = today.getTime() - dueDate.getTime()
  return diffMs > 0 ? Math.floor(diffMs / 86400000) : 0
}

function resolveInstallmentStatus(item: InstallmentRow) {
  if (item.quitado) {
    return { label: 'RECEBIDA', className: 'pill--success' }
  }

  if (getOverdueDays(item) > 0) {
    return { label: 'ATRASADA', className: 'pill--danger' }
  }

  return { label: 'ABERTA', className: 'pill--warning' }
}

function resolveContractStatus(group: ContractGroup) {
  const valorEmAberto = Number(group.valor_em_aberto ?? 0)
  const valorEmAtraso = Number(group.valor_em_atraso ?? 0)
  if (group.quitado || valorEmAberto <= 0) {
    return { label: 'QUITADO', className: 'pill--success' }
  }

  if (valorEmAtraso > 0) {
    return { label: 'ATRASADO', className: 'pill--danger' }
  }

  return { label: 'EM ABERTO', className: 'pill--warning' }
}
</script>

<style scoped>
.filters-grid--accounts-receivable {
  grid-template-columns: minmax(12rem, 1fr) minmax(14rem, 1.35fr) minmax(10rem, 0.9fr) minmax(10rem, 0.9fr) minmax(10rem, 0.9fr) minmax(6.25rem, 0.6fr);
  align-items: end;
}

.accounts-receivable-date-field {
  display: grid;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #5f6d78;
  align-self: end;
}

.accounts-receivable-status-toggle {
  display: inline-grid;
  grid-template-columns: 1fr 1fr;
  min-height: 34px;
  border: 1px solid rgba(249, 115, 22, 0.22);
  border-radius: 3px;
  overflow: hidden;
  background: rgba(249, 115, 22, 0.09);
  align-self: end;
}

.accounts-receivable-status-toggle__option {
  border: 0;
  padding: 0 14px;
  background: transparent;
  color: #1b2730;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  cursor: pointer;
  transition: background-color 140ms ease, color 140ms ease;
}

.accounts-receivable-status-toggle__option + .accounts-receivable-status-toggle__option {
  border-left: 1px solid rgba(249, 115, 22, 0.18);
}

.accounts-receivable-status-toggle__option--active {
  background: rgba(31, 157, 104, 0.14);
  color: #1b7f56;
}

.accounts-receivable-status-toggle__option--quitado {
  font-size: 11px;
}

.accounts-receivable-status-toggle__option {
  font-size: 11px;
}

.accounts-receivable-filter-button {
  width: 100%;
  min-width: 0;
  padding-inline: 10px;
  justify-self: stretch;
}

.accounts-receivable-actions-column {
  width: 8rem;
}

.accounts-receivable-actions-cell {
  min-width: 7.5rem;
}

.accounts-receivable-group-button {
  flex-wrap: wrap;
  row-gap: 8px;
}

.accounts-receivable-group-button--client {
  font-size: 12px;
}

.accounts-receivable-group-button--contract {
  padding-left: 28px;
  background: rgba(31, 157, 104, 0.14);
}

.accounts-receivable-group-button__field {
  font-size: 11px;
  font-weight: 600;
  color: #24303b;
}

.accounts-receivable-group-row--contract :deep(.payment-plan-group-button__icon) {
  color: #c25f12;
}

.accounts-receivable-group-row--contract .accounts-receivable-group-button__field,
.accounts-receivable-group-row--contract .accounts-receivable-group-button__field b {
  color: #c25f12;
  font-weight: 700;
}

.accounts-receivable-installment-cell {
  min-width: 4.5rem;
}

.pill--danger {
  background: rgba(216, 75, 98, 0.14);
  color: #b13951;
}

@media (max-width: 1180px) {
  .filters-grid--accounts-receivable {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .accounts-receivable-group-button--contract {
    padding-left: 12px;
  }
}

@media (max-width: 720px) {
  .filters-grid--accounts-receivable {
    grid-template-columns: 1fr;
  }

  .accounts-receivable-status-toggle {
    width: 100%;
  }

  .accounts-receivable-actions-column {
    width: 6.5rem;
  }
}
</style>