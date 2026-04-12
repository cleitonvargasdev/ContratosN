<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <p class="eyebrow">Cadastro único da empresa</p>
        <h2 class="panel__title">Parâmetros</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="submitForm">
      <div class="parameters-layout field-group--span-2">
        <section class="settings-card settings-card--company">
        <header class="settings-card__header">
          <div>
            <h3>Empresa</h3>
            <p>Dados gerais</p>
          </div>
          <label class="status-switch" :class="form.emitir_sons ? 'status-switch--on' : 'status-switch--off'">
            <input v-model="form.emitir_sons" class="status-switch__input" type="checkbox" />
            <span class="status-switch__track"><span class="status-switch__thumb"></span></span>
            <span class="status-switch__label">{{ form.emitir_sons ? 'Emitir sons' : 'Sem sons' }}</span>
          </label>
        </header>

        <div class="settings-card__grid">
          <label class="field-group field-group--span-2"><span>Nome fantasia</span><input v-model="form.nome_fantasia" class="field" type="text" /></label>
          <label class="field-group field-group--span-2"><span>Razão social</span><input v-model="form.razao_social" class="field" type="text" /></label>
          <label class="field-group"><span>CNPJ</span><input v-model="form.cnpj" class="field" type="text" @blur="formatCnpj" /></label>
          <label class="field-group"><span>Responsável</span><input v-model="form.responsavel" class="field" type="text" /></label>
          <label class="field-group field-group--span-2"><span>E-mail</span><input v-model="form.e_mail" class="field" type="email" /></label>
          <label class="field-group">
            <span>Telefone 1</span>
            <div class="phone-field-row">
              <button
                class="phone-flag-button"
                :class="form.flag_whatsapp_telefone1 ? 'phone-flag-button--active' : ''"
                :title="form.flag_whatsapp_telefone1 ? 'WhatsApp ativo no Telefone 1' : 'Marcar Telefone 1 como WhatsApp'"
                type="button"
                @click="form.flag_whatsapp_telefone1 = !form.flag_whatsapp_telefone1"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path fill="currentColor" d="M12.04 2C6.58 2 2.15 6.35 2.15 11.72c0 1.9.56 3.75 1.62 5.34L2 22l5.12-1.66a10.06 10.06 0 0 0 4.92 1.28h.01c5.46 0 9.89-4.36 9.89-9.73S17.5 2 12.04 2Zm5.76 13.77c-.24.67-1.41 1.28-1.95 1.36-.5.08-1.14.11-1.84-.11-.43-.14-.99-.32-1.7-.62-2.98-1.27-4.93-4.24-5.08-4.44-.15-.2-1.21-1.58-1.21-3.02 0-1.44.76-2.14 1.03-2.43.27-.29.59-.36.79-.36.2 0 .4 0 .58.01.18.01.42-.07.66.51.24.58.81 1.99.88 2.13.07.15.12.32.02.51-.1.2-.15.32-.29.5-.15.17-.31.39-.45.52-.15.14-.31.29-.13.56.18.27.79 1.29 1.7 2.09 1.17 1.04 2.16 1.36 2.47 1.51.31.15.49.13.67-.08.18-.2.78-.89.99-1.2.21-.31.42-.26.71-.15.29.1 1.85.86 2.17 1.01.32.16.53.23.61.36.08.13.08.74-.16 1.41Z" />
                </svg>
              </button>
              <input v-model="form.telefone1" class="field" type="text" @blur="formatPhoneField('telefone1')" />
            </div>
          </label>
          <label class="field-group">
            <span>Telefone 2</span>
            <div class="phone-field-row">
              <button
                class="phone-flag-button"
                :class="form.flag_whatsapp_telefone2 ? 'phone-flag-button--active' : ''"
                :title="form.flag_whatsapp_telefone2 ? 'WhatsApp ativo no Telefone 2' : 'Marcar Telefone 2 como WhatsApp'"
                type="button"
                @click="form.flag_whatsapp_telefone2 = !form.flag_whatsapp_telefone2"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path fill="currentColor" d="M12.04 2C6.58 2 2.15 6.35 2.15 11.72c0 1.9.56 3.75 1.62 5.34L2 22l5.12-1.66a10.06 10.06 0 0 0 4.92 1.28h.01c5.46 0 9.89-4.36 9.89-9.73S17.5 2 12.04 2Zm5.76 13.77c-.24.67-1.41 1.28-1.95 1.36-.5.08-1.14.11-1.84-.11-.43-.14-.99-.32-1.7-.62-2.98-1.27-4.93-4.24-5.08-4.44-.15-.2-1.21-1.58-1.21-3.02 0-1.44.76-2.14 1.03-2.43.27-.29.59-.36.79-.36.2 0 .4 0 .58.01.18.01.42-.07.66.51.24.58.81 1.99.88 2.13.07.15.12.32.02.51-.1.2-.15.32-.29.5-.15.17-.31.39-.45.52-.15.14-.31.29-.13.56.18.27.79 1.29 1.7 2.09 1.17 1.04 2.16 1.36 2.47 1.51.31.15.49.13.67-.08.18-.2.78-.89.99-1.2.21-.31.42-.26.71-.15.29.1 1.85.86 2.17 1.01.32.16.53.23.61.36.08.13.08.74-.16 1.41Z" />
                </svg>
              </button>
              <input v-model="form.telefone2" class="field" type="text" @blur="formatPhoneField('telefone2')" />
            </div>
          </label>
          <label class="field-group field-group--span-2">
            <span>Api WhatsApp MSG</span>
            <div class="field-inline field-inline--popup">
              <select v-model="form.api_whatsapp" class="field" :disabled="apiOptionsLoading">
                <option value="">Selecione</option>
                <option v-for="option in apiWhatsappOptions" :key="option" :value="option">{{ option }}</option>
              </select>
              <button class="secondary-button" :disabled="saving" type="button" @click="openWhatsappModal">Configurar WhatsApp</button>
            </div>
          </label>
          <label class="field-group">
            <span>CEP</span>
            <div class="field-inline">
              <input v-model="form.cep" class="field" maxlength="9" type="text" @blur="handleCepBlur" />
              <button class="secondary-button" :disabled="lookupLoading" type="button" @click="handleCepLookupClick">{{ lookupLoading ? 'Consultando...' : 'Buscar CEP' }}</button>
            </div>
          </label>
          <label class="field-group field-group--span-2"><span>Endereço</span><input v-model="form.endereco" class="field" type="text" @blur="handleAddressBlur" /></label>
          <label class="field-group"><span>Número</span><input v-model.number="form.nro" class="field" min="0" type="number" /></label>
          <label class="field-group"><span>Complemento</span><input v-model="form.complemento" class="field" type="text" /></label>
          <label class="field-group"><span>UF</span><select v-model="form.uf" class="field"><option value="">Selecione</option><option v-for="option in ufs" :key="option.uf" :value="option.uf">{{ option.uf }} - {{ option.uf_nome }}</option></select></label>
          <label class="field-group"><span>Cidade</span><select v-model.number="form.cidade_id" class="field" :disabled="!form.uf || citiesLoading"><option :value="null">Selecione</option><option v-for="option in cities" :key="option.cidade_id" :value="option.cidade_id">{{ option.cidade }}</option></select></label>
          <label class="field-group"><span>Bairro</span><select v-model.number="form.bairrosid" class="field" :disabled="!form.uf || !form.cidade_id || bairrosLoading"><option :value="null">Selecione</option><option v-for="option in bairros" :key="option.bairro_id" :value="option.bairro_id">{{ option.bairro_nome }}</option></select></label>
        </div>

        <p v-if="lookupMessage" class="feedback feedback--info settings-card__feedback">{{ lookupMessage }}</p>
        </section>

        <div class="parameters-layout__side">
          <section class="settings-card settings-card--score">
        <header class="settings-card__header settings-card__header--stacked">
          <div>
            <h3>Regras de score dos clientes</h3>
          </div>
        </header>

        <div class="settings-card__grid settings-card__grid--score">
          <label class="field-group"><span>Valor inicial</span><input v-model.number="form.score_valor_inicial" class="field" type="number" /></label>
          <label class="field-group"><span>Pts atraso parcela</span><input v-model.number="form.score_pontos_atraso_parcela" class="field" type="number" /></label>
          <label class="field-group"><span>Pts atraso quitação</span><input v-model.number="form.score_pontos_atraso_quitacao_contrato" class="field" type="number" /></label>
          <label class="field-group"><span>Pts pagto em dia</span><input v-model.number="form.score_pontos_pagamento_em_dia" class="field" type="number" /></label>
          <label class="field-group"><span>Pts quitação em dia</span><input v-model.number="form.score_pontos_quitacao_em_dia" class="field" type="number" /></label>
          <div class="field-group field-group--score-toggle">
            <span>Atualização</span>
            <div class="score-actions automation-controls-row__actions">
              <label class="status-switch status-switch--compact" :class="form.score_atualizacao_automatica ? 'status-switch--on' : 'status-switch--off'">
                <input v-model="form.score_atualizacao_automatica" class="status-switch__input" type="checkbox" />
                <span class="status-switch__track"><span class="status-switch__thumb"></span></span>
                <span class="status-switch__label">{{ form.score_atualizacao_automatica ? 'Ativa' : 'Inativa' }}</span>
              </label>
              <button class="score-actions__run" :disabled="runningAutomations || saving" type="button" title="Executar rotina agora" aria-label="Executar rotina agora" @click="emit('run-automations')">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M8 5.14v13.72c0 .8.87 1.28 1.54.86l10.77-6.86a1 1 0 0 0 0-1.72L9.54 4.28A1 1 0 0 0 8 5.14Z" fill="currentColor" />
                </svg>
              </button>
            </div>
          </div>
          <div class="field-group field-group--span-3">
            <span>Agendamento automático</span>
            <div class="schedule-picker">
              <div class="schedule-picker__tokens">
                <span v-if="form.score_agendamentos.length === 0" class="schedule-picker__placeholder">Nenhum agendamento configurado.</span>
                <span v-for="(schedule, index) in form.score_agendamentos" :key="`score-${index}`" class="schedule-picker__token">
                  <span>{{ formatSchedule(schedule) }}</span>
                  <button type="button" class="schedule-picker__remove" :disabled="saving" @click="removeSchedule('score', index)">x</button>
                </span>
              </div>
              <button type="button" class="schedule-picker__add" :disabled="saving" @click="openScheduleModal('score')"><span class="schedule-picker__add-main">+</span></button>
            </div>
          </div>
          <div class="field-group field-group--span-3">
            <span>Execução</span>
            <div class="execution-strip">
              <div class="execution-strip__item execution-strip__item--status">
                <span class="schedule-status__badge" :class="statusBadgeClass(form.score_ultima_execucao_sucesso)">{{ statusLabel(form.score_ultima_execucao_sucesso) }}</span>
                <span class="execution-strip__text">{{ formatDateTime(form.score_atualizacao_ultima_execucao) }}</span>
              </div>
              <div class="execution-strip__item execution-strip__item--next">
                <span class="schedule-status__badge schedule-status__badge--warning">Próxima execução</span>
                <span class="execution-strip__text">{{ formatDateTime(form.score_atualizacao_proxima_execucao) }}</span>
              </div>
            </div>
            <div v-if="form.score_ultimo_erro" class="schedule-status">
              <span class="schedule-status__error">{{ form.score_ultimo_erro }}</span>
            </div>
          </div>
        </div>
          </section>

          <section class="settings-card settings-card--automation">
        <header class="settings-card__header settings-card__header--stacked">
          <div>
            <h3>Cobranças automáticas por WhatsApp</h3>
          </div>
        </header>

        <div class="settings-card__grid settings-card__grid--automation">
          <div class="field-group field-group--span-2">
            <span>Agendamento automático</span>
            <div class="schedule-picker">
              <div class="schedule-picker__tokens">
                <span v-if="form.whatsapp_agendamentos.length === 0" class="schedule-picker__placeholder">Nenhum agendamento configurado.</span>
                <span v-for="(schedule, index) in form.whatsapp_agendamentos" :key="`whatsapp-${index}`" class="schedule-picker__token">
                  <span>{{ formatSchedule(schedule) }}</span>
                  <button type="button" class="schedule-picker__remove" :disabled="saving" @click="removeSchedule('whatsapp', index)">x</button>
                </span>
              </div>
              <button type="button" class="schedule-picker__add" :disabled="saving" @click="openScheduleModal('whatsapp')"><span class="schedule-picker__add-main">+</span></button>
            </div>
            <div class="automation-controls-row">
              <label class="field-group automation-controls-row__field"><span>Dias antes</span><input v-model.number="form.whatsapp_cobranca_dias_antes" class="field" min="0" type="number" /></label>
              <label class="field-group automation-controls-row__field"><span>Dias após</span><input v-model.number="form.whatsapp_cobranca_dias_depois" class="field" min="0" type="number" /></label>
              <div class="score-actions automation-controls-row__actions">
                <label class="status-switch status-switch--compact" :class="form.whatsapp_cobranca_automatica ? 'status-switch--on' : 'status-switch--off'">
                  <input v-model="form.whatsapp_cobranca_automatica" class="status-switch__input" type="checkbox" />
                  <span class="status-switch__track"><span class="status-switch__thumb"></span></span>
                  <span class="status-switch__label">{{ form.whatsapp_cobranca_automatica ? 'Ativa' : 'Inativa' }}</span>
                </label>
                <button class="score-actions__run" :disabled="runningAutomations || saving" type="button" title="Executar rotina agora" aria-label="Executar rotina agora" @click="emit('run-automations')">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M8 5.14v13.72c0 .8.87 1.28 1.54.86l10.77-6.86a1 1 0 0 0 0-1.72L9.54 4.28A1 1 0 0 0 8 5.14Z" fill="currentColor" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div class="field-group field-group--span-2">
            <span>Execução</span>
            <div class="execution-strip">
              <div class="execution-strip__item execution-strip__item--status">
                <span class="schedule-status__badge" :class="statusBadgeClass(form.whatsapp_ultima_execucao_sucesso)">{{ statusLabel(form.whatsapp_ultima_execucao_sucesso) }}</span>
                <span class="execution-strip__text">{{ formatDateTime(form.whatsapp_cobranca_ultima_execucao) }}</span>
              </div>
              <div class="execution-strip__item execution-strip__item--next">
                <span class="schedule-status__badge schedule-status__badge--warning">Próxima execução</span>
                <span class="execution-strip__text">{{ formatDateTime(form.whatsapp_cobranca_proxima_execucao) }}</span>
              </div>
            </div>
            <div v-if="form.whatsapp_ultimo_erro" class="schedule-status">
              <span class="schedule-status__error">{{ form.whatsapp_ultimo_erro }}</span>
            </div>
          </div>
          <label class="field-group field-group--span-2"><span>Modelo da mensagem</span><textarea v-model="form.whatsapp_cobranca_modelo" class="field parameters-form__textarea"></textarea></label>
        </div>
          </section>
        </div>
      </div>

      <div class="form-actions form-actions--user field-group--span-2 parameters-form__actions">
        <button class="primary-button primary-button--success form-actions__button" :disabled="saving || loading" type="submit">{{ saving ? 'Salvando...' : 'Salvar' }}</button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="saving || loading" type="button" @click="emit('cancel')">Cancelar</button>
      </div>
    </form>

    <Teleport to="body">
      <div v-if="scheduleModal.open" class="modal-backdrop" @click.self="closeScheduleModal">
        <section class="modal-card modal-card--compact modal-card--profiles">
          <header class="panel__header panel__header--stacked">
            <p class="modal-context">Selecione um ou mais dias da semana e o horário para adicionar à rotina.</p>
          </header>
          <div class="modal-form">
            <div class="field-group">
              <span>Dias da semana</span>
              <div class="schedule-weekdays">
                <label v-for="day in weekdayOptions" :key="day.value" class="schedule-weekdays__item">
                  <input :checked="scheduleModal.dias_semana.includes(day.value)" type="checkbox" @change="toggleScheduleWeekday(day.value)" />
                  <span>{{ day.label }}</span>
                </label>
              </div>
            </div>
            <label class="field-group"><span>Horário</span><input v-model="scheduleModal.horario" class="field" type="time" /></label>
            <p v-if="scheduleModal.error" class="feedback feedback--error">{{ scheduleModal.error }}</p>
            <div class="form-actions"><button class="ghost-button" type="button" @click="closeScheduleModal">Cancelar</button><button class="primary-button" type="button" @click="saveScheduleModal">Adicionar</button></div>
          </div>
        </section>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="whatsappModal.open" class="modal-backdrop" @click.self="closeWhatsappModal">
        <section class="modal-card modal-card--whatsapp">
          <header class="panel__header panel__header--stacked">
            <div>
              <p class="eyebrow">Configuração da integração</p>
              <h3 class="panel__title">Parâmetros do WhatsApp</h3>
            </div>
          </header>
          <div class="modal-card__body modal-card__body--whatsapp">
            <div class="modal-form modal-form--whatsapp">
              <label class="field-group"><span>Usuário da API</span><input v-model="form.usuario_api_whatsapp" class="field" type="text" /></label>
              <label class="field-group">
                <span>Token da API</span>
                <div class="field-inline field-inline--token-generator">
                  <input v-model="form.token_api_whatsapp" class="field" type="text" />
                  <button class="token-generator-button" title="Gerar" aria-label="Gerar" type="button" @click="generateWhatsappToken">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path fill="currentColor" d="M14.5 3a5.5 5.5 0 0 0-5.45 4.75H4.75a2.75 2.75 0 1 0 0 5.5h.8a4 4 0 1 0 7.9 0h1.8a2.75 2.75 0 1 0 0-5.5h-.8A5.5 5.5 0 0 0 14.5 3Zm0 1.5a4 4 0 0 1 3.96 3.45.75.75 0 0 1-.74.8h-3.97a.75.75 0 0 0-.75.75v3.75a2.5 2.5 0 1 1-5 0V9.5a.75.75 0 0 0-.75-.75H4.75a1.25 1.25 0 1 1 0-2.5h4.97a.75.75 0 0 0 .74-.8A4 4 0 0 1 14.5 4.5Zm.75 5.75h3a1.25 1.25 0 1 1 0 2.5h-3v-2.5Z" />
                    </svg>
                  </button>
                </div>
              </label>
              <label class="field-group"><span>Sufixo</span><input v-model="form.sufixo_whatsapp" class="field" type="text" /></label>
              <label class="field-group"><span>País</span><input v-model.number="form.pais_whatsapp" class="field" min="1" type="number" /></label>
              <label class="field-group field-group--span-2"><span>Mensagem renovação</span><textarea v-model="form.msg_renovacao" class="field parameters-form__textarea"></textarea></label>
              <label class="field-group field-group--span-2"><span>Mensagem negociação</span><textarea v-model="form.msg_negociacao" class="field parameters-form__textarea"></textarea></label>
              <label class="field-group field-group--span-2"><span>Mensagem campanha</span><textarea v-model="form.msg_campanha" class="field parameters-form__textarea"></textarea></label>
              <label class="field-group field-group--span-2">
                <span>Regra nono dígito</span>
                <textarea v-model="whatsappModal.regraNonoDigito" class="field parameters-form__textarea parameters-form__textarea--code" placeholder='[{"campo":"DDD","operador":"between","valor":[11,29]}]'></textarea>
              </label>
              <div class="field-group field-group--span-2 whatsapp-modal__switches">
                <label class="status-switch" :class="form.ligar_websocket ? 'status-switch--on' : 'status-switch--off'">
                  <input v-model="form.ligar_websocket" class="status-switch__input" type="checkbox" />
                  <span class="status-switch__track"><span class="status-switch__thumb"></span></span>
                  <span class="status-switch__label">Ligar websocket</span>
                </label>
                <label class="status-switch" :class="form.silenciar_mensagem ? 'status-switch--on' : 'status-switch--off'">
                  <input v-model="form.silenciar_mensagem" class="status-switch__input" type="checkbox" />
                  <span class="status-switch__track"><span class="status-switch__thumb"></span></span>
                  <span class="status-switch__label">Silenciar mensagem</span>
                </label>
              </div>
              <p v-if="whatsappModal.error" class="feedback feedback--error">{{ whatsappModal.error }}</p>
            </div>
          </div>
          <footer class="form-actions modal-form__actions modal-form__actions--whatsapp">
            <button class="ghost-button" type="button" @click="closeWhatsappModal">Cancelar</button>
            <button class="primary-button" type="button" @click="saveWhatsappModal">Salvar</button>
          </footer>
        </section>
      </div>
    </Teleport>

    <p v-if="success" class="feedback feedback--success">{{ success }}</p>
    <p v-if="error" class="feedback feedback--error">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'

