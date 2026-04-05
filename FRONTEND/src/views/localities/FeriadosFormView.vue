<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <h2 class="panel__title">{{ isEdit ? 'Editar feriado' : 'Novo feriado' }}</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="field-group">
        <span>Data</span>
        <input v-model="form.data" class="field" required type="date" />
      </label>

      <label class="field-group">
        <span>Nível do feriado</span>
        <select v-model.number="form.nivel" class="field" required>
          <option :value="1">Nacional</option>
          <option :value="2">Estadual</option>
          <option :value="3">Municipal</option>
        </select>
      </label>

      <label class="field-group">
        <span>Descrição</span>
        <input v-model="form.descricao" class="field" maxlength="50" required type="text" />
      </label>

      <label class="field-group">
        <span>UF</span>
        <select v-model="form.uf" class="field" :disabled="form.nivel === 1" :required="form.nivel === 2 || form.nivel === 3">
          <option value="">Selecione</option>
          <option v-for="item in ufOptions" :key="item.uf_id" :value="item.uf">{{ item.uf }} - {{ item.uf_nome }}</option>
        </select>
      </label>

      <label class="field-group">
        <span>Cidade</span>
        <select v-model.number="form.cidade_id" class="field" :disabled="form.nivel !== 3 || !form.uf" :required="form.nivel === 3">
          <option :value="0">Selecione</option>
          <option v-for="item in cityOptions" :key="item.cidade_id" :value="item.cidade_id">{{ item.uf }} - {{ item.cidade }}</option>
        </select>
      </label>

      <div class="form-actions form-actions--user field-group--span-2">
        <button class="primary-button primary-button--success form-actions__button" :disabled="state.saving" type="submit">{{ state.saving ? 'Salvando...' : 'Salvar' }}</button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="state.saving" type="button" @click="router.push({ name: 'feriados-list' })">Cancelar</button>
      </div>
    </form>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { CidadeOption, FeriadoInput, UFOption } from '@/models/location'
import { errorAlert, successAlert } from '@/services/alertService'
import { createFeriado, getFeriadoById, listCitiesByUf, listUfs, updateFeriado } from '@/services/locationService'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const ufOptions = ref<UFOption[]>([])
const cityOptions = ref<CidadeOption[]>([])
const form = reactive({ data: '', nivel: 1, descricao: '', uf: '', cidade_id: 0 })
const state = reactive({ loading: false, saving: false, error: '' })

onMounted(() => {
  void loadUfOptions()
  if (isEdit.value) {
    void loadRecord()
  }
})

watch(
  () => form.nivel,
  (nivel) => {
    if (nivel === 1) {
      form.uf = ''
      form.cidade_id = 0
      cityOptions.value = []
      return
    }

    if (nivel === 2) {
      form.cidade_id = 0
      cityOptions.value = []
      return
    }

    if (!form.uf) {
      form.cidade_id = 0
      cityOptions.value = []
    }
  },
)

watch(
  () => form.uf,
  (uf) => {
    if (form.nivel !== 3) {
      return
    }
    if (!uf) {
      form.cidade_id = 0
      cityOptions.value = []
      return
    }
    void loadCities(uf)
  },
)

async function loadUfOptions() {
  ufOptions.value = await listUfs()
}

async function loadCities(uf: string) {
  cityOptions.value = await listCitiesByUf(uf)
}

async function loadRecord() {
  state.loading = true
  try {
    const record = await getFeriadoById(Number(route.params.id))
    form.data = record.data
    form.nivel = record.nivel
    form.descricao = record.descricao
    form.uf = record.uf ?? ''
    if (form.nivel === 3 && form.uf) {
      await loadCities(form.uf)
    }
    form.cidade_id = record.cidade_id ?? 0
  } catch {
    await router.replace({ name: 'feriados-list' })
  } finally {
    state.loading = false
  }
}

async function handleSubmit() {
  state.saving = true
  state.error = ''
  try {
    const payload: FeriadoInput = {
      data: form.data,
      nivel: form.nivel,
      descricao: form.descricao,
      uf: form.nivel === 2 || form.nivel === 3 ? form.uf : null,
      cidade_id: form.nivel === 3 ? form.cidade_id : null,
    }

    if (isEdit.value) {
      await updateFeriado(Number(route.params.id), payload)
      await successAlert('Feriado atualizado com sucesso.', 'update')
    } else {
      await createFeriado(payload)
      await successAlert('Feriado cadastrado com sucesso.', 'create')
    }
    await router.push({ name: 'feriados-list' })
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao salvar feriado'
    await errorAlert(state.error)
  } finally {
    state.saving = false
  }
}
</script>
