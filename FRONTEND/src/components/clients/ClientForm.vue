<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <p class="eyebrow">Cadastro de clientes</p>
      </div>
    </header>

    <form class="client-form" @submit.prevent="submitForm">
      <div class="client-form__cards">
        <section class="client-card">
          <header class="client-card__header">
            <div>
              <h3 class="panel__title">Cadastro Empresa</h3>
            </div>
            <div class="client-card__status">
              <label class="status-switch" :class="form.ativo ? 'status-switch--on' : 'status-switch--off'">
                <input v-model="form.ativo" class="status-switch__input" type="checkbox" />
                <span class="status-switch__track"><span class="status-switch__thumb"></span></span>
                <span class="status-switch__label">{{ form.ativo ? 'Ativo' : 'Inativo' }}</span>
              </label>
              <label class="status-switch" :class="form.bloqueado ? 'status-switch--off' : 'status-switch--on'">
                <input v-model="form.bloqueado" class="status-switch__input" type="checkbox" />
                <span class="status-switch__track"><span class="status-switch__thumb"></span></span>
                <span class="status-switch__label">{{ form.bloqueado ? 'Bloqueado' : 'Liberado' }}</span>
              </label>
            </div>
          </header>

          <div class="client-card__grid">
            <label class="field-group field-group--span-2">
              <span>Nome</span>
              <input v-model="form.nome" class="field" required type="text" />
            </label>

            <label class="field-group">
              <span>CPF/CNPJ</span>
              <input v-model="form.cpf_cnpj" class="field" type="text" @blur="formatDocumentField('cpf_cnpj')" />
            </label>

            <label class="field-group">
              <span>RG/IE</span>
              <input v-model="form.rg_ie" class="field" type="text" />
            </label>

            <label class="field-group">
              <span>E-mail</span>
              <input v-model="form.email" class="field" type="email" />
            </label>

            <label class="field-group">
              <span>Telefone</span>
              <input v-model="form.telefone" class="field" type="text" @blur="formatPhoneField('telefone')" />
            </label>

            <label class="field-group">
              <span>Celular principal</span>
              <div class="field-inline field-inline--cellphone">
                <label class="whatsapp-toggle" :class="form.flag_whatsapp ? 'whatsapp-toggle--on' : 'whatsapp-toggle--off'" title="WhatsApp" aria-label="WhatsApp">
                  <input v-model="form.flag_whatsapp" class="whatsapp-toggle__input" type="checkbox" />
                  <span class="whatsapp-toggle__icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" focusable="false">
                      <path d="M12 2.2a9.6 9.6 0 0 0-8.29 14.46L2.5 21.5l4.97-1.19A9.6 9.6 0 1 0 12 2.2Zm0 17.29a7.64 7.64 0 0 1-3.89-1.06l-.28-.17-2.95.7.78-2.88-.18-.29a7.64 7.64 0 1 1 6.52 3.7Zm4.19-5.7c-.23-.12-1.35-.66-1.56-.73-.21-.08-.36-.12-.51.12-.15.23-.59.73-.72.89-.13.15-.27.17-.5.06-.23-.12-.99-.36-1.88-1.16-.69-.61-1.16-1.37-1.3-1.6-.13-.23-.01-.35.1-.47.1-.1.23-.27.34-.4.11-.13.14-.23.22-.39.07-.15.04-.29-.02-.41-.06-.12-.51-1.23-.7-1.69-.18-.44-.37-.38-.51-.39h-.43c-.15 0-.39.06-.6.29-.21.23-.8.78-.8 1.9 0 1.11.82 2.19.93 2.34.12.15 1.59 2.43 3.86 3.4.54.23.95.37 1.27.47.53.17 1.02.15 1.4.09.43-.06 1.35-.55 1.54-1.08.19-.53.19-.98.13-1.08-.05-.1-.2-.15-.43-.27Z" fill="currentColor" />
                    </svg>
                  </span>
                </label>
                <input v-model="form.celular01" class="field" type="text" @blur="formatPhoneField('celular01')" />
              </div>
            </label>

            <label class="field-group">
              <span>Celular secundário</span>
              <input v-model="form.celular02" class="field" type="text" @blur="formatPhoneField('celular02')" />
            </label>

            <div class="field-group field-group--toggle">
              <span>WhatsApp</span>
              <label class="toggle-row">
                <input v-model="form.nao_enviar_whatsapp" type="checkbox" />
                <span>Não enviar WhatsApp</span>
              </label>
            </div>

            <label class="field-group">
              <span>CEP</span>
              <div class="field-inline">
                <input v-model="form.cep" class="field" maxlength="9" type="text" @blur="handleCepBlur" />
                <button class="secondary-button" :disabled="lookupLoading" type="button" @click="handleCepLookupClick">
                  {{ lookupLoading ? 'Consultando...' : 'Buscar CEP' }}
                </button>
              </div>
            </label>

            <label class="field-group">
              <span>UF</span>
              <select v-model="form.uf" class="field">
                <option value="">Selecione</option>
                <option v-for="option in ufs" :key="option.uf" :value="option.uf">{{ option.uf }} - {{ option.uf_nome }}</option>
              </select>
            </label>

            <label class="field-group">
              <span>Cidade</span>
              <select v-model.number="form.cidade_id" class="field" :disabled="!form.uf || companyCitiesLoading">
                <option :value="null">Selecione</option>
                <option v-for="option in companyCities" :key="option.cidade_id" :value="option.cidade_id">{{ option.cidade }}</option>
              </select>
            </label>

            <label class="field-group">
              <span>Bairro</span>
              <select v-model.number="form.bairro_id" class="field" :disabled="!form.uf || !form.cidade_id || companyBairrosLoading">
                <option :value="null">Selecione</option>
                <option v-for="option in companyBairros" :key="option.bairro_id" :value="option.bairro_id">{{ option.bairro_nome }}</option>
              </select>
            </label>

            <label class="field-group field-group--span-2">
              <span>Endereço</span>
              <div class="field-inline field-inline--map">
                <input v-model="form.endereco" class="field" type="text" @blur="handleAddressBlur" />
                <button class="map-inline-button" title="Abrir no mapa" aria-label="Abrir no mapa" type="button" @click="openCompanyMapPopup">
                  <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <path d="M12 2.25a6.75 6.75 0 0 0-6.75 6.75c0 4.72 5.2 10.9 6.11 11.95a.83.83 0 0 0 1.28 0c.91-1.05 6.11-7.23 6.11-11.95A6.75 6.75 0 0 0 12 2.25Zm0 9.25A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5Z" fill="currentColor" />
                  </svg>
                </button>
              </div>
            </label>

            <label class="field-group">
              <span>Número</span>
              <input v-model="form.nro" class="field" type="text" @blur="handleCompanyNumberBlur" />
            </label>

            <label class="field-group">
              <span>Complemento</span>
              <input v-model="form.complemento" class="field" type="text" />
            </label>

            <label class="field-group">
              <span>Cobrador</span>
              <select v-model.number="form.usuario_id" class="field">
                <option :value="null">Selecione</option>
                <option v-for="user in cobradores" :key="user.id" :value="user.id">{{ user.nome }}</option>
              </select>
            </label>

            <label class="field-group">
              <span>Turno de cobrança</span>
              <select v-model="form.turno_cobranca" class="field">
                <option value="">Selecione</option>
                <option v-for="option in turnoOptions" :key="option" :value="option">{{ option }}</option>
              </select>
            </label>
          </div>

        </section>

        <section class="client-card">
          <header class="client-card__header client-card__header--with-score">
            <div>
              <h3 class="panel__title">Responsável</h3>
            </div>

            <div class="client-card__score-corner">
              <div class="score-widget score-widget--corner">
                <div class="score-widget__ring" :style="scoreRingStyle">
                  <div class="score-widget__core">
                    <span class="score-widget__value">{{ normalizedScore }}</span>
                    <span class="score-widget__label">Score</span>
                  </div>
                </div>
              </div>
            </div>
          </header>

          <div class="client-card__grid">
            <label class="field-group field-group--span-2">
              <span>Nome do responsável</span>
              <input v-model="form.contato_responsavel" class="field" type="text" />
            </label>

            <label class="field-group">
              <span>Nacionalidade</span>
              <input v-model="form.nacionalidade" class="field" type="text" />
            </label>

            <label class="field-group">
              <span>Estado civil</span>
              <input v-model="form.estado_civil" class="field" type="text" />
            </label>

            <label class="field-group">
              <span>Profissão</span>
              <input v-model="form.profissao" class="field" type="text" />
            </label>

            <label class="field-group">
              <span>Telefone</span>
              <input v-model="form.fone_responsavel" class="field" type="text" @blur="formatPhoneField('fone_responsavel')" />
            </label>

            <label class="field-group">
              <span>Celular</span>
              <div class="field-inline field-inline--cellphone">
                <label class="whatsapp-toggle" :class="form.flag_whatsapp_responsavel ? 'whatsapp-toggle--on' : 'whatsapp-toggle--off'" title="WhatsApp" aria-label="WhatsApp">
                  <input v-model="form.flag_whatsapp_responsavel" class="whatsapp-toggle__input" type="checkbox" />
                  <span class="whatsapp-toggle__icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" focusable="false">
                      <path d="M12 2.2a9.6 9.6 0 0 0-8.29 14.46L2.5 21.5l4.97-1.19A9.6 9.6 0 1 0 12 2.2Zm0 17.29a7.64 7.64 0 0 1-3.89-1.06l-.28-.17-2.95.7.78-2.88-.18-.29a7.64 7.64 0 1 1 6.52 3.7Zm4.19-5.7c-.23-.12-1.35-.66-1.56-.73-.21-.08-.36-.12-.51.12-.15.23-.59.73-.72.89-.13.15-.27.17-.5.06-.23-.12-.99-.36-1.88-1.16-.69-.61-1.16-1.37-1.3-1.6-.13-.23-.01-.35.1-.47.1-.1.23-.27.34-.4.11-.13.14-.23.22-.39.07-.15.04-.29-.02-.41-.06-.12-.51-1.23-.7-1.69-.18-.44-.37-.38-.51-.39h-.43c-.15 0-.39.06-.6.29-.21.23-.8.78-.8 1.9 0 1.11.82 2.19.93 2.34.12.15 1.59 2.43 3.86 3.4.54.23.95.37 1.27.47.53.17 1.02.15 1.4.09.43-.06 1.35-.55 1.54-1.08.19-.53.19-.98.13-1.08-.05-.1-.2-.15-.43-.27Z" fill="currentColor" />
                    </svg>
                  </span>
                </label>
                <input v-model="form.cel_responsavel" class="field" type="text" @blur="formatPhoneField('cel_responsavel')" />
              </div>
            </label>

            <label class="field-group field-group--span-2">
              <span>CEP</span>
              <div class="field-inline">
                <input v-model="form.cep_responsavel" class="field" maxlength="9" type="text" @blur="handleResponsibleCepBlur" />
                <button class="secondary-button" :disabled="responsibleLookupLoading" type="button" @click="handleResponsibleCepLookupClick">
                  {{ responsibleLookupLoading ? 'Consultando...' : 'Buscar CEP' }}
                </button>
              </div>
            </label>

            <label class="field-group">
              <span>UF</span>
              <select v-model="form.uf_responsavel" class="field">
                <option value="">Selecione</option>
                <option v-for="option in ufs" :key="`responsavel-${option.uf}`" :value="option.uf">{{ option.uf }} - {{ option.uf_nome }}</option>
              </select>
            </label>

            <label class="field-group">
              <span>Cidade</span>
              <select v-model.number="form.cidade_responsavel_id" class="field" :disabled="!form.uf_responsavel || responsibleCitiesLoading">
                <option :value="null">Selecione</option>
                <option v-for="option in responsibleCities" :key="option.cidade_id" :value="option.cidade_id">{{ option.cidade }}</option>
              </select>
            </label>

            <label class="field-group">
              <span>Bairro</span>
              <select v-model.number="form.bairro_id_responsavel" class="field" :disabled="!form.uf_responsavel || !form.cidade_responsavel_id || responsibleBairrosLoading">
                <option :value="null">Selecione</option>
                <option v-for="option in responsibleBairros" :key="option.bairro_id" :value="option.bairro_id">{{ option.bairro_nome }}</option>
              </select>
            </label>

            <label class="field-group field-group--span-2">
              <span>Endereço</span>
              <div class="field-inline field-inline--map">
                <input v-model="form.endereco_responsavel" class="field" type="text" @blur="handleResponsibleAddressBlur" />
                <button class="map-inline-button" title="Abrir no mapa" aria-label="Abrir no mapa" type="button" @click="openResponsibleMapPopup">
                  <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <path d="M12 2.25a6.75 6.75 0 0 0-6.75 6.75c0 4.72 5.2 10.9 6.11 11.95a.83.83 0 0 0 1.28 0c.91-1.05 6.11-7.23 6.11-11.95A6.75 6.75 0 0 0 12 2.25Zm0 9.25A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5Z" fill="currentColor" />
                  </svg>
                </button>
              </div>
            </label>

            <label class="field-group">
              <span>Número</span>
              <input v-model="form.nro_responsavel" class="field" type="text" />
            </label>

            <label class="field-group">
              <span>Complemento</span>
              <input v-model="form.complemento_responsavel" class="field" type="text" />
            </label>
          </div>

        </section>
      </div>

      <section class="client-card client-card--footer">
        <header class="client-card__header client-card__header--financial">
          <div>
            <h3 class="panel__title">Financeiro</h3>
          </div>
        </header>

        <div class="financial-card__layout">
          <div class="financial-card__main">
            <div class="financial-card__grid">
              <label class="field-group">
                <span>Limite de crédito</span>
                <input v-model="form.limite_credito" class="field" inputmode="decimal" type="text" @blur="formatMoneyField('limite_credito')" />
              </label>

              <label class="field-group">
                <span>Débito atual</span>
                <input v-model="form.debito_atual" class="field field--readonly" readonly type="text" />
              </label>

              <label class="field-group">
                <span>Regra de juros</span>
                <select v-model.number="form.regra_juros_id" class="field">
                  <option :value="null">Selecione</option>
                  <option v-for="option in regrasJuros" :key="option.regra_juros_id" :value="option.regra_juros_id">{{ option.descricao || `Regra ${option.regra_juros_id}` }}</option>
                </select>
              </label>

              <label class="field-group">
                <span>Valor em aberto</span>
                <input v-model="form.valor_em_aberto" class="field field--readonly" readonly type="text" />
              </label>

              <label class="field-group">
                <span>Parcelas atrasadas</span>
                <input v-model.number="form.parc_atrasadas" class="field field--readonly" readonly type="number" />
              </label>

              <label class="field-group">
                <span>Parcelas em aberto</span>
                <input v-model.number="form.parc_aberto" class="field field--readonly" readonly type="number" />
              </label>

              <label class="field-group">
                <span>Valor atrasado</span>
                <input v-model="form.valor_atrasado" class="field field--readonly" readonly type="text" />
              </label>

              <label class="field-group">
                <span>Média atraso parcelas (dias)</span>
                <input v-model.number="form.media_atraso_parcelas" class="field field--readonly" readonly type="number" />
              </label>

              <label class="field-group">
                <span>Média atraso contratos (dias)</span>
                <input v-model.number="form.media_atraso_contratos" class="field field--readonly" readonly type="number" />
              </label>

              <div class="field-group field-group--toggle">
                <span>Comissão</span>
                <label class="toggle-row">
                  <input v-model="form.naopagarcomissao" type="checkbox" />
                  <span>Não pagar comissão</span>
                </label>
              </div>

              <div class="field-group field-group--toggle">
                <span>Comissão diferenciada</span>
                <label class="toggle-row">
                  <input v-model="form.comissao_diferente" type="checkbox" />
                  <span>Pagar comissão de:</span>
                </label>
              </div>

              <label class="field-group">
                <span>Percentual</span>
                <input
                  v-model="form.percent_comissao"
                  class="field"
                  :disabled="!form.comissao_diferente || form.naopagarcomissao"
                  inputmode="decimal"
                  type="text"
                  @blur="formatPercentField"
                />
              </label>
            </div>
          </div>
        </div>
      </section>

      <div class="form-actions form-actions--client">
        <button class="primary-button primary-button--success form-actions__button" :disabled="saving" type="submit">
          {{ saving ? 'Salvando...' : 'Salvar' }}
        </button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="saving" type="button" @click="emit('cancel')">Cancelar</button>
      </div>
    </form>

    <p v-if="lookupMessage" class="feedback feedback--info">{{ lookupMessage }}</p>
    <p v-if="responsibleLookupMessage" class="feedback feedback--info">{{ responsibleLookupMessage }}</p>
    <p v-if="mapMessage" class="feedback feedback--info">{{ mapMessage }}</p>
    <p v-if="success" class="feedback feedback--success">{{ success }}</p>
    <p v-if="error" class="feedback feedback--error">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

