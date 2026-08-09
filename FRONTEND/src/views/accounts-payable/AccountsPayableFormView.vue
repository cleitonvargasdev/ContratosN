<template>
  <section class="panel form-panel accounts-payable-form-view">
    <header class="panel__header panel__header--stacked">
      <div>
        <p class="eyebrow">Financeiro</p>
        <h2 class="panel__title">{{ isEdit ? 'Editar conta à pagar' : 'Nova conta à pagar' }}</h2>
      </div>
    </header>

    <form class="accounts-payable-form" @submit.prevent="handleSubmit">
      <section class="accounts-payable-card">
        <div class="accounts-payable-card__header-row">
          <h3 class="accounts-payable-card__title">Dados principais</h3>
          <div class="accounts-payable-card__totals">
            <span class="summary-chip"><strong>{{ formatCurrency(existingOpenAmount + pendingAmount) }}</strong><span>Saldo previsto</span></span>
          </div>
        </div>

        <div class="accounts-payable-card__grid">
          <label class="field-group field-group--span-2">
            <span>Descrição</span>
            <input v-model="form.descricao" class="field" required type="text" />
          </label>

          <label class="field-group field-group--span-2">
            <span>Pessoa vinculada</span>
            <div class="field-inline accounts-payable-person-picker">
              <input :value="selectedPersonLabel" class="field accounts-payable-person-picker__field" placeholder="Selecione cliente, fornecedor ou funcionário" readonly type="text" />
              <button class="secondary-button accounts-payable-person-picker__button" type="button" title="Pesquisar pessoa" aria-label="Pesquisar pessoa" @click="openPersonSearchModal">
                <svg class="accounts-payable-person-picker__icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M10.5 4a6.5 6.5 0 1 0 4.03 11.6l4.44 4.44 1.41-1.41-4.44-4.44A6.5 6.5 0 0 0 10.5 4Zm0 2a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Z" fill="currentColor" />
                </svg>
              </button>
            </div>
          </label>

          <label class="field-group field-group--span-2">
            <span>Observação</span>
            <textarea v-model="form.observacao" class="field field--textarea" rows="3"></textarea>
          </label>
        </div>
      </section>

      <section class="accounts-payable-card">
        <div class="accounts-payable-card__header-row">
          <h3 class="accounts-payable-card__title">Parcelas</h3>
          <div class="accounts-payable-card__actions">
            <button class="secondary-button" type="button" @click="openGenerator">Lançar parcelas</button>
          </div>
        </div>

        <div v-if="isEdit && existingInstallments.length > 0" class="accounts-payable-table-wrap">
          <table class="data-table data-table--cadastro accounts-payable-installments-table">
            <thead>
              <tr>
                <th>Parc.</th>
                <th>Descrição</th>
                <th>Venc.</th>
                <th>R$ Valor</th>
                <th>R$ Juros</th>
                <th>R$ Desc.</th>
                <th>R$ Total</th>
                <th>R$ Pago</th>
                <th>R$ Aberto</th>
                <th>Status</th>
                <th class="actions-column">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="parcela in existingInstallments" :key="parcela.parcela_id">
                <td>{{ String(parcela.numero_parcela || 0).padStart(2, '0') }}</td>
                <td :title="parcela.descricao || '-'">{{ parcela.descricao || '-' }}</td>
                <td>{{ formatShortDate(parcela.vencimento) }}</td>
                <td>{{ formatTableAmount(parcela.valor_original) }}</td>
                <td>{{ formatTableAmount(parcela.acrescimos) }}</td>
                <td>{{ formatTableAmount(parcela.desconto) }}</td>
                <td>{{ formatTableAmount(parcela.valor_total) }}</td>
                <td>{{ formatTableAmount(parcela.valor_pago) }}</td>
                <td>{{ formatTableAmount(parcela.saldo_pagar) }}</td>
                <td>
                  <span :class="['pill', parcela.quitado ? 'pill--success' : 'pill--warning']">{{ parcela.quitado ? 'Quitado' : 'Aberto' }}</span>
                </td>
                <td class="accounts-payable-actions-cell">
                  <div class="payment-editor">
                    <button class="icon-action accounts-payable-actions-menu__trigger" :aria-expanded="actionMenuParcelaId === parcela.parcela_id" aria-label="Abrir ações da parcela" title="Ações" type="button" @click="toggleActionMenu(parcela.parcela_id)">
                      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="12" r="1.8" fill="currentColor"/><circle cx="12" cy="12" r="1.8" fill="currentColor"/><circle cx="19" cy="12" r="1.8" fill="currentColor"/></svg>
                    </button>
                    <div v-if="actionMenuParcelaId === parcela.parcela_id" class="accounts-payable-actions-menu">
                      <button :disabled="parcela.quitado || accountsPayable.state.saving" type="button" @click="openPaymentModal(parcela.parcela_id)">Pagar</button>
                      <button :disabled="parcela.quitado || accountsPayable.state.saving" type="button" @click="handleSettleInstallment(parcela.parcela_id, parcela.saldo_pagar)">Quitar</button>
                      <button :disabled="parcela.pagamentos.length === 0 || accountsPayable.state.saving" type="button" @click="handleRemovePayments(parcela.parcela_id)">Remover Pgto</button>
                      <button class="accounts-payable-actions-menu__delete" :disabled="accountsPayable.state.saving" type="button" @click="handleDeleteInstallment(parcela.parcela_id)">Excluir Parcela</button>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="pendingInstallments.length > 0" class="accounts-payable-table-wrap">
          <table class="data-table data-table--cadastro">
            <thead>
              <tr>
                <th>Parc.</th>
                <th>Descrição</th>
                <th>Vencimento</th>
                <th>Valor</th>
                <th>Juros</th>
                <th>Descontos</th>
                <th>Valor Total</th>
                <th>Observação</th>
                <th class="actions-column">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(parcela, index) in pendingInstallments" :key="`pending-${index}`">
                <td>{{ String(parcela.numero_parcela || index + 1).padStart(2, '0') }}</td>
                <td><input v-model="parcela.descricao" class="field" type="text" /></td>
                <td><input v-model="parcela.vencimento" class="field" type="date" /></td>
                <td><input v-model.number="parcela.valor_original" class="field" min="0" step="0.01" type="number" /></td>
                <td><input v-model.number="parcela.acrescimos" class="field" min="0" step="0.01" type="number" /></td>
                <td><input v-model.number="parcela.desconto" class="field" min="0" step="0.01" type="number" /></td>
                <td>{{ formatCurrency(calculateInstallmentTotal(parcela)) }}</td>
                <td><input v-model="parcela.observacao" class="field" type="text" /></td>
                <td class="actions-cell">
                  <button class="icon-action icon-action--danger" type="button" @click="pendingInstallments.splice(index, 1)">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/></svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div class="form-actions form-actions--user">
        <button class="primary-button primary-button--success form-actions__button" :disabled="accountsPayable.state.saving" type="submit">{{ accountsPayable.state.saving ? 'Salvando...' : 'Salvar' }}</button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="accountsPayable.state.saving" type="button" @click="router.push({ name: 'accounts-payable-list' })">Cancelar</button>
      </div>
    </form>

    <p v-if="accountsPayable.state.error" class="feedback feedback--error">{{ accountsPayable.state.error }}</p>

    <div v-if="generatorOpen" class="accounts-payable-generator-backdrop" @click.self="generatorOpen = false">
      <div class="accounts-payable-generator-modal">
        <header class="accounts-payable-generator-modal__header">
          <h3>Lançar parcelas</h3>
          <button class="icon-action" type="button" @click="generatorOpen = false">×</button>
        </header>

        <div class="accounts-payable-generator-grid">
          <label class="field-group">
            <span>Qtd. parcelas</span>
            <input v-model.number="generator.quantidade" class="field" min="1" step="1" type="number" @input="regeneratePreview" />
          </label>
          <label class="field-group">
            <span>Valor</span>
            <input v-model.number="generator.valor" class="field" min="0" step="0.01" type="number" @input="regeneratePreview" />
          </label>
          <label class="field-group">
            <span>Primeiro vencimento</span>
            <input v-model="generator.primeiroVencimento" class="field" type="date" @input="regeneratePreview" />
          </label>
          <label class="field-group toggle-row accounts-payable-generator-toggle">
            <input v-model="generator.mensal" type="checkbox" @change="regeneratePreview" />
            <span>Mensal</span>
          </label>
          <label class="field-group toggle-row accounts-payable-generator-toggle">
            <input v-model="generator.manual" type="checkbox" @change="regeneratePreview" />
            <span>Manual</span>
          </label>
        </div>

        <div class="accounts-payable-table-wrap">
          <table class="data-table data-table--cadastro">
            <thead>
              <tr>
                <th>Parcela</th>
                <th>Descrição</th>
                <th>Vencimento</th>
                <th>Valor</th>
                <th>Valor Juros</th>
                <th>Valor Desconto</th>
                <th>Valor Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in generatorPreview" :key="`generator-${index}`">
                <td>{{ String(item.numero_parcela || index + 1).padStart(2, '0') }}</td>
                <td><input v-model="item.descricao" class="field" :readonly="!generator.manual" type="text" /></td>
                <td><input v-model="item.vencimento" class="field" :readonly="!generator.manual" type="date" /></td>
                <td><input v-model.number="item.valor_original" class="field" :readonly="!generator.manual" min="0" step="0.01" type="number" /></td>
                <td><input v-model.number="item.acrescimos" class="field" :readonly="!generator.manual" min="0" step="0.01" type="number" /></td>
                <td><input v-model.number="item.desconto" class="field" :readonly="!generator.manual" min="0" step="0.01" type="number" /></td>
                <td>{{ formatCurrency(calculateInstallmentTotal(item)) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="accounts-payable-generator-modal__footer">
          <button class="ghost-button" type="button" @click="generatorOpen = false">Cancelar</button>
          <button class="primary-button" type="button" @click="confirmGenerator">Adicionar parcelas</button>
        </footer>
      </div>
    </div>

    <div v-if="paymentModal.open" class="accounts-payable-generator-backdrop" @click.self="closePaymentModal">
      <section class="accounts-payable-payment-modal" aria-labelledby="payment-modal-title">
        <header class="accounts-payable-generator-modal__header">
          <h3 id="payment-modal-title">Informar pagamento</h3>
          <button class="icon-action" type="button" aria-label="Fechar" @click="closePaymentModal">×</button>
        </header>

        <div v-if="paymentModal.parcelaId !== null" class="accounts-payable-payment-modal__grid">
          <label class="field-group">
            <span>Valor pago</span>
            <input v-model.number="paymentDrafts[paymentModal.parcelaId].valor_pago" class="field" min="0" step="0.01" type="number" />
          </label>
          <label class="field-group">
            <span>Juros</span>
            <input v-model.number="paymentDrafts[paymentModal.parcelaId].juros" class="field" min="0" step="0.01" type="number" />
          </label>
          <label class="field-group">
            <span>Acréscimos</span>
            <input v-model.number="paymentDrafts[paymentModal.parcelaId].acrescimos" class="field" min="0" step="0.01" type="number" />
          </label>
          <label class="field-group">
            <span>Descontos</span>
            <input v-model.number="paymentDrafts[paymentModal.parcelaId].desconto" class="field" min="0" step="0.01" type="number" />
          </label>
        </div>

        <footer class="accounts-payable-generator-modal__footer">
          <button class="ghost-button" :disabled="accountsPayable.state.saving" type="button" @click="closePaymentModal">Cancelar</button>
          <button class="primary-button" :disabled="accountsPayable.state.saving" type="button" @click="confirmPayment">Pagar</button>
        </footer>
      </section>
    </div>

    <Teleport to="body">
      <div v-if="personSearchModal.open" class="modal-backdrop" @click.self="closePersonSearchModal">
        <section class="modal-card accounts-payable-search-modal">
          <header class="panel__header panel__header--stacked">
            <div>
              <h3 class="panel__title">Pesquisar pessoa vinculada</h3>
            </div>
          </header>

          <div class="modal-form accounts-payable-search-modal__content">
            <div class="accounts-payable-search-modal__filters">
              <label class="field-group">
                <span>Busca por nome ou CPF/CNPJ</span>
                <input v-model="personSearchModal.term" class="field" type="text" placeholder="Digite 3 letras ou 3 números para pesquisar." @keydown.enter.prevent="runPersonSearch()" />
              </label>
              <button class="secondary-button accounts-payable-search-modal__search-button" type="button" @click="runPersonSearch()">Pesquisar</button>
            </div>

            <p v-if="!canSearchPeople && personSearchModal.term.trim()" class="feedback feedback--info">Informe ao menos 3 letras ou 3 números para consultar.</p>

            <div class="table-wrap accounts-payable-search-modal__table-wrap">
              <table class="data-table data-table--cadastro accounts-payable-search-modal__table">
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Tipo</th>
                    <th>CPF/CNPJ</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="accountsPayable.state.peopleLoading">
                    <td colspan="3">Pesquisando pessoas...</td>
                  </tr>
                  <tr v-else-if="personSearchResults.length === 0">
                    <td colspan="3">{{ personSearchEmptyMessage }}</td>
                  </tr>
                  <tr v-for="item in personSearchResults" :key="`${item.tipo_pessoa}-${item.entity_id}`" class="data-table__row accounts-payable-search-modal__result-row" @dblclick="selectPerson(item)">
                    <td>{{ item.nome }}</td>
                    <td>{{ formatPersonType(item.tipo_pessoa) }}</td>
                    <td>{{ formatDocument(item.cpf_cnpj) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="form-actions">
              <button class="ghost-button" type="button" @click="closePersonSearchModal">Fechar</button>
            </div>
          </div>
        </section>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type {
  AccountsPayable,
  AccountsPayableInstallmentInput,
  AccountsPayablePaymentInput,
  AccountsPayablePersonOption,
  AccountsPayablePersonType,
} from '@/models/accountsPayable'
import { useAccountsPayableController } from '@/controllers/useAccountsPayableController'
import { confirmActionAlert, errorAlert, infoAlert, successAlert } from '@/services/alertService'

type PaymentDraft = {
  valor_pago: number | null
  juros: number | null
  acrescimos: number | null
  desconto: number | null
}

const accountsPayable = useAccountsPayableController()
const route = useRoute()
const router = useRouter()

const isEdit = computed(() => Boolean(route.params.id))
const form = reactive({
  descricao: '',
  tipo_pessoa: null as AccountsPayablePersonType | null,
  cliente_id: null as number | null,
  usuario_id: null as number | null,
  fornecedor_id: null as number | null,
  observacao: '',
})
const selectedPerson = ref<AccountsPayablePersonOption | null>(null)
const pendingInstallments = reactive<AccountsPayableInstallmentInput[]>([])
const paymentDrafts = reactive<Record<number, PaymentDraft>>({})
const generatorOpen = ref(false)
const paymentModal = reactive({
  open: false,
  parcelaId: null as number | null,
})
const actionMenuParcelaId = ref<number | null>(null)
const personSearchModal = reactive({
  open: false,
  term: '',
  searched: false,
})
const generator = reactive({
  quantidade: 1,
  valor: 0,
  primeiroVencimento: '',
  mensal: true,
  manual: false,
})
const generatorPreview = reactive<AccountsPayableInstallmentInput[]>([])

const personSearchResults = computed(() => accountsPayable.state.peopleOptions)
const existingInstallments = computed(() => [...(accountsPayable.state.currentAccount?.parcelas ?? [])].sort((left, right) => (left.numero_parcela ?? 0) - (right.numero_parcela ?? 0)))
const selectedPersonLabel = computed(() => {
  if (!selectedPerson.value) return ''
  return `${selectedPerson.value.nome} • ${formatPersonType(selectedPerson.value.tipo_pessoa)}${selectedPerson.value.cpf_cnpj ? ` • ${formatDocument(selectedPerson.value.cpf_cnpj)}` : ''}`
})
const existingOpenAmount = computed(() => existingInstallments.value.reduce((total, item) => total + (item.saldo_pagar ?? 0), 0))
const pendingAmount = computed(() => pendingInstallments.reduce((total, item) => total + Number(item.valor_original || 0), 0))
const canSearchPeople = computed(() => hasMinimumSearchTerm(personSearchModal.term))
const personSearchEmptyMessage = computed(() => {
  if (!personSearchModal.searched || !personSearchModal.term.trim()) {
    return 'Informe ao menos 3 letras ou 3 números para consultar.'
  }

  if (!canSearchPeople.value) {
    return 'Informe ao menos 3 letras ou 3 números para consultar.'
  }

  return 'Nenhuma pessoa encontrada.'
})

onMounted(async () => {
  if (!isEdit.value) return
  try {
    await loadAccount(Number(route.params.id))
  } catch {
    await router.replace({ name: 'accounts-payable-list' })
  }
})

async function loadAccount(accountId: number) {
  await accountsPayable.loadAccount(accountId)
  hydrateForm(accountsPayable.state.currentAccount)
}

function hydrateForm(account: AccountsPayable | null) {
  if (!account) return
  form.descricao = account.descricao
  form.tipo_pessoa = account.tipo_pessoa
  form.cliente_id = account.cliente_id
  form.usuario_id = account.usuario_id
  form.fornecedor_id = account.fornecedor_id
  form.observacao = account.observacao ?? ''
  selectedPerson.value = {
    entity_id: account.pessoa_id,
    tipo_pessoa: account.tipo_pessoa,
    nome: account.pessoa_nome,
    cpf_cnpj: account.pessoa_cpf_cnpj,
  }
  syncPaymentDrafts(account)
}

function syncPaymentDrafts(account: AccountsPayable) {
  for (const parcela of account.parcelas) {
    paymentDrafts[parcela.parcela_id] = paymentDrafts[parcela.parcela_id] ?? {
      valor_pago: parcela.saldo_pagar,
      juros: 0,
      acrescimos: 0,
      desconto: 0,
    }
  }
}

function openPersonSearchModal() {
  personSearchModal.open = true
  personSearchModal.term = ''
  personSearchModal.searched = false
  accountsPayable.clearPeopleOptions()
}

function closePersonSearchModal() {
  personSearchModal.open = false
}

async function runPersonSearch() {
  personSearchModal.searched = true
  if (!canSearchPeople.value) {
    accountsPayable.clearPeopleOptions()
    return
  }

  try {
    await accountsPayable.fetchPeopleOptions(personSearchModal.term.trim())
  } catch {
    if (accountsPayable.state.error) {
      await errorAlert(accountsPayable.state.error)
    }
  }
}

function selectPerson(item: AccountsPayablePersonOption) {
  selectedPerson.value = item
  form.tipo_pessoa = item.tipo_pessoa
  form.cliente_id = item.tipo_pessoa === 'cliente' ? item.entity_id : null
  form.usuario_id = item.tipo_pessoa === 'funcionario' ? item.entity_id : null
  form.fornecedor_id = item.tipo_pessoa === 'fornecedor' ? item.entity_id : null
  closePersonSearchModal()
}

function openGenerator() {
  generatorOpen.value = true
  if (!generator.primeiroVencimento) {
    generator.primeiroVencimento = nextSuggestedDueDate()
  }
  regeneratePreview()
}

function regeneratePreview() {
  generatorPreview.splice(0, generatorPreview.length, ...buildGeneratedInstallments())
}

function buildGeneratedInstallments(): AccountsPayableInstallmentInput[] {
  const quantidade = Math.max(1, Number(generator.quantidade || 1))
  const valor = Number(generator.valor || 0)
  const firstDate = parseDateInput(generator.primeiroVencimento || nextSuggestedDueDate())

  const items: AccountsPayableInstallmentInput[] = []
  for (let index = 0; index < quantidade; index += 1) {
    const dueDate = generator.mensal ? addMonths(firstDate, index) : new Date(firstDate)
    items.push({
      numero_parcela: existingInstallments.value.length + pendingInstallments.length + index + 1,
      descricao: quantidade === 1 ? form.descricao || 'Parcela única' : `${form.descricao || 'Parcela'} ${String(index + 1).padStart(2, '0')}`,
      vencimento: formatDateInput(dueDate),
      valor_original: valor,
      acrescimos: 0,
      desconto: 0,
      observacao: null,
    })
  }

  return items
}

function confirmGenerator() {
  pendingInstallments.push(...generatorPreview.map((item) => ({ ...item })))
  generatorOpen.value = false
}

async function handleSubmit() {
  if (!selectedPerson.value || !form.tipo_pessoa) {
    await infoAlert('Selecione a pessoa vinculada antes de salvar.')
    return
  }

  const basePayload = {
    descricao: form.descricao.trim(),
    tipo_pessoa: form.tipo_pessoa,
    cliente_id: form.cliente_id,
    usuario_id: form.usuario_id,
    fornecedor_id: form.fornecedor_id,
    observacao: form.observacao.trim() || null,
  }

  try {
    if (!isEdit.value) {
      if (pendingInstallments.length === 0) {
        await infoAlert('Adicione ao menos uma parcela para lançar a conta a pagar.')
        return
      }
      await accountsPayable.submitAccount({ ...basePayload, parcelas: normalizePendingInstallments() })
      await successAlert('Conta a pagar cadastrada com sucesso.', 'create')
    } else {
      await accountsPayable.submitAccountUpdate(Number(route.params.id), basePayload)
      if (pendingInstallments.length > 0) {
        await accountsPayable.appendInstallments(Number(route.params.id), normalizePendingInstallments())
      }
      await successAlert('Conta a pagar atualizada com sucesso.', 'update')
    }
    pendingInstallments.splice(0, pendingInstallments.length)
    await router.push({ name: 'accounts-payable-list' })
  } catch {
    if (accountsPayable.state.error) {
      await errorAlert(accountsPayable.state.error)
    }
  }
}

async function handleSettleInstallment(parcelaId: number, saldoPagar: number) {
  actionMenuParcelaId.value = null
  await submitPayment(parcelaId, { valor_pago: saldoPagar, juros: 0, acrescimos: 0, desconto: 0 })
}

async function handleRemovePayments(parcelaId: number) {
  actionMenuParcelaId.value = null
  if (!await confirmActionAlert('Remover pagamentos?', 'Todos os pagamentos registrados nesta parcela serão removidos.', 'Remover')) return
  try {
    await accountsPayable.removeInstallmentPayments(parcelaId)
    await successAlert('Pagamentos removidos com sucesso.', 'update')
    await loadAccount(Number(route.params.id))
  } catch {
    if (accountsPayable.state.error) await errorAlert(accountsPayable.state.error)
  }
}

async function handleDeleteInstallment(parcelaId: number) {
  actionMenuParcelaId.value = null
  if (!await confirmActionAlert('Excluir parcela?', 'A parcela e seus pagamentos serão excluídos permanentemente.', 'Excluir')) return
  try {
    await accountsPayable.removeInstallment(parcelaId)
    await successAlert('Parcela excluída com sucesso.', 'delete')
    await loadAccount(Number(route.params.id))
  } catch {
    if (accountsPayable.state.error) await errorAlert(accountsPayable.state.error)
  }
}

function toggleActionMenu(parcelaId: number) {
  actionMenuParcelaId.value = actionMenuParcelaId.value === parcelaId ? null : parcelaId
}

function openPaymentModal(parcelaId: number) {
  const parcela = existingInstallments.value.find((item) => item.parcela_id === parcelaId)
  paymentDrafts[parcelaId] = paymentDrafts[parcelaId] ?? {
    valor_pago: parcela?.saldo_pagar ?? 0,
    juros: 0,
    acrescimos: 0,
    desconto: 0,
  }
  actionMenuParcelaId.value = null
  paymentModal.parcelaId = parcelaId
  paymentModal.open = true
}

function closePaymentModal() {
  paymentModal.open = false
  paymentModal.parcelaId = null
}

async function confirmPayment() {
  if (paymentModal.parcelaId === null) return
  if (await handleRegisterPayment(paymentModal.parcelaId)) {
    closePaymentModal()
  }
}

async function handleRegisterPayment(parcelaId: number): Promise<boolean> {
  const draft = paymentDrafts[parcelaId]
  return submitPayment(parcelaId, {
    valor_pago: draft.valor_pago,
    juros: draft.juros,
    acrescimos: draft.acrescimos,
    desconto: draft.desconto,
  })
}

async function submitPayment(parcelaId: number, payload: AccountsPayablePaymentInput): Promise<boolean> {
  try {
    await accountsPayable.settleInstallment(parcelaId, payload)
    await successAlert('Pagamento registrado com sucesso.', 'update')
    await loadAccount(Number(route.params.id))
    return true
  } catch {
    if (accountsPayable.state.error) {
      await errorAlert(accountsPayable.state.error)
    }
    return false
  }
}

function normalizePendingInstallments(): AccountsPayableInstallmentInput[] {
  return pendingInstallments.map((item, index) => ({
    numero_parcela: existingInstallments.value.length + index + 1,
    descricao: item.descricao?.trim() || null,
    data_referencia_inicial: null,
    data_referencia_final: null,
    vencimento: item.vencimento,
    valor_original: Number(item.valor_original || 0),
    acrescimos: Number(item.acrescimos || 0),
    desconto: Number(item.desconto || 0),
    observacao: item.observacao?.trim() || null,
  }))
}

function formatCurrency(value: number | null) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value ?? 0)
}

function formatTableAmount(value: number | null) {
  return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value ?? 0)
}

function formatShortDate(value: string | null) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit' }).format(new Date(`${value}T00:00:00`))
}

