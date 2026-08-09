<template>
  <section class="panel">
    <header class="panel__header"><h2>Lotes de Comissões</h2><RouterLink class="process-button" to="/comissoes/processar">Processar Comissões</RouterLink></header>
    <div class="filters">
      <label>Funcionário<select v-model="filters.funcionarioId" class="field"><option value="">Todos</option><option v-for="user in users" :key="user.id" :value="String(user.id)">{{ user.nome }}</option></select></label>
      <label>Mês<select v-model="filters.mes" class="field"><option value="">Todos</option><option v-for="month in months" :key="month.value" :value="month.value">{{ month.label }}</option></select></label>
      <label>Ano<input v-model="filters.ano" class="field" inputmode="numeric" /></label>
      <label>Situação<select v-model="filters.situacao" class="field"><option value="">Todos</option><option value="1">Gerada</option><option value="2">Pendente</option><option value="3">Paga</option></select></label>
      <button class="apply-button" type="button" @click="loadBatches">Aplicar filtros</button>
    </div>
    <table class="client-grid"><thead><tr><th>Nº</th><th>Data lote</th><th>Funcionário</th><th>Data inicial</th><th>Data final</th><th>Situação</th><th>Conta a pagar</th><th class="right">Valor lote</th><th class="action">Ação</th></tr></thead><tbody>
      <tr v-for="item in items" :key="item.lote_id"><td>{{ String(item.lote_id).padStart(5, '0') }}</td><td>{{ date(item.data_lote) }}</td><td>{{ item.funcionario_nome }}</td><td>{{ date(item.data_inicial) }}</td><td>{{ date(item.data_final) }}</td><td>{{ label(item.situacao) }}</td><td>{{ item.conta_pagar_id ? String(item.conta_pagar_id).padStart(8, '0') : '-' }}</td><td class="right">{{ money(item.valor_lote) }}</td><td class="action"><div class="action-buttons">
        <RouterLink v-if="item.conta_pagar_id" class="calculator" :to="`/contas-pagar/${item.conta_pagar_id}/editar`" title="Ir para conta a pagar" aria-label="Ir para conta a pagar"><svg viewBox="0 0 32 32" aria-hidden="true"><rect x="5" y="3" width="22" height="26" rx="4"/><path d="M10 9h12M11 16h3m7-1.5v5m-2.5-2.5h5M11 23h3m5 0h3"/></svg></RouterLink>
        <button class="icon-action" type="button" title="Imprimir Lista de Comissões" aria-label="Imprimir Lista de Comissões" @click="printBatch(item.lote_id)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3Zm-3 11H8v-5h8v5Zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1Zm-1-9H6v4h12V3Z" fill="currentColor"/></svg></button>
        <button v-if="item.situacao !== 3" class="icon-action icon-action--danger" type="button" title="Excluir lote de comissão" aria-label="Excluir lote de comissão" @click="removeBatch(item)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor"/></svg></button>
      </div></td></tr>
    </tbody></table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { apiFetch, apiFetchBlob } from '@/services/http'
import { confirmActionAlert, errorAlert, successAlert } from '@/services/alertService'

const items = ref<any[]>([])
const users = ref<any[]>([])
const filters = reactive({ funcionarioId: '', mes: '', ano: String(new Date().getFullYear()), situacao: '' })
const months = [{ value: '01', label: 'Jan' }, { value: '02', label: 'Fev' }, { value: '03', label: 'Mar' }, { value: '04', label: 'Abr' }, { value: '05', label: 'Mai' }, { value: '06', label: 'Jun' }, { value: '07', label: 'Jul' }, { value: '08', label: 'Ago' }, { value: '09', label: 'Set' }, { value: '10', label: 'Out' }, { value: '11', label: 'Nov' }, { value: '12', label: 'Dez' }]
const date = (value: string) => { const parts = String(value).split('-'); return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : '-' }
const money = (value: number) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(value || 0)
const label = (value: number) => ['', 'Gerada', 'Pendente', 'Paga'][value]

onMounted(async () => { const result: any = await apiFetch('/usuarios/?page=1&page_size=100&ativo=true'); users.value = result.items || []; await loadBatches() })
async function loadBatches() { const params = new URLSearchParams(); if (filters.funcionarioId) params.set('funcionario_id', filters.funcionarioId); if (filters.ano && filters.mes) params.set('ano_mes', `${filters.ano}-${filters.mes}`); if (filters.situacao) params.set('situacao', filters.situacao); items.value = await apiFetch(`/financeiro/comissoes/lotes${params.size ? `?${params}` : ''}`) }
async function removeBatch(item: any) { const confirmed = await confirmActionAlert('Excluir lote de comissões?', `A conta a pagar e o lote ${String(item.lote_id).padStart(5, '0')} serão excluídos. As comissões voltarão para a prévia.`, 'Excluir lote'); if (!confirmed) return; try { await apiFetch(`/financeiro/comissoes/lotes/${item.lote_id}`, { method: 'DELETE' }); await loadBatches(); await successAlert('Lote de comissões excluído.', 'delete') } catch (error) { await errorAlert(error instanceof Error ? error.message : 'Não foi possível excluir o lote.') } }
async function printBatch(loteId: number) { try { const blob = await apiFetchBlob(`/financeiro/comissoes/lotes/${loteId}/imprimir`); const url = URL.createObjectURL(blob); window.open(url, '_blank'); window.setTimeout(() => URL.revokeObjectURL(url), 60000) } catch (error) { await errorAlert(error instanceof Error ? error.message : 'Não foi possível imprimir a lista de comissões.') } }
</script>

<style scoped>
.process-button{min-height:34px;display:inline-flex;align-items:center;padding:0 .85rem;border:1px solid #fdba74;border-radius:5px;background:#fff0e7;color:#ea580c;font-size:.8rem;font-weight:700;text-decoration:none}.filters{display:grid;grid-template-columns:2fr 90px 100px 120px auto;gap:.7rem;align-items:end;margin-bottom:1rem}.filters label{display:grid;gap:.35rem;font-size:.8rem;color:#475569}.apply-button{height:34px;padding:0 .85rem;border:0;border-radius:4px;background:#e5e7eb;color:#475569;font-size:.78rem;font-weight:700}.client-grid{width:100%;border-collapse:collapse}.client-grid th{padding:.65rem .55rem;color:#718096;font-size:.7rem;text-transform:uppercase;text-align:left}.client-grid td{padding:.72rem .55rem;border-top:1px solid #e9edf2;font-size:.82rem;color:#334155}.right{text-align:right!important}.action{text-align:center!important}.action-buttons{display:flex;align-items:center;justify-content:center;gap:7px;min-height:28px}.client-grid .action .calculator{width:25px;height:25px;display:flex;flex:0 0 25px;align-items:center;justify-content:center;border:1px solid #fdba74!important;border-radius:5px;background:#fff0e7!important;color:#f97316!important}.client-grid .action .calculator:hover{background:#ffedd5!important}.action-buttons .icon-action{margin:0;flex:0 0 auto}.calculator svg{width:17px;height:17px}.calculator svg rect{fill:#f97316}.calculator svg path{fill:none;stroke:#fff;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
</style>
