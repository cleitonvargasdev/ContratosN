<template>
  <section class="panel batch-receipt-panel">
    <header class="panel__header batch-receipt-panel__header">
      <div>
        <p class="eyebrow">Movimentações</p>
        <h2 class="panel__title">Recebimento em Lote</h2>
      </div>
    </header>

    <div class="batch-receipt-form">
      <label class="field-group">
        <span>Nº Contrato</span>
        <div class="field-inline batch-receipt-contract-picker">
          <input
            v-model="form.contractId"
            ref="contractIdInput"
            class="field field--no-spin batch-receipt-contract-picker__field"
            inputmode="numeric"
            type="number"
            min="1"
            @keydown.enter.prevent="handlePreview"
          />
          <button
            class="secondary-button batch-receipt-contract-picker__button"
            type="button"
            title="Pesquisar contrato"
            aria-label="Pesquisar contrato"
            @click="openContractSearchModal"
          >
            <svg class="batch-receipt-contract-picker__icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M10.5 4a6.5 6.5 0 1 0 4.03 11.6l4.44 4.44 1.41-1.41-4.44-4.44A6.5 6.5 0 0 0 10.5 4Zm0 2a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Z" fill="currentColor" />
            </svg>
          </button>
        </div>
      </label>

      <label class="field-group">
        <span>Valor</span>
        <input v-model="form.amount" class="field" inputmode="decimal" type="text" placeholder="0,00" @blur="formatAmountField" @keydown.enter.prevent="handlePreview" />
      </label>

      <div class="batch-receipt-form__actions">
        <button class="primary-button primary-button--accent-soft" :disabled="loading.preview || loading.confirm" type="button" @click="handlePreview">
          {{ loading.preview ? 'Calculando...' : 'Calcular' }}
        </button>
        <button class="ghost-button" :disabled="loading.preview || loading.confirm" type="button" @click="resetState">Limpar</button>
      </div>
    </div>

    <div v-if="contract" class="summary-row batch-receipt-summary-row">
      <article class="summary-chip summary-chip--wide">
        <strong>{{ contract.contratos_id }}</strong>
        <span>Contrato</span>
      </article>
      <article class="summary-chip summary-chip--wide">
        <strong>{{ contract.cliente_nome || 'Sem cliente' }}</strong>
        <span>Cliente</span>
      </article>
      <article class="summary-chip">
        <strong>{{ formatCurrency(contract.valor_em_aberto) }}</strong>
        <span>Em aberto</span>
      </article>
      <article class="summary-chip">
        <strong>{{ formatCurrency(preview?.valor_distribuido ?? 0) }}</strong>
        <span>Distribuído</span>
      </article>
    </div>

    <p v-if="message" :class="['feedback', message.kind === 'error' ? 'feedback--error' : 'feedback--info']">{{ message.text }}</p>

    <div class="table-wrap batch-receipt-table-wrap">
      <table class="data-table data-table--cadastro batch-receipt-table">
        <thead>
          <tr>
            <th>Parc.</th>
            <th>Vencimento</th>
            <th>Dia Semana</th>
            <th>Valor Total</th>
            <th>Vl. Recebido</th>
            <th>Saldo</th>
            <th>Baixar</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading.preview">
            <td colspan="7">Calculando parcelas disponíveis...</td>
          </tr>
          <tr v-else-if="previewRows.length === 0">
            <td colspan="7">Nenhuma parcela disponível para baixa com o valor informado.</td>
          </tr>
          <tr v-for="row in previewRows" :key="row.id">
            <td>{{ row.parcela }}</td>
            <td>{{ row.vencimento }}</td>
            <td>{{ row.diaSemana }}</td>
            <td>{{ row.valorTotal }}</td>
            <td>{{ row.valorRecebido }}</td>
            <td>{{ row.saldo }}</td>
            <td>{{ row.valorBaixa }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="form-actions batch-receipt-actions">
      <button
        class="primary-button primary-button--success"
        :disabled="loading.preview || loading.confirm || previewRows.length === 0 || !auth.hasPermission('contratos', 'update')"
        type="button"
        @click="handleConfirm"
      >
        {{ loading.confirm ? 'Confirmando...' : 'Confirmar' }}
      </button>
    </div>

    <Teleport to="body">
      <div v-if="contractSearchModal.open" class="modal-backdrop" @click.self="closeContractSearchModal">
        <section class="modal-card batch-receipt-search-modal">
          <header class="panel__header panel__header--stacked">
            <div>
              <h3 class="panel__title">Pesquisar contratos em aberto</h3>
            </div>
          </header>

          <div class="modal-form batch-receipt-search-modal__content">
            <div class="batch-receipt-search-modal__filters">
              <label class="field-group">
                <span>Busca por nome ou CPF/CNPJ</span>
                <input
                  v-model="contractSearchModal.term"
                  class="field"
                  type="text"
                  placeholder="Digite 3 letras ou numero parte do nome ou documento."
                  @keydown.enter.prevent="runContractSearch()"
                />
              </label>
              <button class="secondary-button batch-receipt-search-modal__search-button" type="button" @click="runContractSearch()">Pesquisar</button>
            </div>

            <p v-if="!canSearchContracts && contractSearchModal.term.trim()" class="feedback feedback--info">Informe ao menos 3 letras ou 3 números para consultar.</p>

            <div class="table-wrap batch-receipt-search-modal__table-wrap">
              <table class="data-table data-table--cadastro batch-receipt-search-modal__table">
                <thead>
                  <tr>
                    <th>Nº Contrato</th>
                    <th>Comodato</th>
                    <th>Valor Parcela</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="contractSearchModal.loading">
                    <td colspan="3">Pesquisando contratos...</td>
                  </tr>
                  <tr v-else-if="contractSearchModal.result.items.length === 0">
                    <td colspan="3">{{ contractSearchEmptyMessage }}</td>
                  </tr>
                  <template v-for="clientGroup in contractSearchModal.result.items" :key="clientGroup.client_key">
                    <tr class="payment-plan-group-row accounts-receivable-group-row accounts-receivable-group-row--client batch-receipt-search-modal__client-row">
                      <td colspan="3">
                        <button
                          class="payment-plan-group-button accounts-receivable-group-button accounts-receivable-group-button--client"
                          type="button"
                          @click="toggleContractSearchClientGroup(clientGroup.client_key)"
                        >
                          <span class="payment-plan-group-button__icon">{{ isContractSearchClientGroupOpen(clientGroup.client_key) ? '-' : '+' }}</span>
                          <strong>{{ clientGroup.cliente_nome || 'Cliente não informado' }}</strong>
                          <span class="accounts-receivable-group-button__field"><b>CPF:</b> {{ formatDocument(clientGroup.cliente_cpf_cnpj) }}</span>
                          <span class="payment-plan-group-button__meta">{{ clientGroup.contract_count }} {{ clientGroup.contract_count === 1 ? 'contrato' : 'contratos' }}</span>
                        </button>
                      </td>
                    </tr>

                    <tr
                      v-for="contractGroup in visibleContractSearchContracts(clientGroup)"
                      :key="contractGroup.contract_key"
                      class="payment-plan-group-row accounts-receivable-group-row accounts-receivable-group-row--contract batch-receipt-search-modal__contract-row"
                      @dblclick="selectBatchReceiptContract(contractGroup)"
                    >
                      <td colspan="3">
                        <button
                          class="payment-plan-group-button accounts-receivable-group-button accounts-receivable-group-button--contract batch-receipt-search-modal__contract-button"
                          type="button"
                          @click="selectBatchReceiptContract(contractGroup)"
                        >
                          <span class="accounts-receivable-group-button__field"><b>Nº Contrato:</b> {{ contractGroup.contratos_id }}</span>
                          <span class="accounts-receivable-group-button__field"><b>Comodato:</b> {{ contractGroup.comodato ? 'Sim' : 'Não' }}</span>
                          <span class="accounts-receivable-group-button__field"><b>Valor Parcela:</b> {{ formatCurrency(contractGroup.valor_parcela) }}</span>
                        </button>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>

            <footer v-if="contractSearchModal.result.total > 0" class="pagination-compact batch-receipt-search-modal__pagination">
              <div class="pagination-compact__status">{{ contractSearchRangeLabel }}</div>

              <div class="pagination-compact__actions">
                <button class="pagination-compact__button" type="button" :disabled="contractSearchModal.result.page <= 1" @click="changeContractSearchPage(1)">&#171;</button>
                <button class="pagination-compact__button" type="button" :disabled="contractSearchModal.result.page <= 1" @click="changeContractSearchPage(contractSearchModal.result.page - 1)">&#8249;</button>
                <button class="pagination-compact__button" type="button" :disabled="contractSearchModal.result.page >= contractSearchTotalPages" @click="changeContractSearchPage(contractSearchModal.result.page + 1)">&#8250;</button>
                <button class="pagination-compact__button" type="button" :disabled="contractSearchModal.result.page >= contractSearchTotalPages" @click="changeContractSearchPage(contractSearchTotalPages)">&#187;</button>
              </div>
            </footer>

            <div class="form-actions">
              <button class="ghost-button" type="button" @click="closeContractSearchModal">Fechar</button>
            </div>
          </div>
        </section>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'

import { useAuthController } from '@/controllers/useAuthController'
import type {
  BatchInstallmentReceivePreview,
  BatchReceiptContractSearchClientGroup,
  BatchReceiptContractSearchContractGroup,
  BatchReceiptContractSearchResponse,
  Contract,
} from '@/models/contract'
import { confirmActionAlert, errorAlert, successAlert } from '@/services/alertService'
import { confirmBatchContractReceive, getContractById, previewBatchContractReceive, searchBatchReceiptContracts } from '@/services/contractService'

const auth = useAuthController()

const form = reactive({
  contractId: '',
  amount: '',
})

const contractIdInput = ref<HTMLInputElement | null>(null)
const contract = ref<Contract | null>(null)
const preview = ref<BatchInstallmentReceivePreview | null>(null)
const loading = reactive({
  preview: false,
  confirm: false,
})
const message = ref<{ kind: 'info' | 'error'; text: string } | null>(null)
const contractSearchModal = reactive({
  open: false,
  term: '',
  loading: false,
  result: {
    items: [],
    total: 0,
    page: 1,
    page_size: 8,
  } as BatchReceiptContractSearchResponse,
})
const openedContractSearchClientGroups = reactive<Record<string, boolean>>({})

const previewRows = computed(() =>
  (preview.value?.parcelas ?? []).map((item) => ({
    id: item.installment.id,
    parcela: String(item.installment.parcela_nro ?? '').padStart(2, '0'),
    vencimento: formatDate(item.installment.vencimentol ?? item.installment.vencimento_original),
    diaSemana: item.installment.dia_semana ?? formatWeekday(item.installment.vencimentol ?? item.installment.vencimento_original),
    valorTotal: formatCurrency(item.installment.valor_total),
    valorRecebido: formatCurrency(item.installment.valor_recebido),
    saldo: formatCurrency(item.saldo_restante),
    valorBaixa: formatCurrency(item.valor_recebimento),
  })),
)

const canSearchContracts = computed(() => hasMinimumSearchTerm(contractSearchModal.term))

const contractSearchTotalPages = computed(() => Math.max(1, Math.ceil(contractSearchModal.result.total / contractSearchModal.result.page_size)))

const contractSearchRangeLabel = computed(() => {
  if (contractSearchModal.result.total === 0) {
    return '0-0 de 0'
  }

  const start = (contractSearchModal.result.page - 1) * contractSearchModal.result.page_size + 1
  const end = Math.min(contractSearchModal.result.page * contractSearchModal.result.page_size, contractSearchModal.result.total)
  return `${start}-${end} de ${contractSearchModal.result.total}`
})

const contractSearchEmptyMessage = computed(() => {
  if (!contractSearchModal.term.trim()) {
    return 'Informe ao menos 3 letras ou 3 números para consultar.'
  }

  if (!canSearchContracts.value) {
    return 'Informe ao menos 3 letras ou 3 números para consultar.'
  }

  return 'Nenhum contrato em aberto encontrado.'
})

function resetState() {
  form.contractId = ''
  form.amount = ''
  contract.value = null
  preview.value = null
  message.value = null
}

async function focusContractField() {
  await nextTick()
  contractIdInput.value?.focus()
  contractIdInput.value?.select()
}

function openContractSearchModal() {
  contractSearchModal.open = true
  contractSearchModal.term = ''
  resetContractSearchResult()
}

function closeContractSearchModal() {
  contractSearchModal.open = false
}

async function runContractSearch(page = 1) {
  const term = contractSearchModal.term.trim()
  if (!hasMinimumSearchTerm(term)) {
    contractSearchModal.result = {
      ...contractSearchModal.result,
      items: [],
      total: 0,
      page: 1,
    }
    return
  }

  contractSearchModal.loading = true
  try {
    contractSearchModal.result = await searchBatchReceiptContracts({
      page,
      page_size: contractSearchModal.result.page_size,
      query: term,
    })
  } catch (error) {
    contractSearchModal.result = {
      ...contractSearchModal.result,
      items: [],
      total: 0,
      page,
    }
    await errorAlert(error instanceof Error ? error.message : 'Falha ao pesquisar contratos.')
  } finally {
    contractSearchModal.loading = false
  }
}

function changeContractSearchPage(page: number) {
  void runContractSearch(page)
}

function selectBatchReceiptContract(item: BatchReceiptContractSearchContractGroup) {
  form.contractId = String(item.contratos_id)
  contract.value = null
  preview.value = null
  message.value = null
  closeContractSearchModal()
}

function toggleContractSearchClientGroup(key: string) {
  openedContractSearchClientGroups[key] = !(openedContractSearchClientGroups[key] ?? false)
}

function isContractSearchClientGroupOpen(key: string) {
  return openedContractSearchClientGroups[key] ?? false
}

function visibleContractSearchContracts(group: BatchReceiptContractSearchClientGroup) {
  return isContractSearchClientGroupOpen(group.client_key) ? group.contracts : []
}

function formatAmountField() {
  const parsed = toLocaleNumberOrNull(form.amount)
  form.amount = parsed === null ? '' : formatDecimal(parsed)
}

async function handlePreview() {
  const contractId = toPositiveInteger(form.contractId)
  const amount = toLocaleNumberOrNull(form.amount)

  if (contractId === null) {
    await errorAlert('Informe um número de contrato válido.')
    return
  }

  if (amount === null || amount <= 0) {
    await errorAlert('Informe um valor maior que zero.')
    return
  }

  loading.preview = true
  message.value = null
  try {
    const loadedContract = await getContractById(contractId)
    const openAmount = Number(loadedContract.valor_em_aberto ?? 0)

    if (amount > openAmount) {
      contract.value = loadedContract
      preview.value = null
      message.value = {
        kind: 'error',
        text: 'O valor a distribuir não pode ser maior que o valor a pagar do contrato.',
      }
      await errorAlert(message.value.text)
      return
    }

    const loadedPreview = await previewBatchContractReceive(contractId, {
      valor_recebido: amount,
      data_recebimento: currentDateTimeLocal(),
    })

    contract.value = loadedContract
    preview.value = loadedPreview
    if (loadedPreview.parcelas.length === 0) {
      message.value = {
        kind: 'info',
        text: 'O valor informado não baixa integralmente a próxima parcela em aberto deste contrato.',
      }
    }
  } catch (error) {
    contract.value = null
    preview.value = null
    message.value = {
      kind: 'error',
      text: error instanceof Error ? error.message : 'Falha ao calcular recebimento em lote.',
    }
    await errorAlert(message.value.text)
  } finally {
    loading.preview = false
  }
}

async function handleConfirm() {
  const contractId = toPositiveInteger(form.contractId)
  const amount = toLocaleNumberOrNull(form.amount)

  if (contractId === null || amount === null || amount <= 0 || previewRows.value.length === 0) {
    return
  }

  const openAmount = Number(contract.value?.valor_em_aberto ?? 0)
  if (amount > openAmount) {
    message.value = {
      kind: 'error',
      text: 'O valor a distribuir não pode ser maior que o valor a pagar do contrato.',
    }
    await errorAlert(message.value.text)
    return
  }

  const confirmed = await confirmActionAlert(
    'Confirmar recebimento em lote?',
    'O sistema vai baixar as próximas parcelas em aberto por ordem de vencimento usando o valor informado.',
    'Confirmar',
  )
  if (!confirmed) {
    return
  }

  loading.confirm = true
  try {
    const result = await confirmBatchContractReceive(contractId, {
      valor_recebido: amount,
      data_recebimento: currentDateTimeLocal(),
    })

    contract.value = await getContractById(contractId)
    preview.value = null
    message.value = {
      kind: 'info',
      text: `${result.parcelas_processadas.length} parcela(s) baixada(s) com sucesso.`,
    }
    await successAlert('Recebimento em lote confirmado com sucesso.', 'update')
    resetState()
    await focusContractField()
  } catch (error) {
    const text = error instanceof Error ? error.message : 'Falha ao confirmar recebimento em lote.'
    message.value = { kind: 'error', text }
    await errorAlert(text)
  } finally {
    loading.confirm = false
  }
}

function toPositiveInteger(value: string) {
  const parsed = Number(value)
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return null
  }
  return parsed
}

