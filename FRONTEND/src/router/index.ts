import { createRouter, createWebHistory } from 'vue-router'

import { useAuthController } from '@/controllers/useAuthController'
import MainLayout from '@/components/layout/MainLayout.vue'
import AccountsPayableFormView from '@/views/accounts-payable/AccountsPayableFormView.vue'
import AccountsPayableListView from '@/views/accounts-payable/AccountsPayableListView.vue'
import ClientsCreateView from '@/views/clients/ClientsCreateView.vue'
import ClientsEditView from '@/views/clients/ClientsEditView.vue'
import ClientsListView from '@/views/clients/ClientsListView.vue'
import ApiConfigsFormView from '@/views/apis/ApiConfigsFormView.vue'
import ApiConfigsListView from '@/views/apis/ApiConfigsListView.vue'
import AccountsReceivableListView from '@/views/accounts-receivable/AccountsReceivableListView.vue'
import BrandsFormView from '@/views/brands/BrandsFormView.vue'
import BrandsListView from '@/views/brands/BrandsListView.vue'
import ContractsCreateView from '@/views/contracts/ContractsCreateView.vue'
import ContractsEditView from '@/views/contracts/ContractsEditView.vue'
import ContractsListView from '@/views/contracts/ContractsListView.vue'
import BatchReceiptView from '@/views/contracts/BatchReceiptView.vue'
import DashboardHomeView from '@/views/dashboard/DashboardHomeView.vue'
import LoginView from '@/views/auth/LoginView.vue'
import NegotiationsCreateView from '@/views/negotiations/NegotiationsCreateView.vue'
import NegotiationsListView from '@/views/negotiations/NegotiationsListView.vue'
import NegotiationsViewView from '@/views/negotiations/NegotiationsViewView.vue'
import PaymentPlansFormView from '@/views/payment-plans/PaymentPlansFormView.vue'
import PaymentPlansListView from '@/views/payment-plans/PaymentPlansListView.vue'
import ParametersView from '@/views/parameters/ParametersView.vue'
import ProductsFormView from '@/views/products/ProductsFormView.vue'
import ProductsListView from '@/views/products/ProductsListView.vue'
import ModulePlaceholderView from '@/views/shared/ModulePlaceholderView.vue'
import CommissionsView from '@/views/commissions/CommissionsView.vue'
import CommissionProcessView from '@/views/commissions/CommissionProcessView.vue'
import ProfilesFormView from '@/views/access-control/ProfilesFormView.vue'
import ProfilesListView from '@/views/access-control/ProfilesListView.vue'
import SolicitationsListView from '@/views/solicitations/SolicitationsListView.vue'
import SuppliersFormView from '@/views/suppliers/SuppliersFormView.vue'
import SuppliersListView from '@/views/suppliers/SuppliersListView.vue'
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
import WhatsAppConnectionView from '@/views/whatsapp/WhatsAppConnectionView.vue'
import WhatsAppDispatchesView from '@/views/whatsapp/WhatsAppDispatchesView.vue'

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
        path: 'apis',
        name: 'api-configs-list',
        component: ApiConfigsListView,
        meta: { resource: 'apis', action: 'read' },
      },
      {
        path: 'apis/novo',
        name: 'api-configs-create',
        component: ApiConfigsFormView,
        meta: { resource: 'apis', action: 'create' },
      },
      {
        path: 'apis/:id/editar',
        name: 'api-configs-edit',
        component: ApiConfigsFormView,
        meta: { resource: 'apis', action: 'update' },
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
        path: 'marcas',
        name: 'brands-list',
        component: BrandsListView,
        meta: { resource: 'marcas', action: 'read' },
      },
      {
        path: 'marcas/novo',
        name: 'brands-create',
        component: BrandsFormView,
        meta: { resource: 'marcas', action: 'create' },
      },
      {
        path: 'marcas/:id/editar',
        name: 'brands-edit',
        component: BrandsFormView,
        meta: { resource: 'marcas', action: 'update' },
      },
      {
        path: 'produtos',
        name: 'products-list',
        component: ProductsListView,
        meta: { resource: 'produtos', action: 'read' },
      },
      {
        path: 'produtos/novo',
        name: 'products-create',
        component: ProductsFormView,
        meta: { resource: 'produtos', action: 'create' },
      },
      {
        path: 'produtos/:id/editar',
        name: 'products-edit',
        component: ProductsFormView,
        meta: { resource: 'produtos', action: 'update' },
      },
      {
        path: 'clientes',
        name: 'clients-list',
        component: ClientsListView,
        meta: { resource: 'clientes', action: 'read' },
      },
      {
        path: 'clientes/novo',
        name: 'clients-create',
        component: ClientsCreateView,
        meta: { resource: 'clientes', action: 'create' },
      },
      {
        path: 'clientes/:id/editar',
        name: 'clients-edit',
        component: ClientsEditView,
        meta: { resource: 'clientes', action: 'update' },
      },
      {
        path: 'fornecedores',
        name: 'suppliers-list',
        component: SuppliersListView,
        meta: { resource: 'fornecedores', action: 'read' },
      },
      {
        path: 'fornecedores/novo',
        name: 'suppliers-create',
        component: SuppliersFormView,
        meta: { resource: 'fornecedores', action: 'create' },
      },
      {
        path: 'fornecedores/:id/editar',
        name: 'suppliers-edit',
        component: SuppliersFormView,
        meta: { resource: 'fornecedores', action: 'update' },
      },
      {
        path: 'contas-receber',
        name: 'accounts-receivable-list',
        component: AccountsReceivableListView,
        meta: { resource: 'contratos', action: 'read' },
      },
      {
        path: 'contas-pagar',
        name: 'accounts-payable-list',
        component: AccountsPayableListView,
        meta: { resource: 'contas_pagar', action: 'read' },
      },
      {
        path: 'contas-pagar/novo',
        name: 'accounts-payable-create',
        component: AccountsPayableFormView,
        meta: { resource: 'contas_pagar', action: 'create' },
      },
      {
        path: 'contas-pagar/:id/editar',
        name: 'accounts-payable-edit',
        component: AccountsPayableFormView,
        meta: { resource: 'contas_pagar', action: 'update' },
      },
      {
        path: 'contratos',
        name: 'contracts-list',
        component: ContractsListView,
        meta: { resource: 'contratos', action: 'read' },
      },
      {
        path: 'contratos/novo',
        name: 'contracts-create',
        component: ContractsCreateView,
        meta: { resource: 'contratos', action: 'create' },
      },
      {
        path: 'contratos/:id/editar',
        name: 'contracts-edit',
        component: ContractsEditView,
        meta: { resource: 'contratos', action: 'update' },
      },
      {
        path: 'recebimento-lote',
        name: 'batch-receipt',
        component: BatchReceiptView,
        meta: { resource: 'contratos', action: 'update' },
      },
      {
        path: 'negociacoes',
        name: 'negotiations-list',
        component: NegotiationsListView,
        meta: { resource: 'contratos', action: 'read' },
      },
      {
        path: 'negociacoes/novo',
        name: 'negotiations-create',
        component: NegotiationsCreateView,
        meta: { resource: 'contratos', action: 'create' },
      },
      {
        path: 'negociacoes/:id',
        name: 'negotiations-view',
        component: NegotiationsViewView,
        meta: { resource: 'contratos', action: 'read' },
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
        path: 'parametros',
        name: 'parameters',
        component: ParametersView,
      },
      {
        path: 'contas-whatsapp',
        name: 'whatsapp-connection',
        component: WhatsAppConnectionView,
      },
      {
        path: 'solicitacoes',
        name: 'solicitations',
        component: SolicitationsListView,
        meta: { resource: 'solicitacoes', action: 'read' },
      },
      {
        path: 'envios-whatsapp',
        name: 'whatsapp-dispatches',
        component: WhatsAppDispatchesView,
      },
      {
        path: 'comissoes/processar', name: 'commissions-process', component: CommissionProcessView, meta: { resource: 'contas_pagar', action: 'create' },
      },
      {
        path: 'comissoes', name: 'commissions', component: CommissionsView, meta: { resource: 'contas_pagar', action: 'read' },
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
