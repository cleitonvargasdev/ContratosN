<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <p class="eyebrow">Cadastros diversos</p>
        <h2 class="panel__title">{{ isEdit ? 'Editar marca' : 'Nova marca' }}</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="field-group field-group--span-2">
        <span>Descrição</span>
        <input v-model="form.descricao" class="field" maxlength="30" required type="text" />
      </label>

      <div class="form-actions form-actions--user field-group--span-2">
        <button class="primary-button primary-button--success form-actions__button" :disabled="state.saving" type="submit">{{ state.saving ? 'Salvando...' : 'Salvar' }}</button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="state.saving" type="button" @click="router.push({ name: 'brands-list' })">Cancelar</button>
      </div>
    </form>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorAlert, successAlert } from '@/services/alertService'
import { createBrand, getBrandById, updateBrand } from '@/services/productService'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const form = reactive({ descricao: '' })
const state = reactive({ loading: false, saving: false, error: '' })

onMounted(() => {
  if (isEdit.value) {
    void loadRecord()
  }
})

async function loadRecord() {
  state.loading = true
  try {
    const record = await getBrandById(Number(route.params.id))
    form.descricao = record.descricao ?? ''
  } catch {
    await router.replace({ name: 'brands-list' })
  } finally {
    state.loading = false
  }
}

async function handleSubmit() {
  state.saving = true
  state.error = ''
  try {
    const payload = { descricao: normalizeText(form.descricao) }
    if (isEdit.value) {
      await updateBrand(Number(route.params.id), payload)
      await successAlert('Marca atualizada com sucesso.', 'update')
    } else {
      await createBrand(payload)
      await successAlert('Marca cadastrada com sucesso.', 'create')
    }
    await router.push({ name: 'brands-list' })
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao salvar marca'
    await errorAlert(state.error)
  } finally {
    state.saving = false
  }
}

function normalizeText(value: string) {
  const normalized = value.trim()
  return normalized || null
}
</script>