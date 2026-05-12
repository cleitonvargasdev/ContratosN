<template>
  <Teleport to="body">
    <div v-if="props.open" class="modal-backdrop" @click.self="emit('close')">
      <section class="modal-card modal-card--comodato">
        <header class="panel__header panel__header--stacked comodato-modal__header">
          <div>
            <h3 class="panel__title">Comodato do contrato {{ props.contractId ?? '-' }}</h3>
            <p class="modal-context">Selecione o avalista e monte os produtos vinculados a este contrato.</p>
          </div>
        </header>

        <div class="modal-form comodato-modal__body">
          <label class="field-group comodato-modal__avalista-field">
            <span>Avalista</span>
            <div class="comodato-modal__picker-embedded">
              <input :value="selectedAvalistaLabel" class="field field--readonly comodato-modal__picker-field comodato-modal__picker-field--embedded" readonly type="text" />
              <button class="comodato-modal__picker-button comodato-modal__picker-button--embedded" type="button" title="Pesquisar avalista" aria-label="Pesquisar avalista" @click="openAvalistaLookup">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M10.5 4a6.5 6.5 0 1 0 4.03 11.6l4.44 4.44 1.41-1.41-4.44-4.44A6.5 6.5 0 0 0 10.5 4Zm0 2a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Z" fill="currentColor" />
                </svg>
              </button>
            </div>
          </label>

          <section class="comodato-modal__section comodato-modal__section--produtos">
            <div class="comodato-modal__section-header">
              <h4>Produtos</h4>
              <span class="comodato-modal__selected">{{ draft.items.length }} item(ns) • {{ formatCurrency(orderTotal) }}</span>
            </div>

            <div class="comodato-modal__item-form">
              <label class="field-group comodato-modal__field--product">
                <span>Produto</span>
                <div class="comodato-modal__picker-embedded">
                  <input :value="selectedProductLabel" class="field field--readonly comodato-modal__picker-field comodato-modal__picker-field--embedded" readonly type="text" />
                  <button class="comodato-modal__picker-button comodato-modal__picker-button--embedded" type="button" title="Pesquisar produto" aria-label="Pesquisar produto" @click="openProductLookup">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M10.5 4a6.5 6.5 0 1 0 4.03 11.6l4.44 4.44 1.41-1.41-4.44-4.44A6.5 6.5 0 0 0 10.5 4Zm0 2a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Z" fill="currentColor" />
                    </svg>
                  </button>
                </div>
              </label>

              <label class="field-group comodato-modal__field--compact">
                <span>Quantidade</span>
                <input v-model="draft.itemQuantidade" class="field" inputmode="numeric" min="1" type="number" />
              </label>

              <label class="field-group comodato-modal__field--compact">
                <span>Valor unitário</span>
                <input v-model="draft.itemValorUnitario" class="field" inputmode="decimal" type="text" @blur="formatItemValue" />
              </label>

              <label class="field-group comodato-modal__field--compact">
                <span>Subtotal</span>
                <input :value="formatCurrency(itemSubtotal)" class="field field--readonly" readonly type="text" />
              </label>

              <label class="field-group comodato-modal__field--observation">
                <span>Observação</span>
                <textarea v-model="draft.itemObservacao" class="field field--textarea comodato-modal__observation" rows="2"></textarea>
              </label>

              <label class="field-group comodato-modal__field--total">
                <span>Total do pedido</span>
                <input :value="formatCurrency(orderTotal)" class="field field--readonly" readonly type="text" />
              </label>

              <div class="form-actions comodato-modal__item-actions">
                <button class="primary-button primary-button--success" type="button" @click="addOrUpdateItem">
                  {{ draft.editingItemIndex === null ? 'Incluir produto' : 'Salvar alteração' }}
                </button>
              </div>
            </div>

            <div class="table-wrap comodato-modal__table-wrap">
              <table class="data-table comodato-modal__table">
                <thead>
                  <tr>
                    <th>Produto</th>
                    <th>Qtd.</th>
                    <th>Vl. unit.</th>
                    <th>Subtotal</th>
                    <th class="comodato-modal__actions-header">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="draft.items.length === 0">
                    <td colspan="5">Nenhum produto incluído.</td>
                  </tr>
                  <tr v-for="(item, index) in draft.items" :key="item.localKey">
                    <td>{{ item.produto_descricao }}</td>
                    <td>{{ item.quantidade }}</td>
                    <td>{{ formatCurrency(item.valor_unitario) }}</td>
                    <td>{{ formatCurrency(itemSubtotalValue(item)) }}</td>
                    <td class="comodato-modal__actions-column">
                      <div class="comodato-modal__actions-cell">
                        <button class="contract-installments__action contract-installments__action--edit" type="button" title="Editar item" aria-label="Editar item" @click="editItem(index)">
                          <span class="contract-installments__action-icon" aria-hidden="true">
                            <svg viewBox="0 0 24 24">
                              <path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor" />
                            </svg>
                          </span>
                        </button>
                        <button class="contract-installments__action contract-installments__action--delete" type="button" title="Excluir item" aria-label="Excluir item" @click="removeItem(index)">
                          <span class="contract-installments__action-icon" aria-hidden="true">
                            <svg viewBox="0 0 24 24">
                              <path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor" />
                            </svg>
                          </span>
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <div class="form-actions comodato-modal__footer">
            <button class="ghost-button" :disabled="props.saving" type="button" @click="emit('close')">Fechar</button>
            <button
              v-if="hasExistingComodato"
              class="ghost-button ghost-button--danger"
              :disabled="props.saving"
              type="button"
              @click="handleDeleteComodato"
            >
              Excluir comodato
            </button>
            <button class="primary-button primary-button--success" :disabled="props.saving" type="button" @click="emitSave">
              {{ props.saving ? 'Salvando...' : 'Salvar comodato' }}
            </button>
            <button class="primary-button primary-button--accent-soft" :disabled="props.saving || draft.items.length === 0" type="button" @click="emit('print')">
              Imprimir
            </button>
          </div>
        </div>
      </section>

      <div v-if="avalistaLookupOpen" class="modal-backdrop modal-backdrop--nested" @click.self="closeAvalistaLookup">
        <section class="modal-card modal-card--lookup">
          <header class="panel__header panel__header--stacked">
            <div>
              <h3 class="panel__title">Pesquisar avalista</h3>
            </div>
            <p class="modal-context">Selecione um cliente para preencher o avalista.</p>
          </header>

          <div class="modal-form">
            <label class="field-group">
              <span>Busca</span>
              <input v-model="draft.avalistaTerm" class="field" type="text" placeholder="Digite nome, documento ou endereço" />
            </label>

            <div class="comodato-modal__results">
              <button
                v-for="client in paginatedAvalistas"
                :key="client.clientes_id"
                class="comodato-modal__result"
                :class="{ 'comodato-modal__result--active': draft.avalista_id === client.clientes_id }"
                type="button"
                @click="selectAvalista(client.clientes_id)"
              >
                <strong>{{ client.nome || `Cliente ${client.clientes_id}` }}</strong>
                <span>{{ client.cpf_cnpj || client.telefone || client.celular01 || 'Sem documento/telefone' }}</span>
                <small>{{ formatClientAddress(client) }}</small>
              </button>
              <p v-if="filteredAvalistas.length === 0" class="profile-modal-list__empty">Nenhum avalista encontrado.</p>
            </div>

            <footer v-if="filteredAvalistas.length > 0" class="pagination-compact score-log-pagination">
              <div class="pagination-compact__status">{{ avalistaRangeLabel }}</div>

              <div class="pagination-compact__actions">
                <button class="pagination-compact__button" type="button" :disabled="avalistaLookup.page <= 1" @click="changeAvalistaPage(1)">&#171;</button>
                <button class="pagination-compact__button" type="button" :disabled="avalistaLookup.page <= 1" @click="changeAvalistaPage(avalistaLookup.page - 1)">&#8249;</button>
                <button class="pagination-compact__button" type="button" :disabled="avalistaLookup.page >= avalistaTotalPages" @click="changeAvalistaPage(avalistaLookup.page + 1)">&#8250;</button>
                <button class="pagination-compact__button" type="button" :disabled="avalistaLookup.page >= avalistaTotalPages" @click="changeAvalistaPage(avalistaTotalPages)">&#187;</button>
              </div>
            </footer>

            <div class="form-actions">
              <button class="ghost-button" :disabled="draft.avalista_id === null" type="button" @click="clearAvalista">Limpar</button>
              <button class="ghost-button" type="button" @click="closeAvalistaLookup">Fechar</button>
            </div>
          </div>
        </section>
      </div>

      <div v-if="productLookupOpen" class="modal-backdrop modal-backdrop--nested" @click.self="closeProductLookup">
        <section class="modal-card modal-card--lookup">
          <header class="panel__header panel__header--stacked">
            <div>
              <h3 class="panel__title">Pesquisar produto</h3>
            </div>
            <p class="modal-context">Selecione um produto para o item atual.</p>
          </header>

          <div class="modal-form">
            <label class="field-group">
              <span>Busca</span>
              <input v-model="draft.productTerm" class="field" type="text" placeholder="Digite descrição, modelo, cor ou marca" />
            </label>

            <div class="comodato-modal__results comodato-modal__results--products">
              <button
                v-for="product in filteredProducts"
                :key="product.produto_id"
                class="comodato-modal__result"
                :class="{ 'comodato-modal__result--active': draft.itemProdutoId === product.produto_id }"
                type="button"
                @click="selectProduct(product)"
              >
                <strong>{{ product.descricao || `Produto ${product.produto_id}` }}</strong>
                <span>{{ product.marca_descricao || product.modelo || product.cor || 'Sem complemento' }}</span>
                <small>Valor: {{ formatCurrency(product.valor_venda) }}</small>
              </button>
              <p v-if="!productsLoading && filteredProducts.length === 0" class="profile-modal-list__empty">Nenhum produto encontrado.</p>
              <p v-if="productsLoading" class="feedback feedback--info">Carregando produtos...</p>
              <p v-if="productsError" class="feedback feedback--error">{{ productsError }}</p>
            </div>

            <div class="form-actions">
              <button class="ghost-button" type="button" @click="closeProductLookup">Fechar</button>
            </div>
          </div>
        </section>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