import type { CobradorOption, Client, ClientInput, RegraJurosOption } from '@/models/client'
import type { BairroOption, CidadeOption, UFOption } from '@/models/location'
import { listCobradorOptions, listRegraJurosOptions } from '@/services/clientService'
import { listBairrosByCidade, listCitiesByUf, listUfs, lookupAddressByCep, lookupCepByAddress } from '@/services/locationService'

const turnoOptions = ['Integral', 'Manhã', 'Tarde', 'Noite'] as const

const props = defineProps<{
  mode: 'create' | 'edit'
  saving: boolean
  error: string
  success: string
  initialClient?: Client | null
}>()

const emit = defineEmits<{
  submit: [payload: ClientInput]
  cancel: []
}>()

const ufs = ref<UFOption[]>([])
const companyCities = ref<CidadeOption[]>([])
const responsibleCities = ref<CidadeOption[]>([])
const companyBairros = ref<BairroOption[]>([])
const responsibleBairros = ref<BairroOption[]>([])
const cobradores = ref<CobradorOption[]>([])
const regrasJuros = ref<RegraJurosOption[]>([])
const companyCitiesLoading = ref(false)
const responsibleCitiesLoading = ref(false)
const companyBairrosLoading = ref(false)
const responsibleBairrosLoading = ref(false)
const lookupLoading = ref(false)
const responsibleLookupLoading = ref(false)
const lookupMessage = ref('')
const responsibleLookupMessage = ref('')
const mapMessage = ref('')
let syncingForm = false

