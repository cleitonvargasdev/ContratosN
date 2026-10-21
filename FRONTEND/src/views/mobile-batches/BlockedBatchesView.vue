<template>
  <section class="panel batches">
    <header class="panel__header">
      <div><h2 class="panel__title">Desbloqueio de lotes</h2><p>Conferir conflitos enviados pelos cobradores.</p></div>
      <button class="primary-button" type="button" :disabled="loading" @click="load">Atualizar</button>
    </header>
    <p v-if="error" class="feedback feedback--error">{{ error }}</p>
    <p v-else-if="loading">Carregando lotes bloqueados...</p>
    <p v-else-if="batches.length === 0">Nenhum lote bloqueado.</p>
    <div v-else class="table-wrap"><table class="data-table data-table--cadastro"><thead><tr><th>Lote</th><th>Cobrador</th><th>Motivo</th><th>Itens</th></tr></thead><tbody>
      <template v-for="batch in batches" :key="batch.id">
        <tr class="batch-group-row"><td colspan="4"><button class="batch-group-button" type="button" @click="toggle(batch.id)"><span class="batch-group-button__icon">{{ isOpen(batch.id) ? '-' : '+' }}</span><strong>Lote #{{ batch.id }} · {{ batch.collector_name }}</strong><span class="batch-group-button__reason">{{ batch.block_reason || 'Conferência necessária' }}</span><span class="batch-group-button__meta">{{ batch.items.filter(item => item.blocked).length }} {{ batch.items.filter(item => item.blocked).length === 1 ? 'item bloqueado' : 'itens bloqueados' }}</span></button></td></tr>
        <template v-if="isOpen(batch.id)"><tr class="batch-detail-header"><th>Contrato</th><th>Parcela</th><th>Tipo / motivo</th><th>Valor</th></tr><tr v-for="item in batch.items.filter(item => item.blocked)" :key="item.id" class="data-table__row"><td>{{ item.contract_id ?? '-' }}</td><td>{{ item.installment_number ?? item.installment_id ?? '-' }}</td><td><strong>{{ kindLabel(item.kind) }}</strong><br><span>{{ item.block_reason || '-' }}</span></td><td>{{ money(item.amount_units) }}</td></tr><tr class="batch-unlock-row"><td colspan="4"><button class="primary-button primary-button--success" type="button" :disabled="unlocking === batch.id" @click="unlock(batch)">Desbloquear cobrador</button></td></tr></template>
      </template>
    </tbody></table></div>
  </section>
</template>
<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { listBlockedMobileBatches, unlockMobileBatch, type MobileBatch } from '@/services/mobileBatchService'
const batches = ref<MobileBatch[]>([]); const loading = ref(false); const error = ref(''); const unlocking = ref<number | null>(null); const opened = reactive<Record<number, boolean>>({})
async function load() { loading.value = true; error.value = ''; try { batches.value = await listBlockedMobileBatches(); for (const batch of batches.value) if (!(batch.id in opened)) opened[batch.id] = false } catch (cause) { error.value = cause instanceof Error ? cause.message : 'Não foi possível carregar os lotes.' } finally { loading.value = false } }
function toggle(id: number) { opened[id] = !opened[id] }; function isOpen(id: number) { return opened[id] ?? false }
function money(value: number | null) { return value === null ? '-' : new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value / 10000) }
function kindLabel(kind: string) { return ({ payment: 'Pagamento', unpaid: 'Não pagou', closed: 'Fechado' } as Record<string, string>)[kind] ?? kind }
async function unlock(batch: MobileBatch) { const reason = window.prompt(`Motivo do desbloqueio do lote #${batch.id}:`); if (!reason || reason.trim().length < 3) return; unlocking.value = batch.id; try { await unlockMobileBatch(batch.id, reason.trim()); await load() } catch (cause) { error.value = cause instanceof Error ? cause.message : 'Não foi possível desbloquear o lote.' } finally { unlocking.value = null } }
onMounted(load)
</script>
<style scoped>
.batches { display:grid; gap:16px; } .panel__header { align-items:center; } .panel__header p { color:var(--text-muted); margin:4px 0 0; } .batch-group-row td { border:0; padding:0; } .batch-group-button { align-items:center; background:#fffaf7; border:1px solid #f3e3d8; color:#344150; cursor:pointer; display:grid; gap:12px; grid-template-columns:20px minmax(180px,1fr) minmax(180px,1fr) auto; padding:13px 16px; text-align:left; width:100%; } .batch-group-button:hover { background:#fff6f0; } .batch-group-button__icon { color:#e96c2b; font-weight:800; text-align:center; } .batch-group-button__reason { color:#657487; font-size:13px; } .batch-group-button__meta { color:#718197; font-size:13px; white-space:nowrap; } .batch-detail-header th { background:#fbfcfd; color:#718197; font-size:11px; padding:11px 16px; } .data-table__row span { color:#657487; font-size:12px; } .batch-unlock-row td { padding:12px 16px; } @media (max-width:780px) { .batch-group-button { grid-template-columns:20px 1fr; } .batch-group-button__reason,.batch-group-button__meta { grid-column:2; } }
</style>
