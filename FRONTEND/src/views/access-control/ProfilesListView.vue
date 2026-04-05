<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Seguranca</p>
        <h2 class="panel__title">Perfis</h2>
      </div>
      <RouterLink class="primary-button primary-button--compact primary-button--accent-soft" to="/perfis/novo">Novo perfil</RouterLink>
    </header>

    <div class="filters-grid filters-grid--compact">
      <input v-model="filters.term" class="field" placeholder="Pesquisar perfil" type="text" />
      <button class="secondary-button" type="button" @click="fetchRecords">Aplicar filtros</button>
    </div>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>ID</th>
            <th>Perfil</th>
            <th>Status</th>
            <th>Permissoes</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading"><td colspan="5">Carregando perfis...</td></tr>
          <tr v-else-if="state.items.length === 0"><td colspan="5">Nenhum perfil encontrado.</td></tr>
          <tr v-for="item in state.items" :key="item.id" class="data-table__row">
            <td>{{ item.id }}</td>
            <td>
              <strong>{{ item.nome }}</strong>
              <div>{{ item.descricao || '-' }}</div>
            </td>
            <td>
              <span :class="['pill', item.ativo ? 'pill--success' : 'pill--danger']">
                {{ item.ativo ? 'Ativo' : 'Inativo' }}
              </span>
            </td>
            <td>{{ item.permissions.length }}</td>
            <td class="actions-cell">
              <div class="actions-cell__content">
                <button class="icon-action" type="button" @click="router.push({ name: 'profiles-edit', params: { id: item.id } })">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/></svg>
                </button>
                <button class="icon-action icon-action--danger" type="button" @click="handleDelete(item.id)">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/></svg>
                </button>
              </div>
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

import type { Profile } from '@/models/accessControl'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'
import { deleteProfile, listProfiles } from '@/services/accessControlService'

const router = useRouter()
const filters = reactive({ term: '' })
const state = reactive({ items: [] as Profile[], loading: false, error: '' })

onMounted(() => {
  void fetchRecords()
})

async function fetchRecords() {
  state.loading = true
  state.error = ''
  try {
    state.items = await listProfiles(filters.term || undefined)
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao carregar perfis'
  } finally {
    state.loading = false
  }
}

async function handleDelete(profileId: number) {
  if (!(await confirmDeleteAlert())) return
  try {
    await deleteProfile(profileId)
    await fetchRecords()
    await successAlert('Perfil excluido com sucesso.', 'delete')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao excluir perfil')
  }
}
</script>
