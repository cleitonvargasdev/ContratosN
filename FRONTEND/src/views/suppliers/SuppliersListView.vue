<template>
  <section class="panel">
    <header class="panel__header">
      <div>
        <h2 class="panel__title">Fornecedores</h2>
      </div>
      <RouterLink class="primary-button primary-button--compact primary-button--accent-soft" to="/fornecedores/novo">Novo fornecedor</RouterLink>
    </header>

    <div class="filters-grid filters-grid--compact">
      <input v-model="draft.nome" class="field" placeholder="Pesquisar por nome" type="text" @keydown.enter.prevent="applyFilters" />
      <input v-model="draft.cpf_cnpj" class="field" placeholder="CPF/CNPJ" type="text" @blur="handleDocumentFilterBlur" @keydown.enter.prevent="applyFilters" />
      <select v-model="ativoValue" class="field" @change="applyFilters">
        <option value="">Todos</option>
        <option value="true">Ativos</option>
        <option value="false">Inativos</option>
      </select>
      <button class="secondary-button" type="button" @click="applyFilters">Filtrar</button>
    </div>

    <p v-if="suppliers.state.error" class="feedback feedback--error">{{ suppliers.state.error }}</p>

    <div class="table-wrap">
      <table class="data-table data-table--cadastro">
        <thead>
          <tr>
            <th>Nome</th>
            <th>CPF/CNPJ</th>
            <th>Telefone</th>
            <th>E-mail</th>
            <th>Status</th>
            <th class="actions-column">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="suppliers.state.loading"><td colspan="6">Carregando fornecedores...</td></tr>
          <tr v-else-if="suppliers.state.result.items.length === 0"><td colspan="6">Nenhum fornecedor encontrado.</td></tr>
          <tr v-for="item in suppliers.state.result.items" :key="item.fornecedor_id" class="data-table__row">
            <td>{{ item.nome || '-' }}</td>
            <td>{{ formatDocument(item.cpf_cnpj) || '-' }}</td>
            <td>{{ formatPhone(item.telefone) || '-' }}</td>
            <td>{{ item.email || '-' }}</td>
            <td>
              <span :class="['pill', item.ativo ? 'pill--success' : 'pill--danger']">{{ item.ativo ? 'Ativo' : 'Inativo' }}</span>
            </td>
            <td class="actions-cell">
              <button class="icon-action" type="button" @click="router.push({ name: 'suppliers-edit', params: { id: item.fornecedor_id } })">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor"/></svg>
              </button>
              <button class="icon-action icon-action--danger" type="button" @click="handleDelete(item.fornecedor_id)">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer class="pagination-compact">
      <div class="pagination-compact__meta">
        <label class="pagination-compact__label" for="suppliers-page-size">Itens por pagina:</label>
        <select id="suppliers-page-size" v-model="pageSizeValue" class="pagination-compact__select" @change="changePageSize">
          <option value="8">8</option>
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="50">50</option>
        </select>
      </div>
      <div class="pagination-compact__status">{{ rangeLabel }}</div>
      <div class="pagination-compact__actions">
        <button class="pagination-compact__button" type="button" :disabled="suppliers.state.result.page <= 1" @click="handlePage(1)">&#171;</button>
        <button class="pagination-compact__button" type="button" :disabled="suppliers.state.result.page <= 1" @click="handlePage(suppliers.state.result.page - 1)">&#8249;</button>
        <button class="pagination-compact__button" type="button" :disabled="suppliers.state.result.page >= totalPages" @click="handlePage(suppliers.state.result.page + 1)">&#8250;</button>
        <button class="pagination-compact__button" type="button" :disabled="suppliers.state.result.page >= totalPages" @click="handlePage(totalPages)">&#187;</button>
      </div>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { useSuppliersController } from '@/controllers/useSuppliersController'
import { confirmDeleteAlert, errorAlert, successAlert } from '@/services/alertService'

const suppliers = useSuppliersController()
const router = useRouter()

const draft = reactive({ nome: '', cpf_cnpj: '' })
const ativoValue = ref('')
const pageSizeValue = ref(String(suppliers.state.result.page_size))

const totalPages = computed(() => Math.max(1, Math.ceil(suppliers.state.result.total / suppliers.state.result.page_size)))
const rangeLabel = computed(() => {
  if (suppliers.state.result.total === 0) return '0-0 de 0'
  const start = (suppliers.state.result.page - 1) * suppliers.state.result.page_size + 1
  const end = Math.min(suppliers.state.result.page * suppliers.state.result.page_size, suppliers.state.result.total)
  return `${start}-${end} de ${suppliers.state.result.total}`
})

onMounted(() => {
  void suppliers.fetchSuppliers()
})

function applyFilters() {
  suppliers.patchFilters({
    page: 1,
    nome: draft.nome.trim() || undefined,
    cpf_cnpj: cleanDigits(draft.cpf_cnpj) || undefined,
    ativo: ativoValue.value === '' ? undefined : ativoValue.value === 'true',
  })
  void suppliers.fetchSuppliers()
}

function handleDocumentFilterBlur() {
  draft.cpf_cnpj = formatDocument(draft.cpf_cnpj)
}

function handlePage(page: number) {
  suppliers.patchFilters({ page })
  void suppliers.fetchSuppliers()
}

function changePageSize() {
  suppliers.patchFilters({ page: 1, page_size: Number(pageSizeValue.value) })
  void suppliers.fetchSuppliers()
}

async function handleDelete(supplierId: number) {
  if (!(await confirmDeleteAlert())) return
  try {
    await suppliers.removeSupplier(supplierId)
    await suppliers.fetchSuppliers()
    await successAlert('Fornecedor excluído com sucesso.', 'delete')
  } catch {
    if (suppliers.state.error) {
      await errorAlert(suppliers.state.error)
    }
  }
}

function cleanDigits(value: string | null | undefined) {
  return (value ?? '').replace(/\D/g, '')
}

function formatDocument(value: string | null | undefined) {
  const digits = cleanDigits(value)
  if (digits.length <= 11) {
    return digits.slice(0, 11).replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2')
  }
  return digits.slice(0, 14).replace(/(\d{2})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1/$2').replace(/(\d{4})(\d{1,2})$/, '$1-$2')
}

function formatPhone(value: string | null | undefined) {
  const digits = cleanDigits(value).slice(0, 11)
  if (!digits) return ''
  if (digits.length <= 10) return digits.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{4})(\d)/, '$1-$2')
  return digits.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{5})(\d)/, '$1-$2')
}
</script>