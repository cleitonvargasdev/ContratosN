<template>
  <section class="panel">
    <header class="panel__header"><div><p class="eyebrow">Movimentações</p><h2 class="panel__title">Entrada de estoque</h2><p class="hint">Inclua as linhas e confirme somente ao final.</p></div></header>
    <p v-if="error" class="feedback feedback--error">{{ error }}</p>
    <div class="table-wrap"><table class="data-table stock-entry-table"><thead><tr><th>Produto</th><th>Quantidade</th><th>Condição</th><th>Valor de compra</th><th>Valor de venda</th><th>Ações</th></tr></thead><tbody>
      <tr v-for="(line, index) in lines" :key="line.key"><td><button class="product-picker" type="button" @click="openPicker(index)">{{ line.product ? `${line.product.produto_id} — ${line.product.descricao}` : 'Buscar produto...' }}</button></td><td><input :id="`quantity-${line.key}`" v-model.number="line.quantidade" class="field" min="1" type="number" /></td><td><select v-model="line.condicao" class="field"><option value="novo">Novo</option><option value="usado">Usado</option></select></td><td><input v-model="line.valor_compra" class="field" inputmode="decimal" placeholder="0,00" /></td><td><input v-model="line.valor_venda" class="field" inputmode="decimal" placeholder="0,00" /></td><td class="actions-cell"><button class="icon-action" type="button" title="Adicionar linha" @click="addLine">+</button><button v-if="lines.length > 1" class="icon-action icon-action--danger" type="button" title="Remover linha" @click="removeLine(index)">−</button></td></tr>
    </tbody></table></div>
    <div class="form-actions"><button class="secondary-button" :disabled="saving" type="button" @click="cancel">Cancelar</button><button class="primary-button primary-button--success" :disabled="saving" type="button" @click="confirm">{{ saving ? 'Confirmando...' : 'Confirmar' }}</button></div>
    <div v-if="pickerOpen" class="modal-backdrop" @click.self="pickerOpen = false"><section class="modal-card picker-modal" role="dialog" aria-modal="true"><header class="panel__header"><h3 class="panel__title">Selecionar produto</h3><button class="icon-action" type="button" @click="pickerOpen = false">×</button></header><input v-model="search" autofocus class="field" placeholder="Código ou descrição" @input="searchProducts" /><p v-if="loadingProducts" class="hint">Buscando produtos...</p><div class="picker-results"><button v-for="product in products" :key="product.produto_id" type="button" @click="chooseProduct(product)"><strong>{{ product.produto_id }}</strong> · {{ product.descricao }}<small>Compra: {{ money(product.valor_compra) }} · Venda: {{ money(product.valor_venda) }}</small></button><p v-if="!loadingProducts && !products.length" class="hint">Nenhum produto encontrado.</p></div></section></div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import type { Product } from '@/models/product'
import { listProducts } from '@/services/productService'
import { purchaseStockBatch } from '@/services/stockService'
import { errorAlert, successAlert } from '@/services/alertService'

type Line = { key: string; product: Product | null; quantidade: number; condicao: 'novo' | 'usado'; valor_compra: string; valor_venda: string }
const newLine = (): Line => ({ key: crypto.randomUUID(), product: null, quantidade: 1, condicao: 'novo', valor_compra: '', valor_venda: '' })
const lines = ref<Line[]>([newLine()]); const pickerOpen = ref(false); const pickerIndex = ref(0); const search = ref(''); const products = ref<readonly Product[]>([]); const loadingProducts = ref(false); const saving = ref(false); const error = ref('')
const money = (v: number | null) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v ?? 0)
const parseMoney = (v: string) => Number(v.replace(/\./g, '').replace(',', '.'))
function addLine() { lines.value.push(newLine()) }
function removeLine(index: number) { lines.value.splice(index, 1) }
async function openPicker(index: number) { pickerIndex.value = index; pickerOpen.value = true; search.value = ''; await searchProducts() }
async function searchProducts() { loadingProducts.value = true; try { products.value = (await listProducts({ page: 1, page_size: 20, descricao: search.value, ativo: true })).items } finally { loadingProducts.value = false } }
async function chooseProduct(product: Product) { const line = lines.value[pickerIndex.value]; line.product = product; line.valor_compra = product.valor_compra?.toFixed(2).replace('.', ',') ?? ''; line.valor_venda = product.valor_venda?.toFixed(2).replace('.', ',') ?? ''; pickerOpen.value = false; await nextTick(); document.getElementById(`quantity-${line.key}`)?.focus() }
function cancel() { lines.value = [newLine()]; error.value = '' }
async function confirm() { error.value = ''; const invalid = lines.value.find(line => !line.product || !Number.isInteger(line.quantidade) || line.quantidade < 1 || !Number.isFinite(parseMoney(line.valor_compra)) || !Number.isFinite(parseMoney(line.valor_venda))); if (invalid) { error.value = 'Preencha produto, quantidade e valores de compra e venda em todas as linhas.'; return }; saving.value = true; try { await purchaseStockBatch(lines.value.map(line => ({ produto_id: line.product!.produto_id, operacao_id: crypto.randomUUID(), quantidade: line.quantidade, condicao: line.condicao, valor_compra: parseMoney(line.valor_compra), valor_venda: parseMoney(line.valor_venda) }))); await successAlert('Entrada de estoque registrada com sucesso.'); cancel() } catch (cause) { await errorAlert(cause instanceof Error ? cause.message : 'Não foi possível registrar a entrada.') } finally { saving.value = false } }
</script>

<style scoped>
.stock-entry-table { min-width: 880px; }.stock-entry-table .field { min-width: 105px; }.product-picker { background: #fff; border: 1px solid #d6d8dc; border-radius: 6px; cursor: pointer; min-height: 38px; padding: 8px; text-align: left; width: 100%; }.product-picker:hover { border-color: var(--primary); }.form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 18px; }.picker-modal { max-width: 650px; width: calc(100vw - 2rem); }.picker-results { margin-top: 12px; max-height: 360px; overflow: auto; }.picker-results button { background: #fff; border: 0; border-bottom: 1px solid #e5e7eb; cursor: pointer; display: block; padding: 11px; text-align: left; width: 100%; }.picker-results button:hover { background: #f4f7fb; }.picker-results small { color: var(--text-muted); display: block; margin-top: 3px; }
</style>
