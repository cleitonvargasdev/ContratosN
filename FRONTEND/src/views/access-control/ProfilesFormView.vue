<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <p class="eyebrow">Seguranca</p>
        <h2 class="panel__title">{{ isEdit ? 'Editar perfil' : 'Novo perfil' }}</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="field-group">
        <span>Nome</span>
        <input v-model="form.nome" class="field" required type="text" />
      </label>

      <label class="field-group">
        <span>Status</span>
        <select v-model="statusValue" class="field">
          <option value="true">Ativo</option>
          <option value="false">Inativo</option>
        </select>
      </label>

      <label class="field-group field-group--span-2">
        <span>Descricao</span>
        <input v-model="form.descricao" class="field" type="text" />
      </label>

      <section class="field-group field-group--span-2 permission-board">
        <span>Permissoes por recurso</span>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Grupo</th>
                <th>Recurso</th>
                <th>Ler</th>
                <th>Criar</th>
                <th>Alterar</th>
                <th>Excluir</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in permissionRows" :key="item.resource_key">
                <td>{{ item.resource_group }}</td>
                <td>{{ item.resource_label }}</td>
                <td><input v-model="item.can_read" :disabled="!supports(item, 'read')" type="checkbox" /></td>
                <td><input v-model="item.can_create" :disabled="!supports(item, 'create')" type="checkbox" /></td>
                <td><input v-model="item.can_update" :disabled="!supports(item, 'update')" type="checkbox" /></td>
                <td><input v-model="item.can_delete" :disabled="!supports(item, 'delete')" type="checkbox" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div class="form-actions form-actions--user field-group--span-2">
        <button class="primary-button primary-button--success form-actions__button" :disabled="state.saving" type="submit">
          {{ state.saving ? 'Salvando...' : 'Salvar' }}
        </button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="state.saving" type="button" @click="router.push({ name: 'profiles-list' })">
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

import type { PermissionAction, PermissionResource, ProfileInput } from '@/models/accessControl'
import { errorAlert, successAlert } from '@/services/alertService'
import { createProfile, getProfileById, listPermissionResources, updateProfile } from '@/services/accessControlService'

interface PermissionRow extends PermissionResource {
  can_read: boolean
  can_create: boolean
  can_update: boolean
  can_delete: boolean
}

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const statusValue = computed({
  get: () => String(form.ativo),
  set: (value: string) => {
    form.ativo = value === 'true'
  },
})

const form = reactive({
  nome: '',
  descricao: '',
  ativo: true,
})
const permissionRows = ref<PermissionRow[]>([])
const state = reactive({ loading: false, saving: false, error: '' })

onMounted(() => {
  void initialize()
})

async function initialize() {
  state.loading = true
  try {
    const resources = await listPermissionResources()
    permissionRows.value = resources.map((item) => ({
      ...item,
      can_read: false,
      can_create: false,
      can_update: false,
      can_delete: false,
    }))

    if (isEdit.value) {
      const record = await getProfileById(Number(route.params.id))
      form.nome = record.nome
      form.descricao = record.descricao ?? ''
      form.ativo = record.ativo
      for (const permission of record.permissions) {
        const current = permissionRows.value.find((item) => item.resource_key === permission.resource_key)
        if (!current) continue
        current.can_read = permission.can_read
        current.can_create = permission.can_create
        current.can_update = permission.can_update
        current.can_delete = permission.can_delete
      }
    }
  } catch {
    await router.replace({ name: 'profiles-list' })
  } finally {
    state.loading = false
  }
}

function supports(item: PermissionRow, action: PermissionAction) {
  return item.supported_actions.includes(action)
}

async function handleSubmit() {
  state.saving = true
  state.error = ''
  try {
    const payload: ProfileInput = {
      nome: form.nome,
      descricao: form.descricao.trim() || null,
      ativo: form.ativo,
      permissions: permissionRows.value.map((item) => ({
        resource_key: item.resource_key,
        resource_label: item.resource_label,
        can_read: supports(item, 'read') ? item.can_read : false,
        can_create: supports(item, 'create') ? item.can_create : false,
        can_update: supports(item, 'update') ? item.can_update : false,
        can_delete: supports(item, 'delete') ? item.can_delete : false,
      })),
    }

    if (isEdit.value) {
      await updateProfile(Number(route.params.id), payload)
      await successAlert('Perfil atualizado com sucesso.', 'update')
    } else {
      await createProfile(payload)
      await successAlert('Perfil cadastrado com sucesso.', 'create')
    }

    await router.push({ name: 'profiles-list' })
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Falha ao salvar perfil'
    await errorAlert(state.error)
  } finally {
    state.saving = false
  }
}
</script>
