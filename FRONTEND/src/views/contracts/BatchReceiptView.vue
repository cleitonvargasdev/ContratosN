<template>
  <section class="panel batch-receipt-panel">
    <header class="panel__header batch-receipt-panel__header">
      <div>
        <p class="eyebrow">Movimentações</p>
        <h2 class="panel__title">Recebimento em Lote</h2>
      </div>
    </header>

    <div class="batch-receipt-form">
      <label class="field-group">
        <span>Nº Contrato</span>
        <input v-model="form.contractId" class="field field--no-spin" inputmode="numeric" type="number" min="1" @keydown.enter.prevent="handlePreview" />
      </label>

      <label class="field-group">
        <span>Valor</span>
        <input v-model="form.amount" class="field" inputmode="decimal" type="text" placeholder="0,00" @blur="formatAmountField" @keydown.enter.prevent="handlePreview" />
      </label>

      <div class="batch-receipt-form__actions">
        <button class="primary-button primary-button--accent-soft" :disabled="loading.preview || loading.confirm" type="button" @click="handlePreview">
          {{ loading.preview ? 'Calculando...' : 'Calcular' }}
        </button>
        <button class="ghost-button" :disabled="loading.preview || loading.confirm" type="button" @click="resetState">Limpar</button>
      </div>
    </div>

    <div v-if="contract" class="summary-row batch-receipt-summary-row">
      <article class="summary-chip summary-chip--wide">
        <strong>{{ contract.contratos_id }}</strong>
        <span>Contrato</span>
      </article>
      <article class="summary-chip summary-chip--wide">
        <strong>{{ contract.cliente_nome || 'Sem cliente' }}</strong>
        <span>Cliente</span>
      </article>
      <article class="summary-chip">
        <strong>{{ formatCurrency(contract.valor_em_aberto) }}</strong>
        <span>Em aberto</span>
      </article>
      <article class="summary-chip">
        <strong>{{ formatCurrency(preview?.valor_distribuido ?? 0) }}</strong>
        <span>Distribuído</span>
      </article>
    </div>

    <p v-if="message" :class="['feedback', message.kind === 'error' ? 'feedback--error' : 'feedback--info']">{{ message.text }}</p>

    <div class="table-wrap batch-receipt-table-wrap">
      <table class="data-table data-table--cadastro batch-receipt-table">
        <thead>
          <tr>
            <th>Parc.</th>
            <th>Vencimento</th>
            <th>Dia Semana</th>
            <th>Valor Total</th>
            <th>Vl. Recebido</th>
            <th>Saldo</th>
            <th>Baixar</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading.preview">
            <td colspan="7">Calculando parcelas disponíveis...</td>
          </tr>
          <tr v-else-if="previewRows.length === 0">
            <td colspan="7">Nenhuma parcela disponível para baixa com o valor informado.</td>
          </tr>
          <tr v-for="row in previewRows" :key="row.id">
            <td>{{ row.parcela }}</td>
            <td>{{ row.vencimento }}</td>
            <td>{{ row.diaSemana }}</td>
            <td>{{ row.valorTotal }}</td>
            <td>{{ row.valorRecebido }}</td>
            <td>{{ row.saldo }}</td>
            <td>{{ row.valorBaixa }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="form-actions batch-receipt-actions">
      <button
        class="primary-button primary-button--success"
        :disabled="loading.preview || loading.confirm || previewRows.length === 0 || !auth.hasPermission('contratos', 'update')"
        type="button"
        @click="handleConfirm"
      >
        {{ loading.confirm ? 'Confirmando...' : 'Confirmar' }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { useAuthController } from '@/controllers/useAuthController'
import type { BatchInstallmentReceivePreview, Contract } from '@/models/contract'
import { confirmActionAlert, errorAlert, successAlert } from '@/services/alertService'
import { confirmBatchContractReceive, getContractById, previewBatchContractReceive } from '@/services/contractService'

const auth = useAuthController()

const form = reactive({
  contractId: '',
  amount: '',
})

const contract = ref<Contract | null>(null)
const preview = ref<BatchInstallmentReceivePreview | null>(null)
const loading = reactive({
  preview: false,
  confirm: false,
})
const message = ref<{ kind: 'info' | 'error'; text: string } | null>(null)

const previewRows = computed(() =>
  (preview.value?.parcelas ?? []).map((item) => ({
    id: item.installment.id,
    parcela: String(item.installment.parcela_nro ?? '').padStart(2, '0'),
    vencimento: formatDate(item.installment.vencimentol ?? item.installment.vencimento_original),
    diaSemana: item.installment.dia_semana ?? formatWeekday(item.installment.vencimentol ?? item.installment.vencimento_original),
    valorTotal: formatCurrency(item.installment.valor_total),
    valorRecebido: formatCurrency(item.installment.valor_recebido),
    saldo: formatCurrency(item.saldo_restante),
    valorBaixa: formatCurrency(item.valor_recebimento),
  })),
)

function resetState() {
  form.contractId = ''
  form.amount = ''
  contract.value = null
  preview.value = null
  message.value = null
}

function formatAmountField() {
  const parsed = toLocaleNumberOrNull(form.amount)
  form.amount = parsed === null ? '' : formatDecimal(parsed)
}

async function handlePreview() {
  const contractId = toPositiveInteger(form.contractId)
  const amount = toLocaleNumberOrNull(form.amount)

  if (contractId === null) {
    await errorAlert('Informe um número de contrato válido.')
    return
  }

  if (amount === null || amount <= 0) {
    await errorAlert('Informe um valor maior que zero.')
    return
  }

  loading.preview = true
  message.value = null
  try {
    const [loadedContract, loadedPreview] = await Promise.all([
      getContractById(contractId),
      previewBatchContractReceive(contractId, {
        valor_recebido: amount,
        data_recebimento: currentDateTimeLocal(),
      }),
    ])

    contract.value = loadedContract
    preview.value = loadedPreview
    if (loadedPreview.parcelas.length === 0) {
      message.value = {
        kind: 'info',
        text: 'O valor informado não baixa integralmente a próxima parcela em aberto deste contrato.',
      }
    }
  } catch (error) {
    contract.value = null
    preview.value = null
    message.value = {
      kind: 'error',
      text: error instanceof Error ? error.message : 'Falha ao calcular recebimento em lote.',
    }
    await errorAlert(message.value.text)
  } finally {
    loading.preview = false
  }
}

async function handleConfirm() {
  const contractId = toPositiveInteger(form.contractId)
  const amount = toLocaleNumberOrNull(form.amount)

  if (contractId === null || amount === null || amount <= 0 || previewRows.value.length === 0) {
    return
  }

  const confirmed = await confirmActionAlert(
    'Confirmar recebimento em lote?',
    'O sistema vai baixar as próximas parcelas em aberto por ordem de vencimento usando o valor informado.',
    'Confirmar',
  )
  if (!confirmed) {
    return
  }

  loading.confirm = true
  try {
    const result = await confirmBatchContractReceive(contractId, {
      valor_recebido: amount,
      data_recebimento: currentDateTimeLocal(),
    })

    contract.value = await getContractById(contractId)
    preview.value = null
    message.value = {
      kind: 'info',
      text: `${result.parcelas_processadas.length} parcela(s) baixada(s) com sucesso.`,
    }
    await successAlert('Recebimento em lote confirmado com sucesso.', 'update')
  } catch (error) {
    const text = error instanceof Error ? error.message : 'Falha ao confirmar recebimento em lote.'
    message.value = { kind: 'error', text }
    await errorAlert(text)
  } finally {
    loading.confirm = false
  }
}

function toPositiveInteger(value: string) {
  const parsed = Number(value)
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return null
  }
  return parsed
}

function toLocaleNumberOrNull(value: string) {
  const trimmed = value.trim()
  if (!trimmed) {
    return null
  }

  const normalized = trimmed.replace(/\./g, '').replace(',', '.')
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function formatDecimal(value: number) {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function formatCurrency(value: number | null | undefined) {
  if (typeof value !== 'number') {
    return '-'
  }

  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

function formatDate(value: string | null) {
  if (!value) {
    return '-'
  }

  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) {
    return '-'
  }

  return `${match[3]}/${match[2]}/${match[1]}`
}

function formatWeekday(value: string | null) {
  if (!value) {
    return '-'
  }

  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) {
    return '-'
  }

  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
  return new Intl.DateTimeFormat('pt-BR', { weekday: 'long' }).format(date).toUpperCase()
}

function currentDateTimeLocal() {
  const date = new Date()
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
}
</script>

<style scoped>
.batch-receipt-panel {
  display: grid;
  gap: 1.25rem;
}

.batch-receipt-panel__header {
  margin-bottom: 0;
}

.batch-receipt-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  align-items: end;
}

.batch-receipt-form__actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.batch-receipt-summary-row {
  gap: 0.75rem;
}

.summary-chip--wide {
  min-width: 12rem;
}

.batch-receipt-table-wrap {
  min-height: 16rem;
}

.batch-receipt-table th,
.batch-receipt-table td {
  white-space: nowrap;
}

.batch-receipt-actions {
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .batch-receipt-form {
    grid-template-columns: 1fr;
  }

  .batch-receipt-form__actions {
    justify-content: flex-start;
  }
}
</style>