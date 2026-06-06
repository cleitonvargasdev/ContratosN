<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Financeiro</p>
        <h2 class="panel__title">Contas à Pagar</h2>
      </div>
      <RouterLink class="primary-button primary-button--compact primary-button--accent-soft" to="/contas-pagar/novo">Nova conta</RouterLink>
    </header>

    <div class="filters-grid filters-grid--accounts-payable">
      <div class="accounts-payable-status-toggle" role="group" aria-label="Filtro de status">
        <button class="accounts-payable-status-toggle__option" :class="!quitadoValue ? 'accounts-payable-status-toggle__option--active' : ''" type="button" @click="selectQuitado(false)">Aberto</button>
        <button class="accounts-payable-status-toggle__option accounts-payable-status-toggle__option--quitado" :class="quitadoValue ? 'accounts-payable-status-toggle__option--active' : ''" type="button" @click="selectQuitado(true)">Quitado</button>
      </div>
      <input v-model="draft.pessoa_query" class="field" placeholder="Nome, CPF/CNPJ ou descrição" type="text" @keydown.enter.prevent="applyFilters" />
      <select v-model="draft.tipo_pessoa" class="field" @change="applyFilters">
        <option value="">Todos os tipos</option>
        <option value="cliente">Cliente</option>
        <option value="fornecedor">Fornecedor</option>
        <option value="funcionario">Funcionário</option>
      </select>
      <label class="accounts-payable-date-field">
        <span>Venc. inicial</span>
        <input v-model="draft.data_vencimento_inicial" class="field" type="date" @keydown.enter.prevent="applyFilters" />
      </label>
      <label class="accounts-payable-date-field">
        <span>Venc. final</span>
        <input v-model="draft.data_vencimento_final" class="field" type="date" @keydown.enter.prevent="applyFilters" />
      </label>
      <button class="secondary-button accounts-payable-filter-button" type="button" @click="applyFilters">Filtrar</button>
    </div>

    <p v-if="accountsPayable.state.error" class="feedback feedback--error">{{ accountsPayable.state.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>Pessoa</th>
            <th>CPF/CNPJ</th>
            <th>Tipo</th>
            <th>Próx. vencimento</th>
            <th>Parcelas</th>
            <th>Saldo a pagar</th>
            <th>Status</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="accountsPayable.state.loading"><td colspan="8">Carregando contas a pagar...</td></tr>
          <tr v-else-if="accountsPayable.state.result.items.length === 0"><td colspan="8">Nenhuma conta a pagar encontrada.</td></tr>
          <tr v-for="item in accountsPayable.state.result.items" :key="item.conta_pagar_id" class="data-table__row" @dblclick="router.push({ name: 'accounts-payable-edit', params: { id: item.conta_pagar_id } })">
            <td>
              <div class="accounts-payable-person-cell">
                <strong>{{ item.pessoa_nome }}</strong>
                <small>{{ item.descricao }}</small>
              </div>
            </td>
            <td>{{ item.pessoa_cpf_cnpj || '-' }}</td>
            <td>
              <span class="pill pill--neutral">{{ formatPersonType(item.tipo_pessoa) }}</span>
            </td>
            <td>{{ formatDate(item.proximo_vencimento) }}</td>
            <td>{{ item.quantidade_parcelas_abertas }}/{{ item.quantidade_parcelas }}</td>
            <td>{{ formatCurrency(item.saldo_pagar) }}</td>
            <td>
              <span :class="['pill', item.quitado ? 'pill--success' : 'pill--warning']">{{ item.quitado ? 'Quitado' : 'Em aberto' }}</span>
            </td>
            <td class="actions-cell">
              <button class="icon-action" type="button" @click="router.push({ name: 'accounts-payable-edit', params: { id: item.conta_pagar_id } })">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/></svg>
              </button>
              <button class="icon-action icon-action--danger" type="button" @click="handleDelete(item.conta_pagar_id)">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer class="pagination-compact">
      <div class="pagination-compact__meta">
        <label class="pagination-compact__label" for="accounts-payable-page-size">Itens por pagina:</label>
        <select id="accounts-payable-page-size" v-model="pageSizeValue" class="pagination-compact__select" @change="changePageSize">
          <option value="8">8</option>
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="50">50</option>
        </select>
      </div>
      <div class="pagination-compact__status">{{ rangeLabel }}</div>
      <div class="pagination-compact__actions">
        <button class="pagination-compact__button" type="button" :disabled="accountsPayable.state.result.page <= 1" @click="handlePage(1)">&#171;</button>
        <button class="pagination-compact__button" type="button" :disabled="accountsPayable.state.result.page <= 1" @click="handlePage(accountsPayable.state.result.page - 1)">&#8249;</button>
        <button class="pagination-compact__button" type="button" :disabled="accountsPayable.state.result.page >= totalPages" @click="handlePage(accountsPayable.state.result.page + 1)">&#8250;</button>
        <button class="pagination-compact__button" type="button" :disabled="accountsPayable.state.result.page >= totalPages" @click="handlePage(totalPages)">&#187;</button>
      </div>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import type { AccountsPayablePersonType } from '@/models/accountsPayable'
import { useAccountsPayableController } from '@/controllers/useAccountsPayableController'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'

const accountsPayable = useAccountsPayableController()
const router = useRouter()

const draft = reactive({
  pessoa_query: '',
  tipo_pessoa: '',
  data_vencimento_inicial: accountsPayable.state.filters.data_vencimento_inicial ?? '',
  data_vencimento_final: accountsPayable.state.filters.data_vencimento_final ?? '',
})
const quitadoValue = ref(Boolean(accountsPayable.state.filters.quitado))
const pageSizeValue = ref(String(accountsPayable.state.result.page_size))

const totalPages = computed(() => Math.max(1, Math.ceil(accountsPayable.state.result.total / accountsPayable.state.result.page_size)))
const rangeLabel = computed(() => {
  if (accountsPayable.state.result.total === 0) return '0-0 de 0'
  const start = (accountsPayable.state.result.page - 1) * accountsPayable.state.result.page_size + 1
  const end = Math.min(accountsPayable.state.result.page * accountsPayable.state.result.page_size, accountsPayable.state.result.total)
  return `${start}-${end} de ${accountsPayable.state.result.total}`
})

onMounted(() => {
  void accountsPayable.fetchAccountsPayable()
})

function applyFilters() {
  accountsPayable.patchFilters({
    page: 1,
    quitado: quitadoValue.value,
    pessoa_query: draft.pessoa_query.trim() || undefined,
    tipo_pessoa: (draft.tipo_pessoa || undefined) as AccountsPayablePersonType | undefined,
    data_vencimento_inicial: draft.data_vencimento_inicial || undefined,
    data_vencimento_final: draft.data_vencimento_final || undefined,
  })
  void accountsPayable.fetchAccountsPayable()
}

function selectQuitado(value: boolean) {
  quitadoValue.value = value
  applyFilters()
}

function handlePage(page: number) {
  accountsPayable.patchFilters({ page })
  void accountsPayable.fetchAccountsPayable()
}

function changePageSize() {
  accountsPayable.patchFilters({ page: 1, page_size: Number(pageSizeValue.value) })
  void accountsPayable.fetchAccountsPayable()
}

async function handleDelete(accountId: number) {
  if (!(await confirmDeleteAlert())) return
  try {
    await accountsPayable.removeAccount(accountId)
    await accountsPayable.fetchAccountsPayable()
    await successAlert('Conta a pagar excluída com sucesso.', 'delete')
  } catch {
    if (accountsPayable.state.error) {
      await errorAlert(accountsPayable.state.error)
    }
  }
}

function formatCurrency(value: number | null) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value ?? 0)
}

