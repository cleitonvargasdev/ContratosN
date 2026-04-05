<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Cadastros diversos</p>
        <h2 class="panel__title">Cidades</h2>
      </div>
      <RouterLink class="primary-button primary-button--compact primary-button--accent-soft" to="/cidades/novo">Nova cidade</RouterLink>
    </header>

    <div class="filters-grid">
      <select v-model="filters.uf" class="field">
        <option value="">Todas as UFs</option>
        <option v-for="item in ufOptions" :key="item.uf" :value="item.uf">{{ item.uf }} - {{ item.uf_nome }}</option>
      </select>
      <input v-model="filters.nome" class="field" placeholder="Pesquisar cidade" type="text" />
      <button class="secondary-button" type="button" @click="fetchRecords">Aplicar filtros</button>
    </div>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead><tr><th>ID</th><th>UF</th><th>Cidade</th><th class="actions-column">Ações</th></tr></thead>
        <tbody>
          <tr v-if="state.loading"><td colspan="4">Carregando cidades...</td></tr>
          <tr v-else-if="state.items.length === 0"><td colspan="4">Nenhuma cidade encontrada.</td></tr>
          <tr v-for="item in state.items" :key="item.cidade_id" class="data-table__row">
            <td>{{ item.cidade_id }}</td>
            <td>{{ item.uf }}</td>
            <td>{{ item.cidade }}</td>
            <td class="actions-cell">
              <button class="icon-action" type="button" @click="router.push({ name: 'cities-edit', params: { id: item.cidade_id } })"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/></svg></button>
              <button class="icon-action icon-action--danger" type="button" @click="handleDelete(item.cidade_id)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/></svg></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import type { CidadeOption, UFOption } from '@/models/location'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'
import { deleteCidade, listCities, listUfs } from '@/services/locationService'

const router = useRouter()
const ufOptions = ref<UFOption[]>([])
const filters = reactive({ uf: '', nome: '' })
const state = reactive({ items: [] as CidadeOption[], loading: false, error: '' })

onMounted(() => {
  void loadFilters()
  void fetchRecords()
})

async function loadFilters() {
  ufOptions.value = await listUfs()
}

async function fetchRecords() {
  state.loading = true
  state.error = ''
  try {
    state.items = await listCities({ uf: filters.uf || undefined, nome: filters.nome || undefined })
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao carregar cidades'
  } finally {
    state.loading = false
  }
}

async function handleDelete(cidadeId: number) {
  if (!(await confirmDeleteAlert())) return
  try {
    await deleteCidade(cidadeId)
    await fetchRecords()
    await successAlert('Cidade excluida com sucesso.', 'delete')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao excluir cidade')
  }
}
</script>