import type { BairroOption, CidadeOption, UFOption } from '@/models/location'
import type { Parameter, ParameterInput, ParameterNinthDigitRule, ParameterScheduleEntry } from '@/models/parameter'
import { listBairrosByCidade, listCitiesByUf, listUfs, lookupAddressByCep, lookupCepByAddress } from '@/services/locationService'
import { listWhatsappApiNames } from '@/services/parameterService'

const props = defineProps<{
  initialParameters?: Parameter | null
  loading: boolean
  saving: boolean
  runningAutomations: boolean
  error: string
  success: string
}>()

const emit = defineEmits<{
  submit: [payload: ParameterInput]
  cancel: []
  'run-automations': []
}>()

const ufs = ref<UFOption[]>([])
const cities = ref<CidadeOption[]>([])
const bairros = ref<BairroOption[]>([])
const apiWhatsappOptions = ref<string[]>([])
const citiesLoading = ref(false)
const bairrosLoading = ref(false)
const lookupLoading = ref(false)
const apiOptionsLoading = ref(false)
const lookupMessage = ref('')
let syncingForm = false
const weekdayOptions = [
  { value: 0, label: 'Seg' },
  { value: 1, label: 'Ter' },
  { value: 2, label: 'Qua' },
  { value: 3, label: 'Qui' },
  { value: 4, label: 'Sex' },
  { value: 5, label: 'Sáb' },
  { value: 6, label: 'Dom' },
] as const
const scheduleModal = reactive({ open: false, target: 'score' as 'score' | 'whatsapp', dias_semana: [] as number[], horario: '09:00', error: '' })
const whatsappModal = reactive({ open: false, regraNonoDigito: '[]', error: '' })

