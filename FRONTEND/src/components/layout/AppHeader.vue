<template>
  <header class="topbar">
    <div class="topbar__logout-card">
      <button
        class="topbar__logout-button"
        type="button"
        title="Sair do sistema"
        aria-label="Sair do sistema"
        @click="handleLogout"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M12 3a1 1 0 0 1 1 1v7a1 1 0 1 1-2 0V4a1 1 0 0 1 1-1Zm0 18a8 8 0 0 1-5.657-13.657 1 1 0 1 1 1.414 1.414A6 6 0 1 0 16.243 8.757a1 1 0 0 1 1.414-1.414A8 8 0 0 1 12 21Z"
          />
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

import { useAuthController } from '@/controllers/useAuthController'

const auth = useAuthController()
const router = useRouter()

function handleLogout() {
  auth.logout()
  void router.push({ name: 'login' })
}
</script>