const form = reactive({
  nome: '',
  cpf_cnpj: '',
  rg_ie: '',
  email: '',
  telefone: '',
  celular01: '',
  celular02: '',
  flag_whatsapp: false,
  nao_enviar_whatsapp: false,
  score: 1000,
  limite_credito: '0,00',
  debito_atual: '0,00',
  latitude: '',
  longitude: '',
  cep: '',
  uf: '',
  cidade_id: null as number | null,
  bairro_id: null as number | null,
  endereco: '',
  nro: '',
  complemento: '',
  ativo: true,
  bloqueado: false,
  comissao_diferente: false,
  percent_comissao: '0,00',
  naopagarcomissao: false,
  parc_atrasadas: null as number | null,
  valor_atrasado: '0,00',
  valor_em_aberto: '0,00',
  parc_aberto: null as number | null,
  usuario_id: null as number | null,
  contato_responsavel: '',
  endereco_responsavel: '',
  fone_responsavel: '',
  cel_responsavel: '',
  flag_whatsapp_responsavel: false,
  cep_responsavel: '',
  complemento_responsavel: '',
  uf_responsavel: '',
  cidade_responsavel_id: null as number | null,
  bairro_id_responsavel: null as number | null,
  nro_responsavel: '',
  nacionalidade: '',
  estado_civil: '',
  profissao: '',
  turno_cobranca: '',
  media_atraso_parcelas: null as number | null,
  media_atraso_contratos: null as number | null,
  regra_juros_id: null as number | null,
})

