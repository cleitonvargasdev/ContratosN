<template>
  <section class="solicitations-page">
    <section class="panel solicitations-panel">
      <header class="panel__header solicitations-panel__header">
        <div>
          <h2 class="panel__title">Lista de Solicitações</h2>
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

        <div class="solicitations-filters__actions">
          <button class="primary-button primary-button--success" type="button" @click="handleApply">Atualizar</button>
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table data-table--cadastro solicitation-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>DT/Hora</th>
              <th>Nome</th>
              <th>Telefone</th>
              <th>Documento</th>
              <th>Valor-Parcelas</th>
              <th>Tipo</th>
              <th>Situação</th>
              <th class="actions-column">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="solicitations.state.loading">
              <td colspan="9">Carregando solicitações...</td>
            </tr>
            <tr v-else-if="solicitations.state.result.items.length === 0">
              <td colspan="9">Nenhuma solicitação encontrada.</td>
            </tr>
            <tr v-for="item in solicitations.state.result.items" :key="item.id" class="data-table__row solicitation-row">
              <td>{{ item.id }}</td>
              <td>{{ formatDateTime(item.datahora_solicitacao) }}</td>
              <td>
                <span :class="['solicitation-name-chip', item.cliente_id ? 'solicitation-name-chip--client' : 'solicitation-name-chip--lead']">
                  {{ item.cliente_nome || item.nome_informado || '-' }}
                </span>
              </td>
              <td>{{ formatPhone(item.telefone) }}</td>
              <td>{{ formatDocument(item.cpf_cnpj) }}</td>
              <td>{{ formatValueInstallments(item.valor_pretendido, item.numero_parcelas) }}</td>
              <td>{{ formatType(item.frequencia_pagamento) }}</td>
              <td>
                <span :class="['solicitation-status-chip', `solicitation-status-chip--${normalizeStatus(item.status)}`]">
                  {{ formatStatus(item.status) }}
                </span>
              </td>
              <td class="actions-cell">
                <div class="solicitation-actions" @keydown.esc="closeActionsMenu">
                  <button
                    class="row-menu-button"
                    type="button"
                    title="Abrir ações"
                    aria-label="Abrir ações"
                    aria-haspopup="menu"
                    :aria-expanded="activeMenuId === item.id"
                    @click.stop="toggleActionsMenu(item, $event)"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M12 7a1.75 1.75 0 1 0 0-3.5A1.75 1.75 0 0 0 12 7Zm0 6.75a1.75 1.75 0 1 0 0-3.5 1.75 1.75 0 0 0 0 3.5Zm0 6.75a1.75 1.75 0 1 0 0-3.5 1.75 1.75 0 0 0 0 3.5Z" fill="currentColor"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <Teleport to="body">
        <div v-if="activeMenuId !== null" class="row-actions-menu" :style="menuStyle" role="menu" @click.stop>
          <button
            v-for="action in activeMenuActions"
            :key="action.key"
            class="row-actions-menu__item"
            :class="`row-actions-menu__item--${action.tone}`"
            type="button"
            role="menuitem"
            @click="action.run()"
          >
            {{ action.label }}
          </button>

          <span v-if="activeMenuActions.length === 0" class="row-actions-menu__empty">
            Nenhuma ação disponível
          </span>
        </div>
      </Teleport>

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
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthController } from '@/controllers/useAuthController'
import { useSolicitationsController } from '@/controllers/useSolicitationsController'
import { confirmActionAlert, errorAlert, successAlert } from '@/services/alertService'
import { getSolicitationById, rejectSolicitation } from '@/services/solicitationService'
import type { Solicitation } from '@/models/solicitation'

const auth = useAuthController()
const router = useRouter()
const solicitations = useSolicitationsController()

const filters = reactive({
  termo: '',
  status: 'PENDENTE',
})

const pageSize = ref(8)
const activeMenuId = ref<number | null>(null)
const activeMenuActions = ref<ReturnType<typeof getRowActions>>([])
const menuStyle = ref<Record<string, string>>({})

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
  document.addEventListener('click', handleDocumentClick)
  window.addEventListener('resize', closeActionsMenu)
  window.addEventListener('scroll', closeActionsMenu, true)

  if (!auth.hasPermission('solicitacoes', 'read')) {
    await router.replace({ name: 'dashboard' })
    return
  }

  await refreshList(1)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
  window.removeEventListener('resize', closeActionsMenu)
  window.removeEventListener('scroll', closeActionsMenu, true)
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
  closeActionsMenu()
  await refreshList(1)
}

async function handlePageChange(page: number) {
  closeActionsMenu()
  await refreshList(page)
}

async function handlePageSizeChange() {
  closeActionsMenu()
  await refreshList(1)
}

