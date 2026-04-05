<template>
  <UserForm
    mode="edit"
    :error="users.state.error"
    :initial-user="users.state.currentUser"
    :saving="users.state.saving"
    :success="users.state.success"
    @cancel="handleCancel"
    @submit="handleSubmit"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import UserForm from '@/components/users/UserForm.vue'
import { useAuthController } from '@/controllers/useAuthController'
import { useUsersController } from '@/controllers/useUsersController'
import type { UserCreateInput, UserUpdateInput } from '@/models/user'
import { errorAlert, successAlert } from '@/services/alertService'

const auth = useAuthController()
const users = useUsersController()
const route = useRoute()
const router = useRouter()

onMounted(async () => {
  if (!auth.hasPermission('usuarios', 'update')) {
    await router.replace({ name: 'users-list' })
    return
  }

  try {
    await users.loadUser(Number(route.params.id))
  } catch {
    await router.replace({ name: 'users-list' })
  }
})

async function handleSubmit(payload: UserCreateInput | UserUpdateInput) {
  try {
    await users.submitUserUpdate(Number(route.params.id), payload as UserUpdateInput)
    void successAlert('Cadastro alterado com sucesso.', 'update')
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