<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <p class="eyebrow">Cadastro de usuários</p>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="submitForm">
      <label class="field-group">
        <span>Nome</span>
        <input v-model="form.nome" class="field" required type="text" />
      </label>

      <label class="field-group">
        <span>Login</span>
        <div class="field-inline field-inline--login">
          <input v-model="form.login" class="field" required type="text" />
          <label class="status-switch" :class="form.ativo ? 'status-switch--on' : 'status-switch--off'">
            <input v-model="form.ativo" class="status-switch__input" type="checkbox" />
            <span class="status-switch__track">
              <span class="status-switch__thumb"></span>
            </span>
            <span class="status-switch__label">{{ form.ativo ? 'Ativo' : 'Inativo' }}</span>
          </label>
        </div>
      </label>

      <label class="field-group">
        <span>E-mail</span>
        <input v-model="form.email" class="field" required type="email" />
      </label>

      <label class="field-group">
        <span>Senha {{ mode === 'edit' ? '(opcional)' : '' }}</span>
        <input v-model="form.senha" class="field" :required="mode === 'create'" type="password" />
      </label>

      <label class="field-group">
        <span>Função</span>
        <select v-model="form.funcao" class="field">
          <option v-for="option in functionOptions" :key="option" :value="option">{{ option }}</option>
        </select>
      </label>

      <div class="field-group">
        <span>Perfis parametrizados</span>
        <div class="profile-picker">
          <div class="profile-picker__tokens">
            <span v-if="selectedProfiles.length === 0" class="profile-picker__placeholder">Nenhum perfil selecionado.</span>
            <span v-for="profile in selectedProfiles" :key="profile.id" class="profile-picker__token">
              <span>{{ profile.nome }}</span>
              <button type="button" class="profile-picker__remove" :disabled="saving" @click="removeProfile(profile.id)">x</button>
            </span>
          </div>
          <button
            type="button"
            class="profile-picker__add"
            :disabled="saving"
            aria-label="Adicionar perfil"
            title="Adicionar perfil"
            @click="openProfileModal"
          >
              <span class="profile-picker__add-main">+</span>
          </button>
        </div>
      </div>

      <label class="field-group">
        <span>Telefone</span>
        <input v-model="form.telefone" class="field" type="text" />
      </label>

      <label class="field-group">
        <span>Celular</span>
        <div class="field-inline field-inline--cellphone field-inline--cellphone-user">
          <label
            class="whatsapp-toggle"
            :class="form.flag_whatsapp ? 'whatsapp-toggle--on' : 'whatsapp-toggle--off'"
            title="WhatsApp"
            aria-label="WhatsApp"
          >
            <input v-model="form.flag_whatsapp" class="whatsapp-toggle__input" type="checkbox" />
            <span class="whatsapp-toggle__icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" focusable="false">
                <path
                  d="M12 2.2a9.6 9.6 0 0 0-8.29 14.46L2.5 21.5l4.97-1.19A9.6 9.6 0 1 0 12 2.2Zm0 17.29a7.64 7.64 0 0 1-3.89-1.06l-.28-.17-2.95.7.78-2.88-.18-.29a7.64 7.64 0 1 1 6.52 3.7Zm4.19-5.7c-.23-.12-1.35-.66-1.56-.73-.21-.08-.36-.12-.51.12-.15.23-.59.73-.72.89-.13.15-.27.17-.5.06-.23-.12-.99-.36-1.88-1.16-.69-.61-1.16-1.37-1.3-1.6-.13-.23-.01-.35.1-.47.1-.1.23-.27.34-.4.11-.13.14-.23.22-.39.07-.15.04-.29-.02-.41-.06-.12-.51-1.23-.7-1.69-.18-.44-.37-.38-.51-.39h-.43c-.15 0-.39.06-.6.29-.21.23-.8.78-.8 1.9 0 1.11.82 2.19.93 2.34.12.15 1.59 2.43 3.86 3.4.54.23.95.37 1.27.47.53.17 1.02.15 1.4.09.43-.06 1.35-.55 1.54-1.08.19-.53.19-.98.13-1.08-.05-.1-.2-.15-.43-.27Z"
                  fill="currentColor"
                />
              </svg>
            </span>
          </label>
          <input v-model="form.celular" class="field" type="text" @blur="formatPhoneField('celular')" />
        </div>
      </label>

      <label class="field-group">
        <span>CPF</span>
        <input v-model="form.cpf" class="field" type="text" @blur="formatCpf" />
      </label>

      <label class="field-group">
        <span>RG</span>
        <input v-model="form.rg" class="field" type="text" />
      </label>

      <label class="field-group">
        <span>Data de nascimento</span>
        <input v-model="form.data_nascimento" class="field" type="date" />
      </label>

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
        <select v-model.number="form.cidade_id" class="field" :disabled="!form.uf || citiesLoading">
          <option :value="null">Selecione</option>
          <option v-for="option in cities" :key="option.cidade_id" :value="option.cidade_id">{{ option.cidade }}</option>
        </select>
      </label>

      <label class="field-group">
        <span>Bairro</span>
        <select :value="bairroSelectValue" class="field field--bairro-select" :disabled="!form.uf || !form.cidade_id || bairrosLoading" @change="handleBairroSelectChange">
          <option value="">Selecione</option>
          <option value="__new__">&gt;&gt;&gt;&gt;Cadastrar Novo&lt;&lt;&lt;&lt;</option>
          <option v-for="option in bairros" :key="option.bairro_id" :value="String(option.bairro_id)">{{ option.bairro_nome }}</option>
        </select>
      </label>

      <label class="field-group field-group--span-2">
        <span>Endereco</span>
        <input v-model="form.endereco" class="field" type="text" @blur="handleAddressBlur" />
      </label>

      <label class="field-group">
        <span>Numero</span>
        <input v-model="form.numero" class="field" type="text" @blur="handleAddressBlur" />
      </label>

      <label class="field-group">
        <span>Complemento</span>
        <input v-model="form.complemento" class="field" type="text" />
      </label>

      <div class="form-actions form-actions--user">
        <button class="primary-button primary-button--success form-actions__button" :disabled="saving" type="submit">
          {{ saving ? 'Salvando...' : 'Salvar' }}
        </button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="saving" type="button" @click="emit('cancel')">Cancelar</button>
      </div>

      <Teleport to="body">
        <div v-if="profileModal.open" class="modal-backdrop" @click.self="closeProfileModal">
          <section class="modal-card modal-card--compact modal-card--profiles">
            <header class="panel__header panel__header--stacked">
              <div>
                <h3 class="panel__title">Selecionar perfis</h3>
              </div>
              <p class="modal-context">Escolha um ou mais perfis para compor as permissões do usuário.</p>
            </header>

            <div class="modal-form">
              <label class="field-group">
                <span>Buscar perfil</span>
                <input v-model="profileModal.term" class="field" type="text" placeholder="Digite parte do nome" />
              </label>

              <div class="profile-modal-list">
                <label v-for="profile in filteredProfiles" :key="profile.id" class="profile-modal-list__item">
                  <input :checked="form.perfil_ids.includes(profile.id)" type="checkbox" @change="toggleProfile(profile.id)" />
                  <div>
                    <strong>{{ profile.nome }}</strong>
                    <p v-if="profile.descricao" class="profile-modal-list__description">{{ profile.descricao }}</p>
                  </div>
                </label>
                <p v-if="filteredProfiles.length === 0" class="profile-modal-list__empty">Nenhum perfil encontrado.</p>
              </div>

              <div class="form-actions">
                <button class="ghost-button" type="button" @click="closeProfileModal">Fechar</button>
              </div>
            </div>
          </section>
        </div>

        <div v-if="bairroModal.open" class="modal-backdrop" @click.self="closeBairroModal">
          <section class="modal-card modal-card--compact">
            <header class="panel__header panel__header--stacked">
              <div>
                <h3 class="panel__title">Cadastro de Bairro</h3>
              </div>
              <p class="modal-context">{{ form.uf || 'UF' }}-{{ selectedCityLabel }}</p>
            </header>

            <form class="modal-form" @submit.prevent="submitBairroModal">
              <label class="field-group">
                <span>Nome do Bairro</span>
                <input v-model="bairroModal.nome" class="field" required type="text" />
              </label>

              <p v-if="bairroModal.error" class="feedback feedback--error">{{ bairroModal.error }}</p>

              <div class="form-actions">
                <button class="ghost-button" :disabled="bairroModal.saving" type="button" @click="closeBairroModal">Cancelar</button>
                <button class="primary-button" :disabled="bairroModal.saving" type="submit">
                  {{ bairroModal.saving ? 'Salvando...' : 'Salvar' }}
                </button>
              </div>
            </form>
          </section>
        </div>
      </Teleport>
    </form>

    <p v-if="lookupMessage" class="feedback feedback--info">{{ lookupMessage }}</p>
    <p v-if="success" class="feedback feedback--success">{{ success }}</p>
    <p v-if="error" class="feedback feedback--error">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import type { Profile } from '@/models/accessControl'