const form = reactive({
  nome_fantasia: '',
  razao_social: '',
  endereco: '',
  bairrosid: null as number | null,
  cep: '',
  nro: null as number | null,
  cnpj: '',
  uf: '',
  cidade_id: null as number | null,
  telefone1: '',
  flag_whatsapp_telefone1: false,
  telefone2: '',
  flag_whatsapp_telefone2: false,
  e_mail: '',
  responsavel: '',
  complemento: '',
  emitir_sons: true,
  score_valor_inicial: 1000,
  score_pontos_atraso_parcela: 15,
  score_pontos_atraso_quitacao_contrato: 30,
  score_pontos_pagamento_em_dia: 5,
  score_pontos_quitacao_em_dia: 20,
  score_atualizacao_automatica: false,
  score_agendamentos: [] as ParameterScheduleEntry[],
  score_atualizacao_ultima_execucao: '',
  score_atualizacao_proxima_execucao: '',
  score_ultima_execucao_sucesso: null as boolean | null,
  score_ultimo_erro: '',
  whatsapp_cobranca_automatica: false,
  whatsapp_agendamentos: [] as ParameterScheduleEntry[],
  whatsapp_cobranca_ultima_execucao: '',
  whatsapp_cobranca_proxima_execucao: '',
  whatsapp_ultima_execucao_sucesso: null as boolean | null,
  whatsapp_ultimo_erro: '',
  whatsapp_cobranca_dias_antes: 1,
  whatsapp_cobranca_dias_depois: 1,
  whatsapp_cobranca_modelo: '',
  api_whatsapp: '',
  usuario_api_whatsapp: '',
  token_api_whatsapp: '',
  regra_nono_dig_whats: [] as ParameterNinthDigitRule[],
  sufixo_whatsapp: '',
  msg_renovacao: '',
  msg_negociacao: '',
  pais_whatsapp: 55,
  msg_campanha: '',
  ligar_websocket: false,
  silenciar_mensagem: false,
})