function toLocaleNumberOrNull(value: string) {
  const trimmed = value.trim()
  if (!trimmed) {
    return null
  }

  const normalized = trimmed.replace(/\./g, '').replace(',', '.')
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function hasMinimumSearchTerm(value: string) {
  const trimmed = value.trim()
  const numeric = trimmed.replace(/\D/g, '')
  return trimmed.length >= 3 || numeric.length >= 3
}

function formatDecimal(value: number) {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
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

function formatDocument(value: string | null | undefined) {
  const digits = String(value ?? '').replace(/\D/g, '')
  if (!digits) {
    return '-'
  }

  if (digits.length === 11) {
    return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
  }

  if (digits.length === 14) {
    return digits.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
  }

  return value || digits
}

function resetContractSearchResult() {
  contractSearchModal.result = {
    items: [],
    total: 0,
    page: 1,
    page_size: contractSearchModal.result.page_size,
  }
}

watch(
  () => contractSearchModal.result.items,
  (groups) => {
    const validKeys = new Set(groups.map((group) => group.client_key))

    for (const group of groups) {
      if (!(group.client_key in openedContractSearchClientGroups)) {
        openedContractSearchClientGroups[group.client_key] = false
      }
    }

    for (const key of Object.keys(openedContractSearchClientGroups)) {
      if (!validKeys.has(key)) {
        delete openedContractSearchClientGroups[key]
      }
    }
  },
  { immediate: true },
)

function formatDate(value: string | null) {
  if (!value) {
    return '-'
  }

  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) {
    return '-'
  }

  return `${match[3]}/${match[2]}/${match[1]}`
}

function formatWeekday(value: string | null) {
  if (!value) {
    return '-'
  }

  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) {
    return '-'
  }

  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
  return new Intl.DateTimeFormat('pt-BR', { weekday: 'long' }).format(date).toUpperCase()
}

