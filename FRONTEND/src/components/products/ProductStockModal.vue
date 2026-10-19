<template>
  <Teleport to="body">
    <div class="modal-backdrop stock-backdrop" @click.self="close">
      <section class="modal-card stock-modal" role="dialog" aria-modal="true" aria-labelledby="stock-title">
        <header class="panel__header panel__header--stacked">
          <div><h3 id="stock-title" class="panel__title">{{ returnItemId ? 'Receber devolução' : 'Estoque do produto' }}</h3><p class="modal-context">{{ product?.descricao ?? 'Carregando...' }}</p></div>
          <button class="ghost-button" :disabled="saving" type="button" @click="close">Fechar</button>
        </header>
        <div class="modal-form">
          <p v-if="loadError" class="feedback feedback--error">{{ loadError }}</p>
          <template v-if="product">
            <div class="summary-row">
              <article v-for="entry in summary" :key="entry.label" class="summary-chip"><strong :class="entry.value < 0 ? 'feedback--error' : ''">{{ entry.value }}</strong><span>{{ entry.label }}</span></article>
            </div>
            <p v-if="product.permite_vender_sem_estoque" class="feedback feedback--info">Venda sem estoque permitida. Novos e usados podem apresentar saldo negativo.</p>
            <p v-if="returnItemId" class="feedback feedback--info">Confirme somente os produtos recebidos e aptos para revenda. Pendente: {{ returnRemaining }} unidade(s). A devolução não altera as parcelas do contrato.</p>
            <form class="form-grid" @submit.prevent="submit">
              <fieldset :disabled="saving || loading" class="stock-fields field-group--span-2">
                <label class="field-group"><span>Operação</span><select v-model="form.tipo" class="field" :disabled="Boolean(returnItemId)"><option v-if="!returnItemId" value="entrada">Dar entrada</option><option v-if="!returnItemId" value="baixa">Dar baixa</option><option v-if="!returnItemId" value="ajuste">Ajustar estoque</option><option v-if="returnItemId" value="devolucao">Devolução de cliente</option></select></label>
                <label class="field-group"><span>Condição</span><select v-model="form.condicao" class="field"><option value="novo">Novo · {{ product.estoque_novos }}</option><option value="usado">Usado · {{ product.estoque_usados }}</option></select></label>
                <label class="field-group"><span>{{ form.tipo === 'ajuste' ? 'Quantidade física contada' : 'Quantidade' }}</span><input v-model.number="form.quantidade" class="field" required type="number" step="1" :min="form.tipo === 'ajuste' ? 0 : 1" :max="returnItemId ? returnRemaining : 1000000000" /></label>
                <label class="field-group"><span>Motivo</span><select v-model="form.motivo" class="field"><option v-for="reason in stockReasons[form.tipo]" :key="reason">{{ reason }}</option></select></label>
                <label class="field-group field-group--span-2"><span>Observação / justificativa</span><textarea v-model="form.observacao" class="field" required minlength="3" maxlength="1000" rows="2"></textarea></label>
              </fieldset>
              <p class="feedback feedback--info field-group--span-2">Saldo atual: {{ balance }} · {{ delta >= 0 ? 'Entrada' : 'Saída' }}: {{ Math.abs(delta) }} · Saldo após confirmação: {{ balance + delta }}</p>
              <div class="form-actions field-group--span-2"><button class="secondary-button" :disabled="saving || loading" type="button" @click="reload">Atualizar saldos</button><button class="primary-button primary-button--success" :disabled="saving || loading" type="submit">{{ saving ? 'Registrando...' : 'Confirmar movimentação' }}</button></div>
            </form>
            <h4>Histórico de entradas e saídas</h4>
            <div class="table-wrap"><table class="data-table data-table--users">
              <thead><tr><th>Data</th><th>Operação</th><th>Condição</th><th>Entrada / saída</th><th>Antes</th><th>Depois</th><th>Motivo / observação</th><th>Responsável</th></tr></thead>
              <tbody><tr v-if="!history.items.length"><td colspan="8">Nenhuma movimentação registrada.</td></tr>
                <tr v-for="movement in history.items" :key="movement.movimento_id"><td>{{ new Date(movement.criado_em).toLocaleString('pt-BR') }}</td><td>{{ labels[movement.tipo] ?? movement.tipo }}</td><td>{{ movement.condicao === 'novo' ? 'Novo' : 'Usado' }}</td><td><span :class="['pill', movement.quantidade < 0 ? 'pill--danger' : 'pill--success']">{{ movement.quantidade > 0 ? '+' : '' }}{{ movement.quantidade }}</span></td><td>{{ movement.saldo_antes }}</td><td>{{ movement.saldo_depois }}</td><td>{{ movement.motivo }}<small class="stock-note">{{ movement.observacao }}</small></td><td>{{ movement.usuario_nome }}</td></tr>
              </tbody>
            </table></div>
            <footer class="pagination-compact"><div class="pagination-compact__status">{{ history.total }} movimentações · Página {{ page }}</div><div class="pagination-compact__actions"><button class="pagination-compact__button" :disabled="page <= 1 || loading || saving" type="button" @click="changePage(-1)">‹</button><button class="pagination-compact__button" :disabled="page * 10 >= history.total || loading || saving" type="button" @click="changePage(1)">›</button></div></footer>
          </template>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import type { Product } from '@/models/product'
