<template>
  <section class="panel form-panel contract-form-panel">
    <div class="contract-tabs" role="tablist" aria-label="Abas do contrato">
      <button class="contract-tabs__button" :class="{ 'contract-tabs__button--active': activeTab === 'dados' }" type="button" @click="activeTab = 'dados'">
        Dados do contrato
      </button>
      <button class="contract-tabs__button" :class="{ 'contract-tabs__button--active': activeTab === 'parcelas' }" type="button" @click="activeTab = 'parcelas'">
        Parcelas
      </button>
    </div>

    <form class="contract-form" @submit.prevent="submitForm">
      <section v-if="activeTab === 'dados'" class="contract-tab-panel">
        <div class="contract-form__cards">
          <section class="contract-card contract-card--main">
            <header class="contract-card__header">
              <div>
                <h3 class="panel__title">Informações Gerais</h3>
              </div>
              <label class="status-switch contract-status-switch" :class="form.quitado ? 'status-switch--on' : 'status-switch--off'">
                <input :checked="form.quitado" class="status-switch__input" disabled type="checkbox" />
                <span class="status-switch__track"><span class="status-switch__thumb"></span></span>
                <span class="status-switch__label">{{ form.quitado ? 'Quitado' : 'Aberto' }}</span>
              </label>
            </header>

            <div class="contract-card__grid">
              <label class="field-group">
                <span>Nº Contrato</span>
                <div class="field-inline contract-number-field" :class="{ 'contract-number-field--with-action': hasNegotiatedContracts }">
                  <input v-model="form.contratos_id" :disabled="contractEditLocked" class="field field--no-spin" required type="number" />
                  <button
                    v-if="hasNegotiatedContracts"
                    class="contract-number-field__action"
                    type="button"
                    title="Contratos Negociados"
                    aria-label="Contratos Negociados"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M3 6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3h-7a3 3 0 0 0 0 6h7v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6Zm11 5a1 1 0 1 0 0 2h7v-2h-7Z" fill="currentColor" />
                    </svg>
                  </button>
                </div>
              </label>

              <label class="field-group">
                <span>Data Lançto.</span>
                <input v-model="form.data_lancto" class="field field--readonly" readonly type="datetime-local" />
              </label>

              <label class="field-group">
                <span>Data Contrato</span>
                <input v-model="form.data_contrato" :disabled="contractEditLocked" class="field" type="datetime-local" />
              </label>

              <label class="field-group">
                <span>Data Final</span>
                <input v-model="form.data_final" class="field field--readonly" readonly type="datetime-local" />
              </label>

              <label class="field-group field-group--span-2">
                <span>Cliente</span>
                <div class="field-inline contract-client-picker">
                  <input :value="selectedClientLabel" class="field field--readonly" readonly type="text" />
                  <button
                    class="secondary-button contract-client-picker__button"
                    :aria-disabled="contractEditLocked"
                    :class="{ 'secondary-button--disabled': contractEditLocked }"
                    type="button"
                    @click="openClientModal"
                  >
                    Buscar cliente
                  </button>
                </div>
              </label>

              <label class="field-group field-group--span-2">
                <span>Vendedor</span>
                <select v-model.number="form.usuario_id_vendedor" :disabled="contractEditLocked" class="field">
                  <option :value="null">Selecione</option>
                  <option v-for="user in sellerOptions" :key="user.id" :value="user.id">
                    {{ user.nome }}
                  </option>
                </select>
              </label>

              <label class="field-group field-group--span-2">
                <span>OBS</span>
                <textarea v-model="form.obs" :readonly="contractEditLocked" class="field field--textarea contract-obs-textarea" rows="2"></textarea>
              </label>

              <div class="contract-financials-grid field-group field-group--span-2">
                <label class="field-group">
                  <span>Valor Recebido</span>
                  <input v-model="form.valor_recebido" class="field field--readonly contract-financial-field contract-financial-field--received" readonly type="text" />
                </label>

                <label class="field-group">
                  <span>Valor Aberto</span>
                  <input v-model="form.valor_em_aberto" class="field field--readonly contract-financial-field contract-financial-field--open" readonly type="text" />
                </label>

                <label class="field-group">
                  <span>Valor em Atraso</span>
                  <input v-model="form.valor_em_atraso" class="field field--readonly contract-financial-field contract-financial-field--overdue" readonly type="text" />
                </label>
              </div>
            </div>
          </section>

          <section class="contract-card">
            <header class="contract-card__header">
              <div>
                <h3 class="panel__title">Plano e Valores</h3>
              </div>
            </header>

            <div class="contract-card__grid">
              <label class="field-group field-group--span-2">
                <span>Plano de Pagamento</span>
                <select v-model.number="form.plano_id" :disabled="contractEditLocked" class="field" @change="syncPlanDefaults">
                  <option :value="null">Selecione</option>
                  <option v-for="plan in paymentPlans" :key="plan.plano_id" :value="plan.plano_id">
                    {{ plan.descricao || `Plano ${plan.plano_id}` }}
                  </option>
                </select>
              </label>

              <div class="contract-card__triple field-group field-group--span-2">
                <label class="field-group">
                  <span>Valor empréstimo</span>
                  <input v-model="form.valor_empretismo" :readonly="contractEditLocked" class="field" inputmode="decimal" type="text" @blur="formatDecimalField('valor_empretismo')" />
                </label>

                <label class="field-group">
                  <span>Dias</span>
                  <input v-model="form.qtde_dias" :readonly="contractEditLocked" class="field" inputmode="numeric" type="text" />
                </label>

                <label class="field-group">
                  <span>Juros %</span>
                  <input v-model="form.percent_juros" :readonly="contractEditLocked" class="field" inputmode="decimal" type="text" @blur="formatDecimalField('percent_juros')" />
                </label>
              </div>

              <label class="field-group">
                <span>Valor Final</span>
                <input v-model="form.valor_final" :readonly="contractEditLocked" class="field" inputmode="decimal" type="text" @blur="formatDecimalField('valor_final')" />
              </label>

              <label class="field-group">
                <span>Valor Parcela</span>
                <input v-model="form.valor_parcela" :readonly="contractEditLocked" class="field" inputmode="decimal" type="text" @blur="formatDecimalField('valor_parcela')" />
              </label>

              <label class="field-group field-group--span-2">
                <span>Regra de Juros</span>
                <select v-model.number="form.regra_juros_id" class="field">
                  <option :value="null">Selecione</option>
                  <option v-for="rule in regraJurosOptions" :key="rule.regra_juros_id" :value="rule.regra_juros_id">
                    {{ rule.descricao || `Regra ${rule.regra_juros_id}` }}
                  </option>
                </select>
              </label>

              <label class="field-group field-group--span-2">
                <span>Regra Comissão</span>
                <select v-model.number="form.regra_comissao_id" class="field">
                  <option :value="null">Selecione</option>
                  <option v-for="rule in regraComissaoOptions" :key="rule.regra_comissao_id" :value="rule.regra_comissao_id">
                    {{ rule.descricao || `Regra ${rule.regra_comissao_id}` }}
                  </option>
                </select>
              </label>

              <div class="field-group field-group--span-2 contract-days-picker">
                <span>Dias em que realiza cobrança</span>
                <div class="contract-days-picker__grid">
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.sabado" :disabled="contractEditLocked" type="checkbox" />
                    <span>Sábado</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.domingo" :disabled="contractEditLocked" type="checkbox" />
                    <span>Domingo</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.feriado" :disabled="contractEditLocked" type="checkbox" />
                    <span>Feriado</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.mensal" :disabled="contractEditLocked" type="checkbox" />
                    <span>Mensal</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.quinzenal" :disabled="contractEditLocked" type="checkbox" />
                    <span>Quinzenal</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.segunda" :disabled="contractEditLocked" type="checkbox" />
                    <span>Segunda</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.terca" :disabled="contractEditLocked" type="checkbox" />
                    <span>Terça</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.quarta" :disabled="contractEditLocked" type="checkbox" />
                    <span>Quarta</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.quinta" :disabled="contractEditLocked" type="checkbox" />
                    <span>Quinta</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.sexta" :disabled="contractEditLocked" type="checkbox" />
                    <span>Sexta</span>
                  </label>
                </div>
              </div>
            </div>
          </section>
        </div>

      </section>

      <section v-else class="contract-tab-panel">
        <div class="contract-installments">
          <section class="contract-card contract-card--parcelas">
            <header class="contract-card__header contract-card__header--parcelas">
              <div>
                <h3 class="panel__title">Parcelas</h3>
              </div>
            </header>

            <div class="contract-installments__tools">
              <label class="toggle-row">
                <input v-model="form.recorrencia" type="checkbox" />
                <span>Contrato recorrente</span>
              </label>
              <span v-if="installmentsLoading" class="feedback feedback--info contract-installments__status">Atualizando parcelas...</span>
            </div>

            <div class="table-wrap contract-installments__table-wrap">
              <table class="data-table contract-installments__table">
                <thead>
                  <tr>
                    <th>Parc.</th>
                    <th>Vencimento</th>
                    <th>Dia Semana</th>
                    <th>Valor</th>
                    <th>Juros</th>
                    <th>Valor Total</th>
                    <th>Vl. Recebido</th>
                    <th>Pgto</th>
                    <th>Quitar</th>
                    <th>Del</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!installmentsLoading && installmentRows.length === 0">
                    <td colspan="10">Nenhuma parcela gerada.</td>
                  </tr>
                  <tr v-for="row in installmentRows" :key="row.key" :class="{ 'contract-installments__row--paid': row.isPaid }">
                    <td>{{ row.label }}</td>
                    <td>{{ row.dueDate }}</td>
                    <td>{{ row.weekday }}</td>
                    <td>{{ row.baseValue }}</td>
                    <td>{{ row.interestValue }}</td>
                    <td>{{ row.value }}</td>
                    <td>{{ row.receivedValue }}</td>
                    <td>
                      <button class="contract-installments__action contract-installments__action--pay" :disabled="!row.canPay || installmentsSaving" type="button" title="Receber parcela" aria-label="Receber parcela" @click="handleReceiveInstallment(row.id)">
                        <span class="contract-installments__action-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24">
                            <path d="M3 6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3H3V6Zm0 5h18v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7Zm4 3v2h4v-2H7Z" fill="currentColor" />
                          </svg>
                        </span>
                      </button>
                    </td>
                    <td>
                      <button class="contract-installments__action contract-installments__action--settle" :disabled="!row.canSettle || installmentsSaving" type="button" title="Quitar parcela" aria-label="Quitar parcela" @click="handleSettleInstallment(row.id)">
                        <span class="contract-installments__action-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24">
                            <path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" fill="currentColor" />
                          </svg>
                        </span>
                      </button>
                    </td>
                    <td>
                      <button class="contract-installments__action contract-installments__action--delete" :disabled="!row.canDeletePayment || installmentsSaving" type="button" title="Excluir pagamento" aria-label="Excluir pagamento" @click="handleDeleteInstallmentPayment(row.id)">
                        <span class="contract-installments__action-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24">
                            <path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor" />
                          </svg>
                        </span>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </section>

      <div class="form-actions form-actions--contract">
        <button class="primary-button primary-button--success form-actions__button contract-action-button" :disabled="props.saving" type="button" @click="handleNew">
          <span class="contract-action-button__icon">+</span>
          <span>Novo</span>
        </button>
        <button class="primary-button primary-button--success form-actions__button contract-action-button" :disabled="props.saving" type="submit">
          <span class="contract-action-button__icon">✓</span>
          <span>{{ props.saving ? 'Salvando...' : 'Salvar' }}</span>
        </button>
        <button class="ghost-button form-actions__button contract-action-button" :disabled="props.saving" type="button" @click="emit('cancel')">
          <span class="contract-action-button__icon">×</span>
          <span>Fechar</span>
        </button>
        <button class="ghost-button ghost-button--danger form-actions__button contract-action-button" :disabled="props.saving || props.mode === 'create' || !props.canDelete" type="button" @click="emit('delete')">
          <span class="contract-action-button__icon">⌫</span>
          <span>Excluir</span>
        </button>
        <button
          v-if="activeTab === 'dados'"
          class="primary-button primary-button--accent-soft form-actions__button contract-action-button contract-action-button--calculate"
          :disabled="props.saving || !form.cliente_id"
          type="button"
          @click="calculateInstallments"
        >
          <span class="contract-calc-button__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M7 2h10a2 2 0 0 1 2 2v16l-4-2-4 2-4-2-4 2V4a2 2 0 0 1 2-2h2Zm1 5v2h8V7H8Zm0 4v2h8v-2H8Zm0 4v2h5v-2H8Z" fill="currentColor" />
            </svg>
          </span>
          <span>Calcular dias</span>
        </button>
      </div>
    </form>

    <p v-if="props.success" class="feedback feedback--success">{{ props.success }}</p>
    <p v-if="props.error" class="feedback feedback--error">{{ props.error }}</p>

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

            <div class="contract-client-results">
              <button
                v-for="client in filteredClients"
                :key="client.clientes_id"
                class="contract-client-result"
                type="button"
                @click="selectClient(client.clientes_id)"
              >
                <strong>{{ client.nome || 'Sem nome' }}</strong>
                <span>{{ formatDocument(client.cpf_cnpj) }}</span>
                <small>{{ formatClientAddress(client) }}</small>
              </button>
              <p v-if="filteredClients.length === 0" class="profile-modal-list__empty">Nenhum cliente encontrado.</p>
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
import { computed, onMounted, reactive, ref, watch } from 'vue'

