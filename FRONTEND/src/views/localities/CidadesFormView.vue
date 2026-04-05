<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <p class="eyebrow">Cadastros diversos</p>
        <h2 class="panel__title">{{ isEdit ? 'Editar cidade' : 'Nova cidade' }}</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="field-group">
        <span>UF</span>
        <select v-model.number="form.uf_id" class="field" required>
          <option :value="0">Selecione</option>
          <option v-for="item in ufOptions" :key="item.uf_id" :value="item.uf_id">{{ item.uf }} - {{ item.uf_nome }}</option>
        </select>
      </label>
      <label class="field-group">
        <span>Cidade</span>
        <input v-model="form.cidade" class="field" required type="text" />
      </label>
      <div class="form-actions form-actions--user field-group--span-2">
        <button class="primary-button primary-button--success form-actions__button" :disabled="state.saving" type="submit">{{ state.saving ? 'Salvando...' : 'Salvar' }}</button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="state.saving" type="button" @click="handleCancel">Cancelar</button>
      </div>
    </form>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { UFOption } from '@/models/location'
import { errorAlert, successAlert } from '@/services/alertService'
import { createCidade, getCidadeById, listUfs, updateCidade } from '@/services/locationService'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const ufOptions = ref<UFOption[]>([])
const form = reactive({ uf_id: 0, cidade: '' })
const state = reactive({ saving: false, error: '' })

onMounted(() => {
  void loadOptions()
  if (isEdit.value) {
    void loadRecord()
  } else if (route.query.uf_id) {
    form.uf_id = Number(route.query.uf_id)
  }
})

async function loadOptions() {
  ufOptions.value = await listUfs()
}

async function loadRecord() {
  try {
    const record = await getCidadeById(Number(route.params.id))
    form.uf_id = record.uf_id
    form.cidade = record.cidade
  } catch {
    await router.replace({ name: 'cities-list' })
  }
}

async function handleSubmit() {
  state.saving = true
  state.error = ''
  try {
    const payload = { uf_id: form.uf_id, cidade: form.cidade }
    if (isEdit.value) {
      await updateCidade(Number(route.params.id), payload)
      await successAlert('Cidade atualizada com sucesso.', 'update')
    } else {
      await createCidade(payload)
      await successAlert('Cidade cadastrada com sucesso.', 'create')
    }
    const returnTo = typeof route.query.returnTo === 'string' ? route.query.returnTo : null
    if (returnTo) {
      await router.push(returnTo)
    } else {
      await router.push({ name: 'cities-list' })
    }
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao salvar cidade'
    await errorAlert(state.error)
  } finally {
    state.saving = false
  }
}

function handleCancel() {
  const returnTo = typeof route.query.returnTo === 'string' ? route.query.returnTo : null
  if (returnTo) {
    void router.push(returnTo)
    return
  }
  void router.push({ name: 'cities-list' })
}
</script>