<template>
  <aside :class="['sidebar', { 'sidebar--collapsed': props.collapsed }]">
    <div class="sidebar__brand" :title="props.collapsed ? userIdentity : undefined">
      <div v-if="props.collapsed" class="sidebar__brand-mark">VS</div>
      <div v-else class="sidebar__brand-copy">
        <h2>VS-Contratos</h2>
        <p class="sidebar__brand-meta">{{ userIdentity }}</p>
      </div>

      <button
        class="sidebar__collapse-button"
        type="button"
        :title="props.collapsed ? 'Expandir menu' : 'Recolher menu'"
        :aria-label="props.collapsed ? 'Expandir menu' : 'Recolher menu'"
        @click="emit('toggle-collapse')"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12l4.58-4.59Z"
            fill="currentColor"
            :transform="props.collapsed ? 'rotate(180 12 12)' : undefined"
          />
        </svg>
      </button>
    </div>

    <nav v-if="!props.collapsed" class="sidebar__nav">
      <div v-for="section in menuSections" :key="section.title" class="sidebar__group">
        <button class="sidebar__group-button" type="button" @click="toggle(section.title)">
          <span class="sidebar__group-title">
            <span class="sidebar__group-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path :d="iconPaths[section.icon]" fill="currentColor" />
              </svg>
            </span>
            <span>{{ section.title }}</span>
          </span>
          <span class="sidebar__group-chevron" :class="{ 'sidebar__group-chevron--open': opened.has(section.title) }" aria-hidden="true">
            ›
          </span>
        </button>

        <div v-if="opened.has(section.title)" class="sidebar__links">
          <RouterLink
            v-for="link in section.links"
            :key="link.to"
            :to="link.to"
            class="sidebar__link"
            active-class="sidebar__link--active"
          >
            <span class="sidebar__link-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path :d="iconPaths[link.icon]" fill="currentColor" />
              </svg>
            </span>
            <span>{{ link.label }}</span>
          </RouterLink>
        </div>
      </div>
    </nav>

    <nav v-else class="sidebar__nav sidebar__nav--collapsed">
      <div v-for="section in menuSections" :key="section.title" class="sidebar__collapsed-group">
        <button
          class="sidebar__group-button sidebar__group-button--icon-only"
          type="button"
          :title="section.title"
          :aria-label="section.title"
          @click="toggleCollapsedSection(section.title)"
        >
          <span class="sidebar__group-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path :d="iconPaths[section.icon]" fill="currentColor" />
            </svg>
          </span>
        </button>

        <div v-if="collapsedSection === section.title" class="sidebar__collapsed-links">
          <RouterLink
            v-for="link in section.links"
            :key="link.to"
            :to="link.to"
            class="sidebar__link sidebar__link--icon-only"
            active-class="sidebar__link--active"
            :title="link.label"
            :aria-label="link.label"
          >
            <span class="sidebar__link-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path :d="iconPaths[link.icon]" fill="currentColor" />
              </svg>
            </span>
          </RouterLink>
        </div>
      </div>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { useAuthController } from '@/controllers/useAuthController'

const props = defineProps<{
  collapsed: boolean
}>()

const emit = defineEmits<{
  'toggle-collapse': []
}>()

const auth = useAuthController()

const userFunction = computed(() => {
  const profileNames = auth.state.currentUser?.perfil_nomes ?? []
  const joinedProfiles = profileNames.join(' / ')
  if (auth.state.currentUser?.funcao) {
    return auth.state.currentUser.funcao
  }

  if (joinedProfiles) {
    return joinedProfiles
  }

  if (auth.state.currentUser?.perfil_nome) {
    return auth.state.currentUser.perfil_nome
  }

  return 'Operador'
})

const userIdentity = computed(() => {
  const userName = auth.state.currentUser?.nome ?? 'Usuário logado'
  return `${userName} - ${userFunction.value}`
})