import type { Client } from '@/models/client'
import type { ContractComodato, ContractComodatoInput, ContractComodatoItemInput, ContractComodatoItemRead } from '@/models/contract'
import type { Product } from '@/models/product'
import { confirmActionAlert, infoAlert } from '@/services/alertService'
import { listProducts } from '@/services/productService'

type DraftItem = ContractComodatoItemRead & { localKey: string }

const props = defineProps<{
  open: boolean
  saving: boolean
  contractId: number | null
  clientOptions: Client[]
  contractClientId: number | null
  value: ContractComodato | null
}>()

const emit = defineEmits<{
  close: []
  save: [payload: ContractComodatoInput]
  print: []
  delete: []
}>()

const productsLoading = ref(false)
const productsError = ref('')
const productOptions = ref<Product[]>([])
const nextLocalKey = ref(1)
const avalistaLookupOpen = ref(false)
const productLookupOpen = ref(false)
const avalistaLookup = reactive({ page: 1, pageSize: 8 })

const draft = reactive({
  avalista_id: null as number | null,
  avalistaTerm: '',
  productTerm: '',
  itemProdutoId: null as number | null,
  itemQuantidade: '1',
  itemValorUnitario: '',
  itemObservacao: '',
  editingItemIndex: null as number | null,
  items: [] as DraftItem[],
})

