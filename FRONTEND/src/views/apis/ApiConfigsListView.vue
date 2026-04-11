<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <h2 class="panel__title">APIs</h2>
      </div>
      <RouterLink v-if="auth.hasPermission('apis', 'create')" class="primary-button primary-button--compact primary-button--accent-soft" to="/apis/novo">
        Nova API
      </RouterLink>
    </header>

    <div class="filters-grid filters-grid--compact filters-grid--three-columns">
      <input v-model="filters.nome_api" class="field" placeholder="Pesquisar por nome da API" type="text" />
      <select v-model.number="filters.usuario_id" class="field">
        <option :value="null">Todos os usuários</option>
        <option v-for="user in users" :key="user.id" :value="user.id">{{ user.nome }}</option>
      </select>
      <button class="secondary-button" type="button" @click="fetchRecords">Aplicar filtros</button>
    </div>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nome API</th>
            <th>Funcionalidade</th>
            <th>URL</th>
            <th>Usuário</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading"><td colspan="6">Carregando APIs...</td></tr>
          <tr v-else-if="state.items.length === 0"><td colspan="6">Nenhuma API encontrada.</td></tr>
          <tr v-for="item in state.items" :key="item.api_id" class="data-table__row">
            <td>{{ item.api_id }}</td>
            <td>{{ item.nome_api ?? '-' }}</td>
            <td>{{ item.funcionalidade ?? '-' }}</td>
            <td>{{ item.url ?? '-' }}</td>
            <td>{{ item.usuario_nome ?? '-' }}</td>
            <td class="actions-cell">
              <button v-if="auth.hasPermission('apis', 'update')" class="icon-action" type="button" @click="router.push({ name: 'api-configs-edit', params: { id: item.api_id } })">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/></svg>
              </button>
              <button v-if="auth.hasPermission('apis', 'delete')" class="icon-action icon-action--danger" type="button" @click="handleDelete(item.api_id)">
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
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { useAuthController } from '@/controllers/useAuthController'
import type { ApiConfig } from '@/models/apiConfig'
import type { User } from '@/models/user'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'
import { deleteApiConfig, listApiConfigs } from '@/services/apiConfigService'
import { listUsers } from '@/services/userService'

const auth = useAuthController()
const router = useRouter()
const users = ref<User[]>([])
const filters = reactive({ nome_api: '', usuario_id: null as number | null })
const state = reactive({ items: [] as ApiConfig[], loading: false, error: '' })

onMounted(() => {
  void loadUsers()
  void fetchRecords()
})

async function loadUsers() {
  try {
    const response = await listUsers({ page: 1, page_size: 100, ativo: true })
    users.value = [...response.items]
  } catch {
    users.value = []
  }
}

async function fetchRecords() {
  state.loading = true
  state.error = ''
  try {
    const response = await listApiConfigs({
      page: 1,
      page_size: 100,
      nome_api: filters.nome_api || undefined,
      usuario_id: filters.usuario_id ?? undefined,
    })
    state.items = [...response.items]
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao carregar APIs'
  } finally {
    state.loading = false
  }
}

async function handleDelete(apiId: number) {
  if (!(await confirmDeleteAlert())) return
  try {
    await deleteApiConfig(apiId)
    await fetchRecords()
    await successAlert('API excluída com sucesso.', 'delete')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao excluir API')
  }
}
</script>

<style scoped>
.filters-grid--three-columns {
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) auto;
}

@media (max-width: 900px) {
  .filters-grid--three-columns {
    grid-template-columns: 1fr;
  }
}
</style>