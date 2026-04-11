export interface ApiConfig {
  api_id: number
  usuario_id: number | null
  usuario_nome: string | null
  nome_api: string | null
  funcionalidade: string | null
  url: string | null
  key1: string | null
  value1: string | null
  key2: string | null
  value2: string | null
  key3: string | null
  value3: string | null
  key4: string | null
  value4: string | null
  key5: string | null
  value5: string | null
  body: string | null
}

export interface ApiConfigInput {
  usuario_id: number | null
  nome_api: string | null
  funcionalidade: string | null
  url: string | null
  key1: string | null
  value1: string | null
  key2: string | null
  value2: string | null
  key3: string | null
  value3: string | null
  key4: string | null
  value4: string | null
  key5: string | null
  value5: string | null
  body: string | null
}

export interface ApiConfigListFilters {
  page: number
  page_size: number
  nome_api?: string
  usuario_id?: number
}

export interface ApiConfigListResponse {
  items: readonly ApiConfig[]
  total: number
  page: number
  page_size: number
}