onMounted(() => {
  void loadUfsOptions()
  void loadApiWhatsappOptions()
})

watch(
  () => props.initialParameters,
  (parameters) => {
    void syncParametersIntoForm(parameters)
  },
  { immediate: true },
)

watch(
  () => form.uf,
  (uf, previousUf) => {
    if (syncingForm) {
      return
    }

    form.cidade_id = null
    form.bairrosid = null
    bairros.value = []

    if (uf && uf !== previousUf) {
      void loadCitiesOptions(uf)
      return
    }

    cities.value = []
  },
)

watch(
  () => form.cidade_id,
  (cidadeId, previousCidadeId) => {
    if (syncingForm) {
      return
    }

    form.bairrosid = null
    if (cidadeId && cidadeId !== previousCidadeId) {
      void loadBairrosOptions(cidadeId)
      return
    }

    bairros.value = []
  },
)

async function submitForm() {
  await tryResolveCepByAddress()
  if (!applyWhatsappModalRules()) {
    whatsappModal.open = true
    return
  }
  emit('submit', buildPayload())
}

async function loadUfsOptions() {
  if (ufs.value.length > 0) {
    return
  }
  ufs.value = await listUfs()
}

async function loadApiWhatsappOptions() {
  apiOptionsLoading.value = true
  try {
    const options = await listWhatsappApiNames()
    apiWhatsappOptions.value = options
    if (form.api_whatsapp && !options.includes(form.api_whatsapp)) {
      apiWhatsappOptions.value = [...options, form.api_whatsapp].sort((left, right) => left.localeCompare(right))
    }
  } finally {
    apiOptionsLoading.value = false
  }
}

