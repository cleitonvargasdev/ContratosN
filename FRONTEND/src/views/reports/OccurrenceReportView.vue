<template>
  <section class="report-shell">
    <div class="report-box">
      <header><h2>Relatório de Ocorrências</h2><button class="report-close-icon-button" type="button" aria-label="Fechar" title="Fechar" @click="reset"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="2"/></svg></button></header>
      <div class="fields">
        <label>Período <span><input v-model="start" class="field" type="date"><b>até</b><input v-model="end" class="field" type="date"></span></label>
        <label>Funcionário<select v-model="collector" class="field"><option value="">TODOS OS FUNCIONÁRIOS</option><option v-for="user in users" :key="user.id" :value="String(user.id)">{{ user.nome }}</option></select></label>
      </div>
      <footer class="report-actions">
        <button class="report-action-button report-action-button--print" type="button" @click="print"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h10v5H7V3Zm10 11H7v7h10v-7Zm2-7H5a3 3 0 0 0-3 3v6h4v-4h12v4h4v-6a3 3 0 0 0-3-3Zm-2 4.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z" fill="currentColor"/></svg>Imprimir</button>
        <button class="report-action-button" type="button" @click="reset"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="2"/></svg>Fechar</button>
      </footer>
      <p class="hint">Mostra Fechado e Não pagou; o PDF permite abrir a localização no mapa.</p>
      <p v-if="error" class="feedback feedback--error">{{ error }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiFetch, apiFetchBlob } from '@/services/http'

const today = new Date().toISOString().slice(0, 10)
const start = ref(today)
const end = ref(today)
const collector = ref('')
const users = ref<Array<{ id: number; nome: string }>>([])
const error = ref('')

onMounted(async () => {
  try {
    users.value = await apiFetch('/financeiro/relatorios/recebimentos/cobradores')
  } catch {
    error.value = 'Não foi possível carregar os funcionários.'
  }
})

function reset() {
  start.value = today
  end.value = today
  collector.value = ''
  error.value = ''
}

async function print() {
  error.value = ''
  const query = new URLSearchParams({ data_inicial: start.value, data_final: end.value })
  if (collector.value) query.set('cobrador_id', collector.value)
  try {
    const blob = await apiFetchBlob(`/financeiro/relatorios/ocorrencias/imprimir?${query}`)
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank', 'noopener,noreferrer')
    window.setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível gerar o relatório.'
  }
}
</script>

<style scoped>
.report-shell { padding: 24px; }
.report-box { max-width: 580px; margin: auto; border-top: 2px solid #f59e0b; background: #fff; box-shadow: 0 1px 8px #0002; }
.report-box header { padding: 14px 18px; background: #f8fafc; }
.report-box h2 { margin: 0; font-size: 17px; color: #374151; }
.fields { padding: 26px 106px; display: grid; gap: 13px; }
.fields > label { display: grid; grid-template-columns: 78px 1fr; align-items: center; gap: 8px; font-size: 13px; }
.fields span { display: flex; gap: 8px; align-items: center; }
.fields span input { min-width: 0; }
footer { padding: 14px; text-align: center; border-top: 1px solid #e5e7eb; background: #f8fafc; }
footer button { margin: 0 3px; }
.hint, .feedback { margin: 0; padding: 0 18px 14px; font-size: 12px; }
@media (max-width: 600px) { .fields { padding: 20px; } .fields > label { grid-template-columns: 1fr; } }
.report-box header { align-items: center; display: flex; justify-content: space-between; }
footer { background: transparent; border-top: 0; padding: 0 14px 14px; }
</style>
