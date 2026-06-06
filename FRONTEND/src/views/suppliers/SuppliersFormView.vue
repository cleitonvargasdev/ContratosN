<template>
  <section class="panel form-panel">
    <header class="panel__header panel__header--stacked">
      <div>
        <h2 class="panel__title">{{ isEdit ? 'Editar fornecedor' : 'Novo fornecedor' }}</h2>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label class="field-group field-group--span-2">
        <span>Nome</span>
        <input v-model="form.nome" class="field" required type="text" />
      </label>
      <label class="field-group">
        <span>CPF/CNPJ</span>
        <input v-model="form.cpf_cnpj" class="field" maxlength="18" type="text" @blur="formatDocumentField" />
      </label>
      <label class="field-group">
        <span>Telefone</span>
        <input v-model="form.telefone" class="field" maxlength="15" type="text" @blur="formatPhoneField" />
      </label>
      <label class="field-group field-group--span-2">
        <span>E-mail</span>
        <input v-model="form.email" class="field" type="email" />
      </label>
      <label class="field-group">
        <span>CEP</span>
        <div class="field-inline">
          <input v-model="form.cep" class="field" maxlength="9" type="text" @blur="handleCepBlur" />
          <button class="secondary-button" :disabled="lookupLoading || suppliers.state.saving" type="button" @click="handleCepLookupClick">
            {{ lookupLoading ? 'Consultando...' : 'Buscar CEP' }}
          </button>
        </div>
      </label>
      <label class="field-group">
        <span>UF</span>
        <input v-model="form.uf" class="field" maxlength="2" type="text" />
      </label>
      <label class="field-group field-group--span-2">
        <span>Cidade</span>
        <input v-model="form.cidade" class="field" type="text" />
      </label>
      <label class="field-group field-group--span-2">
        <span>Bairro</span>
        <input v-model="form.bairro" class="field" type="text" />
      </label>
      <label class="field-group field-group--span-2">
        <span>Endereço</span>
        <input v-model="form.endereco" class="field" type="text" @blur="handleAddressBlur" />
      </label>
      <label class="field-group">
        <span>Número</span>
        <input v-model="form.numero" class="field" type="text" />
      </label>
      <label class="field-group">
        <span>Complemento</span>
        <input v-model="form.complemento" class="field" type="text" />
      </label>
      <label class="field-group field-group--span-2">
        <span>Observação</span>
        <textarea v-model="form.observacao" class="field field--textarea" rows="4"></textarea>
      </label>
      <label class="field-group field-group--span-2 toggle-row">
        <input v-model="form.ativo" type="checkbox" />
        <span>{{ form.ativo ? 'Fornecedor ativo' : 'Fornecedor inativo' }}</span>
      </label>
      <div class="form-actions form-actions--user field-group--span-2">
        <button class="primary-button primary-button--success form-actions__button" :disabled="suppliers.state.saving" type="submit">
          {{ suppliers.state.saving ? 'Salvando...' : 'Salvar' }}
        </button>
        <button class="ghost-button ghost-button--danger form-actions__button" :disabled="suppliers.state.saving" type="button" @click="router.push({ name: 'suppliers-list' })">Cancelar</button>
      </div>
    </form>

    <p v-if="suppliers.state.error" class="feedback feedback--error">{{ suppliers.state.error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useSuppliersController } from '@/controllers/useSuppliersController'
import type { SupplierInput } from '@/models/supplier'
import { errorAlert, successAlert } from '@/services/alertService'
import { lookupAddressByCep, lookupCepByAddress } from '@/services/locationService'

const suppliers = useSuppliersController()
const route = useRoute()
const router = useRouter()

const isEdit = computed(() => Boolean(route.params.id))
const lookupLoading = ref(false)

const form = reactive<SupplierInput>({
  nome: '',
  cpf_cnpj: null,
  telefone: null,
  email: null,
  cep: null,
  endereco: null,
  numero: null,
  complemento: null,
  bairro: null,
  cidade: null,
  uf: null,
  ativo: true,
  observacao: null,
})

onMounted(async () => {
  if (!isEdit.value) return
  try {
    await suppliers.loadSupplier(Number(route.params.id))
    const current = suppliers.state.currentSupplier
    if (!current) return
    form.nome = current.nome ?? ''
    form.cpf_cnpj = current.cpf_cnpj
    form.telefone = current.telefone
    form.email = current.email
    form.cep = formatCepValue(current.cep)
    form.endereco = current.endereco
    form.numero = current.numero
    form.complemento = current.complemento
    form.bairro = current.bairro
    form.cidade = current.cidade
    form.uf = current.uf
    form.ativo = current.ativo
    form.observacao = current.observacao
    formatDocumentField()
    formatPhoneField()
  } catch {
    await router.replace({ name: 'suppliers-list' })
  }
})

async function handleSubmit() {
  const payload: SupplierInput = {
    nome: (form.nome ?? '').trim() || null,
    cpf_cnpj: emptyToNull(cleanDigits(form.cpf_cnpj)),
    telefone: emptyToNull(cleanDigits(form.telefone)),
    email: form.email?.trim() || null,
    cep: emptyToNull(cleanDigits(form.cep)),
    endereco: emptyToNull(form.endereco),
    numero: emptyToNull(form.numero),
    complemento: emptyToNull(form.complemento),
    bairro: emptyToNull(form.bairro),
    cidade: emptyToNull(form.cidade),
    uf: emptyToNull(form.uf?.toUpperCase().slice(0, 2)),
    ativo: Boolean(form.ativo),
    observacao: form.observacao?.trim() || null,
  }

  try {
    if (isEdit.value) {
      await suppliers.submitSupplierUpdate(Number(route.params.id), payload)
      await successAlert('Fornecedor atualizado com sucesso.', 'update')
    } else {
      await suppliers.submitSupplier(payload)
      await successAlert('Fornecedor cadastrado com sucesso.', 'create')
    }
    await router.push({ name: 'suppliers-list' })
  } catch {
    if (suppliers.state.error) {
      await errorAlert(suppliers.state.error)
    }
  }
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
}

async function applyLookupByCep() {
  const cep = cleanDigits(form.cep)
  if (cep.length !== 8) {
    await errorAlert('Informe um CEP válido para consulta.')
    return
  }

  lookupLoading.value = true
  try {
    const result = await lookupAddressByCep(cep)
    if (!result.found) {
      await errorAlert('CEP não encontrado. O cadastro pode continuar normalmente.')
      return
    }
    applyLookupResult(result)
  } catch {
    await errorAlert('Não foi possível consultar o CEP agora.')
  } finally {
    lookupLoading.value = false
  }
}

async function tryResolveCepByAddress(silent = false) {
  if (cleanDigits(form.cep).length === 8) return
  if (!(form.uf ?? '').trim() || !(form.cidade ?? '').trim() || !(form.endereco ?? '').trim()) return

  lookupLoading.value = true
  try {
    const result = await lookupCepByAddress({
      uf: (form.uf ?? '').trim().toUpperCase(),
      cidade: (form.cidade ?? '').trim(),
      logradouro: (form.endereco ?? '').trim(),
      bairro: (form.bairro ?? '').trim() || undefined,
    })
    if (!result.found) {
      if (!silent) {
        await errorAlert('Endereço sem CEP localizado. Isso não impede o cadastro.')
      }
      return
    }
    applyLookupResult(result)
  } catch {
    if (!silent) {
      await errorAlert('Não foi possível localizar o CEP pelo endereço agora.')
    }
  } finally {
    lookupLoading.value = false
  }
}

function applyLookupResult(result: { cep: string | null; endereco: string | null; complemento: string | null; bairro: string | null; cidade: string | null; uf: string | null }) {
  if (result.cep) form.cep = formatCepValue(result.cep)
  if (result.endereco && !(form.endereco ?? '').trim()) form.endereco = result.endereco
  if (result.complemento && !(form.complemento ?? '').trim()) form.complemento = result.complemento
  if (result.bairro && !(form.bairro ?? '').trim()) form.bairro = result.bairro
  if (result.cidade && !(form.cidade ?? '').trim()) form.cidade = result.cidade
  if (result.uf) form.uf = result.uf
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

function formatDocumentField() {
  form.cpf_cnpj = formatDocument(form.cpf_cnpj)
}

function formatPhone(value: string | null | undefined) {
  const digits = cleanDigits(value).slice(0, 11)
  if (!digits) return ''
  if (digits.length <= 10) return digits.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{4})(\d)/, '$1-$2')
  return digits.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{5})(\d)/, '$1-$2')
}

function formatPhoneField() {
  form.telefone = formatPhone(form.telefone)
}

function formatCepValue(value: string | null | undefined) {
  const digits = cleanDigits(value).slice(0, 8)
  if (digits.length <= 5) return digits
  return `${digits.slice(0, 5)}-${digits.slice(5)}`
}
</script>