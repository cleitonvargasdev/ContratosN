<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <h2 class="panel__title">{{ isEdit ? 'Editar API' : 'Nova API' }}</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="field-group">
        <span>Nome API</span>
        <input v-model="form.nome_api" class="field" maxlength="120" required type="text" />
      </label>

      <label class="field-group">
        <span>Usuário</span>
        <select v-model.number="form.usuario_id" class="field">
          <option :value="null">Selecione</option>
          <option v-for="user in users" :key="user.id" :value="user.id">{{ user.nome }}</option>
        </select>
      </label>

      <label class="field-group field-group--span-2">
        <span>Funcionalidade</span>
        <input v-model="form.funcionalidade" class="field" maxlength="200" type="text" />
      </label>

      <label class="field-group field-group--span-2">
        <span>URL</span>
        <input v-model="form.url" class="field" maxlength="255" type="text" />
      </label>

      <label class="field-group">
        <span>Key 1</span>
        <input v-model="form.key1" class="field" maxlength="100" type="text" />
      </label>
      <label class="field-group">
        <span>Value 1</span>
        <input v-model="form.value1" class="field" maxlength="255" type="text" />
      </label>

      <label class="field-group">
        <span>Key 2</span>
        <input v-model="form.key2" class="field" maxlength="100" type="text" />
      </label>
      <label class="field-group">
        <span>Value 2</span>
        <input v-model="form.value2" class="field" maxlength="255" type="text" />
      </label>

      <label class="field-group">
        <span>Key 3</span>
        <input v-model="form.key3" class="field" maxlength="100" type="text" />
      </label>
      <label class="field-group">
        <span>Value 3</span>
        <input v-model="form.value3" class="field" maxlength="255" type="text" />
      </label>

      <label class="field-group">
        <span>Key 4</span>
        <input v-model="form.key4" class="field" maxlength="100" type="text" />
      </label>
      <label class="field-group">
        <span>Value 4</span>
        <input v-model="form.value4" class="field" maxlength="255" type="text" />
      </label>

      <label class="field-group">
        <span>Key 5</span>
        <input v-model="form.key5" class="field" maxlength="100" type="text" />
      </label>
      <label class="field-group">
        <span>Value 5</span>
        <input v-model="form.value5" class="field" maxlength="255" type="text" />
      </label>

      <label class="field-group field-group--span-2">
        <span>Body</span>
        <textarea v-model="form.body" class="field field--textarea" rows="8"></textarea>
      </label>

      <div class="form-actions form-actions--user field-group--span-2">
        <button class="primary-button primary-button--success form-actions__button" :disabled="state.saving || state.loading" type="submit">
          {{ state.saving ? 'Salvando...' : 'Salvar' }}
        </button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="state.saving" type="button" @click="router.push({ name: 'api-configs-list' })">
          Cancelar
        </button>
      </div>
    </form>

    <p v-if="state.error" class="feedback feedback--error">{{ state.error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { ApiConfigInput } from '@/models/apiConfig'
import type { User } from '@/models/user'
import { errorAlert, successAlert } from '@/services/alertService'
import { createApiConfig, getApiConfigById, updateApiConfig } from '@/services/apiConfigService'
import { listUsers } from '@/services/userService'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const users = ref<User[]>([])
const form = reactive({
  usuario_id: null as number | null,
  nome_api: '',
  funcionalidade: '',
  url: '',
  key1: '',
  value1: '',
  key2: '',
  value2: '',
  key3: '',
  value3: '',
  key4: '',
  value4: '',
  key5: '',
  value5: '',
  body: '',
})
const state = reactive({ loading: false, saving: false, error: '' })

onMounted(() => {
  void loadUsers()
  if (isEdit.value) {
    void loadRecord()
  }
})

async function loadUsers() {
  try {
    const response = await listUsers({ page: 1, page_size: 100, ativo: true })
    users.value = [...response.items]
  } catch {
    users.value = []
  }
}

async function loadRecord() {
  state.loading = true
  try {
    const record = await getApiConfigById(Number(route.params.id))
    form.usuario_id = record.usuario_id
    form.nome_api = record.nome_api ?? ''
    form.funcionalidade = record.funcionalidade ?? ''
    form.url = record.url ?? ''
    form.key1 = record.key1 ?? ''
    form.value1 = record.value1 ?? ''
    form.key2 = record.key2 ?? ''
    form.value2 = record.value2 ?? ''
    form.key3 = record.key3 ?? ''
    form.value3 = record.value3 ?? ''
    form.key4 = record.key4 ?? ''
    form.value4 = record.value4 ?? ''
    form.key5 = record.key5 ?? ''
    form.value5 = record.value5 ?? ''
    form.body = record.body ?? ''
  } catch {
    await router.replace({ name: 'api-configs-list' })
  } finally {
    state.loading = false
  }
}

async function handleSubmit() {
  state.saving = true
  state.error = ''
  try {
    const payload: ApiConfigInput = {
      usuario_id: form.usuario_id,
      nome_api: emptyToNull(form.nome_api),
      funcionalidade: emptyToNull(form.funcionalidade),
      url: emptyToNull(form.url),
      key1: emptyToNull(form.key1),
      value1: emptyToNull(form.value1),
      key2: emptyToNull(form.key2),
      value2: emptyToNull(form.value2),
      key3: emptyToNull(form.key3),
      value3: emptyToNull(form.value3),
      key4: emptyToNull(form.key4),
      value4: emptyToNull(form.value4),
      key5: emptyToNull(form.key5),
      value5: emptyToNull(form.value5),
      body: emptyToNull(form.body),
    }

    if (isEdit.value) {
      await updateApiConfig(Number(route.params.id), payload)
      await successAlert('API atualizada com sucesso.', 'update')
    } else {
      await createApiConfig(payload)
      await successAlert('API cadastrada com sucesso.', 'create')
    }

    await router.push({ name: 'api-configs-list' })
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao salvar API'
    await errorAlert(state.error)
  } finally {
    state.saving = false
  }
}

function emptyToNull(value: string | null | undefined) {
  const normalized = value?.trim() ?? ''
  return normalized ? normalized : null
}
</script>