import type { Client, RegraComissaoOption, RegraJurosOption } from '@/models/client'
import type {
  Contract,
  ContractCreateInput,
  ContractInstallment,
  ContractInstallmentGeneratePayload,
  ContractUpdateInput,
} from '@/models/contract'
import type { CidadeOption } from '@/models/location'
import type { FeriadoOption } from '@/models/location'
import type { PaymentPlanOption } from '@/models/paymentPlan'
import type { User } from '@/models/user'
import {
  deleteReceiptPayment,
  generateContractInstallments,
  listInstallmentReceipts,
  listContractInstallments,
  receiveContractInstallment,
  settleContractInstallment,
} from '@/services/contractService'
import { chooseReceiptToDeletePrompt, confirmActionAlert, errorAlert, infoAlert, receivePaymentPrompt, successAlert } from '@/services/alertService'
import { listClients, listRegraComissaoOptions, listRegraJurosOptions } from '@/services/clientService'
import { listCitiesByUf, listFeriados } from '@/services/locationService'
import { listPaymentPlans } from '@/services/paymentPlanService'
import { listUsers } from '@/services/userService'

const props = defineProps<{
  mode: 'create' | 'edit'
  saving: boolean
  error: string
  success: string
  canDelete: boolean
  initialContract?: Contract | null
  initialClientId?: number | null
}>()