const selectedAvalistaLabel = computed(() => {
  if (draft.avalista_id === null) {
    return 'Nenhum avalista selecionado'
  }
  const client = props.clientOptions.find((item) => item.clientes_id === draft.avalista_id)
  return client?.nome?.trim() ? `${client.clientes_id} - ${client.nome}` : `Cliente ${draft.avalista_id}`
})

const filteredAvalistas = computed(() => {
  const term = draft.avalistaTerm.trim().toLowerCase()
  return props.clientOptions.filter((client) => {
    if (!term) {
      return true
    }
    const haystack = [client.nome, client.cpf_cnpj, client.endereco, client.telefone, client.celular01].filter(Boolean).join(' ').toLowerCase()
    return haystack.includes(term)
  })
})

const avalistaTotalPages = computed(() => Math.max(1, Math.ceil(filteredAvalistas.value.length / avalistaLookup.pageSize)))
const paginatedAvalistas = computed(() => {
  const start = (avalistaLookup.page - 1) * avalistaLookup.pageSize
  const end = start + avalistaLookup.pageSize
  return filteredAvalistas.value.slice(start, end)
})
const avalistaRangeLabel = computed(() => {
  if (filteredAvalistas.value.length === 0) {
    return '0-0 de 0'
  }

  const start = (avalistaLookup.page - 1) * avalistaLookup.pageSize + 1
  const end = Math.min(avalistaLookup.page * avalistaLookup.pageSize, filteredAvalistas.value.length)
  return `${start}-${end} de ${filteredAvalistas.value.length}`
})