const iconPaths = {
  users: 'M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3ZM8 11c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3Zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5C15 14.17 10.33 13 8 13Zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.98 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5Z',
  map: 'M15 5.69 9 3 3 5.31v15.38l6-2.31 6 2.31 6-2.31V3.31l-6 2.38ZM14 18.3l-4-1.55V4.7l4 1.55V18.3Z',
  whatsapp: 'M16.75 13.96c-.25-.13-1.47-.72-1.69-.8-.23-.08-.39-.12-.56.12-.16.25-.64.8-.78.96-.14.17-.29.19-.54.07-.25-.13-1.05-.39-2-1.23-.74-.66-1.24-1.47-1.38-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.29.37-.43.12-.15.16-.25.25-.42.08-.17.04-.31-.02-.43-.06-.13-.56-1.35-.77-1.85-.2-.48-.4-.41-.56-.42h-.47c-.16 0-.42.06-.64.31-.22.25-.84.82-.84 2s.86 2.31.98 2.47c.12.17 1.69 2.58 4.1 3.62.57.25 1.02.4 1.37.51.57.18 1.08.16 1.49.1.45-.07 1.38-.56 1.57-1.11.2-.55.2-1.03.14-1.12-.06-.1-.22-.16-.46-.28ZM12.04 2C6.52 2 2.04 6.47 2.04 12c0 1.95.56 3.77 1.53 5.31L2 22l4.84-1.51A9.94 9.94 0 0 0 12.04 22C17.56 22 22.04 17.53 22.04 12S17.56 2 12.04 2Z',
  bank: 'M3 10V8l9-5 9 5v2H3Zm2 2h2v6H5v-6Zm4 0h2v6H9v-6Zm4 0h2v6h-2v-6Zm4 0h2v6h-2v-6ZM3 20v-2h18v2H3Z',
  ledger: 'M5 3h12a2 2 0 0 1 2 2v14l-4-2-4 2-4-2-4 2V5a2 2 0 0 1 2-2Zm2 4v2h8V7H7Zm0 4v2h8v-2H7Z',
  card: 'M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Zm0 3v2h16V8H4Zm2 6v2h5v-2H6Z',
  contacts: 'M7 4h10a2 2 0 0 1 2 2v12l-4-2-4 2-4-2-4 2V6a2 2 0 0 1 2-2Zm1 3a2 2 0 1 0 4 0 2 2 0 0 0-4 0Zm7 1h2V6h-2v2Zm-7 6h8v-1c0-1.66-3.58-2.5-5-2.5S8 11.34 8 13v1Zm7-2h2v-2h-2v2Z',
  calendar: 'M7 2h2v2h6V2h2v2h3a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h3V2Zm13 8H4v9h16v-9Z',
  wallet: 'M3 7a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2v2h1a1 1 0 0 1 1 1v6a3 3 0 0 1-3 3H5a2 2 0 0 1-2-2V7Zm15 0H5v10h14a1 1 0 0 0 1-1v-1h-3a2 2 0 0 1 0-4h3V9a2 2 0 0 0-2-2Zm-1 6a1 1 0 0 0 0 2h3v-2h-3Z',
  receipt: 'M6 2h12v20l-2.5-1.5L13 22l-2.5-1.5L8 22l-2-1.2V2Zm3 4v2h6V6H9Zm0 4v2h6v-2H9Zm0 4v2h4v-2H9Z',
  route: 'M14 6a3 3 0 1 1 6 0 3 3 0 0 1-6 0ZM4 18a3 3 0 1 1 6 0 3 3 0 0 1-6 0Zm3-1h10v-2H7a3 3 0 0 1 0-6h6V7H7a5 5 0 0 0 0 10Z',
  box: 'M12 2 3 7l9 5 9-5-9-5Zm-7 7v8l7 5v-8L5 9Zm9 13 7-5V9l-7 5v8Z',
  sliders: 'M4 7h10V5H4v2Zm0 12h16v-2H4v2Zm6-6h10v-2H10v2Zm6-9h4V2h-4v2ZM6 15h4v-2H6v2Zm8-6h4V7h-4v2Z',
  contract: 'M6 2h9l5 5v15a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm8 1.5V8h4.5L14 3.5ZM8 12h8v-2H8v2Zm0 4h8v-2H8v2Z',
  unlock: 'M12 1a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2H9V6a3 3 0 1 1 6 0h2a5 5 0 0 0-5-5Z',
  layers: 'M12 2 1 7l11 5 9-4.09V17h2V7L12 2Zm0 13L1 10v4l11 5 11-5v-4l-11 5Zm0 6L1 16v4l11 5 11-5v-4l-11 5Z',
  payment: 'M21 8V7a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-1h-8a3 3 0 0 1 0-6h8Zm-8 5a1 1 0 1 1 0-2h8v2h-8Z',
  report: 'M5 3h14a2 2 0 0 1 2 2v14l-4-3-4 3-4-3-4 3V5a2 2 0 0 1 2-2Zm3 4v2h8V7H8Zm0 4v2h8v-2H8Z',
  history: 'M13 3a9 9 0 1 0 8.95 10h-2.02A7 7 0 1 1 13 5a6.96 6.96 0 0 1 4.95 2.05L15 10h7V3l-2.63 2.63A8.96 8.96 0 0 0 13 3Zm-1 5v5l4.25 2.52.75-1.23-3.5-2.04V8H12Z',
} as const

type SidebarIcon = keyof typeof iconPaths
type SidebarLink = {
  label: string
  to: string
  icon: SidebarIcon
  resource?: string
  action?: 'create' | 'read' | 'update' | 'delete'
}

type SidebarSection = {
  title: string
  icon: SidebarIcon
  links: SidebarLink[]
}

