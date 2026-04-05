export type PermissionAction = 'create' | 'read' | 'update' | 'delete'

export interface ProfilePermission {
  id?: number
  resource_key: string
  resource_label: string | null
  can_read: boolean
  can_create: boolean
  can_update: boolean
  can_delete: boolean
}

export interface PermissionResource {
  resource_key: string
  resource_label: string
  resource_group: string
  supported_actions: PermissionAction[]
}

export interface Profile {
  id: number
  nome: string
  descricao: string | null
  ativo: boolean
  permissions: ProfilePermission[]
  created_at: string
  updated_at: string
}

export interface ProfileInput {
  nome: string
  descricao: string | null
  ativo: boolean
  permissions: ProfilePermission[]
}

export interface UserApiKeyInfo {
  key_prefix: string
  active: boolean
  created_at: string
  rotated_at: string | null
  last_used_at: string | null
}

export interface UserApiKeySecret extends UserApiKeyInfo {
  api_key: string
}