function currentDateTimeLocal() {
  const date = new Date()
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
}
</script>

<style scoped>
.batch-receipt-panel {
  display: grid;
  gap: 1.25rem;
}

.batch-receipt-panel__header {
  margin-bottom: 0;
}

.batch-receipt-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  align-items: end;
}

.field-inline.batch-receipt-contract-picker {
  position: relative;
  display: block;
}

.batch-receipt-contract-picker__field {
  width: 100%;
  padding-right: 46px;
}

.batch-receipt-contract-picker__button {
  position: absolute;
  top: 1px;
  right: 1px;
  bottom: 1px;
  width: 44px;
  min-height: 0;
  padding: 0;
  border-left: 1px solid rgba(249, 115, 22, 0.18);
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  border-top-right-radius: 3px;
  border-bottom-right-radius: 3px;
  background: rgba(249, 115, 22, 0.1);
  color: #d85a04;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.batch-receipt-contract-picker__icon {
  width: 15px;
  height: 15px;
}

.batch-receipt-form__actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.batch-receipt-summary-row {
  gap: 0.75rem;
}

.summary-chip--wide {
  min-width: 12rem;
}

.batch-receipt-table-wrap {
  min-height: 16rem;
}

.batch-receipt-table th,
.batch-receipt-table td {
  white-space: nowrap;
}