const emit = defineEmits<{
  submit: [payload: { contract: ContractCreateInput | ContractUpdateInput; installments: ContractInstallmentGeneratePayload | null }]
  cancel: []
  delete: []
  new: []
}>()

const activeTab = ref<'dados' | 'parcelas'>('dados')
const clientOptions = ref<Client[]>([])
const paymentPlans = ref<PaymentPlanOption[]>([])
const sellerOptions = ref<User[]>([])
const regraJurosOptions = ref<RegraJurosOption[]>([])
const regraComissaoOptions = ref<RegraComissaoOption[]>([])
const persistedInstallments = ref<ContractInstallment[]>([])
const installmentsLoading = ref(false)
const installmentsSaving = ref(false)
const holidayCache = reactive<Record<string, FeriadoOption[]>>({})
const previewInstallmentsPayload = ref<ContractInstallmentGeneratePayload | null>(null)
const generatedInstallments = ref<Array<{ key: string; id: number | null; label: string; dueDate: string; weekday: string; baseValue: string; interestValue: string; value: string; receivedValue: string; canPay: boolean; canSettle: boolean; canDeletePayment: boolean; isPaid: boolean }>>([])
const clientModal = reactive({ open: false, term: '' })
const cityLabels = reactive<Record<number, string>>({})
const billingDays = reactive({
  sabado: false,
  domingo: false,
  feriado: false,
  mensal: false,
  quinzenal: false,
  segunda: true,
  terca: true,
  quarta: true,
  quinta: true,
  sexta: true,
})

const defaultBillingDays = {
  sabado: false,
  domingo: false,
  feriado: false,
  mensal: false,
  quinzenal: false,
  segunda: true,
  terca: true,
  quarta: true,
  quinta: true,
  sexta: true,
} as const

