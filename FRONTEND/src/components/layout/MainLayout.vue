<template>
  <div :class="['shell', { 'shell--sidebar-collapsed': isSidebarCollapsed }]">
    <SidebarAccordion :collapsed="isSidebarCollapsed" @toggle-collapse="toggleSidebar" />

    <div class="shell__content">
      <AppHeader />
      <main class="shell__main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterView } from 'vue-router'

import AppHeader from '@/components/layout/AppHeader.vue'
import SidebarAccordion from '@/components/layout/SidebarAccordion.vue'
import { useAuthController } from '@/controllers/useAuthController'

const isSidebarCollapsed = ref(false)
const auth = useAuthController()

onMounted(async () => {
  await auth.initializeAuth()
  if (auth.isAuthenticated.value) {
    await auth.reloadUser()
  }
})

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}
</script>
