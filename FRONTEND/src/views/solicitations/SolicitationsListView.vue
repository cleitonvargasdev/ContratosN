<template>
  <section class="solicitations-page">
    <section class="panel solicitations-panel">
      <header class="panel__header solicitations-panel__header">
        <div>
          <p class="eyebrow">Solicitações</p>
          <h2 class="panel__title">Lista operacional</h2>
        </div>
        <div class="summary-chip">
          <strong>{{ solicitations.state.pendingCount }}</strong>
          <span>Em aberto</span>
        </div>
      </header>

      <div class="solicitations-filters">
        <label class="field-group">
          <span>Busca</span>
          <input v-model="filters.termo" class="field" type="text" placeholder="Nome, telefone ou CPF/CNPJ" @keyup.enter="handleApply" />
        </label>

        <label class="field-group">
          <span>Status</span>
          <select v-model="filters.status" class="field">
            <option value="PENDENTE">Pendentes</option>
            <option value="APROVADO">Aprovadas</option>
            <option value="REJEITADO">Rejeitadas</option>
            <option value="">Todos</option>
          </select>
        </label>

        <label class="field-group">
          <span>Itens por página</span>
          <select v-model.number="pageSize" class="field" @change="handlePageSizeChange">
            <option :value="8">8</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
        </label>

        <div class="solicitations-filters__actions">
          <button class="primary-button primary-button--success" type="button" @click="handleApply">Atualizar</button>
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table data-table--cadastro solicitation-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Solicitação</th>
              <th>Documento / Frequência</th>
              <th>Valor / Parcelas</th>
              <th>Status</th>
              <th class="actions-column">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="solicitations.state.loading">
              <td colspan="6">Carregando solicitações...</td>
            </tr>
            <tr v-else-if="solicitations.state.result.items.length === 0">
              <td colspan="6">Nenhuma solicitação encontrada.</td>
            </tr>
            <tr v-for="item in solicitations.state.result.items" :key="item.id" class="data-table__row solicitation-row">
              <td>{{ item.id }}</td>
              <td>
                <div class="two-line-cell">
                  <strong>{{ item.cliente_nome || item.nome_informado || '-' }}</strong>
                  <span>{{ formatPhone(item.telefone) }} • {{ formatDateTime(item.datahora_solicitacao) }}</span>
                </div>
              </td>
              <td>
                <div class="two-line-cell">
                  <strong>{{ formatDocument(item.cpf_cnpj) }}</strong>
                  <span>{{ item.frequencia_pagamento || '-' }}</span>
                </div>
              </td>
              <td>
                <div class="two-line-cell">
                  <strong>{{ formatCurrency(item.valor_pretendido) }}</strong>
                  <span>{{ (item.numero_parcelas ?? '-') + ' parcelas' }}</span>
                </div>
              </td>
              <td>
                <div class="two-line-cell two-line-cell--badges">
                  <span :class="['pill', solicitationClientPillClass(item.cliente_id)]">{{ item.cliente_id ? 'Cliente' : 'Não Cliente' }}</span>
                  <span :class="['pill', solicitationStatusPillClass(item.status)]">{{ item.status }}</span>
                </div>
              </td>
              <td class="actions-cell">
                <div class="solicitation-actions">
                  <button
                    v-if="!item.cliente_id"
                    class="icon-action icon-action--success"
                    type="button"
                    title="Cadastrar cliente"
                    aria-label="Cadastrar cliente"
                    @click="handleCreateClient(item.id)"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M15 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4Zm-6 0c2.21 0 4-1.79 4-4S11.21 4 9 4 5 5.79 5 8s1.79 4 4 4Zm0 2c-2.67 0-8 1.34-8 4v2h10v-2c0-1.13.39-2.17 1.02-3.02C11.06 14.36 9.86 14 9 14Zm6 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.98 1.97 3.45V20h8v-2c0-2.66-5.33-4-8-4Z" fill="currentColor"/>
                    </svg>
                  </button>
                  <button
                    v-if="item.cliente_id"
                    class="icon-action icon-action--message"
                    type="button"
                    title="Gerar contrato"
                    aria-label="Gerar contrato"
                    @click="handleCreateContract(item.id)"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M7 3.75A1.75 1.75 0 0 0 5.25 5.5v13A1.75 1.75 0 0 0 7 20.25h10a1.75 1.75 0 0 0 1.75-1.75v-9.19a1.75 1.75 0 0 0-.51-1.24l-3.56-3.56A1.75 1.75 0 0 0 13.44 4H7Zm6.25 1.9 3.1 3.1h-2.35a.75.75 0 0 1-.75-.75V5.65ZM12 10.25a.75.75 0 0 1 .75.75v1.25H14a.75.75 0 0 1 0 1.5h-1.25V15a.75.75 0 0 1-1.5 0v-1.25H10a.75.75 0 0 1 0-1.5h1.25V11a.75.75 0 0 1 .75-.75Z" fill="currentColor"/>
                    </svg>
                  </button>
                  <button
                    v-if="item.status === 'PENDENTE'"
                    class="icon-action icon-action--pending"
                    type="button"
                    title="Marcar como rejeitado"
                    aria-label="Marcar como rejeitado"
                    @click="handleReject(item.id)"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M18.3 5.71 12 12l6.3 6.29-1.41 1.42L10.59 13.4 4.29 19.71 2.88 18.3 9.17 12 2.88 5.71 4.29 4.29l6.3 6.3 6.29-6.3z" fill="currentColor"/>
                    </svg>
                  </button>
                  <button
                    v-if="item.contrato_id"
                    class="icon-action"
                    type="button"
                    title="Abrir contrato"
                    aria-label="Abrir contrato"
                    @click="handleOpenExistingContract(item.contrato_id)"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M12 5c-7 0-10 7-10 7s3 7 10 7 10-7 10-7-3-7-10-7Zm0 11a4 4 0 1 1 0-8 4 4 0 0 1 0 8Z" fill="currentColor"/>
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
          <label class="pagination-compact__label" for="solicitations-page-size">Itens por pagina:</label>
          <select id="solicitations-page-size" v-model.number="pageSize" class="pagination-compact__select" @change="handlePageSizeChange">
            <option :value="8">8</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
        </div>

        <div class="pagination-compact__status">{{ rangeLabel }}</div>

        <div class="pagination-compact__actions">
          <button class="pagination-compact__button" type="button" :disabled="currentPage <= 1" @click="handlePageChange(1)">&#171;</button>
          <button class="pagination-compact__button" type="button" :disabled="currentPage <= 1" @click="handlePageChange(currentPage - 1)">&#8249;</button>
          <button class="pagination-compact__button" type="button" :disabled="currentPage >= totalPages" @click="handlePageChange(currentPage + 1)">&#8250;</button>
          <button class="pagination-compact__button" type="button" :disabled="currentPage >= totalPages" @click="handlePageChange(totalPages)">&#187;</button>
        </div>
      </footer>

      <p v-if="solicitations.state.error" class="feedback feedback--error">{{ solicitations.state.error }}</p>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthController } from '@/controllers/useAuthController'