const form = reactive({
  contratos_id: '',
  data_lancto: '',
  data_contrato: '',
  cliente_id: null as number | null,
  plano_id: null as number | null,
  qtde_dias: '',
  percent_juros: '',
  valor_empretismo: '',
  data_final: '',
  valor_final: '',
  valor_recebido: formatDecimalValue(0),
  valor_em_aberto: formatDecimalValue(0),
  valor_em_atraso: formatDecimalValue(0),
  quitado: false,
  obs: '',
  valor_parcela: '',
  user_add: null as number | null,
  contrato_status: '1',
  negociacao_id: '',
  usuario_id_vendedor: null as number | null,
  comissao_percentual: '',
  valor_comissao_previsto: '',
  valor_comissao_apurada: '',
  regra_comissao_id: null as number | null,
  regra_juros_id: '',
  recorrencia: false,
})

const selectedClientLabel = computed(() => {
  const client = clientOptions.value.find((item) => item.clientes_id === form.cliente_id)
  if (!client) {
    return 'Não selecionado'
  }
  return `${client.clientes_id} - ${client.nome || 'Sem nome'}`
})

const hasNegotiatedContracts = computed(() => Boolean(toNumberOrNull(form.negociacao_id)))
const currentContractId = computed(() => props.initialContract?.contratos_id ?? null)
const contractEditLocked = computed(() => {
  if (props.mode !== 'edit') {
    return false
  }

  if (persistedInstallments.value.some((item) => (item.valor_recebido ?? 0) > 0 || Boolean(item.quitado))) {
    return true
  }

  return (toLocaleNumberOrNull(form.valor_recebido) ?? 0) > 0 || Boolean(form.quitado)
})

const filteredClients = computed(() => {
  const term = clientModal.term.trim().toLowerCase()
  if (!term) {
    return clientOptions.value
  }

  return clientOptions.value.filter((client) => {
    const haystack = [
      client.nome ?? '',
      client.cpf_cnpj ?? '',
      client.endereco ?? '',
      client.nro ?? '',
      cityLabels[client.cidade_id ?? -1] ?? '',
      client.uf ?? '',
    ]
      .join(' ')
      .toLowerCase()

    return haystack.includes(term)
  })
})

const installmentRows = computed(() => {
  if (persistedInstallments.value.length > 0) {
    return persistedInstallments.value.map((item) => ({
      key: `db-${item.id}`,
      id: item.id,
      label: String(item.parcela_nro ?? '').padStart(2, '0'),
      dueDate: formatDateLabel(item.vencimentol ?? item.vencimento_original),
      weekday: formatWeekdayLabel(item.vencimentol ?? item.vencimento_original),
      baseValue: formatCurrency(item.valor_base),
      interestValue: formatCurrency(item.valor_juros),
      value: formatCurrency(item.valor_total),
      receivedValue: formatCurrency(item.valor_recebido),
      canPay: true,
      canSettle: !item.quitado,
      canDeletePayment: Boolean(item.possui_pagamento),
      isPaid: Boolean(item.quitado),
    }))
  }

  if (generatedInstallments.value.length > 0) {
    return generatedInstallments.value
  }

  return []
})

onMounted(() => {
  resetForm()
  void loadOptions()
})

watch(
  () => props.initialContract,
  (contract) => {
    syncContractIntoForm(contract)
  },
  { immediate: true },
)

watch(
  currentContractId,
  (contractId) => {
    generatedInstallments.value = []
    if (contractId) {
      void loadInstallments(contractId)
      return
    }

    persistedInstallments.value = []
  },
  { immediate: true },
)

watch(
  () => props.initialClientId,
  (clientId) => {
    if (props.mode === 'create' && typeof clientId === 'number' && !Number.isNaN(clientId)) {
      form.cliente_id = clientId
    }
  },
  { immediate: true },
)

async function loadOptions() {
  const [clientsResponse, plansResponse, usersResponse, jurosResponse, comissaoResponse] = await Promise.all([
    listClients({ page: 1, page_size: 100, ativo: true }),
    listPaymentPlans(),
    listUsers({ page: 1, page_size: 100, ativo: true }),
    listRegraJurosOptions(),
    listRegraComissaoOptions(),
  ])

  clientOptions.value = [...clientsResponse.items]
  paymentPlans.value = plansResponse
  sellerOptions.value = [...usersResponse.items]
  regraJurosOptions.value = jurosResponse
  regraComissaoOptions.value = comissaoResponse
  await hydrateClientCities()
  if (props.mode === 'create') {
    await assignNextContractNumber()
  }
}

function syncContractIntoForm(contract?: Contract | null) {
  if (!contract) {
    if (props.mode === 'create') {
      resetForm()
    }
    return
  }

  form.contratos_id = String(contract.contratos_id)
  form.data_lancto = toDateTimeLocal(contract.data_lancto)
  form.data_contrato = toDateTimeLocal(contract.data_contrato)
  form.cliente_id = contract.cliente_id
  form.plano_id = contract.plano_id
  form.qtde_dias = formatIntegerValue(contract.qtde_dias)
  form.percent_juros = formatDecimalValue(contract.percent_juros)
  form.valor_empretismo = formatDecimalValue(contract.valor_empretismo)
  form.data_final = toDateTimeLocal(contract.data_final)
  form.valor_final = formatDecimalValue(contract.valor_final)
  form.valor_recebido = formatDecimalValue(contract.valor_recebido)
  form.valor_em_aberto = formatDecimalValue(contract.valor_em_aberto)
  form.valor_em_atraso = formatDecimalValue(contract.valor_em_atraso)
  form.quitado = Boolean(contract.quitado)
  form.obs = contract.obs ?? ''
  form.valor_parcela = formatDecimalValue(contract.valor_parcela)
  form.user_add = contract.user_add
  form.contrato_status = String(contract.contrato_status)
  form.negociacao_id = toStringValue(contract.negociacao_id)
  form.usuario_id_vendedor = contract.usuario_id_vendedor
  form.comissao_percentual = toStringValue(contract.comissao_percentual)
  form.valor_comissao_previsto = toStringValue(contract.valor_comissao_previsto)
  form.valor_comissao_apurada = toStringValue(contract.valor_comissao_apurada)
  form.regra_comissao_id = contract.regra_comissao_id
  form.regra_juros_id = toStringValue(contract.regra_juros_id)
  form.recorrencia = Boolean(contract.recorrencia)
  resetBillingDays()
  previewInstallmentsPayload.value = null
  generatedInstallments.value = []
}

