export interface Supplier {
  fornecedor_id: number
  nome: string | null
  cpf_cnpj: string | null
  telefone: string | null
  email: string | null
  cep: string | null
  endereco: string | null
  numero: string | null
  complemento: string | null
  bairro: string | null
  cidade: string | null
  uf: string | null
  ativo: boolean
  observacao: string | null
}

export interface SupplierInput {
  nome: string | null
  cpf_cnpj: string | null
  telefone: string | null
  email: string | null
  cep: string | null
  endereco: string | null
  numero: string | null
  complemento: string | null
  bairro: string | null
  cidade: string | null
  uf: string | null
  ativo: boolean
  observacao: string | null
}

export interface SupplierListFilters {
  page: number
  page_size: number
  nome?: string
  cpf_cnpj?: string
  ativo?: boolean
}

export interface SupplierListResponse {
  items: readonly Supplier[]
  total: number
  page: number
  page_size: number
}