<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <p class="eyebrow">Cadastros diversos</p>
        <h2 class="panel__title">{{ isEdit ? 'Editar UF' : 'Nova UF' }}</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="field-group">
        <span>UF</span>
        <input v-model="form.uf" class="field" maxlength="2" required type="text" />
      </label>
      <label class="field-group">
        <span>Nome</span>
        <input v-model="form.uf_nome" class="field" required type="text" />
      </label>
      <label class="field-group">
        <span>Codigo IBGE</span>
        <input v-model.number="form.cod_ibge" class="field" min="0" type="number" />
      </label>
      <div class="form-actions form-actions--user field-group--span-2">
        <button class="primary-button primary-button--success form-actions__button" :disabled="state.saving" type="submit">{{ state.saving ? 'Salvando...' : 'Salvar' }}</button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="state.saving" type="button" @click="router.push({ name: 'ufs-list' })">Cancelar</button>
      </div>
    </form>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorAlert, successAlert } from '@/services/alertService'
import { createUf, getUfById, updateUf } from '@/services/locationService'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const form = reactive({ uf: '', uf_nome: '', cod_ibge: null as number | null })
const state = reactive({ loading: false, saving: false, error: '' })

onMounted(() => {
  if (isEdit.value) {
    void loadRecord()
  }
})

async function loadRecord() {
  state.loading = true
  try {
    const record = await getUfById(Number(route.params.id))
    form.uf = record.uf
    form.uf_nome = record.uf_nome
    form.cod_ibge = record.cod_ibge
  } catch {
    await router.replace({ name: 'ufs-list' })
  } finally {
    state.loading = false
  }
}

async function handleSubmit() {
  state.saving = true
  state.error = ''
  try {
    const payload = { uf: form.uf, uf_nome: form.uf_nome, cod_ibge: form.cod_ibge }
    if (isEdit.value) {
      await updateUf(Number(route.params.id), payload)
      await successAlert('UF atualizada com sucesso.', 'update')
    } else {
      await createUf(payload)
      await successAlert('UF cadastrada com sucesso.', 'create')
    }
    await router.push({ name: 'ufs-list' })
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao salvar UF'
    await errorAlert(state.error)
  } finally {
    state.saving = false
  }
}
</script>