function resetForm() {
  resetBillingDays()
  form.contratos_id = ''
  form.data_lancto = currentDateTimeLocal()
  form.data_contrato = currentDateTimeLocal()
  form.cliente_id = props.initialClientId ?? null
  form.plano_id = null
  form.qtde_dias = ''
  form.percent_juros = ''
  form.valor_empretismo = ''
  form.data_final = ''
  form.valor_final = ''
  form.valor_recebido = formatDecimalValue(0)
  form.valor_em_aberto = formatDecimalValue(0)
  form.valor_em_atraso = formatDecimalValue(0)
  form.quitado = false
  form.obs = ''
  form.valor_parcela = ''
  form.user_add = null
  form.contrato_status = '1'
  form.negociacao_id = ''
  form.usuario_id_vendedor = null
  form.comissao_percentual = ''
  form.valor_comissao_previsto = ''
  form.valor_comissao_apurada = ''
  form.regra_comissao_id = null
  form.regra_juros_id = ''
  form.recorrencia = false
  activeTab.value = 'dados'
  persistedInstallments.value = []
  previewInstallmentsPayload.value = null
  generatedInstallments.value = []
  if (props.mode === 'create') {
    void assignNextContractNumber()
  }
}

function syncPlanDefaults() {
  if (contractEditLocked.value) {
    return
  }

  const selectedPlan = paymentPlans.value.find((item) => item.plano_id === form.plano_id)
  if (!selectedPlan) {
    return
  }

  form.valor_empretismo = formatDecimalValue(selectedPlan.valor_base)
  form.qtde_dias = formatIntegerValue(selectedPlan.qtde_dias)
  form.percent_juros = formatDecimalValue(selectedPlan.percent_juros)
  form.valor_parcela = formatDecimalValue(selectedPlan.valor_parcela)
  if (!form.valor_final) {
    form.valor_final = formatDecimalValue(selectedPlan.valor_final)
  }
}

async function calculateInstallments() {
  if (!form.cliente_id) {
    await infoAlert('Selecione o cliente antes de calcular os dias.')
    return
  }

  if (contractEditLocked.value) {
    await infoAlert('Este contrato nao pode mais ser recalculado porque ja possui recebimentos ou parcelas quitadas.')
    return
  }

  const startDate = parseLocalDateTime(form.data_contrato)
  const installmentValue = toLocaleNumberOrNull(form.valor_parcela) ?? toLocaleNumberOrNull(form.valor_final)
  const qtdDias = toIntegerOrNull(form.qtde_dias)

  if (!startDate || installmentValue === null || qtdDias === null || qtdDias <= 0) {
    previewInstallmentsPayload.value = null
    generatedInstallments.value = []
    form.data_final = ''
    if (persistedInstallments.value.length > 0) {
      syncFinancialTotalsFromInstallments()
    } else {
      resetFinancialTotals()
    }
    activeTab.value = 'parcelas'
    return
  }

  const holidaySet = await loadHolidaySet()
  const dueDates = buildDueDates(startDate, qtdDias, holidaySet)
  const endDate = dueDates.at(-1) ?? null
  form.data_final = endDate ? toDateTimeLocal(endDate.toISOString()) : ''

  if (dueDates.length === 0) {
    previewInstallmentsPayload.value = null
    generatedInstallments.value = []
    if (persistedInstallments.value.length > 0) {
      syncFinancialTotalsFromInstallments()
    } else {
      resetFinancialTotals()
    }
    activeTab.value = 'parcelas'
    return
  }

  const payload: ContractInstallmentGeneratePayload = {
    parcelas: dueDates.map((date, index) => ({
      parcela_nro: index + 1,
      vencimento: toApiDateTimeLocal(date),
      valor_total: installmentValue,
    })),
  }

  if (!currentContractId.value) {
    previewInstallmentsPayload.value = payload
    syncFinancialTotalsFromPreview(dueDates, installmentValue)
    generatedInstallments.value = payload.parcelas.map((item) => ({
      key: `preview-${item.parcela_nro}`,
      id: null,
      label: String(item.parcela_nro).padStart(2, '0'),
      dueDate: formatDateLabel(item.vencimento),
      weekday: formatWeekdayLabel(item.vencimento),
      baseValue: formatCurrency(item.valor_total),
      interestValue: formatCurrency(0),
      value: formatCurrency(item.valor_total),
      receivedValue: '-',
      canPay: false,
      canSettle: false,
      canDeletePayment: false,
      isPaid: false,
    }))
    activeTab.value = 'parcelas'
    return
  }

  installmentsSaving.value = true
  try {
    persistedInstallments.value = await generateContractInstallments(currentContractId.value, payload)
    previewInstallmentsPayload.value = null
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
    generatedInstallments.value = []
    activeTab.value = 'parcelas'
    void successAlert('Parcelas geradas em contas a receber.', 'update')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao gerar parcelas do contrato')
  } finally {
    installmentsSaving.value = false
  }
}

async function loadInstallments(contractId: number) {
  installmentsLoading.value = true
  try {
    persistedInstallments.value = await listContractInstallments(contractId)
    previewInstallmentsPayload.value = null
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
  } catch {
    persistedInstallments.value = []
  } finally {
    installmentsLoading.value = false
  }
}