function formatPersonType(value: AccountsPayablePersonType) {
  const labels: Record<AccountsPayablePersonType, string> = {
    cliente: 'Cliente',
    fornecedor: 'Fornecedor',
    funcionario: 'Funcionário',
  }
  return labels[value]
}

function formatDocument(value: string | null) {
  const digits = (value ?? '').replace(/\D/g, '')
  if (!digits) return '-'
  if (digits.length <= 11) {
    return digits.slice(0, 11).replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2')
  }
  return digits.slice(0, 14).replace(/(\d{2})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1/$2').replace(/(\d{4})(\d{1,2})$/, '$1-$2')
}

function calculateInstallmentTotal(item: AccountsPayableInstallmentInput) {
  const valor = Number(item.valor_original || 0)
  const juros = Number(item.acrescimos || 0)
  const desconto = Number(item.desconto || 0)
  return Math.max(valor + juros - desconto, 0)
}

function nextSuggestedDueDate() {
  return formatDateInput(addMonths(new Date(), 1))
}

function parseDateInput(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, (month || 1) - 1, day || 1)
}

function formatDateInput(value: Date) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function addMonths(value: Date, months: number) {
  const date = new Date(value)
  const currentDay = date.getDate()
  date.setDate(1)
  date.setMonth(date.getMonth() + months)
  const daysInMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
  date.setDate(Math.min(currentDay, daysInMonth))
  return date
}

