<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Cadastro de usuarios</p>
        <h2 class="panel__title">Lista operacional</h2>
      </div>
      <RouterLink v-if="props.canCreate" class="primary-button primary-button--compact primary-button--accent-soft" to="/usuarios/novo">Novo +</RouterLink>
    </header>

    <div class="filters-grid">
      <input v-model="draft.nome" class="field" placeholder="Pesquisar por nome" type="text" />
      <input v-model="draft.email" class="field" placeholder="Filtrar por e-mail" type="text" />
      <select v-model="statusFilter" class="field">
        <option value="">Todos</option>
        <option value="true">Ativos</option>
        <option value="false">Inativos</option>
      </select>
      <button class="secondary-button" type="button" @click="applyFilters">Aplicar filtros</button>
    </div>

    <div class="summary-row">
      <article class="summary-chip">
        <strong>{{ props.result.total }}</strong>
        <span>Total</span>
      </article>
    </div>

    <p v-if="props.error" class="feedback feedback--error">{{ props.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--users">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nome</th>
            <th>Login</th>
            <th>E-mail</th>
            <th>Celular</th>
            <th>Função</th>
            <th>Status</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="props.loading">
            <td colspan="8">Carregando usuarios...</td>
          </tr>
          <tr v-else-if="props.result.items.length === 0">
            <td colspan="8">Nenhum usuario encontrado.</td>
          </tr>
          <tr v-for="user in props.result.items" :key="user.id" class="data-table__row">
            <td>{{ user.id }}</td>
            <td>{{ user.nome }}</td>
            <td>{{ user.login }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span class="cellphone-display">
                <span v-if="user.flag_whatsapp && user.celular" class="cellphone-display__whatsapp" aria-label="WhatsApp" title="WhatsApp">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path
                      d="M12 2.2a9.6 9.6 0 0 0-8.29 14.46L2.5 21.5l4.97-1.19A9.6 9.6 0 1 0 12 2.2Zm0 17.29a7.64 7.64 0 0 1-3.89-1.06l-.28-.17-2.95.7.78-2.88-.18-.29a7.64 7.64 0 1 1 6.52 3.7Zm4.19-5.7c-.23-.12-1.35-.66-1.56-.73-.21-.08-.36-.12-.51.12-.15.23-.59.73-.72.89-.13.15-.27.17-.5.06-.23-.12-.99-.36-1.88-1.16-.69-.61-1.16-1.37-1.3-1.6-.13-.23-.01-.35.1-.47.1-.1.23-.27.34-.4.11-.13.14-.23.22-.39.07-.15.04-.29-.02-.41-.06-.12-.51-1.23-.7-1.69-.18-.44-.37-.38-.51-.39h-.43c-.15 0-.39.06-.6.29-.21.23-.8.78-.8 1.9 0 1.11.82 2.19.93 2.34.12.15 1.59 2.43 3.86 3.4.54.23.95.37 1.27.47.53.17 1.02.15 1.4.09.43-.06 1.35-.55 1.54-1.08.19-.53.19-.98.13-1.08-.05-.1-.2-.15-.43-.27Z"
                      fill="currentColor"
                    />
                  </svg>
                </span>
                <span>{{ user.celular || '-' }}</span>
              </span>
            </td>
            <td><span class="pill">{{ user.funcao }}</span></td>
            <td>
              <span :class="['pill', user.ativo ? 'pill--success' : 'pill--danger']">
                {{ user.ativo ? 'Ativo' : 'Inativo' }}
              </span>
            </td>
            <td class="actions-cell">
              <template v-if="props.canUpdate || props.canDelete">
                <button v-if="props.canUpdate" class="icon-action" type="button" title="Alterar cadastro" aria-label="Alterar cadastro" @click="$emit('edit', user.id)">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/>
                  </svg>
                </button>
                <button v-if="props.canDelete" class="icon-action icon-action--danger" type="button" title="Excluir cadastro" aria-label="Excluir cadastro" @click="$emit('delete', user.id)">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/>
                  </svg>
                </button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer class="pagination-compact">
      <div class="pagination-compact__meta">
        <label class="pagination-compact__label" for="page-size">Itens por pagina:</label>
        <select id="page-size" v-model="pageSizeValue" class="pagination-compact__select" @change="changePageSize">
          <option value="8">8</option>
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="50">50</option>
        </select>
      </div>

      <div class="pagination-compact__status">{{ rangeLabel }}</div>

      <div class="pagination-compact__actions">
        <button class="pagination-compact__button" type="button" :disabled="props.result.page <= 1" @click="$emit('change-page', 1)">
          &#171;
        </button>
        <button
          class="pagination-compact__button"
          type="button"
          :disabled="props.result.page <= 1"
          @click="$emit('change-page', props.result.page - 1)"
        >
          &#8249;
        </button>
        <button
          class="pagination-compact__button"
          type="button"
          :disabled="props.result.page >= totalPages"
          @click="$emit('change-page', props.result.page + 1)"
        >
          &#8250;
        </button>
        <button
          class="pagination-compact__button"
          type="button"
          :disabled="props.result.page >= totalPages"
          @click="$emit('change-page', totalPages)"
        >
          &#187;
        </button>
      </div>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, reactive, watch } from 'vue'
import { RouterLink } from 'vue-router'

import type { UserListResponse } from '@/models/user'

const props = defineProps<{
  result: UserListResponse
  loading: boolean
  error: string
  canCreate: boolean
  canUpdate: boolean
  canDelete: boolean
  filters: {
    nome?: string
    email?: string
    ativo?: boolean
  }
}>()

const emit = defineEmits<{
  apply: [payload: { nome?: string; email?: string; ativo?: boolean }]
  'change-page': [page: number]
  'change-page-size': [pageSize: number]
  edit: [userId: number]
  delete: [userId: number]
}>()

const draft = reactive({
  nome: props.filters.nome ?? '',
  email: props.filters.email ?? '',
})

const statusFilter = ref('')
const pageSizeValue = ref(String(props.result.page_size))

const totalPages = computed(() => Math.max(1, Math.ceil(props.result.total / props.result.page_size)))

const rangeLabel = computed(() => {
  if (props.result.total === 0) {
    return '0-0 de 0'
  }

  const start = (props.result.page - 1) * props.result.page_size + 1
  const end = Math.min(props.result.page * props.result.page_size, props.result.total)
  return `${start}-${end} de ${props.result.total}`
})

watch(
  () => props.result.page_size,
  (pageSize) => {
    pageSizeValue.value = String(pageSize)
  },
  { immediate: true },
)

watch(
  () => props.filters,
  (filters) => {
    draft.nome = filters.nome ?? ''
    draft.email = filters.email ?? ''
    statusFilter.value = typeof filters.ativo === 'boolean' ? String(filters.ativo) : ''
  },
  { deep: true, immediate: true },
)

function applyFilters() {
  const ativo = statusFilter.value === '' ? undefined : statusFilter.value === 'true'
  emit('apply', {
    nome: draft.nome || undefined,
    email: draft.email || undefined,
    ativo,
  })
}

function changePageSize() {
  emit('change-page-size', Number(pageSizeValue.value))
}
</script>