async function handleReceiveInstallment(installmentId: number | null) {
  if (!installmentId) {
    return
  }

  const row = persistedInstallments.value.find((item) => item.id === installmentId)
  if (row?.quitado) {
    await infoAlert('Esta parcela ja esta quitada.')
    return
  }

  const remainingValue = row ? Math.max((row.valor_total ?? 0) - (row.valor_recebido ?? 0), 0) : null
  const payment = await receivePaymentPrompt(remainingValue)
  if (!payment) {
    return
  }

  installmentsSaving.value = true
  try {
    const updated = await receiveContractInstallment(installmentId, {
      valor_recebido: payment.valorRecebido,
      data_recebimento: currentDateTimeLocal(),
      desconto: null,
      juros: payment.juros,
    })
    updateInstallmentInState(updated)
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
    void successAlert('Recebimento lançado com sucesso.', 'update')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao registrar recebimento')
  } finally {
    installmentsSaving.value = false
  }
}

async function handleSettleInstallment(installmentId: number | null) {
  if (!installmentId) {
    return
  }

  if (!(await confirmActionAlert('Quitar parcela?', 'A parcela será marcada como quitada mesmo com pagamento inferior ao valor total.', 'Quitar'))) {
    return
  }

  installmentsSaving.value = true
  try {
    const updated = await settleContractInstallment(installmentId, { data_recebimento: currentDateTimeLocal() })
    updateInstallmentInState(updated)
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
    void successAlert('Parcela quitada com sucesso.', 'update')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao quitar parcela')
  } finally {
    installmentsSaving.value = false
  }
}

async function handleDeleteInstallmentPayment(installmentId: number | null) {
  if (!installmentId) {
    return
  }

  installmentsSaving.value = true
  try {
    const receipts = await listInstallmentReceipts(installmentId)
    if (receipts.length === 0) {
      await infoAlert('Nao existem pagamentos lancados para esta parcela.')
      return
    }

    const receiptIds = await chooseReceiptToDeletePrompt(
      receipts.map((receipt) => ({
        id: receipt.recebimento_id,
        title: `${formatCurrency(receipt.valor_recebido)} em ${formatDateLabel(receipt.data_recebimento)}`,
        description: `Recebido por ${receipt.usuario_nome || 'Usuario nao identificado'}${receipt.juros ? ` | Juros ${formatCurrency(receipt.juros)}` : ''}${receipt.desconto ? ` | Desconto ${formatCurrency(receipt.desconto)}` : ''}`,
      })),
    )

    if (!receiptIds || receiptIds.length === 0) {
      return
    }

    let updated: ContractInstallment | null = null
    for (const receiptId of receiptIds) {
      updated = await deleteReceiptPayment(receiptId)
    }

    if (!updated) {
      return
    }

    updateInstallmentInState(updated)
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
    void successAlert('Pagamento excluído com sucesso.', 'delete')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao excluir pagamento da parcela')
  } finally {
    installmentsSaving.value = false
  }
}

function updateInstallmentInState(updated: ContractInstallment) {
  const index = persistedInstallments.value.findIndex((item) => item.id === updated.id)
  if (index === -1) {
    persistedInstallments.value = [...persistedInstallments.value, updated]
    return
  }

  persistedInstallments.value = persistedInstallments.value.map((item) => (item.id === updated.id ? updated : item))
}

function syncQuitadoFromInstallments() {
  form.quitado = persistedInstallments.value.length > 0 && persistedInstallments.value.every((item) => Boolean(item.quitado))
}

function syncFinancialTotalsFromInstallments() {
  syncContractFinalValueFromInstallments()
  applyFinancialTotals(
    summarizeInstallmentTotals(
      persistedInstallments.value.map((item) => ({
        dueDate: item.vencimentol ?? item.vencimento_original,
        totalValue: item.valor_total,
        receivedValue: item.valor_recebido,
        quitado: item.quitado,
      })),
    ),
  )
}

function syncFinancialTotalsFromPreview(dueDates: Date[], installmentValue: number) {
  form.valor_final = formatDecimalValue(dueDates.length * installmentValue)
  applyFinancialTotals(
    summarizeInstallmentTotals(
      dueDates.map((dueDate) => ({
        dueDate: dueDate.toISOString(),
        totalValue: installmentValue,
        receivedValue: 0,
        quitado: false,
      })),
    ),
  )
}

function syncContractFinalValueFromInstallments() {
  if (persistedInstallments.value.length === 0) {
    return
  }

  const totalValue = persistedInstallments.value.reduce((sum, item) => sum + (item.valor_total ?? 0), 0)
  form.valor_final = formatDecimalValue(totalValue)
}

function summarizeInstallmentTotals(
  installments: Array<{ dueDate: string | null; totalValue: number | null; receivedValue: number | null; quitado: boolean | null }>,
) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  let totalReceived = 0
  let totalOpen = 0
  let totalOverdue = 0

  for (const installment of installments) {
    const totalValue = installment.totalValue ?? 0
    const receivedValue = installment.receivedValue ?? 0
    const remainingValue = installment.quitado ? 0 : Math.max(totalValue - receivedValue, 0)

    totalReceived += receivedValue
    totalOpen += remainingValue

    if (remainingValue > 0 && installment.dueDate) {
      const dueDate = new Date(installment.dueDate)
      dueDate.setHours(0, 0, 0, 0)
      if (dueDate < today) {
        totalOverdue += remainingValue
      }
    }
  }

  return {
    valorRecebido: totalReceived,
    valorEmAberto: totalOpen,
    valorEmAtraso: totalOverdue,
  }
}

function applyFinancialTotals(totals: { valorRecebido: number; valorEmAberto: number; valorEmAtraso: number }) {
  form.valor_recebido = formatDecimalValue(totals.valorRecebido) || formatDecimalValue(0)
  form.valor_em_aberto = formatDecimalValue(totals.valorEmAberto) || formatDecimalValue(0)
  form.valor_em_atraso = formatDecimalValue(totals.valorEmAtraso) || formatDecimalValue(0)
}