import { useSolicitationsController } from '@/controllers/useSolicitationsController'
import { confirmActionAlert, errorAlert, successAlert } from '@/services/alertService'
import { getSolicitationById, rejectSolicitation } from '@/services/solicitationService'

const auth = useAuthController()
const router = useRouter()
const solicitations = useSolicitationsController()

const filters = reactive({
  termo: '',
  status: 'PENDENTE',
})

const pageSize = ref(8)

const currentPage = computed(() => solicitations.state.result.page)
const totalPages = computed(() => Math.max(1, Math.ceil(solicitations.state.result.total / solicitations.state.result.page_size)))
const rangeLabel = computed(() => {
  if (solicitations.state.result.total === 0) {
    return '0-0 de 0'
  }

  const start = (solicitations.state.result.page - 1) * solicitations.state.result.page_size + 1
  const end = Math.min(solicitations.state.result.page * solicitations.state.result.page_size, solicitations.state.result.total)
  return `${start}-${end} de ${solicitations.state.result.total}`
})

onMounted(async () => {
  if (!auth.hasPermission('solicitacoes', 'read')) {
    await router.replace({ name: 'dashboard' })
    return
  }

  await refreshList(1)
})

async function refreshList(page = currentPage.value) {
  try {
    solicitations.patchFilters({ ...filters, page, page_size: pageSize.value })
    await Promise.all([solicitations.fetchSolicitations(), solicitations.fetchPendingCount()])
  } catch {
    if (solicitations.state.error) {
      await errorAlert(solicitations.state.error)
    }
  }
}