const baseSections: SidebarSection[] = [
  {
    title: 'Cadastros',
    icon: 'contacts',
    links: [
      { label: 'Usuários', to: '/usuarios', resource: 'usuarios', action: 'read', icon: 'users' },
      { label: 'Perfil de usuários', to: '/perfis', resource: 'perfis', action: 'read', icon: 'contacts' },
      { label: 'Contas WhatsApp', to: '/contas-whatsapp', icon: 'whatsapp' },
      { label: 'Envios WhatsApp', to: '/envios-whatsapp', icon: 'history' },
      { label: 'APIs', to: '/apis', resource: 'apis', action: 'read', icon: 'sliders' },
      { label: 'Contas Bancárias', to: '/modulos/cadastros/contas-bancarias?titulo=Contas%20Banc%C3%A1rias&grupo=Cadastros', icon: 'bank' },
      { label: 'Plano de contas', to: '/modulos/cadastros/plano-de-contas?titulo=Plano%20de%20contas&grupo=Cadastros', icon: 'ledger' },
      { label: 'Planos de Pagamento', to: '/planos-pagamentos', resource: 'planos_pagamentos', action: 'read', icon: 'card' },
      { label: 'Clientes', to: '/clientes', resource: 'clientes', action: 'read', icon: 'contacts' },
      { label: 'Feriados', to: '/feriados', resource: 'localidades_feriados', action: 'read', icon: 'calendar' },
      { label: 'Contas à Pagar', to: '/modulos/cadastros/contas-a-pagar?titulo=Contas%20%C3%A0%20Pagar&grupo=Cadastros', icon: 'wallet' },
      { label: 'Contas à Receber', to: '/modulos/cadastros/contas-a-receber?titulo=Contas%20%C3%A0%20Receber&grupo=Cadastros', icon: 'receipt' },
      { label: 'Rotas', to: '/modulos/cadastros/rotas?titulo=Rotas&grupo=Cadastros', icon: 'route' },
      { label: 'Produtos', to: '/modulos/cadastros/produtos?titulo=Produtos&grupo=Cadastros', icon: 'box' },
      { label: 'Parâmetros', to: '/parametros', icon: 'sliders' },
    ],
  },
  {
    title: 'Movimentações',
    icon: 'contract',
    links: [
      { label: 'Contratos', to: '/contratos', resource: 'contratos', action: 'read', icon: 'contract' },
      { label: 'Mapa de Ocorrências', to: '/modulos/movimentacoes/mapa-de-ocorrencias?titulo=Mapa%20de%20Ocorr%C3%AAncias&grupo=Movimenta%C3%A7%C3%B5es', icon: 'map' },
      { label: 'Desbloqueio', to: '/modulos/movimentacoes/desbloqueio?titulo=Desbloqueio&grupo=Movimenta%C3%A7%C3%B5es', icon: 'unlock' },
      { label: 'Recebimento Lote', to: '/modulos/movimentacoes/recebimento-lote?titulo=Recebimento%20Lote&grupo=Movimenta%C3%A7%C3%B5es', icon: 'layers' },
      { label: 'Pagamentos', to: '/modulos/movimentacoes/pagamentos?titulo=Pagamentos&grupo=Movimenta%C3%A7%C3%B5es', icon: 'payment' },
    ],
  },
  {
    title: 'Relatórios',
    icon: 'report',
    links: [
      { label: 'Contas à Receber', to: '/modulos/relatorios/contas-a-receber?titulo=Contas%20%C3%A0%20Receber&grupo=Relat%C3%B3rios', icon: 'receipt' },
      { label: 'Contas à Pagar', to: '/modulos/relatorios/contas-a-pagar?titulo=Contas%20%C3%A0%20Pagar&grupo=Relat%C3%B3rios', icon: 'wallet' },
      { label: 'Ocorrências', to: '/modulos/relatorios/ocorrencias?titulo=Ocorr%C3%AAncias&grupo=Relat%C3%B3rios', icon: 'report' },
      { label: 'Contratos', to: '/modulos/relatorios/contratos?titulo=Contratos&grupo=Relat%C3%B3rios', icon: 'contract' },
      { label: 'Clientes', to: '/modulos/relatorios/clientes?titulo=Clientes&grupo=Relat%C3%B3rios', icon: 'contacts' },
    ],
  },
  {
    title: 'Consultas',
    icon: 'history',
    links: [
      { label: 'Log de Operações', to: '/modulos/consultas/log-de-operacoes?titulo=Log%20de%20Opera%C3%A7%C3%B5es&grupo=Consultas', icon: 'history' },
    ],
  },
]

const menuSections = computed(() =>
  baseSections
    .map((section) => ({
      ...section,
      links: section.links.filter((link) => !link.resource || auth.hasPermission(link.resource, link.action as 'create' | 'read' | 'update' | 'delete')),
    }))
    .filter((section) => section.links.length > 0),
)

const collapsedSection = ref<string | null>(null)

const opened = reactive(new Set<string>())

watch(
  () => props.collapsed,
  () => {
    opened.clear()
    collapsedSection.value = null
  },
  { immediate: true },
)

function toggle(section: string) {
  if (opened.has(section)) {
    opened.delete(section)
    return
  }

  opened.clear()
  opened.add(section)
}

function toggleCollapsedSection(section: string) {
  collapsedSection.value = collapsedSection.value === section ? null : section
}
</script>