function resetFinancialTotals() {
  applyFinancialTotals({
    valorRecebido: 0,
    valorEmAberto: 0,
    valorEmAtraso: 0,
  })
}

function submitForm() {
  if (props.mode === 'create') {
    emit('submit', {
      contract: buildCreatePayload(),
      installments: previewInstallmentsPayload.value,
    })
    return
  }

  emit('submit', {
    contract: buildUpdatePayload(),
    installments: null,
  })
}

function buildCreatePayload(): ContractCreateInput {
  return {
    contratos_id: Number(form.contratos_id),
    ...buildCommonPayload(),
  }
}

function buildUpdatePayload(): ContractUpdateInput {
  return buildCommonPayload()
}

function buildCommonPayload(): ContractUpdateInput {
  return {
    data_lancto: form.data_lancto || null,
    data_contrato: form.data_contrato || null,
    cliente_id: form.cliente_id,
    plano_id: form.plano_id,
    qtde_dias: toIntegerOrNull(form.qtde_dias),
    percent_juros: toLocaleNumberOrNull(form.percent_juros),
    valor_empretismo: toLocaleNumberOrNull(form.valor_empretismo),
    data_final: form.data_final || null,
    valor_final: toLocaleNumberOrNull(form.valor_final),
    quitado: form.quitado,
    obs: form.obs.trim() || null,
    valor_parcela: toLocaleNumberOrNull(form.valor_parcela),
    user_add: form.user_add,
    contrato_status: Number(form.contrato_status || '1'),
    negociacao_id: toNumberOrNull(form.negociacao_id),
    usuario_id_vendedor: form.usuario_id_vendedor,
    comissao_percentual: toNumberOrNull(form.comissao_percentual),
    valor_comissao_previsto: toNumberOrNull(form.valor_comissao_previsto),
    valor_comissao_apurada: toNumberOrNull(form.valor_comissao_apurada),
    regra_comissao_id: form.regra_comissao_id,
    regra_juros_id: toNumberOrNull(form.regra_juros_id),
    recorrencia: form.recorrencia,
  }
}

function handleNew() {
  if (props.mode === 'create') {
    resetForm()
    return
  }

  emit('new')
}

function openClientModal() {
  if (contractEditLocked.value) {
    void infoAlert('Este contrato nao permite trocar o cliente porque ja possui recebimentos ou parcelas quitadas.')
    return
  }

  clientModal.open = true
  clientModal.term = ''
}

function closeClientModal() {
  clientModal.open = false
  clientModal.term = ''
}

function selectClient(clientId: number) {
  form.cliente_id = clientId
  closeClientModal()
}

async function hydrateClientCities() {
  const ufList = [...new Set(clientOptions.value.map((client) => client.uf).filter((uf): uf is string => Boolean(uf)))]

  await Promise.all(
    ufList.map(async (uf) => {
      const cities = await listCitiesByUf(uf)
      registerCities(cities)
    }),
  )
}

function registerCities(cities: CidadeOption[]) {
  for (const city of cities) {
    cityLabels[city.cidade_id] = city.cidade
  }
}

async function assignNextContractNumber() {
  try {
    const { listContracts } = await import('@/services/contractService')
    const response = await listContracts({ page: 1, page_size: 1 })
    const nextId = response.items[0]?.contratos_id ? response.items[0].contratos_id + 1 : 1
    form.contratos_id = String(nextId)
  } catch {
    form.contratos_id = '1'
  }
}

function currentDateTimeLocal() {
  const date = new Date()
  const timezoneOffset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 16)
}

function toApiDateTimeLocal(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
}

function toDateTimeLocal(value: string | null) {
  if (!value) {
    return ''
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  const timezoneOffset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 16)
}

function parseLocalDateTime(value: string) {
  if (!value) {
    return null
  }

  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/)
  if (!match) {
    return null
  }

  const parsed = new Date(
    Number(match[1]),
    Number(match[2]) - 1,
    Number(match[3]),
    Number(match[4]),
    Number(match[5]),
  )
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function resetBillingDays() {
  billingDays.sabado = defaultBillingDays.sabado
  billingDays.domingo = defaultBillingDays.domingo
  billingDays.feriado = defaultBillingDays.feriado
  billingDays.mensal = defaultBillingDays.mensal
  billingDays.quinzenal = defaultBillingDays.quinzenal
  billingDays.segunda = defaultBillingDays.segunda
  billingDays.terca = defaultBillingDays.terca
  billingDays.quarta = defaultBillingDays.quarta
  billingDays.quinta = defaultBillingDays.quinta
  billingDays.sexta = defaultBillingDays.sexta
}

function toStringValue(value: number | null | undefined) {
  return typeof value === 'number' ? String(value) : ''
}

