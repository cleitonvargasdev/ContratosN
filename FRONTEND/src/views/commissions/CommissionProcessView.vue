<template>
  <section class="panel">
    <header class="panel__header">
      <h2>Processar Comissões</h2>
      <RouterLink class="ghost-button commission-back-button" to="/comissoes">Voltar</RouterLink>
    </header>

    <div class="controls">
      <label class="employee-field">Funcionário
        <select v-model="userId" class="field"><option value="">Selecione</option><option v-for="user in users" :key="user.id" :value="user.id">{{ user.nome }}</option></select>
      </label>
      <label>Processar até<input v-model="endDate" class="field" type="date" /></label>
      <label class="portfolio-card">
        <span>Todos da Carteira</span>
        <input v-model="todosCarteira" type="checkbox" />
      </label>
      <button class="primary-button preview-button" type="button" :disabled="!userId" @click="loadPreview">Gerar prévia</button>
    </div>
    <p class="period-hint">Considera comissões elegíveis de 01/01/1900 até a data informada.</p>
    <p v-if="message" class="message">{{ message }}</p>

    <template v-if="items.length">
      <div class="grid-head">
        <label title="Marcar / Desmarcar todos"><input v-model="all" type="checkbox" @change="toggleAll" /> Todos</label>
      </div>
      <div class="table-wrap">
      <table class="data-table data-table--cadastro commissions-grid">
        <thead><tr><th>Marcar</th><th>Data</th><th>Contrato</th><th>Parcela</th><th>Tipo</th><th>Taxa %</th><th>Valor Comissão</th></tr></thead>
        <tbody>
          <tr v-for="item in items" :key="item.comissao_id" class="data-table__row">
            <td><input v-model="selected" :value="item.comissao_id" type="checkbox" /></td>
            <td>{{ date(item.competencia) }}</td><td>{{ String(item.contrato_id).padStart(8, '0') }}</td><td>{{ item.parcela_nro || '-' }}</td>
            <td>{{ item.tipo === 'cobranca' ? 'Recebimento' : 'Venda' }}</td><td>{{ number(item.percentual) }}</td><td>{{ money(item.valor_comissao) }}</td>
          </tr>
        </tbody>
      </table>
      </div>
      <div class="process-actions"><button class="process-button" type="button" :disabled="!selected.length" @click="process">Processar</button></div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { apiFetch } from '@/services/http'

const users = ref<any[]>([])
const items = ref<any[]>([])
const selected = ref<number[]>([])
const all = ref(true)
const userId = ref('')
const endDate = ref(new Date().toISOString().slice(0, 10))
const todosCarteira = ref(false)
const message = ref('')

async function loadPreview() {
  try {
    const query = new URLSearchParams({ funcionario_id: userId.value, data_final: endDate.value, todos_carteira: String(todosCarteira.value) })
    items.value = await apiFetch(`/financeiro/comissoes/previa?${query}`)
    selected.value = items.value.map((item: any) => item.comissao_id)
    all.value = true
    message.value = items.value.length ? 'Prévia carregada.' : 'Nenhuma comissão elegível encontrada.'
  } catch (error) { message.value = error instanceof Error ? error.message : 'Falha ao carregar prévia.' }
}

onMounted(async () => { const result: any = await apiFetch('/usuarios/?page=1&page_size=100&ativo=true'); users.value = result.items || [] })
function toggleAll() { selected.value = all.value ? items.value.map((item: any) => item.comissao_id) : [] }
function date(value: string) { const parts = String(value).split('-'); return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : value }
function money(value: number) { return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value || 0) }
function number(value: number) { return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value || 0) }
async function process() {
  try {
    await apiFetch('/financeiro/comissoes/reprocessar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ funcionario_id: Number(userId.value), data_final: endDate.value, todos_carteira: todosCarteira.value, comissao_ids: selected.value }) })
    message.value = 'Lote e conta a pagar gerados.'
    items.value = []; selected.value = []
  } catch (error) { message.value = error instanceof Error ? error.message : 'Falha ao processar.' }
}
</script>

<style scoped>
.controls{display:grid;grid-template-columns:minmax(380px,1fr) 160px 175px 110px;gap:.75rem;align-items:end}.controls label{display:grid;gap:.3rem;font-size:.82rem;color:#475569}.commission-back-button{display:inline-flex;align-items:center;justify-content:center;text-decoration:none;background:rgba(59,130,246,.1);border-color:rgba(59,130,246,.24);color:#2563eb}.commission-back-button:hover{background:rgba(59,130,246,.17);border-color:rgba(59,130,246,.34)}.preview-button{width:110px;padding:0 8px}.portfolio-card{height:34px;min-height:34px;box-sizing:border-box;padding:0 .65rem;grid-template-columns:1fr auto!important;align-items:center;gap:.55rem!important;border:1px solid #d9e9df;border-radius:5px;background:#f2fbf5;color:#2c6c4c!important;font-weight:600}.portfolio-card input,.grid-head input,.commissions-grid input[type="checkbox"]{appearance:none;width:14px;height:14px;margin:0;border:1px solid #fb923c;border-radius:3px;background:#fff;cursor:pointer}.portfolio-card input:checked,.grid-head input:checked,.commissions-grid input[type="checkbox"]:checked{background:#fb923c;box-shadow:inset 0 0 0 3px #fff}.period-hint{margin:.65rem 0;color:#64748b;font-size:.8rem}.message{margin:.5rem 0;color:#475569}.grid-head{display:flex;justify-content:flex-start;margin-top:1rem}.grid-head label{display:inline-flex;align-items:center;gap:.45rem;color:#334155;font-size:.82rem;font-weight:600;cursor:pointer}.commissions-grid th:nth-last-child(2),.commissions-grid th:last-child,.commissions-grid td:nth-last-child(2),.commissions-grid td:last-child{text-align:right}.process-actions{display:flex;justify-content:flex-end;margin-top:10px}.process-button{min-height:34px;padding:0 1rem;border:1px solid #9ed5b3;border-radius:5px;background:#eaf8ee;color:#23734a;font-size:.8rem;font-weight:700}.process-button:disabled{opacity:.55;cursor:not-allowed}
</style>
