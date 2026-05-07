<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <p class="eyebrow">Cadastro de produtos</p>
        <h2 class="panel__title">{{ isEdit ? 'Editar produto' : 'Novo produto' }}</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="field-group field-group--span-2">
        <span>Descrição</span>
        <input v-model="form.descricao" class="field" maxlength="60" required type="text" />
      </label>

      <label class="field-group">
        <span>Marca</span>
        <select v-model="form.marca_id" class="field">
          <option value="">Selecione</option>
          <option v-for="brand in brandOptions" :key="brand.marca_id" :value="String(brand.marca_id)">{{ brand.descricao }}</option>
        </select>
      </label>

      <label class="field-group">
        <span>Status</span>
        <label class="status-switch" :class="form.ativo ? 'status-switch--on' : 'status-switch--off'">
          <input v-model="form.ativo" class="status-switch__input" type="checkbox" />
          <span class="status-switch__track">
            <span class="status-switch__thumb"></span>
          </span>
          <span class="status-switch__label">{{ form.ativo ? 'Ativo' : 'Inativo' }}</span>
        </label>
      </label>

      <label class="field-group">
        <span>Valor Compra</span>
        <input :value="display.valor_compra" class="field" inputmode="decimal" type="text" @input="updateCurrencyField('valor_compra', $event)" @blur="normalizeCurrencyField('valor_compra')" />
      </label>

      <label class="field-group">
        <span>Valor Venda</span>
        <input :value="display.valor_venda" class="field" inputmode="decimal" type="text" @input="updateCurrencyField('valor_venda', $event)" @blur="normalizeCurrencyField('valor_venda')" />
      </label>

      <label class="field-group">
        <span>Garantia (dias)</span>
        <input v-model="form.garantia" class="field" min="0" type="number" />
      </label>

      <label class="field-group">
        <span>Estoque</span>
        <input v-model="form.estoque" class="field" min="0" type="number" />
      </label>

      <label class="field-group">
        <span>Modelo</span>
        <input v-model="form.modelo" class="field" maxlength="20" type="text" />
      </label>

      <label class="field-group">
        <span>Cor</span>
        <input v-model="form.cor" class="field" maxlength="15" type="text" />
      </label>

      <div class="form-actions form-actions--user field-group--span-2">
        <button class="primary-button primary-button--success form-actions__button" :disabled="state.saving" type="submit">{{ state.saving ? 'Salvando...' : 'Salvar' }}</button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="state.saving" type="button" @click="router.push({ name: 'products-list' })">Cancelar</button>
      </div>
    </form>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { BrandOption, ProductInput } from '@/models/product'
import { errorAlert, successAlert } from '@/services/alertService'
import { createProduct, getProductById, listBrandOptions, updateProduct } from '@/services/productService'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const brandOptions = ref<BrandOption[]>([])
const form = reactive({
  descricao: '',
  valor_compra: null as number | null,
  valor_venda: null as number | null,
  marca_id: '',
  garantia: '',
  ativo: true,
  estoque: '',
  modelo: '',
  cor: '',
})
const display = reactive({
  valor_compra: '',
  valor_venda: '',
})
const state = reactive({ loading: false, saving: false, error: '' })

onMounted(() => {
  void initialize()
})

async function initialize() {
  state.loading = true
  try {
    brandOptions.value = await listBrandOptions()
    if (isEdit.value) {
      const record = await getProductById(Number(route.params.id))
      form.descricao = record.descricao ?? ''
      form.valor_compra = formatNumberInput(record.valor_compra)
      form.valor_venda = formatNumberInput(record.valor_venda)
      syncDisplayFields()
      form.marca_id = record.marca_id == null ? '' : String(record.marca_id)
      form.garantia = formatIntegerInput(record.garantia)
      form.ativo = record.ativo
      form.estoque = formatIntegerInput(record.estoque)
      form.modelo = record.modelo ?? ''
      form.cor = record.cor ?? ''
    }
  } catch {
    await router.replace({ name: 'products-list' })
  } finally {
    state.loading = false
  }
}

async function handleSubmit() {
  state.saving = true
  state.error = ''
  try {
    normalizeCurrencyField('valor_compra')
    normalizeCurrencyField('valor_venda')

    const payload: ProductInput = {
      descricao: normalizeText(form.descricao),
      valor_compra: parseNullableNumber(form.valor_compra),
      valor_venda: parseNullableNumber(form.valor_venda),
      marca_id: parseNullableInteger(form.marca_id),
      garantia: parseNullableInteger(form.garantia),
      ativo: Boolean(form.ativo),
      estoque: parseNullableInteger(form.estoque),
      modelo: normalizeText(form.modelo),
      cor: normalizeText(form.cor),
    }

    if (isEdit.value) {
      await updateProduct(Number(route.params.id), payload)
      await successAlert('Produto atualizado com sucesso.', 'update')
    } else {
      await createProduct(payload)
      await successAlert('Produto cadastrado com sucesso.', 'create')
    }
    await router.push({ name: 'products-list' })
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao salvar produto'
    await errorAlert(state.error)
  } finally {
    state.saving = false
  }
}

function normalizeText(value: string) {
  const normalized = value.trim()
  return normalized || null
}

function parseNullableNumber(value: string | number | null | undefined) {
  if (value == null) {
    return null
  }
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null
  }
  if (!value.trim()) {
    return null
  }
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function parseNullableInteger(value: string | number | null | undefined) {
  if (value == null) {
    return null
  }
  if (typeof value === 'number') {
    return Number.isFinite(value) ? Math.trunc(value) : null
  }
  if (!value.trim()) {
    return null
  }
  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) ? parsed : null
}

function formatNumberInput(value: number | null) {
  return value == null ? null : value
}

function formatIntegerInput(value: number | null) {
  return value == null ? '' : String(Math.trunc(value))
}

function normalizeCurrencyField(field: 'valor_compra' | 'valor_venda') {
  const currentValue = form[field]
  if (currentValue == null || Number.isNaN(currentValue)) {
    display[field] = ''
    return
  }

  form[field] = roundCurrency(currentValue)
  display[field] = formatDecimal(form[field])
}

function updateCurrencyField(field: 'valor_compra' | 'valor_venda', event: Event) {
  const target = event.target as HTMLInputElement
  display[field] = target.value
  form[field] = parseDecimal(target.value)
}

function parseDecimal(value: string) {
  const normalized = value.replace(/\./g, '').replace(',', '.').replace(/[^\d.\-]/g, '')
  if (!normalized.trim()) {
    return null
  }
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function roundCurrency(value: number) {
  return Math.round((value + Number.EPSILON) * 100) / 100
}

function formatDecimal(value: number | null) {
  return value == null ? '' : value.toFixed(2).replace('.', ',')
}

function syncDisplayFields() {
  display.valor_compra = formatDecimal(form.valor_compra)
  display.valor_venda = formatDecimal(form.valor_venda)
}
</script>

<style scoped>
.status-switch {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 18px;
  cursor: pointer;
}

.status-switch__input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.status-switch__track {
  position: relative;
  width: 28px;
  height: 16px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.35);
  transition: background 180ms ease;
}

.status-switch__thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 3px 8px rgba(15, 23, 42, 0.18);
  transition: transform 180ms ease;
}

.status-switch--on .status-switch__track {
  background: rgba(22, 163, 74, 0.75);
}

.status-switch--on .status-switch__thumb {
  transform: translateX(12px);
}

.status-switch__label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-color, #24303b);
}
</style>