function formatDecimalValue(value: number | null | undefined) {
  if (typeof value !== 'number') {
    return ''
  }

  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function formatIntegerValue(value: number | null | undefined) {
  if (typeof value !== 'number') {
    return ''
  }

  return String(Math.trunc(value))
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

function toIntegerOrNull(value: string) {
  const parsed = toLocaleNumberOrNull(value)
  if (parsed === null) {
    return null
  }

  return Math.trunc(parsed)
}

function toNumberOrNull(value: string) {
  const trimmed = value.trim()
  if (!trimmed) {
    return null
  }

  const parsed = Number(trimmed)
  return Number.isFinite(parsed) ? parsed : null
}

function formatDecimalField(field: 'valor_empretismo' | 'percent_juros' | 'valor_final' | 'valor_parcela') {
  const parsed = toLocaleNumberOrNull(form[field])
  form[field] = parsed === null ? '' : formatDecimalValue(parsed)
}

function buildDueDates(startDate: Date, qtdDias: number, holidaySet: Set<string>) {
  if (billingDays.mensal) {
    return buildMonthlyDueDates(startDate, qtdDias, holidaySet)
  }

  if (billingDays.quinzenal) {
    return buildBiweeklyDueDates(startDate, qtdDias, holidaySet)
  }

  return buildWeeklyDueDates(startDate, qtdDias, holidaySet)
}

function buildMonthlyDueDates(startDate: Date, qtdDias: number, holidaySet: Set<string>) {
  const dates: Date[] = []
  const cursor = new Date(startDate)
  let generated = 0

  while (generated < qtdDias) {
    const candidate = new Date(cursor)
    if (shouldIncludeDate(candidate, holidaySet)) {
      dates.push(candidate)
      generated += 1
    }
    cursor.setMonth(cursor.getMonth() + 1)
  }

  return dates
}

function buildBiweeklyDueDates(startDate: Date, qtdDias: number, holidaySet: Set<string>) {
  const dates: Date[] = []
  const cursor = new Date(startDate)
  let generated = 0

  while (generated < qtdDias) {
    const candidate = new Date(cursor)
    if (shouldIncludeDate(candidate, holidaySet)) {
      dates.push(candidate)
      generated += 1
    }
    cursor.setDate(cursor.getDate() + 15)
  }

  return dates
}

function buildWeeklyDueDates(startDate: Date, qtdDias: number, holidaySet: Set<string>) {
  const allowedWeekdays = new Set<number>()
  if (billingDays.domingo) allowedWeekdays.add(0)
  if (billingDays.segunda) allowedWeekdays.add(1)
  if (billingDays.terca) allowedWeekdays.add(2)
  if (billingDays.quarta) allowedWeekdays.add(3)
  if (billingDays.quinta) allowedWeekdays.add(4)
  if (billingDays.sexta) allowedWeekdays.add(5)
  if (billingDays.sabado) allowedWeekdays.add(6)

  const dates: Date[] = []
  const cursor = new Date(startDate)
  let generated = 0

  while (generated < qtdDias) {
    if (allowedWeekdays.has(cursor.getDay()) && shouldIncludeDate(cursor, holidaySet)) {
      dates.push(new Date(cursor))
      generated += 1
    }
    cursor.setDate(cursor.getDate() + 1)
  }

  return dates
}

function shouldIncludeDate(date: Date, holidaySet: Set<string>) {
  if (!billingDays.feriado && holidaySet.has(formatDateKey(date))) {
    return false
  }

  return true
}

async function loadHolidaySet() {
  if (billingDays.feriado) {
    return new Set<string>()
  }

  const client = clientOptions.value.find((item) => item.clientes_id === form.cliente_id)
  const nationalCacheKey = '__nacionais__'

  if (!holidayCache[nationalCacheKey]) {
    holidayCache[nationalCacheKey] = await listFeriados({ nivel: 1 })
  }

  if (!client) {
    return new Set(holidayCache[nationalCacheKey].map((item) => formatDateKey(item.data)))
  }

  const cacheKey = `${client.uf ?? ''}:${client.cidade_id ?? ''}`
  if (!holidayCache[cacheKey]) {
    const [estaduais, municipais] = await Promise.all([
      client.uf ? listFeriados({ nivel: 2, uf: client.uf }) : Promise.resolve([]),
      typeof client.cidade_id === 'number' ? listFeriados({ nivel: 3, cidade_id: client.cidade_id }) : Promise.resolve([]),
    ])
    holidayCache[cacheKey] = [...holidayCache[nationalCacheKey], ...estaduais, ...municipais]
  }

  return new Set(holidayCache[cacheKey].map((item) => formatDateKey(item.data)))
}

function formatDateKey(value: Date | string) {
  if (typeof value === 'string') {
    const isoMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
    if (isoMatch) {
      return `${isoMatch[1]}-${isoMatch[2]}-${isoMatch[3]}`
    }
  }

  const date = typeof value === 'string' ? new Date(value) : value
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatDateLabel(value: string | null) {
  if (!value) {
    return '-'
  }

  const calendarDate = parseCalendarDate(value)
  if (!calendarDate) {
    return '-'
  }

  return `${String(calendarDate.day).padStart(2, '0')}/${String(calendarDate.month).padStart(2, '0')}/${calendarDate.year}`
}

function formatWeekdayLabel(value: string | null) {
  if (!value) {
    return '-'
  }

  const calendarDate = parseCalendarDate(value)
  if (!calendarDate) {
    return '-'
  }

  return new Intl.DateTimeFormat('pt-BR', { weekday: 'long' })
    .format(new Date(calendarDate.year, calendarDate.month - 1, calendarDate.day))
    .toUpperCase()
}

function parseCalendarDate(value: string) {
  const isoMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!isoMatch) {
    return null
  }

  return {
    year: Number(isoMatch[1]),
    month: Number(isoMatch[2]),
    day: Number(isoMatch[3]),
  }
}

function formatCurrency(value: number | null) {
  if (typeof value !== 'number') {
    return '-'
  }

  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

function formatDocument(value: string | null | undefined) {
  const digits = (value ?? '').replace(/\D/g, '')
  if (!digits) {
    return '-'
  }
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
  const city = client.cidade_id ? cityLabels[client.cidade_id] ?? `Cidade ${client.cidade_id}` : 'Cidade não informada'
  const number = client.nro?.trim() ? `, ${client.nro.trim()}` : ''
  const uf = client.uf ? `-${client.uf}` : ''
  const address = client.endereco?.trim() || 'Endereço não informado'
  return `${address}${number} ${city}${uf}`.trim()
}
</script>