const normalizedScore = computed(() => Math.max(0, Math.min(1000, Number(form.score) || 0)))
const scorePercentage = computed(() => (normalizedScore.value / 1000) * 100)
const scoreRingStyle = computed(() => ({
  background: `conic-gradient(#f97316 0 ${scorePercentage.value}%, rgba(36, 48, 59, 0.12) ${scorePercentage.value}% 100%)`,
}))

void initializeOptions()

watch(
  () => props.initialClient,
  (client) => {
    void syncClientIntoForm(client)
  },
  { immediate: true },
)

watch(
  () => form.uf,
  (uf, previousUf) => {
    if (syncingForm) return
    form.cidade_id = null
    form.bairro_id = null
    companyBairros.value = []
    if (uf && uf !== previousUf) {
      void loadCompanyCities(uf)
      return
    }
    companyCities.value = []
  },
)

watch(
  () => form.cidade_id,
  (cidadeId, previousCidadeId) => {
    if (syncingForm) return
    form.bairro_id = null
    if (cidadeId && cidadeId !== previousCidadeId) {
      void loadCompanyBairros(cidadeId)
      return
    }
    companyBairros.value = []
  },
)

watch(
  () => form.uf_responsavel,
  (uf, previousUf) => {
    if (syncingForm) return
    form.cidade_responsavel_id = null
    form.bairro_id_responsavel = null
    responsibleBairros.value = []
    if (uf && uf !== previousUf) {
      void loadResponsibleCities(uf)
      return
    }
    responsibleCities.value = []
  },
)

watch(
  () => form.cidade_responsavel_id,
  (cidadeId, previousCidadeId) => {
    if (syncingForm) return
    form.bairro_id_responsavel = null
    if (cidadeId && cidadeId !== previousCidadeId) {
      void loadResponsibleBairros(cidadeId)
      return
    }
    responsibleBairros.value = []
  },
)

async function initializeOptions() {
  await Promise.allSettled([loadUfsOptions(), loadCobradoresOptions(), loadRegrasJurosOptions()])
}

async function loadUfsOptions() {
  if (ufs.value.length > 0) return
  ufs.value = await listUfs()
}

async function loadCobradoresOptions() {
  cobradores.value = await listCobradorOptions()
}

async function loadRegrasJurosOptions() {
  regrasJuros.value = await listRegraJurosOptions()
}

async function loadCompanyCities(uf: string) {
  companyCitiesLoading.value = true
  try {
    companyCities.value = await listCitiesByUf(uf)
  } finally {
    companyCitiesLoading.value = false
  }
}

async function loadResponsibleCities(uf: string) {
  responsibleCitiesLoading.value = true
  try {
    responsibleCities.value = await listCitiesByUf(uf)
  } finally {
    responsibleCitiesLoading.value = false
  }
}

async function loadCompanyBairros(cidadeId: number) {
  companyBairrosLoading.value = true
  try {
    companyBairros.value = await listBairrosByCidade(cidadeId)
  } finally {
    companyBairrosLoading.value = false
  }
}

