<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <h2 class="panel__title">Planos de Pagamento</h2>
      </div>
      <RouterLink class="primary-button primary-button--compact primary-button--accent-soft" to="/planos-pagamentos/novo">Novo plano</RouterLink>
    </header>

    <div class="filters-grid filters-grid--compact">
      <input v-model="filters.descricao" class="field" placeholder="Pesquisar por descrição" type="text" />
      <button class="secondary-button" type="button" @click="fetchRecords">Aplicar filtros</button>
    </div>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>ID</th>
            <th>Descrição</th>
            <th>Valor do Plano</th>
            <th>Qtde Dias</th>
            <th>% Juros a.m.</th>
            <th>Valor Parcela</th>
            <th>Valor Final</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading"><td colspan="8">Carregando planos de pagamento...</td></tr>
          <tr v-else-if="state.items.length === 0"><td colspan="8">Nenhum plano encontrado.</td></tr>
          <template v-for="group in groupedItems" :key="group.key">
            <tr class="payment-plan-group-row">
              <td colspan="8">
                <button
                  class="payment-plan-group-button"
                  type="button"
                  @click="toggleGroup(group.key)"
                >
                  <span class="payment-plan-group-button__icon">{{ isGroupOpen(group.key) ? '-' : '+' }}</span>
                  <strong>Valor do plano {{ formatCurrency(group.value) }}</strong>
                  <span class="payment-plan-group-button__meta">{{ group.items.length }} {{ group.items.length === 1 ? 'plano' : 'planos' }}</span>
                </button>
              </td>
            </tr>
            <tr v-for="item in visibleItems(group)" :key="item.plano_id" class="data-table__row">
              <td class="payment-plan-grouped-cell">{{ item.plano_id }}</td>
              <td class="payment-plan-grouped-cell">{{ item.descricao ?? '-' }}</td>
              <td>{{ formatCurrency(item.valor_base) }}</td>
              <td>{{ item.qtde_dias ?? '-' }}</td>
              <td>{{ formatNumber(item.percent_juros) }}</td>
              <td>{{ formatCurrency(item.valor_parcela) }}</td>
              <td>{{ formatCurrency(item.valor_final) }}</td>
              <td class="actions-cell">
                <button class="icon-action" type="button" @click="router.push({ name: 'payment-plans-edit', params: { id: item.plano_id } })">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/></svg>
                </button>
                <button class="icon-action icon-action--danger" type="button" @click="handleDelete(item.plano_id)">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/></svg>
                </button>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import type { PaymentPlanOption } from '@/models/paymentPlan'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'
import { deletePaymentPlan, listPaymentPlans } from '@/services/paymentPlanService'

const router = useRouter()
const filters = reactive({ descricao: '' })
const state = reactive({ items: [] as PaymentPlanOption[], loading: false, error: '' })
const openedGroups = reactive<Record<string, boolean>>({})

const groupedItems = computed(() => {
  const groups = new Map<string, { key: string; value: number | null; items: PaymentPlanOption[] }>()

  for (const item of state.items) {
    const key = item.valor_base == null ? '__empty__' : item.valor_base.toFixed(2)
    const current = groups.get(key)
    if (current) {
      current.items.push(item)
      continue
    }

    groups.set(key, {
      key,
      value: item.valor_base,
      items: [item],
    })
  }

  return Array.from(groups.values())
})

onMounted(() => {
  void fetchRecords()
})

async function fetchRecords() {
  state.loading = true
  state.error = ''
  try {
    state.items = await listPaymentPlans(filters.descricao || undefined)
    syncOpenedGroups()
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao carregar planos de pagamento'
  } finally {
    state.loading = false
  }
}

async function handleDelete(planoId: number) {
  if (!(await confirmDeleteAlert())) return
  try {
    await deletePaymentPlan(planoId)
    await fetchRecords()
    await successAlert('Plano excluído com sucesso.', 'delete')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao excluir plano')
  }
}

function syncOpenedGroups() {
  for (const group of groupedItems.value) {
    if (!(group.key in openedGroups)) {
      openedGroups[group.key] = group.items.length <= 1
    }
  }

  for (const key of Object.keys(openedGroups)) {
    if (!groupedItems.value.some((group) => group.key === key)) {
      delete openedGroups[key]
    }
  }
}

function toggleGroup(key: string) {
  if (!(key in openedGroups)) {
    openedGroups[key] = true
    return
  }
  openedGroups[key] = !openedGroups[key]
}

function isGroupOpen(key: string) {
  return openedGroups[key] ?? false
}

function visibleItems(group: { key: string; items: PaymentPlanOption[] }) {
  return isGroupOpen(group.key) ? group.items : []
}

function formatNumber(value: number | null) {
  return value == null ? '-' : value.toFixed(2)
}

function formatCurrency(value: number | null) {
  return value == null ? '-' : new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}
</script>