import type { BairroOption, CidadeOption, UFOption } from '@/models/location'
import type { User, UserCreateInput, UserUpdateInput } from '@/models/user'
import { errorAlert, successAlert } from '@/services/alertService'
import { listProfiles } from '@/services/accessControlService'
import { createBairro, listBairrosByCidade, listCitiesByUf, listUfs, lookupAddressByCep, lookupCepByAddress } from '@/services/locationService'

const props = defineProps<{
  mode: 'create' | 'edit'
  saving: boolean
  error: string
  success: string
  initialUser?: User | null
}>()

const emit = defineEmits<{
  submit: [payload: UserCreateInput | UserUpdateInput]
  cancel: []
}>()

const ufs = ref<UFOption[]>([])
const profiles = ref<Profile[]>([])
const cities = ref<CidadeOption[]>([])
const bairros = ref<BairroOption[]>([])
const citiesLoading = ref(false)
const bairrosLoading = ref(false)
const lookupLoading = ref(false)
const lookupMessage = ref('')
let syncingForm = false
const bairroModal = reactive({ open: false, nome: '', saving: false, error: '' })
const profileModal = reactive({ open: false, term: '' })
const functionOptions = ['Administrador', 'Cobrador', 'Operador', 'Vendedor'] as const

const form = reactive({
  nome: '',
  login: '',
  email: '',
  senha: '',
  funcao: 'Operador' as User['funcao'],
  perfil_ids: [] as number[],
  telefone: '',
  celular: '',
  flag_whatsapp: false,
  cep: '',
  endereco: '',
  numero: '',
  complemento: '',
  bairro_id: null as number | null,
  cidade_id: null as number | null,
  uf: '',
  cpf: '',
  rg: '',
  data_nascimento: '',
  ativo: true,
})