async function loadResponsibleBairros(cidadeId: number) {
  responsibleBairrosLoading.value = true
  try {
    responsibleBairros.value = await listBairrosByCidade(cidadeId)
  } finally {
    responsibleBairrosLoading.value = false
  }
}

async function syncClientIntoForm(client?: Client | null) {
  if (!client) {
    if (props.mode === 'create') resetForm()
    return
  }

  syncingForm = true
  try {
    await initializeOptions()

    form.nome = client.nome ?? ''
    form.cpf_cnpj = formatDocument(client.cpf_cnpj)
    form.rg_ie = client.rg_ie ?? ''
    form.email = client.email ?? ''
    form.telefone = formatPhone(client.telefone)
    form.celular01 = formatPhone(client.celular01)
    form.celular02 = formatPhone(client.celular02)
    form.flag_whatsapp = client.flag_whatsapp
    form.nao_enviar_whatsapp = client.nao_enviar_whatsapp
    form.score = client.score ?? 1000
    form.limite_credito = formatMoney(client.limite_credito)
    form.debito_atual = formatMoney(client.debito_atual)
    form.latitude = client.latitude ?? ''
    form.longitude = client.longitude ?? ''
    form.cep = formatCepValue(client.cep)
    form.uf = client.uf ?? ''
    form.endereco = client.endereco ?? ''
    form.nro = client.nro ?? ''
    form.complemento = client.complemento ?? ''
    form.ativo = client.ativo
    form.bloqueado = client.bloqueado
    form.comissao_diferente = client.comissao_diferente
    form.percent_comissao = formatMoney(client.percent_comissao)
    form.naopagarcomissao = client.naopagarcomissao
    form.parc_atrasadas = client.parc_atrasadas ?? null
    form.valor_atrasado = formatMoney(client.valor_atrasado)
    form.valor_em_aberto = formatMoney(client.valor_em_aberto)
    form.parc_aberto = client.parc_aberto ?? null
    form.usuario_id = client.usuario_id ?? null
    form.contato_responsavel = client.contato_responsavel ?? ''
    form.endereco_responsavel = client.endereco_responsavel ?? ''
    form.fone_responsavel = formatPhone(client.fone_responsavel)
    form.cel_responsavel = formatPhone(client.cel_responsavel)
    form.flag_whatsapp_responsavel = client.flag_whatsapp_responsavel
    form.cep_responsavel = formatCepValue(client.cep_responsavel)
    form.complemento_responsavel = client.complemento_responsavel ?? ''
    form.uf_responsavel = client.uf_responsavel ?? ''
    form.cidade_responsavel_id = client.cidade_responsavel_id ?? null
    form.bairro_id_responsavel = client.bairro_id_responsavel ?? null
    form.nro_responsavel = client.nro_responsavel ?? ''
    form.nacionalidade = client.nacionalidade ?? ''
    form.estado_civil = client.estado_civil ?? ''
    form.profissao = client.profissao ?? ''
    form.turno_cobranca = client.turno_cobranca ?? ''
    form.media_atraso_parcelas = client.media_atraso_parcelas ?? null
    form.media_atraso_contratos = client.media_atraso_contratos ?? null
    form.regra_juros_id = client.regra_juros_id ?? null

    if (form.uf) {
      await loadCompanyCities(form.uf)
    } else {
      companyCities.value = []
    }
    form.cidade_id = client.cidade_id ?? null
    if (form.cidade_id) {
      await loadCompanyBairros(form.cidade_id)
    } else {
      companyBairros.value = []
    }
    form.bairro_id = client.bairro_id ?? null

    if (form.uf_responsavel) {
      await loadResponsibleCities(form.uf_responsavel)
    } else {
      responsibleCities.value = []
    }
    form.cidade_responsavel_id = client.cidade_responsavel_id ?? null
    if (form.cidade_responsavel_id) {
      await loadResponsibleBairros(form.cidade_responsavel_id)
    } else {
      responsibleBairros.value = []
    }
    form.bairro_id_responsavel = client.bairro_id_responsavel ?? null
  } finally {
    syncingForm = false
  }
}

async function submitForm() {
  await tryResolveCepByAddress()
  await tryResolveResponsibleCepByAddress()
  await ensureCompanyCoordinates()
  emit('submit', buildPayload())
  if (!props.error && props.mode === 'create') resetForm()
}

async function handleCepBlur() {
  form.cep = formatCepValue(form.cep)
  if (cleanDigits(form.cep).length !== 8) return
  await applyLookupByCep()
}

async function handleCepLookupClick() {
  await applyLookupByCep()
}

async function handleAddressBlur() {
  await tryResolveCepByAddress(true)
  await ensureCompanyCoordinates()
}

async function handleCompanyNumberBlur() {
  await ensureCompanyCoordinates()
}

async function handleResponsibleCepBlur() {
  form.cep_responsavel = formatCepValue(form.cep_responsavel)
  if (cleanDigits(form.cep_responsavel).length !== 8) return
  await applyResponsibleLookupByCep()
}

async function handleResponsibleCepLookupClick() {
  await applyResponsibleLookupByCep()
}

async function handleResponsibleAddressBlur() {
  await tryResolveResponsibleCepByAddress(true)
}

async function applyLookupByCep() {
  const cep = cleanDigits(form.cep)
  if (cep.length !== 8) {
    lookupMessage.value = 'Informe um CEP valido para consulta.'
    return
  }
  lookupLoading.value = true
  try {
    const result = await lookupAddressByCep(cep)
    if (!result.found) {
      lookupMessage.value = 'CEP nao encontrado. O cadastro pode continuar normalmente.'
      return
    }
    await applyLookupResult(result)
    lookupMessage.value = `Endereco localizado via ${result.source ?? 'servico externo'}.`
  } catch {
    lookupMessage.value = 'Nao foi possivel consultar o CEP agora.'
  } finally {
    lookupLoading.value = false
  }
}

