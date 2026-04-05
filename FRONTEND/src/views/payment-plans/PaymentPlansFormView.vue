<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <h2 class="panel__title">{{ isEdit ? 'Editar plano de pagamento' : 'Novo plano de pagamento' }}</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="field-group field-group--span-2">
        <span>Descrição</span>
        <input v-model="form.descricao" class="field" maxlength="50" required type="text" />
      </label>
      <label class="field-group">
        <span>Valor Base</span>
        <input :value="display.valor_base" class="field" inputmode="decimal" type="text" @input="updateCurrencyField('valor_base', $event)" @blur="normalizeCurrencyField('valor_base')" />
      </label>
      <label class="field-group">
        <span>Qtde Dias</span>
        <input v-model.number="form.qtde_dias" class="field" min="1" type="number" @input="setLastEdited('qtde_dias')" @blur="applyCalculationRules" />
      </label>
      <label class="field-group">
        <span>Valor Parcela</span>
        <input :value="display.valor_parcela" class="field" inputmode="decimal" type="text" @input="updateCurrencyField('valor_parcela', $event)" @blur="normalizeCurrencyField('valor_parcela')" />
      </label>
      <label class="field-group">
        <span>Valor Final</span>
        <input :value="display.valor_final" class="field" readonly type="text" />
      </label>
      <label class="field-group">
        <span>% Juros ao mês</span>
        <input :value="display.percent_juros" class="field" readonly type="text" />
      </label>
      <div class="form-actions form-actions--user field-group--span-2">
        <button class="primary-button primary-button--success form-actions__button" :disabled="state.saving" type="submit">{{ state.saving ? 'Salvando...' : 'Salvar' }}</button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="state.saving" type="button" @click="router.push({ name: 'payment-plans-list' })">Cancelar</button>
      </div>
    </form>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { PaymentPlanInput } from '@/models/paymentPlan'
import { errorAlert, successAlert } from '@/services/alertService'
import { createPaymentPlan, getPaymentPlanById, updatePaymentPlan } from '@/services/paymentPlanService'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const lastEditedField = ref<'valor_base' | 'qtde_dias' | 'valor_parcela' | null>(null)
const form = reactive({
  descricao: '',
  qtde_dias: null as number | null,
  percent_juros: null as number | null,
  valor_parcela: null as number | null,
  valor_base: null as number | null,
  valor_final: null as number | null,
})
const display = reactive({
  valor_base: '',
  valor_parcela: '',
  valor_final: '',
  percent_juros: '',
})
const state = reactive({ loading: false, saving: false, error: '' })

onMounted(() => {
  if (isEdit.value) {
    void loadRecord()
  }
})

async function loadRecord() {
  state.loading = true
  try {
    const record = await getPaymentPlanById(Number(route.params.id))
    form.descricao = record.descricao ?? ''
    form.qtde_dias = record.qtde_dias
    form.percent_juros = record.percent_juros
    form.valor_parcela = record.valor_parcela
    form.valor_base = record.valor_base
    form.valor_final = record.valor_final
    syncDisplayFields()
  } catch {
    await router.replace({ name: 'payment-plans-list' })
  } finally {
    state.loading = false
  }
}

async function handleSubmit() {
  state.saving = true
  state.error = ''
  try {
    applyCalculationRules()

    const payload: PaymentPlanInput = {
      descricao: form.descricao.trim() || null,
      qtde_dias: form.qtde_dias,
      percent_juros: form.percent_juros,
      valor_parcela: form.valor_parcela,
      valor_base: form.valor_base,
      valor_final: form.valor_final,
    }

    if (isEdit.value) {
      await updatePaymentPlan(Number(route.params.id), payload)
      await successAlert('Plano atualizado com sucesso.', 'update')
    } else {
      await createPaymentPlan(payload)
      await successAlert('Plano cadastrado com sucesso.', 'create')
    }
    await router.push({ name: 'payment-plans-list' })
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao salvar plano de pagamento'
    await errorAlert(state.error)
  } finally {
    state.saving = false
  }
}

function setLastEdited(field: 'valor_base' | 'qtde_dias' | 'valor_parcela') {
  lastEditedField.value = field
}

function normalizeCurrencyField(field: 'valor_base' | 'valor_parcela') {
  const currentValue = form[field]
  if (currentValue == null || Number.isNaN(currentValue)) {
    display[field] = ''
    applyCalculationRules()
    return
  }
  form[field] = roundCurrency(currentValue)
  display[field] = formatDecimal(form[field])
  applyCalculationRules()
}

function updateCurrencyField(field: 'valor_base' | 'valor_parcela', event: Event) {
  const target = event.target as HTMLInputElement
  display[field] = target.value
  form[field] = parseDecimal(target.value)
  setLastEdited(field)
}

function applyCalculationRules() {
  const qtdeDias = form.qtde_dias ?? 0
  const valorBase = form.valor_base
  const valorParcela = form.valor_parcela

  if (qtdeDias > 0 && valorBase != null && valorParcela != null) {
    const valorFinal = form.valor_parcela * qtdeDias
    form.valor_final = roundCurrency(valorFinal)
    form.percent_juros = roundInterest(calculateMonthlyInterestFromFinal(valorBase, valorFinal, qtdeDias))
  } else if (qtdeDias > 0 && form.valor_parcela != null) {
    form.valor_final = roundCurrency(form.valor_parcela * qtdeDias)
    form.percent_juros = null
  } else {
    form.valor_final = null
    form.percent_juros = null
  }

  syncDisplayFields()
}

function calculateMonthlyInterestFromFinal(valorBase: number, valorFinal: number, qtdeDias: number) {
  if (qtdeDias <= 0 || valorBase <= 0 || valorFinal <= 0) {
    return 0
  }
  if (valorFinal <= valorBase) {
    return 0
  }
  const periodInMonths = qtdeDias / 30
  if (periodInMonths <= 0) {
    return 0
  }
  return (((valorFinal / valorBase) ** (1 / periodInMonths)) - 1) * 100
}

function roundCurrency(value: number) {
  return Math.round((value + Number.EPSILON) * 100) / 100
}

function roundInterest(value: number) {
  return Math.round((value + Number.EPSILON) * 100) / 100
}

function parseDecimal(value: string) {
  const normalized = value.replace(/\./g, '').replace(',', '.').replace(/[^\d.\-]/g, '')
  if (!normalized.trim()) {
    return null
  }
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function formatDecimal(value: number | null) {
  return value == null ? '' : value.toFixed(2).replace('.', ',')
}

function syncDisplayFields() {
  display.valor_base = formatDecimal(form.valor_base)
  display.valor_parcela = formatDecimal(form.valor_parcela)
  display.valor_final = formatDecimal(form.valor_final)
  display.percent_juros = formatDecimal(form.percent_juros)
}
</script>