const selectedProductLabel = computed(() => {
  if (draft.itemProdutoId === null) {
    return 'Nenhum produto selecionado'
  }
  const product = productOptions.value.find((item) => item.produto_id === draft.itemProdutoId)
  return product?.descricao?.trim() ? `${product.produto_id} - ${product.descricao}` : `Produto ${draft.itemProdutoId}`
})

const itemSubtotal = computed(() => {
  const quantity = Number(draft.itemQuantidade)
  const unitValue = parseMoney(draft.itemValorUnitario) ?? 0
  if (!Number.isFinite(quantity) || quantity <= 0) {
    return 0
  }
  return quantity * unitValue
})

const orderTotal = computed(() => draft.items.reduce((total, item) => total + itemSubtotalValue(item), 0))
const hasExistingComodato = computed(() => (props.value?.total_itens ?? 0) > 0 || props.value?.avalista_id !== null)

const filteredProducts = computed(() => {
  const term = draft.productTerm.trim().toLowerCase()
  return productOptions.value.filter((product) => {
    if (!term) {
      return true
    }
    const haystack = [product.descricao, product.marca_descricao, product.modelo, product.cor].filter(Boolean).join(' ').toLowerCase()
    return haystack.includes(term)
  })
})

watch(
  () => props.open,
  (open) => {
    if (!open) {
      return
    }
    syncFromProps()
    if (productOptions.value.length === 0) {
      void loadProducts()
    }
  },
  { immediate: true },
)

watch(
  () => props.value,
  () => {
    if (props.open) {
      syncFromProps()
    }
  },
)

function syncFromProps() {
  draft.avalista_id = props.value?.avalista_id ?? null
  draft.avalistaTerm = ''
  draft.productTerm = ''
  draft.editingItemIndex = null
  draft.items = (props.value?.items ?? []).map((item) => ({ ...item, localKey: `saved-${item.item_id}` }))
  resetItemEditor()
  avalistaLookupOpen.value = false
  productLookupOpen.value = false
}

async function loadProducts() {
  productsLoading.value = true
  productsError.value = ''
  try {
    const response = await listProducts({ page: 1, page_size: 100, ativo: true })
    productOptions.value = [...response.items]
  } catch (error) {
    productsError.value = error instanceof Error ? error.message : 'Falha ao carregar produtos'
  } finally {
    productsLoading.value = false
  }
}

watch(
  () => draft.avalistaTerm,
  () => {
    avalistaLookup.page = 1
  },
)

watch(filteredAvalistas, () => {
  if (avalistaLookup.page > avalistaTotalPages.value) {
    avalistaLookup.page = avalistaTotalPages.value
  }
})

function selectAvalista(clientId: number) {
  draft.avalista_id = clientId
  avalistaLookupOpen.value = false
}

function clearAvalista() {
  draft.avalista_id = null
}

function selectProduct(product: Product) {
  const isDifferentProduct = draft.itemProdutoId !== product.produto_id
  draft.itemProdutoId = product.produto_id
  draft.itemValorUnitario = formatMoneyInput(product.valor_venda)
  if (isDifferentProduct) {
    draft.itemQuantidade = '1'
    draft.itemObservacao = ''
  }
  productLookupOpen.value = false
}

function openAvalistaLookup() {
  draft.avalistaTerm = ''
  avalistaLookup.page = 1
  avalistaLookupOpen.value = true
}