async function tryResolveCepByAddress(silent = false) {
  if (cleanDigits(form.cep).length === 8) return
  const selectedCity = companyCities.value.find((item) => item.cidade_id === form.cidade_id)
  const selectedBairro = companyBairros.value.find((item) => item.bairro_id === form.bairro_id)
  if (!form.uf || !selectedCity || !form.endereco.trim()) return
  lookupLoading.value = true
  try {
    const result = await lookupCepByAddress({
      uf: form.uf,
      cidade: selectedCity.cidade,
      logradouro: form.endereco,
      bairro: selectedBairro?.bairro_nome,
    })
    if (!result.found) {
      if (!silent) lookupMessage.value = 'Endereco sem CEP localizado. Isso nao impede o cadastro.'
      return
    }
    await applyLookupResult(result)
    lookupMessage.value = ''
  } catch {
    if (!silent) lookupMessage.value = 'Nao foi possivel localizar o CEP pelo endereco agora.'
  } finally {
    lookupLoading.value = false
  }
}

async function applyLookupResult(result: { cep: string | null; endereco: string | null; complemento: string | null; uf: string | null; cidade_id: number | null; bairro_id: number | null }) {
  if (result.cep) form.cep = formatCepValue(result.cep)
  if (result.endereco && !form.endereco) form.endereco = result.endereco
  if (result.complemento && !form.complemento) form.complemento = result.complemento
  if (result.uf) {
    syncingForm = true
    form.uf = result.uf
    await loadCompanyCities(result.uf)
    form.cidade_id = result.cidade_id ?? null
    if (form.cidade_id) {
      await loadCompanyBairros(form.cidade_id)
      form.bairro_id = result.bairro_id ?? null
    } else {
      companyBairros.value = []
      form.bairro_id = null
    }
    syncingForm = false
  }
}

async function applyResponsibleLookupByCep() {
  const cep = cleanDigits(form.cep_responsavel)
  if (cep.length !== 8) {
    responsibleLookupMessage.value = 'Informe um CEP valido para consulta.'
    return
  }
  responsibleLookupLoading.value = true
  try {
    const result = await lookupAddressByCep(cep)
    if (!result.found) {
      responsibleLookupMessage.value = 'CEP nao encontrado. O cadastro pode continuar normalmente.'
      return
    }
    await applyResponsibleLookupResult(result)
    responsibleLookupMessage.value = `Endereco localizado via ${result.source ?? 'servico externo'}.`
  } catch {
    responsibleLookupMessage.value = 'Nao foi possivel consultar o CEP agora.'
  } finally {
    responsibleLookupLoading.value = false
  }
}

async function tryResolveResponsibleCepByAddress(silent = false) {
  if (cleanDigits(form.cep_responsavel).length === 8) return
  const selectedCity = responsibleCities.value.find((item) => item.cidade_id === form.cidade_responsavel_id)
  const selectedBairro = responsibleBairros.value.find((item) => item.bairro_id === form.bairro_id_responsavel)
  if (!form.uf_responsavel || !selectedCity || !form.endereco_responsavel.trim()) return
  responsibleLookupLoading.value = true
  try {
    const result = await lookupCepByAddress({
      uf: form.uf_responsavel,
      cidade: selectedCity.cidade,
      logradouro: form.endereco_responsavel,
      bairro: selectedBairro?.bairro_nome,
    })
    if (!result.found) {
      if (!silent) responsibleLookupMessage.value = 'Endereco sem CEP localizado. Isso nao impede o cadastro.'
      return
    }
    await applyResponsibleLookupResult(result)
    responsibleLookupMessage.value = ''
  } catch {
    if (!silent) responsibleLookupMessage.value = 'Nao foi possivel localizar o CEP pelo endereco agora.'
  } finally {
    responsibleLookupLoading.value = false
  }
}

async function applyResponsibleLookupResult(result: { cep: string | null; endereco: string | null; complemento: string | null; uf: string | null; cidade_id: number | null; bairro_id: number | null }) {
  if (result.cep) form.cep_responsavel = formatCepValue(result.cep)
  if (result.endereco && !form.endereco_responsavel) form.endereco_responsavel = result.endereco
  if (result.complemento && !form.complemento_responsavel) form.complemento_responsavel = result.complemento
  if (result.uf) {
    syncingForm = true
    form.uf_responsavel = result.uf
    await loadResponsibleCities(result.uf)
    form.cidade_responsavel_id = result.cidade_id ?? null
    if (form.cidade_responsavel_id) {
      await loadResponsibleBairros(form.cidade_responsavel_id)
      form.bairro_id_responsavel = result.bairro_id ?? null
    } else {
      responsibleBairros.value = []
      form.bairro_id_responsavel = null
    }
    syncingForm = false
  }
}