async function loadCitiesOptions(uf: string) {
  citiesLoading.value = true
  try {
    cities.value = await listCitiesByUf(uf)
  } finally {
    citiesLoading.value = false
  }
}

async function loadBairrosOptions(cidadeId: number) {
  bairrosLoading.value = true
  try {
    bairros.value = await listBairrosByCidade(cidadeId)
  } finally {
    bairrosLoading.value = false
  }
}

async function syncParametersIntoForm(parameters?: Parameter | null) {
  if (!parameters) {
    return
  }

  syncingForm = true
  await loadUfsOptions()

  form.nome_fantasia = parameters.nome_fantasia ?? ''
  form.razao_social = parameters.razao_social ?? ''
  form.endereco = parameters.endereco ?? ''
  form.bairrosid = null
  form.cep = formatCepValue(parameters.cep)
  form.nro = parameters.nro
  form.cnpj = formatCnpjValue(parameters.cnpj)
  form.uf = parameters.uf ?? ''
  form.cidade_id = null
  form.telefone1 = formatPhoneValue(parameters.telefone1)
  form.flag_whatsapp_telefone1 = parameters.flag_whatsapp_telefone1 ?? false
  form.telefone2 = formatPhoneValue(parameters.telefone2)
  form.flag_whatsapp_telefone2 = parameters.flag_whatsapp_telefone2 ?? false
  form.e_mail = parameters.e_mail ?? ''
  form.responsavel = parameters.responsavel ?? ''
  form.complemento = parameters.complemento ?? ''
  form.emitir_sons = parameters.emitir_sons
  form.score_valor_inicial = parameters.score_valor_inicial
  form.score_pontos_atraso_parcela = parameters.score_pontos_atraso_parcela
  form.score_pontos_atraso_quitacao_contrato = parameters.score_pontos_atraso_quitacao_contrato
  form.score_pontos_pagamento_em_dia = parameters.score_pontos_pagamento_em_dia
  form.score_pontos_quitacao_em_dia = parameters.score_pontos_quitacao_em_dia
  form.score_atualizacao_automatica = parameters.score_atualizacao_automatica
  form.score_agendamentos = [...parameters.score_agendamentos]
  form.score_atualizacao_ultima_execucao = parameters.score_atualizacao_ultima_execucao ?? ''
  form.score_atualizacao_proxima_execucao = parameters.score_atualizacao_proxima_execucao ?? ''
  form.score_ultima_execucao_sucesso = parameters.score_ultima_execucao_sucesso
  form.score_ultimo_erro = parameters.score_ultimo_erro ?? ''
  form.whatsapp_cobranca_automatica = parameters.whatsapp_cobranca_automatica
  form.whatsapp_agendamentos = [...parameters.whatsapp_agendamentos]
  form.whatsapp_cobranca_ultima_execucao = parameters.whatsapp_cobranca_ultima_execucao ?? ''
  form.whatsapp_cobranca_proxima_execucao = parameters.whatsapp_cobranca_proxima_execucao ?? ''
  form.whatsapp_ultima_execucao_sucesso = parameters.whatsapp_ultima_execucao_sucesso
  form.whatsapp_ultimo_erro = parameters.whatsapp_ultimo_erro ?? ''
  form.whatsapp_cobranca_dias_antes = parameters.whatsapp_cobranca_dias_antes
  form.whatsapp_cobranca_dias_depois = parameters.whatsapp_cobranca_dias_depois
  form.whatsapp_cobranca_modelo = parameters.whatsapp_cobranca_modelo ?? ''
  form.api_whatsapp = parameters.api_whatsapp ?? ''
  form.usuario_api_whatsapp = parameters.usuario_api_whatsapp ?? ''
  form.token_api_whatsapp = parameters.token_api_whatsapp ?? ''
  form.regra_nono_dig_whats = [...parameters.regra_nono_dig_whats]
  whatsappModal.regraNonoDigito = formatNinthDigitRules(parameters.regra_nono_dig_whats)
  form.sufixo_whatsapp = parameters.sufixo_whatsapp ?? ''
  form.msg_renovacao = parameters.msg_renovacao ?? ''
  form.msg_negociacao = parameters.msg_negociacao ?? ''
  form.pais_whatsapp = parameters.pais_whatsapp
  form.msg_campanha = parameters.msg_campanha ?? ''
  form.ligar_websocket = parameters.ligar_websocket
  form.silenciar_mensagem = parameters.silenciar_mensagem

  if (form.uf) {
    await loadCitiesOptions(form.uf)
  } else {
    cities.value = []
  }

  form.cidade_id = parameters.cidade_id ?? null

  if (form.cidade_id) {
    await loadBairrosOptions(form.cidade_id)
  } else {
    bairros.value = []
  }

  form.bairrosid = parameters.bairrosid ?? null
  syncingForm = false
}

async function handleCepBlur() {
  form.cep = formatCepValue(form.cep)
  if (cleanDigits(form.cep).length !== 8) {
    return
  }
  await applyLookupByCep()
}

async function handleCepLookupClick() {
  await applyLookupByCep()
}