function closeAvalistaLookup() {
  avalistaLookupOpen.value = false
}

function changeAvalistaPage(page: number) {
  if (page < 1 || page > avalistaTotalPages.value) {
    return
  }

  avalistaLookup.page = page
}

function openProductLookup() {
  draft.productTerm = ''
  productLookupOpen.value = true
  if (productOptions.value.length === 0 && !productsLoading.value) {
    void loadProducts()
  }
}

function closeProductLookup() {
  productLookupOpen.value = false
}

function resetItemEditor() {
  draft.itemProdutoId = null
  draft.itemQuantidade = '1'
  draft.itemValorUnitario = ''
  draft.itemObservacao = ''
  draft.editingItemIndex = null
}

function formatItemValue() {
  draft.itemValorUnitario = formatMoneyInput(parseMoney(draft.itemValorUnitario))
}

function addOrUpdateItem() {
  if (draft.itemProdutoId === null) {
    void infoAlert('Selecione um produto para continuar.')
    return
  }

  const quantity = Number(draft.itemQuantidade)
  if (!Number.isFinite(quantity) || quantity <= 0) {
    void infoAlert('Informe uma quantidade válida para o produto.')
    return
  }

  const product = productOptions.value.find((item) => item.produto_id === draft.itemProdutoId)
  if (!product) {
    void infoAlert('Produto selecionado não encontrado na lista atual.')
    return
  }

  const nextItem: DraftItem = {
    item_id: draft.editingItemIndex === null ? 0 : draft.items[draft.editingItemIndex]?.item_id ?? 0,
    produto_id: product.produto_id,
    produto_descricao: product.descricao || `Produto ${product.produto_id}`,
    quantidade: quantity,
    valor_unitario: parseMoney(draft.itemValorUnitario),
    observacao: draft.itemObservacao.trim() || null,
    localKey: draft.editingItemIndex === null ? `local-${nextLocalKey.value++}` : draft.items[draft.editingItemIndex]?.localKey ?? `local-${nextLocalKey.value++}`,
  }

  if (draft.editingItemIndex === null) {
    draft.items.push(nextItem)
  } else {
    draft.items.splice(draft.editingItemIndex, 1, nextItem)
  }

  resetItemEditor()
}

function editItem(index: number) {
  const item = draft.items[index]
  draft.editingItemIndex = index
  draft.itemProdutoId = item.produto_id
  draft.itemQuantidade = String(item.quantidade)
  draft.itemValorUnitario = formatMoneyInput(item.valor_unitario)
  draft.itemObservacao = item.observacao || ''
}

function removeItem(index: number) {
  draft.items.splice(index, 1)
  if (draft.editingItemIndex === index) {
    resetItemEditor()
  } else if (draft.editingItemIndex !== null && draft.editingItemIndex > index) {
    draft.editingItemIndex -= 1
  }
}

function itemSubtotalValue(item: { quantidade: number; valor_unitario: number | null }) {
  return Number(item.quantidade || 0) * Number(item.valor_unitario || 0)
}

function emitSave() {
  const payload: ContractComodatoInput = {
    avalista_id: draft.avalista_id,
    items: draft.items.map<ContractComodatoItemInput>((item) => ({
      item_id: item.item_id > 0 ? item.item_id : null,
      produto_id: item.produto_id,
      quantidade: item.quantidade,
      valor_unitario: item.valor_unitario,
      observacao: item.observacao,
    })),
  }
  emit('save', payload)
}

async function handleDeleteComodato() {
  const confirmed = await confirmActionAlert('Excluir comodato?', 'Essa ação remove o avalista e todos os itens do comodato.', 'Excluir')
  if (!confirmed) {
    return
  }

  emit('delete')
}

function formatClientAddress(client: Client) {
  return [client.endereco, client.nro, client.uf].filter(Boolean).join(' - ') || 'Sem endereço'
}

function parseMoney(value: string | number | null) {
  if (value === null || value === '') {
    return null
  }
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null
  }
  const normalized = value.trim()
  if (!normalized) {
    return null
  }
  const sanitized = normalized.includes(',') && normalized.includes('.') ? normalized.replace(/\./g, '').replace(',', '.') : normalized.replace(',', '.')
  const parsed = Number(sanitized)
  return Number.isFinite(parsed) ? parsed : null
}