const bairroSelectValue = computed(() => (form.bairro_id === null ? '' : String(form.bairro_id)))
const selectedCityLabel = computed(() => cities.value.find((item) => item.cidade_id === form.cidade_id)?.cidade ?? 'Nao selecionada')
const selectedProfiles = computed(() =>
  form.perfil_ids.map((profileId) => profiles.value.find((profile) => profile.id === profileId)).filter((profile): profile is Profile => Boolean(profile)),
)
const filteredProfiles = computed(() => {
  const term = profileModal.term.trim().toLowerCase()
  if (!term) {
    return profiles.value
  }

  return profiles.value.filter((profile) => {
    const haystack = `${profile.nome} ${profile.descricao ?? ''}`.toLowerCase()
    return haystack.includes(term)
  })
})

onMounted(() => {
  void loadUfsOptions()
  void loadProfilesOptions()
})

watch(
  () => props.initialUser,
  (user) => {
    void syncUserIntoForm(user)
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
    form.bairro_id = null
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

    form.bairro_id = null
    if (cidadeId && cidadeId !== previousCidadeId) {
      void loadBairrosOptions(cidadeId)
      return
    }

    bairros.value = []
  },
)

async function submitForm() {
  await tryResolveCepByAddress()

  if (props.mode === 'create') {
    emit('submit', buildCreatePayload())
  } else {
    emit('submit', buildUpdatePayload())
  }

  if (!props.error && props.mode === 'create') {
    resetForm()
  }
}

async function loadUfsOptions() {
  if (ufs.value.length > 0) {
    return
  }

  ufs.value = await listUfs()
}