function buildPayload(): ClientInput {
  return {
    nome: emptyToNull(form.nome),
    rg: null,
    cpf_cnpj: emptyToNull(cleanDigits(form.cpf_cnpj)),
    endereco: emptyToNull(form.endereco),
    bairro_id: form.bairro_id,
    cidade_id: form.cidade_id,
    uf: emptyToNull(form.uf),
    usuario_id: form.usuario_id,
    cnpj: null,
    telefone: emptyToNull(cleanDigits(form.telefone)),
    celular01: emptyToNull(cleanDigits(form.celular01)),
    celular02: emptyToNull(cleanDigits(form.celular02)),
    flag_whatsapp: form.flag_whatsapp,
    nao_enviar_whatsapp: form.nao_enviar_whatsapp,
    email: emptyToNull(form.email),
    limite_credito: parseMoney(form.limite_credito),
    debito_atual: parseMoney(form.debito_atual),
    latitude: emptyToNull(form.latitude),
    longitude: emptyToNull(form.longitude),
    rg_ie: emptyToNull(form.rg_ie),
    cep: emptyToNull(cleanDigits(form.cep)),
    nro: emptyToNull(form.nro),
    complemento: emptyToNull(form.complemento),
    ativo: form.ativo,
    bloqueado: form.bloqueado,
    comissao_diferente: form.comissao_diferente,
    percent_comissao: parseMoney(form.percent_comissao),
    naopagarcomissao: form.naopagarcomissao,
    parc_atrasadas: form.parc_atrasadas,
    valor_atrasado: parseMoney(form.valor_atrasado),
    valor_em_aberto: parseMoney(form.valor_em_aberto),
    parc_aberto: form.parc_aberto,
    contato_responsavel: emptyToNull(form.contato_responsavel),
    endereco_responsavel: emptyToNull(form.endereco_responsavel),
    fone_responsavel: emptyToNull(cleanDigits(form.fone_responsavel)),
    cel_responsavel: emptyToNull(cleanDigits(form.cel_responsavel)),
    flag_whatsapp_responsavel: form.flag_whatsapp_responsavel,
    cep_responsavel: emptyToNull(cleanDigits(form.cep_responsavel)),
    complemento_responsavel: emptyToNull(form.complemento_responsavel),
    uf_responsavel: emptyToNull(form.uf_responsavel),
    cidade_responsavel_id: form.cidade_responsavel_id,
    bairro_id_responsavel: form.bairro_id_responsavel,
    nro_responsavel: emptyToNull(form.nro_responsavel),
    nacionalidade: emptyToNull(form.nacionalidade),
    estado_civil: emptyToNull(form.estado_civil),
    profissao: emptyToNull(form.profissao),
    turno_cobranca: emptyToNull(form.turno_cobranca),
    score: form.score,
    media_atraso_parcelas: form.media_atraso_parcelas,
    media_atraso_contratos: form.media_atraso_contratos,
    regra_juros_id: form.regra_juros_id,
  }
}

function resetForm() {
  form.nome = ''
  form.cpf_cnpj = ''
  form.rg_ie = ''
  form.email = ''
  form.telefone = ''
  form.celular01 = ''
  form.celular02 = ''
  form.flag_whatsapp = false
  form.nao_enviar_whatsapp = false
  form.score = 1000
  form.limite_credito = '0,00'
  form.debito_atual = '0,00'
  form.latitude = ''
  form.longitude = ''
  form.cep = ''
  form.uf = ''
  form.cidade_id = null
  form.bairro_id = null
  form.endereco = ''
  form.nro = ''
  form.complemento = ''
  form.ativo = true
  form.bloqueado = false
  form.comissao_diferente = false
  form.percent_comissao = '0,00'
  form.naopagarcomissao = false
  form.parc_atrasadas = null
  form.valor_atrasado = '0,00'
  form.valor_em_aberto = '0,00'
  form.parc_aberto = null
  form.usuario_id = null
  form.contato_responsavel = ''
  form.endereco_responsavel = ''
  form.fone_responsavel = ''
  form.cel_responsavel = ''
  form.flag_whatsapp_responsavel = false
  form.cep_responsavel = ''
  form.complemento_responsavel = ''
  form.uf_responsavel = ''
  form.cidade_responsavel_id = null
  form.bairro_id_responsavel = null
  form.nro_responsavel = ''
  form.nacionalidade = ''
  form.estado_civil = ''
  form.profissao = ''
  form.turno_cobranca = ''
  form.media_atraso_parcelas = null
  form.media_atraso_contratos = null
  form.regra_juros_id = null
  companyCities.value = []
  companyBairros.value = []
  responsibleCities.value = []
  responsibleBairros.value = []
  lookupMessage.value = ''
  responsibleLookupMessage.value = ''
  mapMessage.value = ''
}

async function openCompanyMapPopup() {
  const coordinates = await ensureCompanyCoordinates()
  const query = buildAddressQuery('company')
  openMapPopup(coordinates ? `${coordinates.lat},${coordinates.lon}` : query)
}

async function openResponsibleMapPopup() {
  const query = buildAddressQuery('responsible')
  if (!query) {
    mapMessage.value = 'Preencha o endereço do responsável para abrir o mapa.'
    return
  }
  openMapPopup(query)
}

function openMapPopup(query: string | null) {
  if (!query) {
    mapMessage.value = 'Preencha endereço, cidade e UF para abrir o mapa.'
    return
  }
  mapMessage.value = ''
  const url = `https://www.google.com/maps?q=${encodeURIComponent(query)}`
  window.open(url, 'googleMapsPopup', 'popup=yes,width=1080,height=760,left=120,top=80')
}

async function ensureCompanyCoordinates() {
  const query = buildAddressQuery('company')
  if (!query) {
    form.latitude = ''
    form.longitude = ''
    return null
  }

  form.latitude = ''
  form.longitude = ''
  const result = await geocodeQuery(query)
  if (result) {
    form.latitude = result.lat
    form.longitude = result.lon
  }
  return result
}

function buildAddressQuery(target: 'company' | 'responsible') {
  if (target === 'company') {
    const city = companyCities.value.find((item) => item.cidade_id === form.cidade_id)?.cidade ?? ''
    return [
      form.endereco,
      form.nro,
      companyBairros.value.find((item) => item.bairro_id === form.bairro_id)?.bairro_nome ?? '',
      city,
      form.uf,
      'Brasil',
    ]
      .map((item) => item?.trim())
      .filter(Boolean)
      .join(', ')
  }
  const city = responsibleCities.value.find((item) => item.cidade_id === form.cidade_responsavel_id)?.cidade ?? ''
  return [
    form.endereco_responsavel,
    form.nro_responsavel,
    responsibleBairros.value.find((item) => item.bairro_id === form.bairro_id_responsavel)?.bairro_nome ?? '',
    city,
    form.uf_responsavel,
    'Brasil',
  ]
    .map((item) => item?.trim())
    .filter(Boolean)
    .join(', ')
}

