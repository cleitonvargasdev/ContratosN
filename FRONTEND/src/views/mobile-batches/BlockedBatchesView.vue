<template>
  <section class="panel batches">
    <header class="panel__header"><div><h2 class="panel__title">Desbloqueio de lotes</h2><p>Conferir conflitos enviados pelos cobradores.</p></div><button class="primary-button" type="button" :disabled="loading" @click="load">Atualizar</button></header>
    <p v-if="error" class="feedback feedback--error">{{ error }}</p><p v-else-if="loading">Carregando lotes bloqueados...</p><p v-else-if="batches.length === 0">Nenhum lote bloqueado.</p>
    <div v-else class="table-wrap"><table class="data-table"><thead><tr><th>Lote</th><th>Cobrador</th><th>Motivo</th><th>Itens</th><th></th></tr></thead><tbody><template v-for="batch in batches" :key="batch.id"><tr><td>#{{ batch.id }}</td><td>{{ batch.user_id }}</td><td>{{ batch.block_reason || '-' }}</td><td>{{ batch.items.filter(item => item.blocked).length }} bloqueado(s)</td><td><button class="secondary-button" type="button" @click="toggle(batch.id)">{{ opened === batch.id ? 'Fechar' : 'Ver itens' }}</button></td></tr><tr v-if="opened === batch.id"><td colspan="5"><table class="detail"><thead><tr><th>Contrato</th><th>Parcela</th><th>Tipo</th><th>Valor</th><th>Motivo</th></tr></thead><tbody><tr v-for="item in batch.items.filter(item => item.blocked)" :key="item.id"><td>{{ item.contract_id ?? '-' }}</td><td>{{ item.installment_id ?? '-' }}</td><td>{{ item.kind }}</td><td>{{ money(item.amount_units) }}</td><td>{{ item.block_reason || '-' }}</td></tr></tbody></table><button class="primary-button primary-button--success" type="button" :disabled="unlocking === batch.id" @click="unlock(batch)">Desbloquear cobrador</button></td></tr></template></tbody></table></div>
  </section>
</template>
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listBlockedMobileBatches, unlockMobileBatch, type MobileBatch } from '@/services/mobileBatchService'
const batches = ref<MobileBatch[]>([]); const loading = ref(false); const error = ref(''); const opened = ref<number | null>(null); const unlocking = ref<number | null>(null)
async function load() { loading.value = true; error.value = ''; try { batches.value = await listBlockedMobileBatches() } catch (cause) { error.value = cause instanceof Error ? cause.message : 'Não foi possível carregar os lotes.' } finally { loading.value = false } }
function toggle(id: number) { opened.value = opened.value === id ? null : id }
function money(value: number | null) { return value === null ? '-' : new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value / 10000) }
async function unlock(batch: MobileBatch) { const reason = window.prompt(`Motivo do desbloqueio do lote #${batch.id}:`); if (!reason || reason.trim().length < 3) return; unlocking.value = batch.id; try { await unlockMobileBatch(batch.id, reason.trim()); await load() } catch (cause) { error.value = cause instanceof Error ? cause.message : 'Não foi possível desbloquear o lote.' } finally { unlocking.value = null } }
onMounted(load)
</script>
<style scoped>.batches { display:grid; gap:16px; } .panel__header { align-items:center; } .panel__header p { color:var(--text-muted); margin:4px 0 0; } .detail { width:100%; margin:8px 0 14px; border-collapse:collapse; } .detail th,.detail td { border-bottom:1px solid #e4e9ef; padding:8px; text-align:left; } .secondary-button { padding:7px 10px; }</style>
