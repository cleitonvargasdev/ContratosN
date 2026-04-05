<template>
  <div class="login-shell">
    <section class="login-panel login-panel--form">
      <div class="login-form-head">
        <p class="login-form-brand">VS-Contratos</p>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <label class="field-group">
          <span>Login</span>
          <input v-model="credentials.username" class="field" placeholder="ana.souza" required type="text" />
        </label>

        <label class="field-group">
          <span>Senha</span>
          <input v-model="credentials.password" class="field" placeholder="123456" required type="password" />
        </label>

        <button class="primary-button primary-button--block" :disabled="auth.state.loading" type="submit">
          {{ auth.state.loading ? 'Autenticando...' : 'Entrar no sistema' }}
        </button>
      </form>

      <p v-if="auth.state.error" class="feedback feedback--error">{{ auth.state.error }}</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthController } from '@/controllers/useAuthController'

const auth = useAuthController()
const router = useRouter()

const credentials = reactive({
  username: 'ana.souza',
  password: '123456',
})

async function handleSubmit() {
  try {
    await auth.login({ ...credentials })
    await router.push({ name: 'dashboard' })
  } catch {
    return
  }
}
</script>
