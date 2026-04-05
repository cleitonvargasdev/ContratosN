import type { ProfilePermission, UserApiKeyInfo } from '@/models/accessControl'

export type UserFunction = string

export interface UserAddressFields {
  telefone: string | null
  celular: string | null
  flag_whatsapp: boolean
  cep: string | null
  endereco: string | null
  numero: string | null
  complemento: string | null
  bairro_id: number | null
  cidade_id: number | null
  uf: string | null
  cpf: string | null
  rg: string | null
  data_nascimento: string | null
}

export interface User extends UserAddressFields {
  id: number
  nome: string
  login: string
  email: string
  funcao: UserFunction
  perfil_id: number | null
  perfil_nome: string | null
  api_key_info: UserApiKeyInfo | null
  ativo: boolean
  created_at: string
  updated_at: string
}

export interface AuthenticatedUser extends User {
  permissions: ProfilePermission[]
}

export interface UserCreateInput extends UserAddressFields {
  nome: string
  login: string
  email: string
  senha: string
  funcao: UserFunction
  perfil_id: number | null
  ativo: boolean
}

export interface UserUpdateInput extends UserAddressFields {
  nome: string
  login: string
  email: string
  senha?: string
  funcao: UserFunction
  perfil_id: number | null
  ativo: boolean
}

export interface UserListFilters {
  page: number
  page_size: number
  nome?: string
  email?: string
  ativo?: boolean
}

export interface UserListResponse {
  items: readonly User[]
  total: number
  page: number
  page_size: number
}