import { getProductById } from '@/services/productService'
import { confirmActionAlert, errorAlert, successAlert } from '@/services/alertService'
import { getStockHistory, moveStock, stockReasons, type StockHistory, type StockInput, type StockKind } from '@/services/stockService'

const props = defineProps<{ productId: number; returnItemId?: number; returnRemaining?: number }>()
const emit = defineEmits<{ close: []; changed: [] }>()
const product = ref<Product | null>(null)
const history = ref<StockHistory>({ items: [], total: 0, page: 1, page_size: 10 })
const page = ref(1)
const saving = ref(false)
const loading = ref(true)
const loadError = ref('')
const labels: Record<string, string> = { entrada: 'Entrada', baixa: 'Baixa', ajuste: 'Ajuste', devolucao: 'Devolução', venda: 'Venda' }
const form = reactive({ tipo: (props.returnItemId ? 'devolucao' : 'entrada') as StockKind, condicao: (props.returnItemId ? 'usado' : 'novo') as 'novo' | 'usado', quantidade: 1, motivo: props.returnItemId ? 'Devolução de cliente' : 'Estoque inicial', observacao: '' })
// Retain the key on retries of an identical request, including network failures.
let pending: { signature: string; key: string } | null = null
const summary = computed(() => [{ label: 'Novos', value: product.value?.estoque_novos ?? 0 }, { label: 'Usados', value: product.value?.estoque_usados ?? 0 }, { label: 'Total', value: product.value?.estoque ?? 0 }])
const balance = computed(() => (form.condicao === 'novo' ? product.value?.estoque_novos : product.value?.estoque_usados) ?? 0)
const delta = computed(() => form.tipo === 'ajuste' ? Number(form.quantidade) - balance.value : (form.tipo === 'baixa' ? -1 : 1) * Number(form.quantidade))
watch(() => form.tipo, kind => { form.motivo = stockReasons[kind][0]; form.quantidade = kind === 'ajuste' ? Math.max(0, balance.value) : 1 })
onMounted(reload)
function close() { if (!saving.value) emit('close') }
async function reload() {
  loading.value = true
  loadError.value = ''
  try {
    const [record, movements] = await Promise.all([getProductById(props.productId), getStockHistory(props.productId, page.value)])
    product.value = record
    history.value = movements
  } catch (error) { loadError.value = error instanceof Error ? error.message : 'Falha ao carregar estoque'; await errorAlert(loadError.value) }
  finally { loading.value = false }
}
async function changePage(direction: number) { page.value += direction; await reload() }
async function submit() {
  if (!product.value || saving.value) return
  if (!Number.isSafeInteger(form.quantidade) || form.quantidade < (form.tipo === 'ajuste' ? 0 : 1) || form.observacao.trim().length < 3) {
    await errorAlert('Informe uma quantidade inteira válida e uma justificativa com pelo menos 3 caracteres.'); return
  }
  if (form.tipo === 'baixa' && balance.value + delta.value < 0) { await errorAlert('A baixa não pode superar o saldo disponível nesta condição.'); return }
  saving.value = true
  try {
    const data = { ...form, observacao: form.observacao.trim(), ...(form.tipo === 'ajuste' ? { versao_esperada: product.value.estoque_versao } : {}), ...(props.returnItemId ? { item_id: props.returnItemId } : {}) }
    const signature = JSON.stringify(data)
    if (pending?.signature !== signature) pending = { signature, key: operationId() }
    const payload: StockInput = { ...data, operacao_id: pending.key }
    if (!(await confirmActionAlert(`${labels[form.tipo]} de estoque?`, `${form.condicao === 'novo' ? 'Novos' : 'Usados'}: ${balance.value} → ${balance.value + delta.value}. ${Math.abs(delta.value)} unidade(s) de ${delta.value < 0 ? 'saída' : 'entrada'}.`, 'Confirmar'))) return
    await moveStock(props.productId, payload)
    pending = null
    form.observacao = ''
    page.value = 1
    await reload()
    await successAlert('Movimentação registrada com sucesso.')
    emit('changed')
  } catch (error) { await errorAlert(error instanceof Error ? error.message : 'Falha ao movimentar estoque') }
  finally { saving.value = false }
}
function operationId() {
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 15) | 64
  bytes[8] = (bytes[8] & 63) | 128
  const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}
</script>

<style scoped>
.stock-backdrop { z-index: 1001; }
.stock-modal { width: min(1150px, calc(100vw - 2rem)); max-height: calc(100vh - 3rem); overflow: auto; }
.stock-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; border: 0; padding: 0; margin: 0; min-width: 0; }
.stock-note { display: block; max-width: 320px; white-space: normal; overflow-wrap: anywhere; }
@media (max-width: 650px) { .stock-fields { grid-template-columns: 1fr; } .stock-fields .field-group--span-2 { grid-column: auto; } }
</style>