async function loadProfilesOptions() {
  profiles.value = await listProfiles()
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

async function syncUserIntoForm(user?: User | null) {
  if (!user) {
    if (props.mode === 'create') {
      resetForm()
    }
    return
  }

  syncingForm = true
  await loadUfsOptions()

  form.nome = user.nome
  form.login = user.login
  form.email = user.email
  form.senha = ''
  form.funcao = normalizeFunctionValue(user.funcao)
  form.perfil_ids = user.perfil_ids.length > 0 ? [...user.perfil_ids] : user.perfil_id ? [user.perfil_id] : []
  form.telefone = user.telefone ?? ''
  form.celular = user.celular ?? ''
  form.flag_whatsapp = user.flag_whatsapp
  form.cep = formatCepValue(user.cep)
  form.endereco = user.endereco ?? ''
  form.numero = user.numero ?? ''
  form.complemento = user.complemento ?? ''
  form.uf = user.uf ?? ''
  form.cpf = formatCpfValue(user.cpf)
  form.rg = user.rg ?? ''
  form.data_nascimento = user.data_nascimento ?? ''
  form.ativo = user.ativo

  if (form.uf) {
    await loadCitiesOptions(form.uf)
  } else {
    cities.value = []
  }

  form.cidade_id = user.cidade_id ?? null

  if (form.cidade_id) {
    await loadBairrosOptions(form.cidade_id)
  } else {
    bairros.value = []
  }

  form.bairro_id = user.bairro_id ?? null
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

async function handleAddressBlur() {
  await tryResolveCepByAddress(true)
}

async function tryResolveCepByAddress(silent = false) {
  if (cleanDigits(form.cep).length === 8) {
    return
  }

  const selectedCity = cities.value.find((item) => item.cidade_id === form.cidade_id)
  const selectedBairro = bairros.value.find((item) => item.bairro_id === form.bairro_id)

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
        lookupMessage.value = 'Endereco sem CEP localizado. Isso nao impede o cadastro.'
      }
      return
    }

    await applyLookupResult(result)
    lookupMessage.value = ''
  } catch {
    if (!silent) {
      lookupMessage.value = 'Nao foi possivel localizar o CEP pelo endereco agora.'
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
      form.bairro_id = result.bairro_id ?? null
    } else {
      bairros.value = []
      form.bairro_id = null
    }
    syncingForm = false
  }
}

function buildBasePayload() {
  return {
    nome: form.nome,
    login: form.login,
    email: form.email,
    funcao: normalizeFunctionValue(form.funcao),
    perfil_ids: [...form.perfil_ids],
    telefone: emptyToNull(form.telefone),
    celular: emptyToNull(form.celular),
    flag_whatsapp: form.flag_whatsapp,
    cep: emptyToNull(cleanDigits(form.cep)),
    endereco: emptyToNull(form.endereco),
    numero: emptyToNull(form.numero),
    complemento: emptyToNull(form.complemento),
    bairro_id: form.bairro_id,
    cidade_id: form.cidade_id,
    uf: emptyToNull(form.uf),
    cpf: emptyToNull(cleanDigits(form.cpf)),
    rg: emptyToNull(form.rg),
    data_nascimento: emptyToNull(form.data_nascimento),
    ativo: form.ativo,
  }
}

function buildCreatePayload(): UserCreateInput {
  return {
    ...buildBasePayload(),
    senha: form.senha,
  }
}

function buildUpdatePayload(): UserUpdateInput {
  const payload: UserUpdateInput = buildBasePayload()
  if (form.senha) {
    payload.senha = form.senha
  }
  return payload
}

function resetForm() {
  form.nome = ''
  form.login = ''
  form.email = ''
  form.senha = ''
  form.funcao = 'Operador'
  form.perfil_ids = []
  form.telefone = ''
  form.celular = ''
  form.flag_whatsapp = false
  form.cep = ''
  form.endereco = ''
  form.numero = ''
  form.complemento = ''
  form.bairro_id = null
  form.cidade_id = null
  form.uf = ''
  form.cpf = ''
  form.rg = ''
  form.data_nascimento = ''
  form.ativo = true
  cities.value = []
  bairros.value = []
  lookupMessage.value = ''
}

function emptyToNull(value: string | null | undefined) {
  const normalized = value?.trim() ?? ''
  return normalized ? normalized : null
}

function normalizeFunctionValue(value: string | null | undefined) {
  if (!value) {
    return 'Operador'
  }

  if (value === 'admin') {
    return 'Administrador'
  }

  if (value === 'usuario') {
    return 'Operador'
  }

  return value
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

function formatCpfValue(value: string | null | undefined) {
  const digits = cleanDigits(value).slice(0, 11)
  return digits
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2')
}

function formatPhoneValue(value: string | null | undefined) {
  const digits = cleanDigits(value).slice(0, 11)
  if (digits.length <= 10) {
    return digits
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d)/, '$1-$2')
  }

  return digits
    .replace(/(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d)/, '$1-$2')
}

function formatCpf() {
  form.cpf = formatCpfValue(form.cpf)
}

function formatPhoneField(field: 'telefone' | 'celular') {
  form[field] = formatPhoneValue(form[field])
}

