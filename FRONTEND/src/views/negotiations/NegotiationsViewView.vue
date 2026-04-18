<template>
  <section class="panel form-panel">
    <header class="panel__header">
      <div>
        <p class="eyebrow">Movimentações</p>
        <h2 class="panel__title">Negociação #{{ negotiationId }}</h2>
      </div>
      <div class="panel__header-actions">
        <button class="secondary-button" type="button" @click="handlePrint">Imprimir</button>
        <button class="ghost-button" type="button" @click="handleBack">Voltar</button>
      </div>
    </header>

    <p v-if="loading" class="feedback">Carregando...</p>
    <p v-if="error" class="feedback feedback--error">{{ error }}</p>

    <div v-if="negotiation" class="negotiation-detail">
      <div class="negotiation-detail__grid">
        <div class="field-group">
          <span>Cliente</span>
          <input :value="negotiation.cliente_nome || '-'" class="field field--readonly" readonly type="text" />
        </div>
        <div class="field-group">
          <span>Data</span>
          <input :value="formatDate(negotiation.data_negociacao)" class="field field--readonly" readonly type="text" />
        </div>
        <div class="field-group">
          <span>Usuário</span>
          <input :value="negotiation.usuario_nome || '-'" class="field field--readonly" readonly type="text" />
        </div>
        <div class="field-group">
          <span>Valor Total em Aberto</span>
          <input :value="formatCurrency(negotiation.valor_total_aberto)" class="field field--readonly" readonly type="text" />
        </div>
        <div class="field-group">
          <span>Qtde Parcelas</span>
          <input :value="negotiation.qtde_parcelas" class="field field--readonly" readonly type="text" />
        </div>
        <div class="field-group">
          <span>Valor Parcela</span>
          <input :value="formatCurrency(negotiation.valor_parcela)" class="field field--readonly" readonly type="text" />
        </div>
        <div class="field-group">
          <span>Contrato Gerado</span>
          <div class="field-inline">
            <input :value="negotiation.contrato_gerado_id || '-'" class="field field--readonly" readonly type="text" />
            <button v-if="negotiation.contrato_gerado_id" class="secondary-button" type="button" @click="goToContract">Ver Contrato</button>
          </div>
        </div>
        <div class="field-group">
          <span>Situação</span>
          <span :class="['pill', negotiation.contrato_quitado ? 'pill--success' : 'pill--warning']">
            {{ negotiation.contrato_quitado ? 'QUITADO' : 'PENDENTE' }}
          </span>
        </div>
      </div>

      <div v-if="negotiation.obs" class="field-group" style="margin-top: 1rem;">
        <span>Observação</span>
        <textarea :value="negotiation.obs" class="field field--textarea field--readonly" readonly rows="3"></textarea>
      </div>

      <div v-if="negotiation.contratos_originais.length > 0" class="negotiation-detail__section">
        <h3 class="panel__title">Contratos Originais</h3>
        <div class="table-wrap">
          <table class="data-table data-table--cadastro">
            <thead>
              <tr>
                <th>Contrato</th>
                <th>Valor em Aberto na Negociação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in negotiation.contratos_originais" :key="item.id" class="data-table__row">
                <td>{{ item.contrato_id }}</td>
                <td>{{ formatCurrency(item.valor_aberto) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { Negotiation } from '@/models/negotiation'
import { errorAlert } from '@/services/alertService'
import { getNegotiationById, printNegotiationPdf } from '@/services/negotiationService'

const route = useRoute()
const router = useRouter()

const negotiationId = Number(route.params.id)
const negotiation = ref<Negotiation | null>(null)
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  loading.value = true
  try {
    negotiation.value = await getNegotiationById(negotiationId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Falha ao carregar negociação'
  } finally {
    loading.value = false
  }
})

function goToContract() {
  if (negotiation.value?.contrato_gerado_id) {
    void router.push({ name: 'contracts-edit', params: { id: negotiation.value.contrato_gerado_id } })
  }
}

async function handlePrint() {
  try {
    const blob = await printNegotiationPdf(negotiationId)
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  } catch (e) {
    await errorAlert(e instanceof Error ? e.message : 'Falha ao imprimir negociação')
  }
}

function handleBack() {
  void router.push({ name: 'negotiations-list' })
}

function formatDate(value: string | null) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('pt-BR').format(new Date(value))
}

function formatCurrency(value: number | null | undefined) {
  if (typeof value !== 'number') return '-'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}
</script>

<style scoped>
.negotiation-detail {
  padding: 1rem;
}

.negotiation-detail__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.negotiation-detail__section {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
</style>