async function applyLookupByCep() {
  const cep = cleanDigits(form.cep)
  if (cep.length !== 8) {
    lookupMessage.value = 'Informe um CEP válido para consulta.'
    return
  }

  lookupLoading.value = true
  try {
    const result = await lookupAddressByCep(cep)
    if (!result.found) {
      lookupMessage.value = 'CEP não encontrado. O cadastro pode continuar normalmente.'
      return
    }

    await applyLookupResult(result)
    lookupMessage.value = `Endereço localizado via ${result.source ?? 'serviço externo'}.`
  } catch {
    lookupMessage.value = 'Não foi possível consultar o CEP agora.'
  } finally {
    lookupLoading.value = false
  }
}

async function handleAddressBlur() {
  await tryResolveCepByAddress(true)
}

async function tryResolveCepByAddress(silent = false) {
  if (cleanDigits(form.cep).length === 8) {
    return
  }

  const selectedCity = cities.value.find((item) => item.cidade_id === form.cidade_id)
  const selectedBairro = bairros.value.find((item) => item.bairro_id === form.bairrosid)

  if (!form.uf || !selectedCity || !form.endereco.trim()) {
    return
  }

  lookupLoading.value = true
  try {
    const result = await lookupCepByAddress({
      uf: form.uf,
      cidade: selectedCity.cidade,
      logradouro: form.endereco,
      bairro: selectedBairro?.bairro_nome,
    })

    if (!result.found) {
      if (!silent) {
        lookupMessage.value = 'Endereço sem CEP localizado. Isso não impede o cadastro.'
      }
      return
    }

    await applyLookupResult(result)
    lookupMessage.value = ''
  } catch {
    if (!silent) {
      lookupMessage.value = 'Não foi possível localizar o CEP pelo endereço agora.'
    }
  } finally {
    lookupLoading.value = false
  }
}

async function applyLookupResult(result: {
  cep: string | null
  endereco: string | null
  complemento: string | null
  uf: string | null
  cidade_id: number | null
  bairro_id: number | null
}) {
  if (result.cep) {
    form.cep = formatCepValue(result.cep)
  }
  if (result.endereco && !form.endereco) {
    form.endereco = result.endereco
  }
  if (result.complemento && !form.complemento) {
    form.complemento = result.complemento
  }
  if (result.uf) {
    syncingForm = true
    form.uf = result.uf
    await loadCitiesOptions(result.uf)
    form.cidade_id = result.cidade_id ?? null
    if (form.cidade_id) {
      await loadBairrosOptions(form.cidade_id)
      form.bairrosid = result.bairro_id ?? null
    } else {
      bairros.value = []
      form.bairrosid = null
    }
    syncingForm = false
  }
}

function buildPayload(): ParameterInput {
  return {
    nome_fantasia: emptyToNull(form.nome_fantasia),
    razao_social: emptyToNull(form.razao_social),
    endereco: emptyToNull(form.endereco),
    bairrosid: form.bairrosid,
    cep: emptyToNull(cleanDigits(form.cep)),
    nro: form.nro,
    cnpj: emptyToNull(cleanDigits(form.cnpj)),
    uf: emptyToNull(form.uf),
    cidade_id: form.cidade_id,
    telefone1: emptyToNull(cleanDigits(form.telefone1)),
    flag_whatsapp_telefone1: form.flag_whatsapp_telefone1,
    telefone2: emptyToNull(cleanDigits(form.telefone2)),
    flag_whatsapp_telefone2: form.flag_whatsapp_telefone2,
    e_mail: emptyToNull(form.e_mail),
    responsavel: emptyToNull(form.responsavel),
    complemento: emptyToNull(form.complemento),
    emitir_sons: form.emitir_sons,
    score_valor_inicial: Number(form.score_valor_inicial || 0),
    score_pontos_atraso_parcela: Number(form.score_pontos_atraso_parcela || 0),
    score_pontos_atraso_quitacao_contrato: Number(form.score_pontos_atraso_quitacao_contrato || 0),
    score_pontos_pagamento_em_dia: Number(form.score_pontos_pagamento_em_dia || 0),
    score_pontos_quitacao_em_dia: Number(form.score_pontos_quitacao_em_dia || 0),
    score_atualizacao_automatica: form.score_atualizacao_automatica,
    score_agendamentos: [...form.score_agendamentos],
    whatsapp_cobranca_automatica: form.whatsapp_cobranca_automatica,
    whatsapp_agendamentos: [...form.whatsapp_agendamentos],
    whatsapp_cobranca_dias_antes: Number(form.whatsapp_cobranca_dias_antes || 0),
    whatsapp_cobranca_dias_depois: Number(form.whatsapp_cobranca_dias_depois || 0),
    whatsapp_cobranca_modelo: emptyToNull(form.whatsapp_cobranca_modelo),
    api_whatsapp: emptyToNull(form.api_whatsapp),
    usuario_api_whatsapp: emptyToNull(form.usuario_api_whatsapp),
    token_api_whatsapp: emptyToNull(form.token_api_whatsapp),
    regra_nono_dig_whats: [...form.regra_nono_dig_whats],
    sufixo_whatsapp: emptyToNull(form.sufixo_whatsapp),
    msg_renovacao: emptyToNull(form.msg_renovacao),
    msg_negociacao: emptyToNull(form.msg_negociacao),
    pais_whatsapp: Number(form.pais_whatsapp || 0),
    msg_campanha: emptyToNull(form.msg_campanha),
    ligar_websocket: form.ligar_websocket,
    silenciar_mensagem: form.silenciar_mensagem,
  }
}

function openScheduleModal(target: 'score' | 'whatsapp') {
  scheduleModal.open = true
  scheduleModal.target = target
  scheduleModal.dias_semana = []
  scheduleModal.horario = '09:00'
  scheduleModal.error = ''
}

function closeScheduleModal() {
  scheduleModal.open = false
  scheduleModal.error = ''
}

function openWhatsappModal() {
  whatsappModal.open = true
  whatsappModal.regraNonoDigito = formatNinthDigitRules(form.regra_nono_dig_whats)
  whatsappModal.error = ''
}

function closeWhatsappModal() {
  whatsappModal.open = false
  whatsappModal.error = ''
}

function saveWhatsappModal() {
  if (!applyWhatsappModalRules()) {
    return
  }
  emit('submit', buildPayload())
  closeWhatsappModal()
}

function applyWhatsappModalRules() {
  try {
    form.regra_nono_dig_whats = parseNinthDigitRules(whatsappModal.regraNonoDigito)
    whatsappModal.error = ''
    return true
  } catch (error) {
    whatsappModal.error = error instanceof Error ? error.message : 'Regra do nono dígito inválida.'
    return false
  }
}