function formatMoneyInput(value: string | number | null) {
  const parsed = parseMoney(value)
  if (parsed === null) {
    return ''
  }
  return parsed.toFixed(2).replace('.', ',')
}

function formatCurrency(value: number | null) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value ?? 0)
}
</script>

<style scoped>
.modal-card--comodato {
  width: min(1100px, calc(100vw - 2rem));
  max-height: calc(100vh - 3rem);
  overflow: auto;
}

.modal-card--lookup {
  width: min(760px, calc(100vw - 2rem));
  max-height: calc(100vh - 4rem);
  overflow: auto;
}

.modal-backdrop--nested {
  background: rgba(15, 23, 42, 0.5);
}

.comodato-modal__body {
  display: grid;
  gap: 1rem;
}

.comodato-modal__section {
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 3px;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.78);
}

.comodato-modal__section-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.comodato-modal__section-header h4 {
  margin: 0;
}

.comodato-modal__selected {
  color: #475569;
  font-size: 0.92rem;
}

.comodato-modal__results {
  display: grid;
  gap: 0.55rem;
  max-height: 220px;
  overflow: auto;
  margin-top: 0.75rem;
}

.comodato-modal__results--products {
  max-height: 180px;
}

.comodato-modal__picker {
  align-items: stretch;
}

.comodato-modal__picker-embedded {
  position: relative;
  width: 100%;
}

.comodato-modal__picker-field {
  flex: 1 1 auto;
}

.comodato-modal__picker-field--embedded {
  padding-right: 3.2rem;
}

.comodato-modal__picker-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.9rem;
  padding-inline: 0.75rem;
}

.comodato-modal__picker-button--embedded {
  position: absolute;
  top: 0;
  right: 0;
  transform: none;
  min-width: 2.8rem;
  width: 2.8rem;
  height: calc(100% - 1px);
  padding: 0;
  border: 0;
  border-radius: 0 0.35rem 0.35rem 0;
  background: #f59e0b;
  color: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.12), inset 0 0 0 1px rgba(255, 255, 255, 0.12);
}

.comodato-modal__picker-button--embedded:hover {
  background: #ea9509;
}

.comodato-modal__picker-button--embedded:focus-visible {
  outline: 2px solid rgba(245, 158, 11, 0.3);
  outline-offset: 1px;
}

.comodato-modal__picker-button svg {
  width: 1.18rem;
  height: 1.18rem;
}

.comodato-modal__result {
  display: grid;
  gap: 0.2rem;
  text-align: left;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 14px;
  padding: 0.8rem 0.9rem;
  background: #fff;
}

.comodato-modal__result--active {
  border-color: #0f766e;
  box-shadow: 0 0 0 1px rgba(15, 118, 110, 0.16);
}

.comodato-modal__inline-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.75rem;
}

.comodato-modal__item-form {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: minmax(0, 2.4fr) repeat(3, minmax(120px, 0.75fr));
  margin-top: 1rem;
  align-items: end;
}

.comodato-modal__field--compact {
  min-width: 0;
}

.comodato-modal__field--product {
  min-width: 0;
}

.comodato-modal__field--observation {
  grid-column: 1 / span 2;
}

.comodato-modal__field--total {
  min-width: 0;
}

.comodato-modal__observation {
  min-height: 4.3rem;
  resize: vertical;
}

.comodato-modal__item-actions {
  justify-content: flex-end;
  align-self: end;
}

.comodato-modal__table-wrap {
  margin-top: 1rem;
}

.comodato-modal__table th,
.comodato-modal__table td {
  vertical-align: middle;
}

.comodato-modal__actions-cell {
  display: inline-flex;
  gap: 0.4rem;
  justify-content: flex-end;
  width: 100%;
}

.comodato-modal__actions-header,
.comodato-modal__actions-column {
  text-align: right;
}

.comodato-modal__footer {
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .comodato-modal__item-form {
    grid-template-columns: 1fr;
  }

  .comodato-modal__field--observation {
    grid-column: auto;
  }

  .comodato-modal__item-actions {
    justify-content: stretch;
  }
}
</style>