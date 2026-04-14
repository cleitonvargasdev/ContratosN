<template>
  <div :class="['shell', { 'shell--sidebar-collapsed': isSidebarCollapsed }]">
    <SidebarAccordion :collapsed="isSidebarCollapsed" @toggle-collapse="toggleSidebar" />

    <div class="shell__content">
      <AppHeader />
      <main class="shell__main">
        <nav v-if="breadcrumbs.length" class="breadcrumbs" aria-label="Breadcrumb">
          <template v-for="(crumb, index) in breadcrumbs" :key="`${crumb.label}-${index}`">
            <span v-if="index > 0" class="breadcrumbs__separator" aria-hidden="true">&gt;</span>
            <RouterLink v-if="crumb.to && index < breadcrumbs.length - 1" class="breadcrumbs__link" :to="crumb.to">
              {{ crumb.label }}
            </RouterLink>
            <span v-else class="breadcrumbs__current" :aria-current="index === breadcrumbs.length - 1 ? 'page' : undefined">
              {{ crumb.label }}
            </span>
          </template>
        </nav>
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, type RouteLocationRaw } from 'vue-router'

import AppHeader from '@/components/layout/AppHeader.vue'
import SidebarAccordion from '@/components/layout/SidebarAccordion.vue'
import { useAuthController } from '@/controllers/useAuthController'

type BreadcrumbItem = {
  label: string
  to?: RouteLocationRaw
}

const isSidebarCollapsed = ref(false)
const auth = useAuthController()
const route = useRoute()

const moduleLabels: Record<string, string> = {
  'api-configs': 'APIs',
  users: 'Usuarios',
  clients: 'Clientes',
  contracts: 'Contratos',
  'payment-plans': 'Planos Pagamentos',
  profiles: 'Perfis',
  ufs: 'UFs',
  cities: 'Cidades',
  bairros: 'Bairros',
  feriados: 'Feriados',
}

const standaloneLabels: Record<string, string> = {
  parameters: 'Parametros',
  'whatsapp-connection': 'Contas WhatsApp',
  'whatsapp-dispatches': 'Envios WhatsApp',
}

const breadcrumbs = computed<BreadcrumbItem[]>(() => {
  const routeName = typeof route.name === 'string' ? route.name : ''

  if (!routeName || routeName === 'dashboard') {
    return []
  }

  if (routeName === 'module-placeholder') {
    const group = formatLabel(String(route.params.group ?? 'modulos'))
    const slug = formatLabel(String(route.params.slug ?? 'modulo'))

    return [
      { label: 'Dashboard', to: { name: 'dashboard' } },
      { label: group },
      { label: slug },
    ]
  }

  if (standaloneLabels[routeName]) {
    return [
      { label: 'Dashboard', to: { name: 'dashboard' } },
      { label: standaloneLabels[routeName] },
    ]
  }

  const routeMatch = routeName.match(/^(.*)-(list|create|edit)$/)
  if (!routeMatch) {
    return [
      { label: 'Dashboard', to: { name: 'dashboard' } },
      { label: formatLabel(routeName) },
    ]
  }

  const [, moduleKey, action] = routeMatch
  const moduleLabel = moduleLabels[moduleKey] ?? formatLabel(moduleKey)

  if (action === 'list') {
    return [
      { label: 'Dashboard', to: { name: 'dashboard' } },
      { label: moduleLabel },
    ]
  }

  return [
    { label: 'Dashboard', to: { name: 'dashboard' } },
    { label: `Lista ${moduleLabel}`, to: { name: `${moduleKey}-list` } },
    { label: moduleLabel },
  ]
})

onMounted(async () => {
  await auth.initializeAuth()
  if (auth.isAuthenticated.value) {
    await auth.reloadUser()
  }
})

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

function formatLabel(value: string) {
  return value
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}
</script>

<style scoped>
.breadcrumbs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 18px;
  color: var(--text-muted);
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.breadcrumbs__separator {
  color: rgba(36, 48, 59, 0.32);
}

.breadcrumbs__link {
  color: var(--accent-strong);
  font-weight: 700;
  transition: color 160ms ease;
}

.breadcrumbs__link:hover {
  color: var(--accent);
}

.breadcrumbs__current {
  color: #24303b;
  font-weight: 800;
}

@media (max-width: 720px) {
  .breadcrumbs {
    margin-bottom: 14px;
    font-size: 0.78rem;
    letter-spacing: 0.05em;
  }
}
</style>