function toggleScheduleWeekday(day: number) {
  if (scheduleModal.dias_semana.includes(day)) {
    scheduleModal.dias_semana = scheduleModal.dias_semana.filter((item) => item !== day)
    return
  }
  scheduleModal.dias_semana = [...scheduleModal.dias_semana, day].sort((left, right) => left - right)
}

function saveScheduleModal() {
  if (scheduleModal.dias_semana.length === 0) {
    scheduleModal.error = 'Selecione ao menos um dia da semana.'
    return
  }
  if (!scheduleModal.horario) {
    scheduleModal.error = 'Informe o horário do agendamento.'
    return
  }

  const nextEntries = scheduleModal.dias_semana.map((day) => ({ dias_semana: [day], horario: scheduleModal.horario }))
  if (scheduleModal.target === 'score') {
    form.score_agendamentos = dedupeSchedules([...form.score_agendamentos, ...nextEntries])
  } else {
    form.whatsapp_agendamentos = dedupeSchedules([...form.whatsapp_agendamentos, ...nextEntries])
  }
  closeScheduleModal()
}

function removeSchedule(target: 'score' | 'whatsapp', index: number) {
  if (target === 'score') {
    form.score_agendamentos = form.score_agendamentos.filter((_, itemIndex) => itemIndex !== index)
    return
  }
  form.whatsapp_agendamentos = form.whatsapp_agendamentos.filter((_, itemIndex) => itemIndex !== index)
}

function dedupeSchedules(items: ParameterScheduleEntry[]) {
  const seen = new Set<string>()
  return items.filter((item) => {
    const key = `${item.dias_semana.join(',')}-${item.horario}`
    if (seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
}

function formatSchedule(schedule: ParameterScheduleEntry) {
  const days = schedule.dias_semana.map((day) => weekdayOptions.find((item) => item.value === day)?.label ?? day).join(', ')
  return `${days} às ${schedule.horario}`
}

function statusLabel(value: boolean | null) {
  if (value === true) {
    return 'Realizada com sucesso'
  }
  if (value === false) {
    return 'Executada com erro'
  }
  return 'Ainda não executada'
}

function statusBadgeClass(value: boolean | null) {
  if (value === true) {
    return 'schedule-status__badge--success'
  }
  if (value === false) {
    return 'schedule-status__badge--error'
  }
  return 'schedule-status__badge--neutral'
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return 'Ainda não executado'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString('pt-BR')
}

function emptyToNull(value: string | null | undefined) {
  const normalized = value?.trim() ?? ''
  return normalized ? normalized : null
}

function cleanDigits(value: string | null | undefined) {
  return (value ?? '').replace(/\D/g, '')
}

function formatCepValue(value: string | null | undefined) {
  const digits = cleanDigits(value).slice(0, 8)
  if (digits.length <= 5) {
    return digits
  }
  return `${digits.slice(0, 5)}-${digits.slice(5)}`
}

function formatPhoneValue(value: string | null | undefined) {
  const digits = cleanDigits(value).slice(0, 11)
  if (digits.length <= 10) {
    return digits.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{4})(\d)/, '$1-$2')
  }
  return digits.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{5})(\d)/, '$1-$2')
}

function formatCnpjValue(value: string | null | undefined) {
  const digits = cleanDigits(value).slice(0, 14)
  return digits
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1/$2')
    .replace(/(\d{4})(\d{1,2})$/, '$1-$2')
}

function formatPhoneField(field: 'telefone1' | 'telefone2') {
  form[field] = formatPhoneValue(form[field])
}

function formatCnpj() {
  form.cnpj = formatCnpjValue(form.cnpj)
}

function formatNinthDigitRules(value: ParameterNinthDigitRule[] | null | undefined) {
  return JSON.stringify(value ?? [], null, 2)
}

function parseNinthDigitRules(value: string) {
  const normalized = value.trim()
  if (!normalized) {
    return []
  }
  const parsed = JSON.parse(normalized)
  if (!Array.isArray(parsed)) {
    throw new Error('A regra do nono dígito deve ser uma lista JSON.')
  }
  return parsed.map((item) => {
    if (!item || typeof item !== 'object') {
      throw new Error('Cada regra do nono dígito deve ser um objeto JSON.')
    }
    const campo = typeof item.campo === 'string' ? item.campo.trim() : ''
    const operador = typeof item.operador === 'string' ? item.operador.trim() : ''
    if (!campo || !operador) {
      throw new Error('Cada regra do nono dígito precisa de campo e operador.')
    }
    return { campo, operador, valor: 'valor' in item ? item.valor : null }
  })
}

function generateWhatsappToken() {
  form.token_api_whatsapp = crypto.randomUUID()
}
</script>

<style scoped>
.phone-field-row {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 0;
  align-items: stretch;
}

.phone-field-row .field {
  min-height: 34px;
  border-left: 0;
  border-radius: 0 3px 3px 0;
}

.phone-flag-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  min-height: 34px;
  border: 1px solid rgba(20, 184, 166, 0.22);
  border-radius: 3px 0 0 3px;
  background: rgba(226, 232, 240, 0.72);
  color: rgba(71, 85, 105, 0.9);
  cursor: pointer;
}

.phone-flag-button svg {
  width: 16px;
  height: 16px;
}

.phone-flag-button--active {
  background: rgba(22, 163, 74, 0.16);
  color: #15803d;
  border-color: rgba(22, 163, 74, 0.32);
}

.field-inline--popup {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.55rem;
}

.field-inline--token-generator {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 34px;
  gap: 0;
  align-items: stretch;
}

.field-inline--token-generator .field {
  border-right: 0;
  border-radius: 3px 0 0 3px;
}

.token-generator-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  min-height: 34px;
  border: 1px solid rgba(249, 115, 22, 0.22);
  border-radius: 0 3px 3px 0;
  background: rgba(255, 243, 234, 0.96);
  color: #c65a11;
  cursor: pointer;
}

.token-generator-button svg {
  width: 16px;
  height: 16px;
}

.token-generator-button:hover {
  background: rgba(255, 234, 220, 0.98);
}

.modal-card--whatsapp {
  width: min(760px, calc(100vw - 2rem));
  max-height: min(88vh, 820px);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
}

