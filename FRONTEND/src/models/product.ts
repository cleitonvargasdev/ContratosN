export interface Brand {
  marca_id: number
  descricao: string | null
}

export interface BrandOption {
  marca_id: number
  descricao: string
}

export interface BrandInput {
  descricao: string | null
}

export interface BrandListFilters {
  page: number
  page_size: number
  descricao?: string
}

export interface BrandListResponse {
  items: readonly Brand[]
  total: number
  page: number
  page_size: number
}

export interface Product {
  produto_id: number
  descricao: string | null
  valor_compra: number | null
  valor_venda: number | null
  marca_id: number | null
  marca_descricao: string | null
  garantia: number | null
  ativo: boolean
  estoque: number | null
  modelo: string | null
  cor: string | null
  marca?: Brand | null
}

export interface ProductInput {
  descricao: string | null
  valor_compra: number | null
  valor_venda: number | null
  marca_id: number | null
  garantia: number | null
  ativo: boolean
  estoque: number | null
  modelo: string | null
  cor: string | null
}

export interface ProductListFilters {
  page: number
  page_size: number
  descricao?: string
  marca_id?: number
  ativo?: boolean
}

export interface ProductListResponse {
  items: readonly Product[]
  total: number
  page: number
  page_size: number
}