async function handleApply() {
  await refreshList(1)
}

async function handlePageChange(page: number) {
  await refreshList(page)
}

async function handlePageSizeChange() {
  await refreshList(1)
}

async function handleCreateClient(solicitationId: number) {
  try {
    await getSolicitationById(solicitationId)
    void router.push({
      name: 'clients-create',
      query: {
        solicitacao_id: String(solicitationId),
        gerar_contrato: '1',
      },
    })
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao abrir a solicitação.')
  }
}

async function handleCreateContract(solicitationId: number) {
  try {
    const detail = await getSolicitationById(solicitationId)
    const clientId = detail.cliente_existente?.clientes_id ?? detail.cliente_id
    void router.push({
      name: 'contracts-create',
      query: {
        solicitacao_id: String(solicitationId),
        ...(clientId ? { cliente_id: String(clientId) } : {}),
      },
    })
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao abrir a solicitação.')
  }
}

function handleOpenExistingContract(contractId: number) {
  void router.push({
    name: 'contracts-edit',
    params: { id: contractId },
  })
}

async function handleReject(solicitationId: number) {
  const confirmed = await confirmActionAlert(
    'Marcar como rejeitado?',
    'Essa solicitação sairá da fila de pendentes e ficará marcada como rejeitada.',
    'Rejeitar',
  )

  if (!confirmed) {
    return
  }

  try {
    await rejectSolicitation(solicitationId)
    await successAlert('Solicitação marcada como rejeitada.', 'update')
    await refreshList(currentPage.value)
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao rejeitar a solicitação.')
  }
}

function normalizeStatus(value: string) {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'pendente'
}

function solicitationStatusPillClass(status: string) {
  const normalized = normalizeStatus(status)
  if (normalized === 'aprovado') return 'pill--success'
  if (normalized === 'rejeitado') return 'pill--danger'
  return 'pill--pending'
}

function solicitationClientPillClass(clientId: number | null) {
  return clientId ? 'pill--success' : 'pill--danger'
}

function formatCurrency(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return '-'
  }

  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

function formatDateTime(value: string | null) {
  if (!value) {
    return '-'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date)
}

function formatDocument(value: string | null) {
  if (!value) {
    return '-'
  }

  const digits = value.replace(/\D/g, '')
  if (digits.length === 11) {
    return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
  }
  if (digits.length === 14) {
    return digits.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
  }

  return value
}

function formatPhone(value: string | null) {
  if (!value) {
    return '-'
  }

  const digits = value.replace(/\D/g, '')
  if (digits.length === 11) {
    return digits.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3')
  }
  if (digits.length === 10) {
    return digits.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3')
  }

  return value
}
</script>

<style scoped>
.solicitations-page {
  display: grid;
}

.solicitations-panel {
  display: grid;
  gap: 16px;
}

.solicitations-panel__header {
  align-items: flex-start;
}

.solicitations-panel :deep(.field) {
  border-radius: 3px;
}

.solicitations-filters {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1.8fr) minmax(180px, 0.7fr) auto;
}

.solicitations-filters__actions {
  display: flex;
  align-items: flex-end;
}


.solicitation-table :deep(td),
.solicitation-table :deep(th) {
  vertical-align: middle;
}

.solicitation-row td {
  background: transparent;
}

.two-line-cell {
  display: grid;
  gap: 4px;
}

.two-line-cell strong {
  color: #24303b;
  font-size: 13px;
}

.two-line-cell span {
  color: var(--text-muted);
  font-size: 12px;
}

.two-line-cell--badges {
  gap: 6px;
}

.pill--pending {
  background: rgba(249, 115, 22, 0.14);
  color: #c86718;
}

.solicitation-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.icon-action--success {
  background: rgba(31, 157, 104, 0.12);
  color: #1f9d68;
}

.icon-action--success:hover {
  background: rgba(31, 157, 104, 0.2);
}

.icon-action--pending {
  background: rgba(249, 115, 22, 0.12);
  color: #c86718;
}

.icon-action--pending:hover {
  background: rgba(249, 115, 22, 0.2);
}

@media (max-width: 860px) {
  .solicitations-filters {
    grid-template-columns: 1fr 1fr auto;
  }
}

@media (max-width: 640px) {
  .solicitations-filters {
    grid-template-columns: 1fr;
  }

  .solicitations-filters__actions {
    align-items: stretch;
  }
}
</style>