.modal-card__body--whatsapp {
  min-height: 0;
  overflow-y: auto;
  padding-right: 0.2rem;
}

.modal-form--whatsapp {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem 1rem;
}

.modal-form__actions--whatsapp {
  margin-top: 0.75rem;
  padding-top: 0.85rem;
  border-top: 1px solid rgba(133, 148, 166, 0.22);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(245, 248, 251, 0.98));
  justify-content: flex-end;
}

.whatsapp-modal__switches {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.parameters-form__textarea--code {
  min-height: 140px;
  font-family: Consolas, 'Courier New', monospace;
}
.settings-card {
  display: grid;
  gap: 1rem;
  padding: 1.1rem 1.2rem;
  border: 1px solid rgba(133, 148, 166, 0.2);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(245, 248, 251, 0.96));
}

.parameters-layout {
  display: grid;
  grid-template-columns: minmax(320px, 0.95fr) minmax(420px, 1.05fr);
  gap: 1rem;
  align-items: stretch;
}

.parameters-layout__side {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 1rem;
  height: 100%;
}

.settings-card--company {
  gap: 0.85rem;
}

.settings-card--company .settings-card__grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.7rem 0.85rem;
}

.settings-card--company .field-group--span-2 {
  grid-column: span 2;
}

.settings-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.settings-card__header--stacked {
  align-items: flex-start;
}

.settings-card__header h3 {
  margin: 0;
  font-size: 1rem;
}

.settings-card__header p {
  margin: 0.2rem 0 0;
  color: rgba(15, 23, 42, 0.68);
  font-size: 0.9rem;
}

.settings-card__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.95rem 1rem;
}

.settings-card--score .settings-card__grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.settings-card--automation .settings-card__grid {
  gap: 0.75rem 0.85rem;
}

.settings-card--automation {
  height: 100%;
}

.automation-controls-row {
  display: grid;
  grid-template-columns: minmax(140px, 1fr) minmax(140px, 1fr) max-content;
  gap: 0.5rem;
  align-items: end;
}

.automation-controls-row__actions {
  width: max-content;
  justify-self: end;
}

.automation-controls-row__field {
  min-width: 0;
}

.automation-controls-row__field .field {
  width: 100%;
}

.field-group--span-3 {
  grid-column: span 3;
}

.field-group--score-toggle {
  display: grid;
  align-content: start;
  gap: 0.45rem;
  min-width: 0;
}

.field-group--score-toggle .score-actions {
  grid-template-columns: minmax(0, 1fr) 42px;
  width: 100%;
}

.score-actions {
  display: grid;
  grid-template-columns: 108px 42px;
  gap: 0.45rem;
  width: max-content;
}

.status-switch--compact {
  min-height: 34px;
  padding-right: 0.45rem;
}

.status-switch--compact .status-switch__label {
  font-size: 0.78rem;
}

.score-actions__run {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  min-height: 34px;
  border: 1px solid rgba(249, 115, 22, 0.18);
  border-radius: 6px;
  background: rgba(249, 115, 22, 0.12);
  color: rgba(216, 90, 4, 0.92);
  cursor: pointer;
}

.score-actions__run svg {
  width: 16px;
  height: 16px;
}

.score-actions__run:hover {
  background: rgba(249, 115, 22, 0.18);
}

.score-actions__run:disabled {
  opacity: 0.55;
  cursor: default;
}

.settings-card__feedback {
  margin: 0;
}

.schedule-picker {
  display: flex;
  align-items: stretch;
  min-height: 34px;
  border: 1px solid rgba(85, 103, 122, 0.14);
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.92);
  overflow: hidden;
}

.schedule-picker__tokens {
  flex: 1 1 auto;
  min-width: 0;
  padding: 3px 6px;
  display: flex;
  flex-wrap: nowrap;
  gap: 0.35rem;
  align-items: center;
  overflow-x: auto;
}

.schedule-picker__placeholder {
  color: rgba(15, 23, 42, 0.55);
  font-size: 12px;
  white-space: nowrap;
}

.schedule-picker__token {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.18rem 0.42rem;
  border-radius: 3px;
  background: #e8f3ea;
  color: #123524;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.schedule-picker__remove {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-weight: 700;
  line-height: 1;
  padding: 0;
}

.schedule-picker__add {
  flex: 0 0 34px;
  width: 34px;
  border: 0;
  border-left: 1px solid rgba(249, 115, 22, 0.16);
  background: rgba(249, 115, 22, 0.12);
  color: rgba(216, 90, 4, 0.92);
  cursor: pointer;
}

.schedule-picker__add-main {
  font-size: 18px;
  font-weight: 800;
}

.schedule-status {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.schedule-status__badge {
  display: inline-flex;
  align-items: center;
  padding: 0.26rem 0.55rem;
  border-radius: 3px;
  font-size: 0.74rem;
  font-weight: 700;
}

.schedule-status__badge--success { background: rgba(22, 163, 74, 0.16); color: #166534; }
.schedule-status__badge--error { background: rgba(220, 38, 38, 0.16); color: #991b1b; }
.schedule-status__badge--neutral { background: rgba(100, 116, 139, 0.14); color: #334155; }
.schedule-status__badge--warning { background: rgba(249, 115, 22, 0.16); color: #c2410c; }

.schedule-status__error {
  color: #991b1b;
  font-size: 0.82rem;
}

.execution-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.execution-strip__item {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-height: 34px;
  padding: 0.45rem 0.65rem;
  border-radius: 3px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.82);
}

.execution-strip__item--next {
  justify-content: flex-end;
  background: rgba(255, 247, 237, 0.92);
  border-color: rgba(249, 115, 22, 0.18);
}

.execution-strip__text {
  font-size: 0.82rem;
  color: rgba(15, 23, 42, 0.78);
  font-weight: 600;
}

.schedule-weekdays {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.5rem;
}

.schedule-weekdays__item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.field-inline--schedule {
  align-items: center;
}

.field-inline__suffix {
  font-size: 0.85rem;
  color: rgba(15, 23, 42, 0.62);
}

.parameters-form__textarea {
  min-height: 88px;
  resize: vertical;
}

.parameters-form__actions {
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .parameters-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .execution-strip {
    grid-template-columns: minmax(0, 1fr);
  }

  .automation-controls-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .execution-strip__item--next {
    justify-content: flex-start;
  }

  .settings-card__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .settings-card__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>