function hasMinimumSearchTerm(value: string) {
  const trimmed = value.trim()
  const numeric = trimmed.replace(/\D/g, '')
  return trimmed.length >= 3 || numeric.length >= 3
}
</script>

<style scoped>
.accounts-payable-form {
  display: grid;
  gap: 1rem;
}

.accounts-payable-card {
  border: 1px solid rgba(38, 57, 77, 0.08);
  border-radius: 3px;
  background: #fff;
  padding: 1rem;
  display: grid;
  gap: 1rem;
}

.accounts-payable-card__header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.accounts-payable-card__title {
  margin: 0;
}

.accounts-payable-card__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.accounts-payable-person-picker {
  align-items: stretch;
}

.accounts-payable-person-picker__field {
  flex: 1 1 auto;
}

.accounts-payable-person-picker__button {
  min-width: 44px;
  padding-inline: 0;
}

.accounts-payable-person-picker__icon {
  width: 1rem;
  height: 1rem;
}

.accounts-payable-table-wrap {
  overflow-x: auto;
}

.accounts-payable-table-wrap:has(.accounts-payable-installments-table) {
  overflow-x: visible;
}

.accounts-payable-installments-table {
  min-width: 0;
  table-layout: fixed;
  width: 100%;
}

.accounts-payable-installments-table th,
.accounts-payable-installments-table td {
  overflow: hidden;
  padding-inline: 0.4rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.accounts-payable-installments-table th:first-child,
.accounts-payable-installments-table td:first-child {
  width: 44px;
}

.accounts-payable-installments-table th:nth-child(2),
.accounts-payable-installments-table td:nth-child(2) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 30%;
}

