<template>
  <UserForm
    mode="create"
    :error="users.state.error"
    :saving="users.state.saving"
    :success="users.state.success"
    @cancel="handleCancel"
    @submit="handleSubmit"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import UserForm from '@/components/users/UserForm.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useUsersController } from '@/controllers/useUsersController'
import type { UserCreateInput, UserUpdateInput } from '@/models/user'
import { errorAlert, successAlert } from '@/services/alertService'

const auth = useAuthController()
const users = useUsersController()
const router = useRouter()

onMounted(() => {
  if (!auth.hasPermission('usuarios', 'create')) {
    void router.replace({ name: 'users-list' })
  }
})

async function handleSubmit(payload: UserCreateInput | UserUpdateInput) {
  try {
    await users.submitUser(payload as UserCreateInput)
    void successAlert('Novo cadastro salvo com sucesso.', 'create')
    await new Promise((resolve) => window.setTimeout(resolve, 1000))
    await router.push({ name: 'users-list' })
  } catch {
    if (users.state.error) {
      await errorAlert(users.state.error)
    }
    return
  }
}

function handleCancel() {
  void router.push({ name: 'users-list' })
}
</script>