async function handleCreateClient(solicitationId: number) {
  closeActionsMenu()
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
  closeActionsMenu()
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

async function handleApprove(solicitationId: number, clientId: number | null) {
  closeActionsMenu()
  if (!clientId) {
    return
  }

  await handleCreateContract(solicitationId)
}

function handleOpenExistingContract(contractId: number) {
  closeActionsMenu()
  void router.push({
    name: 'contracts-edit',
    params: { id: contractId },
  })
}

async function handleReject(solicitationId: number) {
  closeActionsMenu()
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

function toggleActionsMenu(solicitation: Solicitation, event: MouseEvent) {
  if (activeMenuId.value === solicitation.id) {
    closeActionsMenu()
    return
  }

  const trigger = event.currentTarget
  if (!(trigger instanceof HTMLElement)) {
    return
  }

  const rect = trigger.getBoundingClientRect()
  activeMenuId.value = solicitation.id
  activeMenuActions.value = getRowActions(solicitation)
  menuStyle.value = {
    position: 'fixed',
    top: `${rect.bottom + 6}px`,
    left: `${Math.max(12, rect.right - 190)}px`,
  }
}

function closeActionsMenu() {
  activeMenuId.value = null
  activeMenuActions.value = []
}

function handleDocumentClick(event: MouseEvent) {
  const target = event.target
  if (!(target instanceof HTMLElement)) {
    return
  }

  if (target.closest('.solicitation-actions') || target.closest('.row-actions-menu')) {
    return
  }

  closeActionsMenu()
}

function getRowActions(item: Solicitation) {
  const actions: Array<{
    key: string
    label: string
    tone: 'default' | 'success' | 'danger' | 'message'
    run: () => void
  }> = []

  if (canApproveSolicitation(item.status, item.cliente_id)) {
    actions.push({
      key: 'approve',
      label: 'Aprovar solicitação',
      tone: 'success',
      run: () => {
        void handleApprove(item.id, item.cliente_id)
      },
    })
  }

  if (canRejectSolicitation(item.status)) {
    actions.push({
      key: 'reject',
      label: 'Reprovar solicitação',
      tone: 'danger',
      run: () => {
        void handleReject(item.id)
      },
    })
  }

  if (canCreateClient(item.status, item.cliente_id)) {
    actions.push({
      key: 'create-client',
      label: 'Cadastrar cliente',
      tone: 'message',
      run: () => {
        void handleCreateClient(item.id)
      },
    })
  }

  if (canOpenExistingContract(item.status, item.contrato_id)) {
    actions.push({
      key: 'open-contract',
      label: 'Abrir contrato',
      tone: 'default',
      run: () => {
        handleOpenExistingContract(item.contrato_id!)
      },
    })
  }

  return actions
}

function normalizeStatus(value: string) {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'pendente'
}

function formatStatus(status: string) {
  const normalized = normalizeStatus(status)
  if (normalized === 'aprovado') return 'Aprovado'
  if (normalized === 'rejeitado') return 'Rejeitado'
  return 'Pendente'
}

function canApproveSolicitation(status: string, clientId: number | null) {
  return normalizeStatus(status) === 'pendente' && Boolean(clientId)
}

function canRejectSolicitation(status: string) {
  return normalizeStatus(status) === 'pendente'
}

function canCreateClient(status: string, clientId: number | null) {
  return normalizeStatus(status) === 'pendente' && !clientId
}

function canOpenExistingContract(status: string, contractId: number | null) {
  return normalizeStatus(status) === 'aprovado' && typeof contractId === 'number' && contractId > 0
}

function formatCurrency(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return '-'
  }

  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

function formatValueInstallments(value: number | null, installments: number | null) {
  const formattedValue = formatCurrency(value)
  const formattedInstallments = typeof installments === 'number' && installments > 0 ? `${installments}X` : '-'
  return `${formattedValue} - ${formattedInstallments}`
}

function formatType(value: string | null) {
  if (!value) {
    return '-'
  }

  return value
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
  justify-content: flex-end;
}

.solicitation-table :deep(td),
.solicitation-table :deep(th) {
  vertical-align: middle;
}

.solicitation-table :deep(th),
.solicitation-table :deep(td) {
  white-space: nowrap;
}

.solicitation-row td {
  background: transparent;
}

.solicitation-name-chip {
  border-radius: 3px;
  display: inline-flex;
  max-width: 220px;
  overflow: hidden;
  padding: 6px 10px;
  text-overflow: ellipsis;
}

.solicitation-name-chip--client {
  background: rgba(31, 157, 104, 0.14);
  color: #176f4a;
}

.solicitation-name-chip--lead {
  background: rgba(220, 38, 38, 0.14);
  color: #b42318;
}

.solicitation-status-chip {
  border-radius: 3px;
  display: inline-flex;
  min-width: 104px;
  justify-content: center;
  padding: 6px 10px;
}

.solicitation-status-chip--pendente {
  background: rgba(249, 115, 22, 0.14);
  color: #c86718;
}

.solicitation-status-chip--aprovado {
  background: rgba(31, 157, 104, 0.14);
  color: #176f4a;
}

.solicitation-status-chip--rejeitado {
  background: rgba(220, 38, 38, 0.14);
  color: #b42318;
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
  justify-content: flex-end;
  min-width: 56px;
}

.row-menu-button {
  border: 0;
  border-radius: 3px;
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.06);
  color: #425466;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.row-menu-button:hover,
.row-menu-button[aria-expanded='true'] {
  background: rgba(15, 23, 42, 0.12);
  color: #16212b;
}

.row-menu-button svg {
  width: 18px;
  height: 18px;
}

.row-actions-menu {
  z-index: 20;
  min-width: 190px;
  padding: 6px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 3px;
  background: #ffffff;
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.16);
  display: grid;
  gap: 4px;
}

.row-actions-menu__item {
  border: 0;
  border-radius: 3px;
  padding: 9px 10px;
  text-align: left;
  background: transparent;
  color: #24303b;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.row-actions-menu__item:hover {
  background: rgba(15, 23, 42, 0.06);
}

.row-actions-menu__item--success {
  color: #176f4a;
}

.row-actions-menu__item--success:hover {
  background: rgba(31, 157, 104, 0.12);
}

.row-actions-menu__item--danger {
  color: #b42318;
}

.row-actions-menu__item--danger:hover {
  background: rgba(220, 38, 38, 0.12);
}

.row-actions-menu__item--message {
  color: #2563eb;
}

.row-actions-menu__item--message:hover {
  background: rgba(59, 130, 246, 0.12);
}

.row-actions-menu__empty {
  padding: 9px 10px;
  color: var(--text-muted);
  font-size: 13px;
}

@media (max-width: 860px) {
  .solicitations-filters {
    grid-template-columns: 1fr;
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