.accounts-payable-installments-table th:nth-child(3),
.accounts-payable-installments-table td:nth-child(3) {
  width: 62px;
}

.accounts-payable-installments-table th:nth-child(n + 4):nth-child(-n + 9),
.accounts-payable-installments-table td:nth-child(n + 4):nth-child(-n + 9) {
  width: 68px;
}

.accounts-payable-installments-table th:nth-last-child(2),
.accounts-payable-installments-table td:nth-last-child(2) {
  text-align: right;
  width: 68px;
}

.accounts-payable-installments-table th:last-child,
.accounts-payable-installments-table td:last-child {
  text-align: right;
  width: 48px;
}

.payment-editor {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  justify-content: flex-end;
  position: relative;
}

.accounts-payable-installments-table td.accounts-payable-actions-cell {
  overflow: visible;
}

.accounts-payable-actions-menu__trigger {
  padding: 0.35rem;
}

.accounts-payable-actions-menu__trigger svg {
  height: 1.25rem;
  width: 1.25rem;
}

.accounts-payable-actions-menu {
  background: #fff;
  border: 1px solid rgba(38, 57, 77, 0.14);
  border-radius: 6px;
  box-shadow: 0 8px 22px rgba(18, 27, 34, 0.16);
  display: grid;
  min-width: 120px;
  overflow: hidden;
  position: absolute;
  right: 0;
  bottom: calc(100% + 0.3rem);
  top: auto;
  z-index: 50;
}