async function geocodeQuery(query: string) {
  try {
    const params = new URLSearchParams({ format: 'jsonv2', limit: '1', q: query })
    const response = await fetch(`https://nominatim.openstreetmap.org/search?${params.toString()}`, {
      headers: { Accept: 'application/json' },
    })
    if (!response.ok) return null
    const results = (await response.json()) as Array<{ lat: string; lon: string }>
    return results[0] ?? null
  } catch {
    return null
  }
}

function emptyToNull(value: string | null | undefined) {
  const normalized = value?.trim() ?? ''
  return normalized ? normalized : null
}

function cleanDigits(value: string | null | undefined) {
  return (value ?? '').replace(/\D/g, '')
}

function formatDocument(value: string | null | undefined) {
  const digits = cleanDigits(value)
  if (digits.length <= 11) {
    return digits.slice(0, 11).replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2')
  }
  return digits.slice(0, 14).replace(/(\d{2})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1/$2').replace(/(\d{4})(\d{1,2})$/, '$1-$2')
}

function formatDocumentField(field: 'cpf_cnpj') {
  form[field] = formatDocument(form[field])
}

function formatPhone(value: string | null | undefined) {
  const digits = cleanDigits(value).slice(0, 11)
  if (!digits) return ''
  if (digits.length <= 10) return digits.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{4})(\d)/, '$1-$2')
  return digits.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{5})(\d)/, '$1-$2')
}

function formatPhoneField(field: 'telefone' | 'celular01' | 'celular02' | 'fone_responsavel' | 'cel_responsavel') {
  form[field] = formatPhone(form[field])
}

function formatCepValue(value: string | null | undefined) {
  const digits = cleanDigits(value).slice(0, 8)
  if (digits.length <= 5) return digits
  return `${digits.slice(0, 5)}-${digits.slice(5)}`
}

function parseMoney(value: string) {
  const normalized = value.replace(/\./g, '').replace(',', '.').trim()
  if (!normalized) return null
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function formatMoney(value: number | null | undefined) {
  const numeric = value ?? 0
  return numeric.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatMoneyField(field: 'limite_credito') {
  const parsed = parseMoney(form[field])
  form[field] = formatMoney(parsed)
}

function formatPercentField() {
  form.percent_comissao = formatMoney(parseMoney(form.percent_comissao))
}
</script>

<style scoped>
.client-form {
  display: grid;
  gap: 18px;
}

.client-form__cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.client-card {
  padding: 16px;
  border: 1px solid rgba(36, 48, 59, 0.08);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.88);
}

.client-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.client-card__header--financial {
  margin-bottom: 18px;
}

.client-card__header--with-score {
  position: relative;
  padding-right: 82px;
}

.client-card__score-corner {
  position: absolute;
  top: -10px;
  right: 0;
}

.client-card__status {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.client-card__grid,
.financial-card__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.client-card--footer {
  margin-top: 2px;
}

.financial-card__layout {
  display: block;
}

.financial-card__main {
  display: grid;
  gap: 0;
}

.field-inline--map {
  align-items: stretch;
  gap: 0;
}

.field-inline--map .field {
  flex: 1;
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.map-inline-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  min-width: 44px;
  border: 1px solid rgba(249, 115, 22, 0.22);
  border-left: 0;
  border-radius: 0 3px 3px 0;
  background: linear-gradient(135deg, rgba(255, 243, 234, 0.98), rgba(255, 234, 220, 0.94));
  color: #c65a11;
  padding: 0;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.map-inline-button svg {
  width: 18px;
  height: 18px;
}

.map-inline-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 18px rgba(198, 90, 17, 0.14);
}

.map-inline-button:focus-visible {
  outline: 2px solid rgba(249, 115, 22, 0.28);
  outline-offset: 2px;
}

.score-widget {
  display: flex;
  justify-content: center;
}

.score-widget__ring {
  position: relative;
  display: grid;
  place-items: center;
  width: 85px;
  height: 85px;
  padding: 6px;
  border-radius: 50%;
  box-shadow: inset 0 0 0 1px rgba(36, 48, 59, 0.04), 0 14px 28px rgba(48, 63, 77, 0.1);
}

.score-widget--corner .score-widget__ring {
  width: 68px;
  height: 68px;
  padding: 5px;
}

.score-widget__core {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.96);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-widget__value {
  font-size: 1rem;
  line-height: 1;
  font-weight: 800;
  color: #24303b;
}

.score-widget--corner .score-widget__value {
  font-size: 0.88rem;
}

.score-widget__label {
  margin-top: 3px;
  font-size: 0.48rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(36, 48, 59, 0.58);
}

.score-widget--corner .score-widget__label {
  margin-top: 2px;
  font-size: 0.5rem;
}

.field--readonly {
  background: rgba(238, 242, 246, 0.88);
  color: rgba(36, 48, 59, 0.78);
}

.commission-panel {
  display: grid;
  gap: 12px;
}

.commission-panel__line {
  display: grid;
  grid-template-columns: 1fr 140px;
  gap: 12px;
  align-items: center;
}

.toggle-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.field-group--toggle {
  justify-content: center;
}

.field-group--toggle .toggle-row {
  min-height: 34px;
}

.financial-card__grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: start;
}

.form-actions--client {
  justify-content: flex-end;
}

@media (max-width: 1100px) {
  .client-form__cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .client-card__grid,
  .financial-card__grid,
  .commission-panel__line {
    grid-template-columns: 1fr;
  }
}
</style>