.batch-receipt-actions {
  justify-content: flex-end;
}

.batch-receipt-search-modal {
  width: min(920px, calc(100vw - 32px));
}

.batch-receipt-search-modal__content {
  display: grid;
  gap: 1rem;
}

.batch-receipt-search-modal__filters {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: end;
}

.batch-receipt-search-modal__search-button {
  min-width: 6.5rem;
  min-height: 34px;
}

.batch-receipt-search-modal__table-wrap {
  min-height: 18rem;
}

.batch-receipt-search-modal__table th,
.batch-receipt-search-modal__table td {
  white-space: nowrap;
}

.batch-receipt-search-modal__row {
  cursor: pointer;
}

.batch-receipt-search-modal__client-row td {
  border-bottom: 1px solid rgba(249, 115, 22, 0.12);
}

.batch-receipt-search-modal__contract-row {
  cursor: pointer;
}

.batch-receipt-search-modal__contract-button {
  padding-left: 28px;
}

.batch-receipt-search-modal__pagination {
  justify-content: space-between;
}

@media (max-width: 900px) {
  .batch-receipt-form {
    grid-template-columns: 1fr;
  }

  .batch-receipt-form__actions {
    justify-content: flex-start;
  }

  .batch-receipt-search-modal__filters {
    grid-template-columns: 1fr;
  }
}
</style>