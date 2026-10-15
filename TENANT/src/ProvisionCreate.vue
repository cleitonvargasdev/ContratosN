<script setup>
import { onMounted, ref } from 'vue'

const props = defineProps({ api: { type: Function, required: true } })
const emit = defineEmits(['close', 'saved', 'manual'])
const dialog = ref(null)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const defaults = ref(null)
const code = ref('')
const domain = ref('')
const form = ref({})
const scoreLabels = {
  score_valor_inicial: 'Score inicial', score_pontos_atraso_parcela: 'Atraso de parcela',
  score_pontos_atraso_quitacao_contrato: 'Quitação em atraso', score_pontos_pagamento_em_dia: 'Pagamento em dia',
  score_pontos_quitacao_em_dia: 'Quitação em dia', score_pontos_negociacao: 'Negociação',
}

async function loadDefaults() {
  error.value = ''; loading.value = true
  try {
    defaults.value = await props.api('/provision/defaults')
    form.value = { ...defaults.value.bootstrap, token_api_whatsapp: '' }
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}
onMounted(() => { dialog.value.showModal(); loadDefaults() })
async function save() {
  saving.value = true; error.value = ''
  try {
    const hostname = domain.value.trim().toLowerCase().replace(/\.$/, '')
    await props.api('/tenants', { method: 'POST', body: JSON.stringify({
      code: code.value.trim().toLowerCase(), domains: [hostname], public_base_url: `https://${hostname}`,
      provision: true, bootstrap: { ...form.value, token_api_whatsapp: form.value.usar_token_modelo ? null : form.value.token_api_whatsapp },
    }) })
    emit('saved')
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}
</script>

<template>
  <dialog ref="dialog" class="editor-dialog provision-create" aria-labelledby="provision-title" @cancel.prevent="!saving && emit('close')">
    <form @submit.prevent="save">
      <header class="dialog-heading"><div><span class="eyebrow">NOVA EMPRESA</span><h2 id="provision-title">Criar tenant e publicar site</h2></div><button type="button" class="close-button" :disabled="saving" aria-label="Fechar" @click="emit('close')">×</button></header>
      <div class="dialog-body">
        <div v-if="error" class="alert error" role="alert">{{ error }} <button v-if="!defaults" type="button" class="text-button" @click="loadDefaults">Tentar novamente</button></div>
        <p v-if="loading" role="status">Carregando as configurações atuais…</p>
        <template v-else-if="defaults">
          <p v-if="!defaults.available" class="alert error">O serviço de criação ainda não está disponível. Ative o provisionador no Ubuntu e o modo multitenant antes de criar uma empresa automaticamente.</p>
          <fieldset :disabled="saving"><legend>Empresa e endereço</legend>
            <div class="form-grid"><label>Código<input v-model="code" required pattern="[a-z][a-z0-9_-]{0,62}" maxlength="63" placeholder="Ex.: xyz" /></label><label>Domínio já apontado<input v-model="domain" required maxlength="253" placeholder="xyz.vstec.net" /><small>Sem https://, porta ou caminho.</small></label></div>
            <div class="form-grid"><label>Nome fantasia<input v-model="form.nome_fantasia" required maxlength="150" /></label><label>Razão social<input v-model="form.razao_social" required maxlength="150" /></label></div>
          </fieldset>
          <div class="bootstrap-summary"><strong>Acesso inicial da empresa</strong><p>Login <b>Admin</b> · Senha <b>Admin</b><br>Função e perfil: <b>Administrador</b></p><small>Um banco novo, sem clientes, contratos ou movimentações. Altere a senha depois do primeiro acesso.</small></div>
          <fieldset :disabled="saving"><legend>Parâmetros do WhatsApp</legend>
            <p class="muted">Integração: <strong>quepasa</strong>. Revise as sugestões antes de continuar.</p>
            <label>Usuário da API<input v-model="form.usuario_api_whatsapp" maxlength="100" autocomplete="off" /></label>
            <label class="checkbox-label"><input v-model="form.usar_token_modelo" type="checkbox" /> Usar o token atual da empresa modelo {{ defaults.has_token ? '(configurado)' : '(não configurado)' }}</label>
            <label v-if="!form.usar_token_modelo">Token da API<input v-model="form.token_api_whatsapp" type="password" maxlength="120" autocomplete="new-password" placeholder="Token da conexão desta empresa" /></label>
            <div class="form-grid"><label>Sufixo<input v-model="form.sufixo_whatsapp" required maxlength="30" /></label><label>País<input v-model.number="form.pais_whatsapp" required type="number" min="1" max="999" /></label></div>
            <label>Mensagem de renovação<textarea v-model="form.msg_renovacao" rows="3" maxlength="10000"></textarea></label>
            <label>Mensagem de negociação<textarea v-model="form.msg_negociacao" rows="3" maxlength="10000"></textarea></label>
            <label>Mensagem de campanha<textarea v-model="form.msg_campanha" rows="3" maxlength="10000"></textarea></label>
            <p class="field-note">Usar o mesmo token reaproveita a conexão de WhatsApp do modelo. WhatsApp e automações começam desativados; habilite após conferir a conexão de cada empresa.</p>
          </fieldset>
          <details><summary>Padrões que serão carregados</summary><p>Perfis: {{ defaults.profiles.join(', ') || 'Administrador' }}. {{ defaults.api_count }} cadastros de APIs.</p><dl class="score-defaults"><template v-for="(value, key) in defaults.score" :key="key"><dt>{{ scoreLabels[key] || key }}</dt><dd>{{ value }}</dd></template></dl></details>
          <p class="field-note">O processo valida o domínio, cria o banco, carrega os padrões, configura HTTPS e testa o login. Você acompanha cada etapa no painel e pode retomar em caso de falha.</p>
        </template>
      </div>
      <footer class="dialog-footer"><button type="button" class="text-button" :disabled="saving" @click="emit('manual')">Vincular banco existente</button><button type="button" class="secondary" :disabled="saving" @click="emit('close')">Cancelar</button><button class="primary" :disabled="loading || saving || !defaults?.available">{{ saving ? 'Enviando…' : 'Criar e publicar' }}</button></footer>
    </form>
  </dialog>
</template>

<style scoped>
.provision-create{width:min(760px,calc(100% - 32px))}fieldset{border:0;padding:0;margin:0 0 20px}legend{font-weight:700;font-size:14px;margin-bottom:20px}.bootstrap-summary{background:#f0f6ed;border:1px solid #dbe8d6;border-radius:10px;padding:18px;margin-bottom:26px;font-size:13px}.bootstrap-summary p{line-height:1.8;margin:10px 0}details{font-size:12px;margin:20px 0;color:#536b5b}summary{cursor:pointer;font-weight:600;margin-bottom:16px}.score-defaults{display:grid;grid-template-columns:1fr auto;gap:8px 20px}.score-defaults dd{margin:0;font-weight:700}.dialog-footer{flex-wrap:wrap}.dialog-footer .text-button{margin-right:auto}@media(max-width:500px){.dialog-footer .text-button{width:100%;text-align:left;margin-bottom:10px}}
</style>
