<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <p class="eyebrow">Cadastros diversos</p>
        <h2 class="panel__title">{{ isEdit ? 'Editar bairro' : 'Novo bairro' }}</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="field-group">
        <span>UF</span>
        <select v-model="form.uf" class="field" required>
          <option value="">Selecione</option>
          <option v-for="item in ufOptions" :key="item.uf_id" :value="item.uf">{{ item.uf }} - {{ item.uf_nome }}</option>
        </select>
      </label>
      <label class="field-group">
        <span>Cidade</span>
        <select v-model.number="form.cidade_id" class="field" :disabled="!form.uf" required>
          <option :value="0">Selecione</option>
          <option v-for="item in cityOptions" :key="item.cidade_id" :value="item.cidade_id">{{ item.uf }} - {{ item.cidade }}</option>
        </select>
      </label>
      <label class="field-group">
        <span>Bairro</span>
        <input v-model="form.bairro_nome" class="field" required type="text" />
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { CidadeOption, UFOption } from '@/models/location'
import { errorAlert, successAlert } from '@/services/alertService'
import { createBairro, getBairroById, listCitiesByUf, listUfs, updateBairro } from '@/services/locationService'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const ufOptions = ref<UFOption[]>([])
const cityOptions = ref<CidadeOption[]>([])
const form = reactive({ uf: '', cidade_id: 0, bairro_nome: '' })
const state = reactive({ saving: false, error: '' })

onMounted(() => {
  void loadUfOptions()
  if (isEdit.value) {
    void loadRecord()
  } else if (route.query.uf) {
    form.uf = String(route.query.uf)
  }
})

watch(
  () => form.uf,
  (uf, previousUf) => {
    if (!uf) {
      cityOptions.value = []
      form.cidade_id = 0
      return
    }

    if (uf !== previousUf) {
      form.cidade_id = 0
    }

    void loadCities(uf)
  },
)

watch(
  () => route.query.cidade_id,
  (cidadeId) => {
    if (!isEdit.value && cidadeId && Number(cidadeId) > 0) {
      form.cidade_id = Number(cidadeId)
    }
  },
  { immediate: true },
)

async function loadUfOptions() {
  ufOptions.value = await listUfs()
}

async function loadCities(uf: string) {
  cityOptions.value = await listCitiesByUf(uf)

  if (route.query.cidade_id && Number(route.query.cidade_id) > 0 && !isEdit.value) {
    form.cidade_id = Number(route.query.cidade_id)
  }
}

async function loadRecord() {
  try {
    const record = await getBairroById(Number(route.params.id))
    form.uf = record.uf ?? ''
    if (form.uf) {
      await loadCities(form.uf)
    }
    form.cidade_id = record.cidade_id
    form.bairro_nome = record.bairro_nome
  } catch {
    await router.replace({ name: 'bairros-list' })
  }
}

async function handleSubmit() {
  state.saving = true
  state.error = ''
  try {
    const payload = { cidade_id: form.cidade_id, bairro_nome: form.bairro_nome }
    if (isEdit.value) {
      await updateBairro(Number(route.params.id), payload)
      await successAlert('Bairro atualizado com sucesso.', 'update')
    } else {
      await createBairro(payload)
      await successAlert('Bairro cadastrado com sucesso.', 'create')
    }
    const returnTo = typeof route.query.returnTo === 'string' ? route.query.returnTo : null
    if (returnTo) {
      await router.push(returnTo)
    } else {
      await router.push({ name: 'bairros-list' })
    }
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao salvar bairro'
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
  void router.push({ name: 'bairros-list' })
}
</script>