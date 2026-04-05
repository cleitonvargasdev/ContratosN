<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <h2 class="panel__title">Feriados</h2>
      </div>
      <RouterLink class="primary-button primary-button--compact primary-button--accent-soft" to="/feriados/novo">Novo feriado</RouterLink>
    </header>

    <div class="filters-grid filters-grid--feriados">
      <select v-model.number="filters.nivel" class="field">
        <option :value="0">Todos os níveis</option>
        <option :value="1">Nacional</option>
        <option :value="2">Estadual</option>
        <option :value="3">Municipal</option>
      </select>
      <select v-model="filters.uf" class="field">
        <option value="">Todas as UFs</option>
        <option v-for="item in ufOptions" :key="item.uf_id" :value="item.uf">{{ item.uf }} - {{ item.uf_nome }}</option>
      </select>
      <select v-model.number="filters.cidade_id" class="field">
        <option :value="0">Todas as cidades</option>
        <option v-for="item in cityOptions" :key="item.cidade_id" :value="item.cidade_id">{{ item.uf }} - {{ item.cidade }}</option>
      </select>
      <input v-model="filters.descricao" class="field" placeholder="Pesquisar descrição" type="text" />
      <button class="secondary-button" type="button" @click="fetchRecords">Aplicar filtros</button>
    </div>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>ID</th>
            <th>Data</th>
            <th>Nível</th>
            <th>UF</th>
            <th>Cidade</th>
            <th>Descrição</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading"><td colspan="7">Carregando feriados...</td></tr>
          <tr v-else-if="state.items.length === 0"><td colspan="7">Nenhum feriado encontrado.</td></tr>
          <tr v-for="item in state.items" :key="item.feriado_id" class="data-table__row">
            <td>{{ item.feriado_id }}</td>
            <td>{{ formatDisplayDate(item.data) }}</td>
            <td>{{ nivelLabels[item.nivel] ?? item.nivel }}</td>
            <td>{{ item.uf ?? '-' }}</td>
            <td>{{ item.cidade ?? '-' }}</td>
            <td>{{ item.descricao }}</td>
            <td class="actions-cell">
              <button class="icon-action" type="button" @click="router.push({ name: 'feriados-edit', params: { id: item.feriado_id } })"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/></svg></button>
              <button class="icon-action icon-action--danger" type="button" @click="handleDelete(item.feriado_id)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/></svg></button>
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

import type { CidadeOption, FeriadoOption, UFOption } from '@/models/location'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'
import { deleteFeriado, listCities, listFeriados, listUfs } from '@/services/locationService'

const router = useRouter()
const ufOptions = ref<UFOption[]>([])
const cityOptions = ref<CidadeOption[]>([])
const filters = reactive({ nivel: 0, uf: '', cidade_id: 0, descricao: '' })
const state = reactive({ items: [] as FeriadoOption[], loading: false, error: '' })

const nivelLabels: Record<number, string> = {
  1: 'Nacional',
  2: 'Estadual',
  3: 'Municipal',
}

onMounted(() => {
  void loadFilters()
  void fetchRecords()
})

async function loadFilters() {
  ufOptions.value = await listUfs()
  cityOptions.value = await listCities()
}

async function fetchRecords() {
  state.loading = true
  state.error = ''
  try {
    state.items = await listFeriados({
      nivel: filters.nivel || undefined,
      uf: filters.uf || undefined,
      cidade_id: filters.cidade_id || undefined,
      descricao: filters.descricao || undefined,
    })
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao carregar feriados'
  } finally {
    state.loading = false
  }
}

async function handleDelete(feriadoId: number) {
  if (!(await confirmDeleteAlert())) return
  try {
    await deleteFeriado(feriadoId)
    await fetchRecords()
    await successAlert('Feriado excluído com sucesso.', 'delete')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao excluir feriado')
  }
}

function formatDisplayDate(value: string) {
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) {
    return value
  }
  return `${day}/${month}/${year}`
}
</script>
