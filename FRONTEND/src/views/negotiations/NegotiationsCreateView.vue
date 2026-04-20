<template>
  <section class="panel form-panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Movimentações</p>
        <h2 class="panel__title">Nova Negociação</h2>
      </div>
    </header>

    <div class="negotiation-form">
      <!-- Client Picker -->
      <div class="negotiation-form__client-section">
        <label class="field-group">
          <span>Cliente</span>
          <div class="field-inline contract-client-picker">
            <input :value="selectedClientLabel" class="field field--readonly" readonly type="text" />
            <button class="secondary-button contract-client-picker__button" type="button" title="Consultar cliente" aria-label="Consultar cliente" @click="openClientModal">
              <svg class="contract-client-picker__icon" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M10.5 4a6.5 6.5 0 1 0 4.03 11.6l4.44 4.44 1.41-1.41-4.44-4.44A6.5 6.5 0 0 0 10.5 4Zm0 2a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Z" fill="currentColor" />
              </svg>
            </button>
          </div>
        </label>
      </div>

      <!-- Open contracts grid -->
      <div v-if="selectedClientId !== null" class="negotiation-form__contracts-section">
        <h3 class="panel__title">Contratos Abertos</h3>
        <p v-if="loadingContracts" class="feedback">Carregando contratos...</p>
        <p v-else-if="openContracts.length === 0" class="feedback feedback--warning">Nenhum contrato em aberto para este cliente.</p>

        <div v-if="displayedContracts.length > 0" class="table-wrap">
          <table class="data-table data-table--cadastro">
            <thead>
              <tr>
                <th style="width: 40px;">
                  <input type="checkbox" :checked="allSelected" :indeterminate.prop="someSelected && !allSelected" @change="toggleAll" />
                </th>
                <th>Contrato</th>
                <th>Data Contrato</th>
                <th>Valor Empréstimo</th>
                <th>Valor em Aberto</th>
                <th>Valor Parcela</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="contract in displayedContracts" :key="contract.contratos_id" class="data-table__row">
                <td>
                  <input type="checkbox" :checked="selectedContractIds.has(contract.contratos_id)" @change="toggleContract(contract.contratos_id)" />
                </td>
                <td>{{ contract.contratos_id }}</td>
                <td>{{ formatDate(contract.data_contrato) }}</td>
                <td>{{ formatCurrency(contract.valor_empretismo) }}</td>
                <td>{{ formatCurrency(contract.valor_em_aberto) }}</td>
                <td>{{ formatCurrency(contract.valor_parcela) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Summary -->
        <div v-if="selectedContractIds.size > 0" class="negotiation-form__summary">
          <div class="negotiation-form__summary-grid">
            <label class="field-group">
              <span>Valor Total em Aberto</span>
              <input :value="formatCurrency(totalAberto)" class="field field--readonly" readonly type="text" />
            </label>
            <label class="field-group">
              <span>Qtde Parcelas</span>
              <input v-model.number="form.qtde_parcelas" class="field" type="number" min="1" @input="recalcValorParcela" />
            </label>
            <label class="field-group">
              <span>Valor Parcela</span>
              <input v-model="form.valor_parcela_display" class="field" type="text" inputmode="decimal" @blur="formatValorParcela" />
            </label>
          </div>

          <!-- Billing day flags -->
          <div class="negotiation-form__flags">
            <span class="negotiation-form__flags-label">Dias de cobrança</span>
            <div class="contract-days-picker__grid">
              <label class="contract-days-picker__item">
                <input v-model="form.cobranca_segunda" type="checkbox" />
                <span>Segunda</span>
              </label>
              <label class="contract-days-picker__item">
                <input v-model="form.cobranca_terca" type="checkbox" />
                <span>Terça</span>
              </label>
              <label class="contract-days-picker__item">
                <input v-model="form.cobranca_quarta" type="checkbox" />
                <span>Quarta</span>
              </label>
              <label class="contract-days-picker__item">
                <input v-model="form.cobranca_quinta" type="checkbox" />
                <span>Quinta</span>
              </label>
              <label class="contract-days-picker__item">
                <input v-model="form.cobranca_sexta" type="checkbox" />
                <span>Sexta</span>
              </label>
              <label class="contract-days-picker__item">
                <input v-model="form.cobranca_sabado" type="checkbox" />
                <span>Sábado</span>
              </label>
              <label class="contract-days-picker__item">
                <input v-model="form.cobranca_domingo" type="checkbox" />
                <span>Domingo</span>
              </label>
              <label class="contract-days-picker__item">
                <input v-model="form.cobranca_feriado" type="checkbox" />
                <span>Feriado</span>
              </label>
              <label class="contract-days-picker__item">
                <input v-model="form.cobranca_mensal" type="checkbox" />
                <span>Mensal</span>
              </label>
              <label class="contract-days-picker__item">
                <input v-model="form.cobranca_quinzenal" type="checkbox" />
                <span>Quinzenal</span>
              </label>
            </div>
          </div>

          <label class="field-group">
            <span>Observação</span>
            <textarea v-model="form.obs" class="field field--textarea" rows="2"></textarea>
          </label>

          <div class="form-actions">
            <button class="ghost-button" type="button" @click="handleCancel">Cancelar</button>
            <button class="primary-button" type="button" :disabled="saving" @click="handleGenerate">
              {{ saving ? 'Gerando...' : 'Gerar Negociação' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Client Search Modal -->
    <Teleport to="body">
      <div v-if="clientModal.open" class="modal-backdrop" @click.self="closeClientModal">
        <section class="modal-card modal-card--clients-search">
          <header class="panel__header panel__header--stacked">
            <div>
              <h3 class="panel__title">Selecionar cliente</h3>
            </div>
            <p class="modal-context">Pesquise por empresa ou CPF/CNPJ.</p>
          </header>

          <div class="modal-form">
            <label class="field-group">
              <span>Busca</span>
              <input v-model="clientModal.term" class="field" type="text" placeholder="Digite nome, documento ou endereço" />
            </label>

            <div class="negotiation-client-results">
              <p v-if="clientSearch.loading" class="feedback">Carregando clientes...</p>
              <button
                v-for="client in clientSearch.result.items"
                :key="client.clientes_id"
                class="negotiation-client-result"
                type="button"
                @click="selectClient(client.clientes_id)"
              >
                <div class="negotiation-client-result__header">
                  <strong>{{ client.nome || 'Sem nome' }}</strong>
                  <small class="negotiation-client-result__balance">Saldo devedor: {{ formatCurrency(client.valor_em_aberto) }}</small>
                </div>
                <span>{{ formatDocument(client.cpf_cnpj) }}</span>
                <small>{{ formatClientAddress(client) }}</small>
              </button>
              <p v-if="!clientSearch.loading && clientSearch.result.items.length === 0" class="profile-modal-list__empty">Nenhum cliente encontrado.</p>
            </div>

            <div class="negotiation-client-pagination">
              <small>{{ clientRangeLabel }}</small>
              <div class="negotiation-client-pagination__actions">
                <button class="ghost-button" type="button" :disabled="clientSearch.result.page <= 1 || clientSearch.loading" @click="changeClientPage(clientSearch.result.page - 1)">Anterior</button>
                <span>Página {{ clientSearch.result.page }} de {{ clientTotalPages }}</span>
                <button class="ghost-button" type="button" :disabled="clientSearch.result.page >= clientTotalPages || clientSearch.loading" @click="changeClientPage(clientSearch.result.page + 1)">Próxima</button>
              </div>
            </div>

            <div class="form-actions">
              <button class="ghost-button" type="button" @click="closeClientModal">Fechar</button>
            </div>
          </div>
        </section>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import type { Client, ClientListResponse } from '@/models/client'
import type { OpenContractForNegotiation } from '@/models/negotiation'
import { confirmActionAlert, errorAlert, successAlert } from '@/services/alertService'
import { listClients } from '@/services/clientService'
import { listOpenContracts, createNegotiation } from '@/services/negotiationService'

const router = useRouter()

const openContracts = ref<OpenContractForNegotiation[]>([])
const selectedClientId = ref<number | null>(null)
const selectedContractIds = reactive(new Set<number>())
const loadingContracts = ref(false)
const saving = ref(false)

const selectedClient = ref<Client | null>(null)

const clientModal = reactive({ open: false, term: '', page: 1, pageSize: 8 })
const clientSearch = reactive({
  loading: false,
  result: {
    items: [] as Client[],
    total: 0,
    page: 1,
    page_size: 8,
  } as ClientListResponse,
})

const form = reactive({
  qtde_parcelas: 1,
  valor_parcela_display: '',
  obs: '' as string | null,
  cobranca_segunda: true,
  cobranca_terca: true,
  cobranca_quarta: true,
  cobranca_quinta: true,
  cobranca_sexta: true,
  cobranca_sabado: false,
  cobranca_domingo: false,
  cobranca_feriado: false,
  cobranca_mensal: false,
  cobranca_quinzenal: false,
})

const selectedClientLabel = computed(() => {
  if (!selectedClient.value || selectedClientId.value === null) return 'Não selecionado'
  return `${selectedClient.value.clientes_id} - ${selectedClient.value.nome || 'Sem nome'}`
})

const displayedContracts = computed(() => openContracts.value)

const allSelected = computed(() => displayedContracts.value.length > 0 && displayedContracts.value.every((c) => selectedContractIds.has(c.contratos_id)))
const someSelected = computed(() => displayedContracts.value.some((c) => selectedContractIds.has(c.contratos_id)))

const totalAberto = computed(() => {
  let total = 0
  for (const contract of displayedContracts.value) {
    if (selectedContractIds.has(contract.contratos_id)) {
      total += contract.valor_em_aberto
    }
  }
  return total
})

const clientTotalPages = computed(() => Math.max(1, Math.ceil(clientSearch.result.total / clientSearch.result.page_size)))

const clientRangeLabel = computed(() => {
  if (clientSearch.result.total === 0) {
    return '0-0 de 0'
  }

  const start = (clientSearch.result.page - 1) * clientSearch.result.page_size + 1
  const end = Math.min(clientSearch.result.page * clientSearch.result.page_size, clientSearch.result.total)
  return `${start}-${end} de ${clientSearch.result.total}`
})

let clientSearchDebounce: number | null = null

watch(() => clientModal.term, () => {
  if (!clientModal.open) {
    return
  }
  clientModal.page = 1
  if (clientSearchDebounce !== null) {
    window.clearTimeout(clientSearchDebounce)
  }
  clientSearchDebounce = window.setTimeout(() => {
    void fetchClientPage()
  }, 250)
})

function toggleAll() {
  if (allSelected.value) {
    for (const c of displayedContracts.value) {
      selectedContractIds.delete(c.contratos_id)
    }
  } else {
    for (const c of displayedContracts.value) {
      selectedContractIds.add(c.contratos_id)
    }
  }
  recalcValorParcela()
}

function toggleContract(contractId: number) {
  if (selectedContractIds.has(contractId)) {
    selectedContractIds.delete(contractId)
  } else {
    selectedContractIds.add(contractId)
  }
  recalcValorParcela()
}

function recalcValorParcela() {
  if (form.qtde_parcelas > 0 && totalAberto.value > 0) {
    const valor = totalAberto.value / form.qtde_parcelas
    form.valor_parcela_display = formatDecimalInput(valor)
  }
}

function formatValorParcela() {
  const parsed = parseDecimalInput(form.valor_parcela_display)
  if (parsed !== null) {
    form.valor_parcela_display = formatDecimalInput(parsed)
  }
}

function openClientModal() {
  clientModal.open = true
  clientModal.term = ''
  clientModal.page = 1
  void fetchClientPage()
}

function closeClientModal() {
  clientModal.open = false
  clientModal.term = ''
  if (clientSearchDebounce !== null) {
    window.clearTimeout(clientSearchDebounce)
    clientSearchDebounce = null
  }
}

async function selectClient(clientId: number) {
  selectedClientId.value = clientId
  selectedClient.value = clientSearch.result.items.find((item) => item.clientes_id === clientId) ?? null
  selectedContractIds.clear()
  closeClientModal()

  loadingContracts.value = true
  try {
    openContracts.value = await listOpenContracts(clientId)
  } catch (error) {
    openContracts.value = []
    await errorAlert(error instanceof Error ? error.message : 'Falha ao carregar contratos abertos do cliente')
  } finally {
    loadingContracts.value = false
  }
}

async function fetchClientPage() {
  clientSearch.loading = true
  try {
    const trimmed = clientModal.term.trim()
    const digits = trimmed.replace(/\D/g, '')
    clientSearch.result = await listClients({
      page: clientModal.page,
      page_size: clientModal.pageSize,
      ativo: true,
      nome: digits.length >= 11 ? undefined : trimmed || undefined,
      cpf_cnpj: digits.length >= 11 ? digits : undefined,
      endereco: digits.length >= 11 ? undefined : trimmed || undefined,
    })
  } finally {
    clientSearch.loading = false
  }
}

function changeClientPage(page: number) {
  clientModal.page = page
  void fetchClientPage()
}

async function handleGenerate() {
  if (selectedClientId.value === null) {
    await errorAlert('Selecione um cliente.')
    return
  }
  if (selectedContractIds.size === 0) {
    await errorAlert('Selecione ao menos um contrato.')
    return
  }

  const valorParcela = parseDecimalInput(form.valor_parcela_display)
  if (!valorParcela || valorParcela <= 0) {
    await errorAlert('Informe um valor de parcela válido.')
    return
  }

  const confirmed = await confirmActionAlert(
    'Gerar negociação?',
    `Serão negociados ${selectedContractIds.size} contrato(s), gerando um novo contrato com ${form.qtde_parcelas} parcela(s) de ${form.valor_parcela_display}.`,
    'Gerar',
  )
  if (!confirmed) return

  saving.value = true
  try {
    const result = await createNegotiation({
      cliente_id: selectedClientId.value,
      contratos_ids: Array.from(selectedContractIds),
      qtde_parcelas: form.qtde_parcelas,
      valor_parcela: valorParcela,
      obs: form.obs || null,
      cobranca_segunda: form.cobranca_segunda,
      cobranca_terca: form.cobranca_terca,
      cobranca_quarta: form.cobranca_quarta,
      cobranca_quinta: form.cobranca_quinta,
      cobranca_sexta: form.cobranca_sexta,
      cobranca_sabado: form.cobranca_sabado,
      cobranca_domingo: form.cobranca_domingo,
      cobranca_feriado: form.cobranca_feriado,
      cobranca_mensal: form.cobranca_mensal,
      cobranca_quinzenal: form.cobranca_quinzenal,
    })

    await successAlert('Negociação gerada com sucesso.', 'create')
    await router.push({ name: 'negotiations-view', params: { id: result.negociacao_id } })
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao gerar negociação')
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  void router.push({ name: 'negotiations-list' })
}

function formatDate(value: string | null) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('pt-BR').format(new Date(value))
}

function formatCurrency(value: number | null | undefined) {
  if (typeof value !== 'number') return '-'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

function formatDocument(value: string | null | undefined) {
  const digits = (value ?? '').replace(/\D/g, '')
  if (!digits) return '-'
  if (digits.length <= 11) {
    return digits
      .slice(0, 11)
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2')
  }
  return digits
    .slice(0, 14)
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1/$2')
    .replace(/(\d{4})(\d{1,2})$/, '$1-$2')
}

function formatClientAddress(client: Client) {
  const number = client.nro?.trim() ? `, ${client.nro.trim()}` : ''
  const uf = client.uf ? `-${client.uf}` : ''
  const address = client.endereco?.trim() || 'Endereço não informado'
  return `${address}${number}${uf}`.trim()
}

function parseDecimalInput(value: string | undefined): number | null {
  const trimmed = (value ?? '').trim()
  if (!trimmed) return null
  const normalized = trimmed.replace(/\./g, '').replace(',', '.')
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function formatDecimalInput(value: number): string {
  return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value)
}
</script>

<style scoped>
.negotiation-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem;
}

.negotiation-form__client-section {
  max-width: 500px;
}

.negotiation-form__contracts-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.negotiation-form__summary {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
  padding: 1rem;
  background: var(--surface-secondary, #f8fafc);
  border-radius: 8px;
  border: 1px solid var(--border-secondary, #e2e8f0);
}

.negotiation-form__summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.negotiation-form__flags {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.negotiation-form__flags-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary, #64748b);
}

.negotiation-client-results {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 340px;
  overflow-y: auto;
}

.negotiation-client-result {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  width: 100%;
  padding: 0.9rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  background: #ffffff;
  text-align: left;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.negotiation-client-result:hover {
  border-color: #f97316;
  box-shadow: 0 0 0 1px rgba(249, 115, 22, 0.14);
}

.negotiation-client-result__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.negotiation-client-result__balance {
  color: #475569;
  font-weight: 600;
  white-space: nowrap;
}

.negotiation-client-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 0.75rem;
}

.negotiation-client-pagination__actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

@media (max-width: 760px) {
  .negotiation-form__summary-grid {
    grid-template-columns: 1fr;
  }

  .negotiation-client-result__header,
  .negotiation-client-pagination {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
