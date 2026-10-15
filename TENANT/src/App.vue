<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import ProvisionCreate from './ProvisionCreate.vue'

const base = (import.meta.env.VITE_API_BASE_URL || '/api/platform').replace(/\/$/, '')
const token = ref(sessionStorage.getItem('tenant-session') || '')
const user = ref(null)
const page = ref('tenants')
const tenants = ref([])
const users = ref([])
const search = ref('')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const notice = ref('')
const modalError = ref('')
const modal = ref(null)
const dialog = ref(null)
const form = ref({})
const login = ref({ login: '', senha: '' })
const ready = ref(false)
const provisionOpen = ref(false)
const jobs = ref([])
const retrying = ref(null)
let pollTimer
const stepLabels = { queued: 'Aguardando início', dns: 'Validando domínio', database: 'Preparando banco e cadastros', nginx: 'Configurando o site', certificate: 'Emitindo certificado HTTPS', verification: 'Testando o site e o login', ready: 'Pronto para usar' }
function tenantJob(id) { return jobs.value.find(job => job.tenant_id === id) }
async function loadJobs() { jobs.value = await api('/provision/jobs') }
async function pollJobs() {
  if (user.value && !loading.value) {
    try {
      const previous = JSON.stringify(jobs.value)
      await loadJobs()
      if (previous !== JSON.stringify(jobs.value)) tenants.value = await api('/tenants')
    } catch (e) { error.value = e.message }
  }
  pollTimer = window.setTimeout(pollJobs, 5000)
}
onUnmounted(() => window.clearTimeout(pollTimer))
async function createdTenant() {
  provisionOpen.value = false
  notice.value = 'Criação iniciada. Acompanhe as etapas abaixo.'
  await load()
}
function manualTenant() { provisionOpen.value = false; openModal('tenant') }
async function retryJob(job) {
  retrying.value = job.id; error.value = ''
  try { await api(`/provision/jobs/${job.id}/retry`, { method: 'POST' }); await loadJobs() }
  catch (e) { error.value = e.message }
  finally { retrying.value = null }
}
let focusOrigin