function formatDate(value: string | null) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('pt-BR').format(new Date(`${value}T00:00:00`))
}

function formatPersonType(value: AccountsPayablePersonType) {
  const labels: Record<AccountsPayablePersonType, string> = {
    cliente: 'Cliente',
    fornecedor: 'Fornecedor',
    funcionario: 'Funcionário',
  }
  return labels[value]
}
</script>

<style scoped>
.filters-grid--accounts-payable {
  grid-template-columns: minmax(12rem, 1fr) minmax(14rem, 1.35fr) minmax(10rem, 0.9fr) minmax(10rem, 0.9fr) minmax(10rem, 0.9fr) minmax(6.25rem, 0.6fr);
  align-items: end;
}

.accounts-payable-status-toggle {
  display: inline-grid;
  grid-template-columns: 1fr 1fr;
  min-height: 34px;
  border: 1px solid rgba(249, 115, 22, 0.22);
  border-radius: 3px;
  overflow: hidden;
  background: rgba(249, 115, 22, 0.09);
  align-self: end;
}

.accounts-payable-status-toggle__option {
  border: 0;
  padding: 0 14px;
  background: transparent;
  color: #1b2730;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  cursor: pointer;
  transition: background-color 140ms ease, color 140ms ease;
}

.accounts-payable-status-toggle__option + .accounts-payable-status-toggle__option {
  border-left: 1px solid rgba(249, 115, 22, 0.18);
}

.accounts-payable-status-toggle__option--active {
  background: rgba(31, 157, 104, 0.14);
  color: #1b7f56;
}

.accounts-payable-status-toggle__option--quitado.accounts-payable-status-toggle__option--active {
  background: rgba(31, 157, 104, 0.14);
  color: #1b7f56;
}

.accounts-payable-status-toggle__option--quitado {
  font-size: 11px;
}

.accounts-payable-date-field {
  display: grid;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #5f6d78;
  align-self: end;
}

.accounts-payable-filter-button {
  width: 100%;
  min-width: 0;
  padding-inline: 10px;
  justify-self: stretch;
}

.accounts-payable-person-cell {
  display: grid;
  gap: 0.2rem;
}

.accounts-payable-person-cell small {
  color: #61788e;
}

@media (max-width: 1180px) {
  .filters-grid--accounts-payable {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .filters-grid--accounts-payable {
    grid-template-columns: 1fr;
  }

  .accounts-payable-status-toggle {
    width: 100%;
  }
}
</style>