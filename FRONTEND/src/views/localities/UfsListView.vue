<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Cadastros diversos</p>
        <h2 class="panel__title">UFs</h2>
      </div>
      <RouterLink class="primary-button primary-button--compact primary-button--accent-soft" to="/ufs/novo">Nova UF</RouterLink>
    </header>

    <div class="filters-grid filters-grid--compact">
      <input v-model="filters.term" class="field" placeholder="Pesquisar por UF ou nome" type="text" />
      <button class="secondary-button" type="button" @click="fetchRecords">Aplicar filtros</button>
    </div>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>ID</th>
            <th>UF</th>
            <th>Nome</th>
            <th>IBGE</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading"><td colspan="5">Carregando UFs...</td></tr>
          <tr v-else-if="state.items.length === 0"><td colspan="5">Nenhuma UF encontrada.</td></tr>
          <tr v-for="item in state.items" :key="item.uf_id" class="data-table__row">
            <td>{{ item.uf_id }}</td>
            <td>{{ item.uf }}</td>
            <td>{{ item.uf_nome }}</td>
            <td>{{ item.cod_ibge ?? '-' }}</td>
            <td class="actions-cell">
              <button class="icon-action" type="button" @click="router.push({ name: 'ufs-edit', params: { id: item.uf_id } })">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/></svg>
              </button>
              <button class="icon-action icon-action--danger" type="button" @click="handleDelete(item.uf_id)">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import type { UFOption } from '@/models/location'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'
import { deleteUf, listUfs } from '@/services/locationService'

const router = useRouter()
const filters = reactive({ term: '' })
const state = reactive({ items: [] as UFOption[], loading: false, error: '' })

onMounted(() => {
  void fetchRecords()
})

async function fetchRecords() {
  state.loading = true
  state.error = ''
  try {
    state.items = await listUfs(filters.term || undefined)
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao carregar UFs'
  } finally {
    state.loading = false
  }
}

async function handleDelete(ufId: number) {
  if (!(await confirmDeleteAlert())) return
  try {
    await deleteUf(ufId)
    await fetchRecords()
    await successAlert('UF excluida com sucesso.', 'delete')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao excluir UF')
  }
}
</script>