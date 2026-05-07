<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Cadastros diversos</p>
        <h2 class="panel__title">Marcas</h2>
      </div>
      <RouterLink class="primary-button primary-button--compact primary-button--accent-soft" to="/marcas/novo">Nova +</RouterLink>
    </header>

    <div class="filters-grid filters-grid--compact">
      <input v-model="filters.descricao" class="field" placeholder="Pesquisar por descrição" type="text" />
      <button class="secondary-button" type="button" @click="applyFilters">Aplicar filtros</button>
    </div>

    <div class="summary-row">
      <article class="summary-chip">
        <strong>{{ state.result.total }}</strong>
        <span>Total</span>
      </article>
    </div>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>ID</th>
            <th>Descrição</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading"><td colspan="3">Carregando marcas...</td></tr>
          <tr v-else-if="state.result.items.length === 0"><td colspan="3">Nenhuma marca encontrada.</td></tr>
          <tr v-for="item in state.result.items" :key="item.marca_id" class="data-table__row">
            <td>{{ item.marca_id }}</td>
            <td>{{ item.descricao ?? '-' }}</td>
            <td class="actions-cell">
              <button class="icon-action" type="button" title="Alterar cadastro" aria-label="Alterar cadastro" @click="router.push({ name: 'brands-edit', params: { id: item.marca_id } })">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/></svg>
              </button>
              <button class="icon-action icon-action--danger" type="button" title="Excluir cadastro" aria-label="Excluir cadastro" @click="handleDelete(item.marca_id)">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer class="pagination-compact">
      <div class="pagination-compact__meta">
        <label class="pagination-compact__label" for="brands-page-size">Itens por pagina:</label>
        <select id="brands-page-size" v-model.number="filters.page_size" class="pagination-compact__select" @change="changePageSize">
          <option :value="8">8</option>
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
      </div>

      <div class="pagination-compact__status">{{ rangeLabel }}</div>

      <div class="pagination-compact__actions">
        <button class="pagination-compact__button" type="button" :disabled="state.result.page <= 1" @click="changePage(1)">&#171;</button>
        <button class="pagination-compact__button" type="button" :disabled="state.result.page <= 1" @click="changePage(state.result.page - 1)">&#8249;</button>
        <button class="pagination-compact__button" type="button" :disabled="state.result.page >= totalPages" @click="changePage(state.result.page + 1)">&#8250;</button>
        <button class="pagination-compact__button" type="button" :disabled="state.result.page >= totalPages" @click="changePage(totalPages)">&#187;</button>
      </div>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import type { BrandListResponse } from '@/models/product'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'
import { deleteBrand, listBrands } from '@/services/productService'

const router = useRouter()
const filters = reactive({ page: 1, page_size: 8, descricao: '' })
const state = reactive({
  loading: false,
  error: '',
  result: {
    items: [],
    total: 0,
    page: 1,
    page_size: 8,
  } as BrandListResponse,
})

const totalPages = computed(() => Math.max(1, Math.ceil(state.result.total / state.result.page_size)))

const rangeLabel = computed(() => {
  if (state.result.total === 0) {
    return '0-0 de 0'
  }

  const start = (state.result.page - 1) * state.result.page_size + 1
  const end = Math.min(state.result.page * state.result.page_size, state.result.total)
  return `${start}-${end} de ${state.result.total}`
})

onMounted(() => {
  void fetchRecords()
})

async function fetchRecords() {
  state.loading = true
  state.error = ''
  try {
    state.result = await listBrands({
      page: filters.page,
      page_size: filters.page_size,
      descricao: filters.descricao || undefined,
    })
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao carregar marcas'
  } finally {
    state.loading = false
  }
}

function applyFilters() {
  filters.page = 1
  void fetchRecords()
}

function changePage(page: number) {
  filters.page = page
  void fetchRecords()
}

function changePageSize() {
  filters.page = 1
  void fetchRecords()
}

async function handleDelete(brandId: number) {
  if (!(await confirmDeleteAlert())) return
  try {
    await deleteBrand(brandId)
    await fetchRecords()
    await successAlert('Marca excluída com sucesso.', 'delete')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao excluir marca')
  }
}
</script>