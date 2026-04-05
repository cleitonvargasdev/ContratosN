import { createRouter, createWebHistory } from 'vue-router'

import { useAuthController } from '@/controllers/useAuthController'
import MainLayout from '@/components/layout/MainLayout.vue'
import DashboardHomeView from '@/views/dashboard/DashboardHomeView.vue'
import LoginView from '@/views/auth/LoginView.vue'
import PaymentPlansFormView from '@/views/payment-plans/PaymentPlansFormView.vue'
import PaymentPlansListView from '@/views/payment-plans/PaymentPlansListView.vue'
import ModulePlaceholderView from '@/views/shared/ModulePlaceholderView.vue'
import ProfilesFormView from '@/views/access-control/ProfilesFormView.vue'
import ProfilesListView from '@/views/access-control/ProfilesListView.vue'
import BairrosFormView from '@/views/localities/BairrosFormView.vue'
import BairrosListView from '@/views/localities/BairrosListView.vue'
import CidadesFormView from '@/views/localities/CidadesFormView.vue'
import CidadesListView from '@/views/localities/CidadesListView.vue'
import FeriadosFormView from '@/views/localities/FeriadosFormView.vue'
import FeriadosListView from '@/views/localities/FeriadosListView.vue'
import UfsFormView from '@/views/localities/UfsFormView.vue'
import UfsListView from '@/views/localities/UfsListView.vue'
import UsersCreateView from '@/views/users/UsersCreateView.vue'
import UsersEditView from '@/views/users/UsersEditView.vue'
import UsersListView from '@/views/users/UsersListView.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guestOnly: true },
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: DashboardHomeView,
        meta: { resource: 'dashboard', action: 'read' },
      },
      {
        path: 'usuarios',
        name: 'users-list',
        component: UsersListView,
        meta: { resource: 'usuarios', action: 'read' },
      },
      {
        path: 'usuarios/novo',
        name: 'users-create',
        component: UsersCreateView,
        meta: { resource: 'usuarios', action: 'create' },
      },
      {
        path: 'usuarios/:id/editar',
        name: 'users-edit',
        component: UsersEditView,
        meta: { resource: 'usuarios', action: 'update' },
      },
      {
        path: 'planos-pagamentos',
        name: 'payment-plans-list',
        component: PaymentPlansListView,
        meta: { resource: 'planos_pagamentos', action: 'read' },
      },
      {
        path: 'planos-pagamentos/novo',
        name: 'payment-plans-create',
        component: PaymentPlansFormView,
        meta: { resource: 'planos_pagamentos', action: 'create' },
      },
      {
        path: 'planos-pagamentos/:id/editar',
        name: 'payment-plans-edit',
        component: PaymentPlansFormView,
        meta: { resource: 'planos_pagamentos', action: 'update' },
      },
      {
        path: 'perfis',
        name: 'profiles-list',
        component: ProfilesListView,
        meta: { resource: 'perfis', action: 'read' },
      },
      {
        path: 'perfis/novo',
        name: 'profiles-create',
        component: ProfilesFormView,
        meta: { resource: 'perfis', action: 'create' },
      },
      {
        path: 'perfis/:id/editar',
        name: 'profiles-edit',
        component: ProfilesFormView,
        meta: { resource: 'perfis', action: 'update' },
      },
      {
        path: 'ufs',
        name: 'ufs-list',
        component: UfsListView,
        meta: { resource: 'localidades_ufs', action: 'read' },
      },
      {
        path: 'ufs/novo',
        name: 'ufs-create',
        component: UfsFormView,
        meta: { resource: 'localidades_ufs', action: 'create' },
      },
      {
        path: 'ufs/:id/editar',
        name: 'ufs-edit',
        component: UfsFormView,
        meta: { resource: 'localidades_ufs', action: 'update' },
      },
      {
        path: 'cidades',
        name: 'cities-list',
        component: CidadesListView,
        meta: { resource: 'localidades_cidades', action: 'read' },
      },
      {
        path: 'cidades/novo',
        name: 'cities-create',
        component: CidadesFormView,
        meta: { resource: 'localidades_cidades', action: 'create' },
      },
      {
        path: 'cidades/:id/editar',
        name: 'cities-edit',
        component: CidadesFormView,
        meta: { resource: 'localidades_cidades', action: 'update' },
      },
      {
        path: 'bairros',
        name: 'bairros-list',
        component: BairrosListView,
        meta: { resource: 'localidades_bairros', action: 'read' },
      },
      {
        path: 'bairros/novo',
        name: 'bairros-create',
        component: BairrosFormView,
        meta: { resource: 'localidades_bairros', action: 'create' },
      },
      {
        path: 'bairros/:id/editar',
        name: 'bairros-edit',
        component: BairrosFormView,
        meta: { resource: 'localidades_bairros', action: 'update' },
      },
      {
        path: 'feriados',
        name: 'feriados-list',
        component: FeriadosListView,
        meta: { resource: 'localidades_feriados', action: 'read' },
      },
      {
        path: 'feriados/novo',
        name: 'feriados-create',
        component: FeriadosFormView,
        meta: { resource: 'localidades_feriados', action: 'create' },
      },
      {
        path: 'feriados/:id/editar',
        name: 'feriados-edit',
        component: FeriadosFormView,
        meta: { resource: 'localidades_feriados', action: 'update' },
      },
      {
        path: 'modulos/:group/:slug',
        name: 'module-placeholder',
        component: ModulePlaceholderView,
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthController()
  await auth.initializeAuth()

  if (to.meta.requiresAuth && !auth.isAuthenticated.value) {
    return { name: 'login' }
  }

  if (to.meta.guestOnly && auth.isAuthenticated.value) {
    return { name: 'dashboard' }
  }

  const resource = typeof to.meta.resource === 'string' ? to.meta.resource : undefined
  const action = typeof to.meta.action === 'string' ? to.meta.action : 'read'
  if (resource && !auth.hasPermission(resource, action as 'create' | 'read' | 'update' | 'delete')) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