function resetSession() {
  token.value = ''; user.value = null; tenants.value = []; users.value = []; jobs.value = []; provisionOpen.value = false
  sessionStorage.removeItem('tenant-session')
  closeModal()
}
async function api(path, options = {}) {
  const response = await fetch(`${base}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(token.value ? { Authorization: `Bearer ${token.value}` } : {}) },
  })
  if (response.status === 204) return null
  let result
  try { result = await response.json() } catch { throw new Error('Não foi possível acessar a API. Verifique se ela está em execução.') }
  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') resetSession()
    const detail = Array.isArray(result.detail)
      ? result.detail.map(item => `${item.loc.slice(1).join('.')}: ${item.msg}`).join('; ')
      : result.detail
    throw new Error(detail || 'Não foi possível concluir a operação')
  }
  return result
}
async function load() {
  loading.value = true; error.value = ''
  try {
    const [tenantRows, userRows] = await Promise.all([api('/tenants'), api('/usuarios')])
    tenants.value = tenantRows; users.value = userRows
    await loadJobs()
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}
async function signIn() {
  saving.value = true; error.value = ''; notice.value = ''
  try {
    const result = await api('/auth/login', { method: 'POST', body: JSON.stringify(login.value) })
    token.value = result.access_token; user.value = result.user
    sessionStorage.setItem('tenant-session', token.value)
    login.value.senha = ''
    await load()
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}
async function signOut() {
  try { await api('/auth/logout', { method: 'POST' }); resetSession() }
  catch (e) { error.value = e.message }
}
onMounted(async () => {
  if (token.value) {
    try { user.value = await api('/auth/me'); await load() }
    catch (e) { resetSession(); error.value = e.message }
  }
  ready.value = true
  pollTimer = window.setTimeout(pollJobs, 5000)
})
const filtered = computed(() => {
  const query = search.value.toLocaleLowerCase('pt-BR')
  return page.value === 'tenants'
    ? tenants.value.filter(row => `${row.code} ${row.domains.join(' ')}`.toLowerCase().includes(query))
    : users.value.filter(row => `${row.nome} ${row.login}`.toLowerCase().includes(query))
})
const activeCount = computed(() => tenants.value.filter(row => row.active).length)
function changePage(value) { page.value = value; search.value = ''; notice.value = '' }
async function openModal(kind, row) {
  focusOrigin = document.activeElement
  modal.value = kind; modalError.value = ''; notice.value = ''
  form.value = kind === 'tenant'
    ? row ? { ...row, domainsText: row.domains.join('\n') } : { code: '', domainsText: '', public_base_url: '', database_url_env: '', webhook_secret_env: '', active: true, automations_enabled: false, whatsapp_enabled: false }
    : row ? { ...row, senha: '' } : { nome: '', login: '', senha: '', ativo: true }
  await nextTick(); dialog.value.showModal()
}
function closeModal() {
  dialog.value?.close(); modal.value = null
  focusOrigin?.focus?.()
}
function suggest() {
  const code = form.value.code.trim().toLowerCase()
  form.value.code = code
  if (!form.value.database_url_env) form.value.database_url_env = `TENANT_${code.toUpperCase().replaceAll('-', '_')}_DATABASE_URL`
  if (!form.value.webhook_secret_env) form.value.webhook_secret_env = `TENANT_${code.toUpperCase().replaceAll('-', '_')}_WEBHOOK_SECRET`
}
function suggestUrl() {
  if (!form.value.public_base_url && form.value.domainsText.trim()) form.value.public_base_url = `https://${form.value.domainsText.trim().split(/\s+/)[0]}`
}
async function save() {
  saving.value = true; modalError.value = ''
  const editing = Boolean(form.value.id)
  const ownPassword = modal.value === 'user' && form.value.id === user.value.id && form.value.senha
  try {
    let payload; let endpoint
    if (modal.value === 'tenant') {
      const { id, domainsText, domains, ...values } = form.value
      payload = { ...values, domains: domainsText.trim().split(/[\s,;]+/).filter(Boolean) }
      endpoint = '/tenants' + (editing ? `/${encodeURIComponent(id)}` : '')
    } else {
      const { id, ...values } = form.value
      payload = { ...values, senha: values.senha || undefined }
      endpoint = '/usuarios' + (editing ? `/${id}` : '')
    }
    const result = await api(endpoint, { method: editing ? 'PUT' : 'POST', body: JSON.stringify(payload) })
    if (modal.value === 'user' && result.id === user.value.id) user.value = result
    closeModal()
    if (ownPassword) {
      resetSession(); notice.value = 'Senha alterada. Entre novamente com a nova senha.'
    } else {
      notice.value = editing ? 'Cadastro atualizado com sucesso.' : 'Cadastro criado com sucesso.'
      await load()
    }
  } catch (e) { modalError.value = e.message; if (!user.value) error.value = e.message }
  finally { saving.value = false }
}
</script>

<template>
  <div v-if="!ready" class="startup" role="status">Carregando Tenant…</div>
  <main v-else-if="!user" class="login-layout">
    <section class="login-intro">
      <div class="brand"><span class="brand-icon">T</span> Tenant<span class="brand-dot">.</span></div>
      <div class="intro-copy"><span class="eyebrow">ADMINISTRAÇÃO DA PLATAFORMA</span><h1>Cada empresa.<br>Um único lugar.</h1><p>Organize os tenants e gerencie os acessos da sua operação.</p><div class="intro-lines"><span>01 <b>Empresas e domínios</b></span><span>02 <b>Controle de acesso</b></span><span>03 <b>Gestão de serviços</b></span></div></div>
      <span class="intro-footer">TENANT / CENTRAL ADMINISTRATIVA</span>
    </section>
    <section class="login-panel"><form class="login-form" @submit.prevent="signIn"><span class="eyebrow">BEM-VINDO</span><h2>Acesse sua central</h2><p class="muted">Use seu acesso administrativo para continuar.</p><div v-if="error" class="alert error" role="alert">{{ error }}</div><div v-if="notice" class="alert success" role="status">{{ notice }}</div><label>Usuário<input v-model="login.login" required maxlength="64" autocomplete="username" placeholder="Seu usuário" autofocus /></label><label>Senha<input v-model="login.senha" type="password" required maxlength="128" autocomplete="current-password" placeholder="Sua senha" /></label><button class="primary login-submit" :disabled="saving">{{ saving ? 'Entrando…' : 'Entrar na plataforma →' }}</button><p class="login-note">Acesso exclusivo à administração dos tenants.</p></form></section>
  </main>
  <div v-else class="app-shell">
    <aside class="sidebar"><div class="brand"><span class="brand-icon">T</span> Tenant<span class="brand-dot">.</span></div><p class="nav-caption">WORKSPACE</p><nav aria-label="Principal"><button :class="{ selected: page === 'tenants' }" @click="changePage('tenants')"><span aria-hidden="true">▦</span> Tenants <span class="nav-count">{{ tenants.length }}</span></button><button :class="{ selected: page === 'users' }" @click="changePage('users')"><span aria-hidden="true">♙</span> Usuários</button></nav><div class="sidebar-bottom"><span class="status-dot"></span> Administração da plataforma</div></aside>
    <div class="workspace"><header class="topbar"><span>Plataforma <span class="breadcrumb">/ {{ page === 'tenants' ? 'Tenants' : 'Usuários' }}</span></span><div class="account"><button class="account-button" title="Editar meu usuário e senha" @click="openModal('user', user)"><span class="avatar">{{ user.nome.slice(0, 1) }}</span><span>{{ user.nome }}<small>{{ user.login }}</small></span></button><button class="text-button" @click="signOut">Sair ↗</button></div></header>
      <main class="content"><div class="page-heading"><div><span class="eyebrow">{{ page === 'tenants' ? 'GESTÃO DE EMPRESAS' : 'CONTROLE DE ACESSO' }}</span><h1>{{ page === 'tenants' ? 'Seus tenants' : 'Usuários da plataforma' }}</h1><p class="muted">{{ page === 'tenants' ? 'Gerencie as empresas, seus domínios e serviços.' : 'Gerencie quem pode administrar os tenants da sua operação.' }}</p></div><button class="primary" :disabled="loading" @click="page === 'tenants' ? provisionOpen = true : openModal('user')">＋ {{ page === 'tenants' ? 'Novo tenant' : 'Novo usuário' }}</button></div>
        <div v-if="error" class="alert error" role="alert">{{ error }}</div><div v-if="notice" class="alert success" role="status">{{ notice }}</div>
        <section v-if="page === 'tenants' && jobs.length" class="provision-jobs" aria-label="Andamento das criações">
          <article v-for="job in jobs" :key="job.id" class="provision-job" :class="job.state">
            <div><strong>{{ job.tenant_id }}</strong><span class="job-step">{{ stepLabels[job.step] || job.step }}</span><p v-if="job.state === 'failed'" role="alert">{{ job.error }}</p><small v-else-if="job.state !== 'ready'">{{ job.state === 'queued' ? 'Aguardando o serviço do Ubuntu.' : 'Criação em andamento. Você pode continuar usando o painel.' }}</small><small v-else>Usuário inicial: Admin · senha inicial: Admin</small></div>
            <button v-if="job.state === 'failed'" class="secondary" :disabled="retrying === job.id" @click="retryJob(job)">{{ retrying === job.id ? 'Retomando…' : 'Retomar criação' }}</button>
            <a v-if="job.state === 'ready'" class="site-link" :href="tenants.find(row => row.id === job.tenant_id)?.public_base_url" target="_blank" rel="noopener noreferrer">Abrir site ↗</a>
          </article>
        </section>
        <section v-if="page === 'tenants'" class="stats" aria-label="Resumo"><article><span>Total de tenants</span><strong>{{ tenants.length.toString().padStart(2, '0') }}</strong><small>Empresas cadastradas</small></article><article><span><i class="status-dot"></i> Tenants ativos</span><strong>{{ activeCount.toString().padStart(2, '0') }}</strong><small>Acesso habilitado</small></article><article><span>Tenants inativos</span><strong>{{ (tenants.length - activeCount).toString().padStart(2, '0') }}</strong><small>Acesso suspenso</small></article></section>
        <section class="list-card"><div class="list-toolbar"><div><h2>{{ page === 'tenants' ? 'Empresas cadastradas' : 'Acessos administrativos' }}</h2><span class="muted">{{ filtered.length }} {{ filtered.length === 1 ? 'registro' : 'registros' }}</span></div><div class="search-actions"><input v-model="search" type="search" :aria-label="page === 'tenants' ? 'Buscar tenant ou domínio' : 'Buscar nome ou login'" :placeholder="page === 'tenants' ? 'Buscar tenant ou domínio…' : 'Buscar nome ou login…'" /><button class="secondary" :disabled="loading" @click="load">Atualizar</button></div></div>
          <div v-if="loading" class="empty" role="status">Carregando registros…</div>
          <div v-else-if="!filtered.length" class="empty"><span class="empty-symbol">{{ search ? '⌕' : '＋' }}</span><h3>{{ search ? 'Nenhum resultado encontrado' : page === 'tenants' ? 'Seu primeiro tenant começa aqui' : 'Nenhum usuário encontrado' }}</h3><p>{{ search ? 'Tente buscar por outro termo.' : 'Use o botão acima para adicionar um cadastro.' }}</p></div>
          <div v-else class="table-scroll"><table><thead><tr v-if="page === 'tenants'"><th>Tenant / domínio</th><th>Status</th><th>Serviços</th><th class="align-right">Ações</th></tr><tr v-else><th>Usuário</th><th>Login</th><th>Status</th><th class="align-right">Ações</th></tr></thead><tbody><tr v-for="row in filtered" :key="row.id"><template v-if="page === 'tenants'"><td><div class="tenant-cell"><span class="tenant-avatar">{{ row.code.slice(0, 2).toUpperCase() }}</span><div><strong>{{ row.code }}</strong><small v-for="domain in row.domains" :key="domain">{{ domain }}</small></div></div></td><td><span class="badge" :class="row.active ? 'active' : 'inactive'">{{ row.active ? 'Ativo' : 'Inativo' }}</span></td><td><div class="services"><span :class="{ enabled: row.automations_enabled }">Automações {{ row.automations_enabled ? '✓' : '—' }}</span><span :class="{ enabled: row.whatsapp_enabled }">WhatsApp {{ row.whatsapp_enabled ? '✓' : '—' }}</span></div></td></template><template v-else><td><strong>{{ row.nome }}</strong><small v-if="row.id === user.id">Seu usuário</small></td><td>{{ row.login }}</td><td><span class="badge" :class="row.ativo ? 'active' : 'inactive'">{{ row.ativo ? 'Ativo' : 'Inativo' }}</span></td></template><td class="align-right"><button class="edit-button" :disabled="page === 'tenants' && !!tenantJob(row.id) && tenantJob(row.id).state !== 'ready'" :aria-label="`Editar ${row.code || row.nome}`" @click="openModal(page === 'tenants' ? 'tenant' : 'user', row)">Editar ↗</button></td></tr></tbody></table></div>
        </section><footer class="page-footer"><span>Tenant</span> Central de administração</footer>
      </main>
    </div>
  </div>
  <ProvisionCreate v-if="provisionOpen && user" :api="api" @close="provisionOpen = false" @saved="createdTenant" @manual="manualTenant" />
  <dialog ref="dialog" class="editor-dialog" aria-labelledby="dialog-title" @cancel.prevent="!saving && closeModal()">
    <form v-if="modal" @submit.prevent="save"><div class="dialog-heading"><div><span class="eyebrow">{{ modal === 'tenant' ? 'EMPRESA' : 'ACESSO ADMINISTRATIVO' }}</span><h2 id="dialog-title">{{ form.id ? 'Editar' : 'Novo' }} {{ modal === 'tenant' ? 'tenant' : 'usuário' }}</h2></div><button type="button" class="close-button" aria-label="Fechar" :disabled="saving" @click="closeModal">×</button></div><div class="dialog-body"><div v-if="modalError" class="alert error" role="alert">{{ modalError }}</div>
      <template v-if="modal === 'tenant'"><div class="form-grid"><label>Código da empresa<input v-model="form.code" required pattern="[a-z][a-z0-9_-]{0,62}" maxlength="63" :disabled="!!form.id" placeholder="Ex.: cv" @blur="suggest" /></label><label>URL pública<input v-model="form.public_base_url" required type="url" maxlength="255" placeholder="https://cvfinanceiro.vstec.net" /></label></div><label>Domínios<textarea v-model="form.domainsText" required rows="3" placeholder="cvfinanceiro.vstec.net" @blur="suggestUrl"></textarea><small>Um domínio por linha, sem https:// e sem caminhos.</small></label><div class="form-grid"><label>Variável de conexão do banco<input v-model="form.database_url_env" required pattern="TENANT_[A-Z0-9_]+" maxlength="128" :disabled="!!form.id" placeholder="TENANT_CV_DATABASE_URL" /></label><label>Variável do segredo de webhook<input v-model="form.webhook_secret_env" required pattern="TENANT_[A-Z0-9_]+" maxlength="128" placeholder="TENANT_CV_WEBHOOK_SECRET" /></label></div><p class="field-note">Informe os nomes das variáveis já configuradas no servidor. O banco da empresa deve existir antes do cadastro.</p><div class="toggle-list"><label><input v-model="form.active" type="checkbox" /><span>Tenant ativo<small>Permitir acesso da empresa ao sistema</small></span></label><label><input v-model="form.automations_enabled" type="checkbox" /><span>Automações<small>Executar rotinas automáticas desta empresa</small></span></label><label><input v-model="form.whatsapp_enabled" type="checkbox" /><span>WhatsApp<small>Habilitar a integração da empresa</small></span></label></div></template>
      <template v-else><label>Nome<input v-model="form.nome" required maxlength="120" autocomplete="name" /></label><label>Login<input v-model="form.login" required maxlength="64" :disabled="!!form.id" autocomplete="off" /></label><label>{{ form.id ? 'Nova senha (opcional)' : 'Senha' }}<input v-model="form.senha" type="password" :required="!form.id" maxlength="128" autocomplete="new-password" /><small v-if="form.id">Deixe em branco para manter a senha atual. Alterar a senha encerra as sessões desse usuário.</small></label><label class="checkbox-label"><input v-model="form.ativo" type="checkbox" :disabled="form.id === user?.id" /> Usuário ativo</label><p class="field-note">Usuários deste painel podem administrar todos os tenants e os acessos da plataforma.</p></template>
    </div><div class="dialog-footer"><button type="button" class="secondary" :disabled="saving" @click="closeModal">Cancelar</button><button class="primary" :disabled="saving">{{ saving ? 'Salvando…' : 'Salvar cadastro' }}</button></div></form>
  </dialog>
</template>

<style scoped>
.provision-jobs{display:grid;gap:10px;margin-bottom:24px}.provision-job{display:flex;justify-content:space-between;align-items:center;gap:20px;background:#fff;border:1px solid #dce5e0;border-left:4px solid #6b8da8;border-radius:9px;padding:17px 20px;font-size:13px}.provision-job.ready{border-left-color:#43835c}.provision-job.failed{border-left-color:#b75e44}.job-step{margin-left:15px;color:#5d7567}.provision-job small{margin-top:5px}.provision-job p{margin:8px 0;color:#a14432}.site-link{font-weight:600;color:#226a4d;white-space:nowrap}.provision-job.failed{background:#fffaf7}@media(max-width:600px){.provision-job{align-items:flex-start;flex-direction:column}.job-step{display:block;margin:7px 0}}
</style>