.accounts-payable-actions-menu button {
  background: transparent;
  border: 0;
  color: #26394d;
  cursor: pointer;
  padding: 0.65rem 0.8rem;
  text-align: left;
}

.accounts-payable-actions-menu button:hover:not(:disabled) {
  background: rgba(249, 115, 22, 0.1);
}

.accounts-payable-actions-menu button:disabled {
  color: #94a3b8;
  cursor: not-allowed;
}

.accounts-payable-actions-menu__delete {
  color: #b42318 !important;
}

.accounts-payable-generator-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(18, 27, 34, 0.48);
  display: grid;
  place-items: center;
  padding: 1rem;
  z-index: 30;
}

.accounts-payable-generator-modal {
  width: min(1080px, 100%);
  max-height: 90vh;
  overflow: auto;
  background: #fffaf6;
  border-radius: 3px;
  padding: 1rem;
  display: grid;
  gap: 1rem;
}

.accounts-payable-payment-modal {
  background: #fffaf6;
  border-radius: 3px;
  display: grid;
  gap: 1rem;
  padding: 1rem;
  width: min(560px, 100%);
}

.accounts-payable-payment-modal__grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.accounts-payable-generator-modal__header,
.accounts-payable-generator-modal__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.accounts-payable-generator-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.accounts-payable-generator-toggle {
  align-self: end;
}

.accounts-payable-search-modal {
  width: min(960px, 100%);
}

.accounts-payable-search-modal__content {
  display: grid;
  gap: 0.75rem;
}

.accounts-payable-search-modal__filters {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: end;
}

.accounts-payable-search-modal__search-button {
  min-width: 120px;
}

.accounts-payable-search-modal__table-wrap {
  max-height: 420px;
}

.accounts-payable-search-modal__result-row {
  cursor: pointer;
}

.accounts-payable-search-modal__result-row:hover td {
  background: rgba(249, 115, 22, 0.08);
}

@media (max-width: 960px) {
  .accounts-payable-card__grid,
  .accounts-payable-generator-grid,
  .accounts-payable-payment-modal__grid,
  .accounts-payable-search-modal__filters {
    grid-template-columns: 1fr;
  }

  .accounts-payable-card__header-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
