<script setup>
import { onMounted, ref } from 'vue'
const props = defineProps({ api: { type: Function, required: true } })
const data = ref(null)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const notice = ref('')
const tokenAction = ref('keep')
const newToken = ref('')
const scoreFields = {
  score_valor_inicial: 'Score inicial', score_pontos_atraso_parcela: 'Pontos por atraso de parcela',
  score_pontos_atraso_quitacao_contrato: 'Pontos por quitação em atraso', score_pontos_pagamento_em_dia: 'Pontos por pagamento em dia',
  score_pontos_quitacao_em_dia: 'Pontos por quitação em dia', score_pontos_negociacao: 'Pontos por negociação',
}
const messages = { msg_renovacao: 'Mensagem de renovação', msg_negociacao: 'Mensagem de negociação', msg_campanha: 'Mensagem de campanha' }
const actions = { read: 'Consultar', create: 'Criar', update: 'Editar', delete: 'Excluir' }
const ruleValues = ref([])
function accept(result) {
  data.value = result
  ruleValues.value = result.parameters.regra_nono_dig_whats.map(r => JSON.stringify(r.valor))
  tokenAction.value = 'keep'; newToken.value = ''
}
async function load() {
  loading.value = true; error.value = ''; notice.value = ''
  try { accept(await props.api('/provision/config')) }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}
