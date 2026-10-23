<template>
  <section class="report-shell"><div class="report-box">
    <header><h2>Relatório de Contas a Receber</h2></header>
    <div class="fields">
      <label>Período <span><input v-model="start" class="field" type="date"><b>até</b><input v-model="end" class="field" type="date"></span></label>
      <label>Funcionário<select v-model="employee" class="field"><option value="">TODOS OS FUNCIONÁRIOS</option><option v-for="user in users" :key="user.id" :value="String(user.id)">{{ user.nome }}</option></select></label>
      <label>Cliente<input v-model="clientTerm" class="field" placeholder="Digite ao menos 3 letras ou números" @input="searchClients"></label>
      <ul v-if="clients.length" class="suggestions"><li v-for="item in clients" :key="item.clientes_id" @click="selectClient(item)">{{ item.nome }} <small>{{ item.cpf_cnpj || '' }}</small></li></ul>
      <p v-if="selectedClient" class="selected-client">Cliente: {{ selectedClient.nome }} <button @click="clearClient">×</button></p>
      <label>Comodato<select v-model="comodato" class="field"><option value="">COM E SEM COMODATO</option><option value="true">SOMENTE COM COMODATO</option><option value="false">SOMENTE SEM COMODATO</option></select></label>
    </div>
    <footer><button class="primary-button" @click="print">🖨 Imprimir</button><button @click="reset">✖ Cancelar</button></footer>
    <p v-if="error" class="feedback feedback--error">{{ error }}</p>
  </div></section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiFetch, apiFetchBlob } from '@/services/http'

const today = new Date().toISOString().slice(0, 10)
type Client = { clientes_id: number; nome: string | null; cpf_cnpj: string | null }
const start = ref(today), end = ref(today), employee = ref(''), comodato = ref(''), error = ref(''), clientTerm = ref(''), clients = ref<Client[]>([]), selectedClient = ref<Client | null>(null)
const users = ref<Array<{ id: number; nome: string }>>([])
let searchTimer: number | undefined
onMounted(async () => { try { users.value = await apiFetch('/financeiro/relatorios/recebimentos/cobradores') } catch { error.value = 'Não foi possível carregar os funcionários.' } })
function searchClients() { selectedClient.value = null; window.clearTimeout(searchTimer); const term = clientTerm.value.trim(); if (term.length < 3) { clients.value = []; return }; searchTimer = window.setTimeout(async () => { try { clients.value = (await apiFetch<{ items: Client[] }>(`/clientes/?page=1&page_size=8&nome=${encodeURIComponent(term)}`)).items } catch { clients.value = [] } }, 250) }
function selectClient(client: Client) { selectedClient.value = client; clientTerm.value = client.nome || ''; clients.value = [] }
function clearClient() { selectedClient.value = null; clientTerm.value = ''; clients.value = [] }
function reset() { start.value = today; end.value = today; employee.value = ''; comodato.value = ''; clearClient(); error.value = '' }
async function print() {
  error.value = ''
  const query = new URLSearchParams({ data_inicial: start.value, data_final: end.value })
  if (employee.value) query.set('funcionario_id', employee.value)
  if (selectedClient.value) query.set('cliente_id', String(selectedClient.value.clientes_id))
  if (comodato.value) query.set('comodato', comodato.value)
  try { const blob = await apiFetchBlob(`/financeiro/relatorios/contas-a-receber/imprimir?${query}`), url = URL.createObjectURL(blob); window.open(url, '_blank', 'noopener,noreferrer'); window.setTimeout(() => URL.revokeObjectURL(url), 60000) } catch (cause) { error.value = cause instanceof Error ? cause.message : 'Não foi possível gerar o relatório.' }
}
</script>

<style scoped>
.report-shell{padding:24px}.report-box{max-width:580px;margin:auto;border-top:2px solid #f59e0b;background:#fff;box-shadow:0 1px 8px #0002}.report-box header{padding:14px 18px;background:#f8fafc}.report-box h2{margin:0;font-size:17px;color:#374151}.fields{position:relative;padding:26px 106px;display:grid;gap:13px}.fields>label{display:grid;grid-template-columns:78px 1fr;align-items:center;gap:8px;font-size:13px}.fields span{display:flex;gap:8px;align-items:center}.fields span input{min-width:0}.suggestions{position:absolute;z-index:3;left:192px;right:106px;top:135px;margin:0;padding:0;list-style:none;border:1px solid #cbd5e1;background:#fff}.suggestions li{padding:6px 8px;cursor:pointer}.suggestions li:hover{background:#eff6ff}.suggestions small{color:#64748b}.selected-client{margin:0 0 0 86px;font-size:12px;color:#475569}.selected-client button{border:0;background:none;color:#dc2626;font-size:16px}footer{padding:14px;text-align:center;border-top:1px solid #e5e7eb;background:#f8fafc}footer button{margin:0 3px}.feedback{margin:0;padding:0 18px 14px;font-size:12px}@media(max-width:600px){.fields{padding:20px}.fields>label{grid-template-columns:1fr}.selected-client{margin-left:0}.suggestions{left:20px;right:20px;top:166px}}
</style>