function handleBairroSelectChange(event: Event) {
  const target = event.target as HTMLSelectElement
  if (target.value === '__new__') {
    if (!form.uf || !form.cidade_id) {
      lookupMessage.value = 'Selecione primeiro a UF e a cidade para cadastrar um novo bairro.'
      form.bairro_id = null
      return
    }

    openBairroModal()
    return
  }

  form.bairro_id = target.value ? Number(target.value) : null
}

function openProfileModal() {
  profileModal.open = true
  profileModal.term = ''
}

function closeProfileModal() {
  profileModal.open = false
  profileModal.term = ''
}

function toggleProfile(profileId: number) {
  if (form.perfil_ids.includes(profileId)) {
    removeProfile(profileId)
    return
  }

  form.perfil_ids = [...form.perfil_ids, profileId]
}

function removeProfile(profileId: number) {
  form.perfil_ids = form.perfil_ids.filter((item) => item !== profileId)
}

function openBairroModal() {
  bairroModal.open = true
  bairroModal.nome = ''
  bairroModal.error = ''
}

function closeBairroModal() {
  bairroModal.open = false
  bairroModal.nome = ''
  bairroModal.error = ''
}

async function submitBairroModal() {
  if (!form.cidade_id) {
    bairroModal.error = 'Selecione uma cidade antes de cadastrar o bairro.'
    return
  }

  bairroModal.saving = true
  bairroModal.error = ''
  try {
    const created = await createBairro({ cidade_id: form.cidade_id, bairro_nome: bairroModal.nome })
    await loadBairrosOptions(form.cidade_id)
    form.bairro_id = created.bairro_id
    closeBairroModal()
    await successAlert('Bairro cadastrado com sucesso.', 'create')
  } catch (error) {
    bairroModal.error = error instanceof Error ? error.message : 'Falha ao salvar bairro'
    await errorAlert(bairroModal.error)
  } finally {
    bairroModal.saving = false
  }
}
</script>

<style scoped>
.profile-picker {
  display: flex;
  align-items: stretch;
  min-height: 34px;
  height: 34px;
  border: 1px solid rgba(85, 103, 122, 0.14);
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.92);
  overflow: hidden;
}

.profile-picker__tokens {
  flex: 1 1 auto;
  min-width: 0;
  padding: 3px 6px;
  display: flex;
  flex-wrap: nowrap;
  gap: 0.35rem;
  align-items: center;
  overflow-x: auto;
  overflow-y: hidden;
}

.profile-picker__placeholder {
  color: rgba(15, 23, 42, 0.55);
  font-size: 12px;
  white-space: nowrap;
}

.profile-picker__token {
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

.profile-picker__remove {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-weight: 700;
  line-height: 1;
  padding: 0;
}

.profile-picker__add {
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  border: 0;
  border-left: 1px solid rgba(249, 115, 22, 0.16);
  background: rgba(249, 115, 22, 0.12);
  color: rgba(216, 90, 4, 0.92);
  cursor: pointer;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.profile-picker__add:hover {
  background: rgba(249, 115, 22, 0.18);
}

.profile-picker__add-main {
  font-size: 18px;
  font-weight: 800;
}

.profile-picker__add:disabled,
.profile-picker__remove:disabled {
  cursor: default;
  opacity: 0.55;
}

select.field {
  height: 34px;
}

.modal-card--profiles {
  max-width: 34rem;
}

.profile-modal-list {
  display: grid;
  gap: 0.65rem;
  max-height: 20rem;
  overflow-y: auto;
}

.profile-modal-list__item {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.8rem;
  align-items: start;
  padding: 0.8rem 0.9rem;
  border-radius: 0.9rem;
  background: rgba(15, 23, 42, 0.04);
}

.profile-modal-list__description {
  margin: 0.2rem 0 0;
  color: rgba(15, 23, 42, 0.62);
  font-size: 0.92rem;
}

.profile-modal-list__empty {
  margin: 0;
  text-align: center;
  color: rgba(15, 23, 42, 0.55);
}

.field-inline--cellphone-user {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 0;
  align-items: stretch;
}

.field-inline--cellphone-user .field {
  min-height: 34px;
  border-left: 0;
  border-radius: 0 3px 3px 0;
}

.field-inline--cellphone-user .whatsapp-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  min-height: 34px;
  border-radius: 3px 0 0 3px;
}

.field-inline--cellphone-user .whatsapp-toggle__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.field-inline--cellphone-user .whatsapp-toggle__icon svg {
  width: 16px;
  height: 16px;
}
</style>