onMounted(load)
async function save() {
  saving.value = true; error.value = ''; notice.value = ''
  try {
    const parameters = { ...data.value.parameters,
      token_api_whatsapp: tokenAction.value === 'keep' ? null : tokenAction.value === 'clear' ? '' : newToken.value,
      regra_nono_dig_whats: data.value.parameters.regra_nono_dig_whats.map((r, i) => {
        try { return { ...r, valor: JSON.parse(ruleValues.value[i]) } }
        catch { throw new Error(`Valor da regra ${i + 1} inválido. Use um número, texto entre aspas ou lista.`) }
      }),
    }
    accept(await props.api('/provision/config', { method: 'PUT', body: JSON.stringify({
      version: data.value.version, parameters, profiles: data.value.profiles, apis: data.value.apis,
    }) }))
    notice.value = 'Configuração salva. Os próximos tenants usarão estes padrões.'
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}
function permission(profile, resource) {
  return profile.permissions.find(p => p.resource_key === resource.key)
}
function setPermission(profile, resource, action, checked) {
  let row = permission(profile, resource)
  if (!row) {
    row = { resource_key: resource.key, resource_label: resource.label, can_read: false, can_create: false, can_update: false, can_delete: false }
    profile.permissions.push(row)
  }
  row[`can_${action}`] = checked
}
function addRule() {
  data.value.parameters.regra_nono_dig_whats.push({ campo: '', operador: '', valor: '' })
  ruleValues.value.push('""')
}
</script>

<template>
  <div class="page-heading"><div><span class="eyebrow">NOVAS EMPRESAS</span><h1>Configuração inicial</h1><p class="muted">Defina os dados que serão carregados ao criar um tenant.</p></div><button class="secondary" :disabled="saving || loading" @click="load">Recarregar</button></div>
  <p v-if="loading" role="status">Carregando configuração…</p>
  <div v-if="error" class="alert error" role="alert">{{ error }}</div>
  <div v-if="notice" class="alert success" role="status">{{ notice }}</div>
  <form v-if="data && !loading" @submit.prevent="save">
    <p class="field-note">As alterações valem para novas criações. Empresas existentes e criações em andamento mantêm seus dados. Versão {{ data.version }} · {{ data.updated_by ? `Alterada por ${data.updated_by}` : 'Carga inicial' }} · {{ new Date(data.updated_at * 1000).toLocaleString('pt-BR') }}</p>
    <fieldset :disabled="saving">
      <section class="config-card"><h2>Empresa</h2><div class="form-grid"><label>Nome fantasia<input v-model="data.parameters.nome_fantasia" required maxlength="150" /></label><label>Razão social<input v-model="data.parameters.razao_social" required maxlength="150" /></label></div><small>Esses nomes podem ser ajustados no cadastro de cada novo tenant. O acesso inicial continua sendo Admin / Admin.</small></section>
      <section class="config-card"><h2>Score</h2><div class="form-grid"><label v-for="(label, key) in scoreFields" :key="key">{{ label }}<input v-model.number="data.parameters[key]" required type="number" min="-2147483648" max="2147483647" step="1" /></label></div></section>
      <section class="config-card"><h2>Cobrança</h2><div class="form-grid"><label>Dias antes do vencimento<input v-model.number="data.parameters.whatsapp_cobranca_dias_antes" required type="number" min="0" max="365" /></label><label>Dias depois do vencimento<input v-model.number="data.parameters.whatsapp_cobranca_dias_depois" required type="number" min="0" max="365" /></label></div><label>Modelo de cobrança<textarea v-model="data.parameters.whatsapp_cobranca_modelo" maxlength="500" rows="3"></textarea></label><small>Agendamentos e cobranças automáticas começam desativados.</small></section>
      <section class="config-card"><h2>WhatsApp · Quepasa</h2><label>Usuário da API<input v-model="data.parameters.usuario_api_whatsapp" maxlength="100" /></label>
        <label>Token<select v-model="tokenAction"><option value="keep">Manter token {{ data.has_token ? 'configurado' : '(não configurado)' }}</option><option value="replace">Substituir token</option><option value="clear">Remover token</option></select></label>
        <label v-if="tokenAction === 'replace'">Novo token<input v-model="newToken" type="password" required maxlength="120" autocomplete="new-password" /></label>
        <div class="form-grid"><label>Sufixo<input v-model="data.parameters.sufixo_whatsapp" required maxlength="30" /></label><label>Código do país<input v-model.number="data.parameters.pais_whatsapp" required type="number" min="1" max="999" /></label></div>
        <label v-for="(label, key) in messages" :key="key">{{ label }}<textarea v-model="data.parameters[key]" maxlength="10000" rows="3"></textarea></label>
        <h3>Regras do nono dígito</h3><div v-for="(rule, i) in data.parameters.regra_nono_dig_whats" :key="i" class="nested-card"><div class="form-grid"><label>Campo<input v-model="rule.campo" required /></label><label>Operador<input v-model="rule.operador" required /></label></div><label>Valor<input v-model="ruleValues[i]" required /><small>Número, texto entre aspas ou lista. Ex.: 55, "9" ou [11, 12].</small></label><button class="secondary" type="button" @click="data.parameters.regra_nono_dig_whats.splice(i, 1); ruleValues.splice(i, 1)">Remover regra</button></div><button class="secondary" type="button" @click="addRule">Adicionar regra</button>
      </section>
      <section class="config-card"><h2>Perfis e permissões</h2><p class="muted">O perfil Administrador sempre recebe acesso completo ao criar a empresa.</p>
        <details v-for="(profile, i) in data.profiles" :key="i" class="nested-card"><summary>{{ profile.nome || 'Novo perfil' }}</summary><label>Nome<input v-model="profile.nome" required maxlength="80" :disabled="profile.nome === 'Administrador'" /></label><label>Descrição<input v-model="profile.descricao" maxlength="255" /></label><label class="checkbox-label"><input v-model="profile.ativo" type="checkbox" :disabled="profile.nome === 'Administrador'" /> Ativo</label>
          <div v-if="profile.nome !== 'Administrador'" class="table-scroll"><table><thead><tr><th>Recurso</th><th v-for="label in actions" :key="label">{{ label }}</th></tr></thead><tbody><tr v-for="resource in data.resources" :key="resource.key"><td>{{ resource.label }}</td><td v-for="(label, action) in actions" :key="action"><input type="checkbox" :aria-label="`${label}: ${resource.label}`" :disabled="!resource.actions.includes(action)" :checked="!!permission(profile, resource)?.[`can_${action}`]" @change="setPermission(profile, resource, action, $event.target.checked)" /></td></tr></tbody></table></div><button v-if="profile.nome !== 'Administrador'" class="secondary" type="button" @click="data.profiles.splice(i, 1)">Remover perfil</button>
        </details><button class="secondary" type="button" @click="data.profiles.push({ nome: '', descricao: '', ativo: true, permissions: [] })">Adicionar perfil</button>
      </section>
      <section class="config-card"><h2>Cadastros de APIs</h2><p class="muted">Cada API será vinculada ao administrador da nova empresa.</p>
        <details v-for="(api, i) in data.apis" :key="i" class="nested-card"><summary>{{ api.nome_api || 'Nova API' }}</summary><div class="form-grid"><label>Nome<input v-model="api.nome_api" maxlength="120" /></label><label>Funcionalidade<input v-model="api.funcionalidade" maxlength="200" /></label></div><label>URL<input v-model="api.url" maxlength="255" /></label><div v-for="n in 5" :key="n" class="form-grid"><label>Chave {{ n }}<input v-model="api[`key${n}`]" maxlength="100" /></label><label>Valor {{ n }}<input v-model="api[`value${n}`]" type="password" maxlength="255" autocomplete="new-password" /></label></div><label>Corpo da requisição<textarea v-model="api.body" rows="5" maxlength="100000"></textarea></label><button class="secondary" type="button" @click="data.apis.splice(i, 1)">Remover API</button></details>
        <button class="secondary" type="button" @click="data.apis.push({ nome_api: '', funcionalidade: '', url: '', body: '' })">Adicionar API</button>
      </section>
      <div class="config-actions"><button class="primary" :disabled="saving">{{ saving ? 'Salvando…' : 'Salvar configuração inicial' }}</button></div>
    </fieldset>
  </form>
</template>

<style scoped>
fieldset{border:0;margin:0;padding:0;min-width:0}.config-card{background:white;border:1px solid var(--border);border-radius:12px;padding:24px;margin-bottom:20px}.nested-card{border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px}summary{cursor:pointer;font-size:14px;font-weight:600;padding:4px 0 14px}select{display:block;width:100%;padding:12px;margin-top:8px;border:1px solid var(--border);border-radius:7px;background:white;color:inherit}.config-actions{display:flex;justify-content:flex-end;margin:24px 0}h3{font-size:14px}td,th{padding:10px}table{font-size:12px}.table-scroll{margin-bottom:15px}
</style>
