export interface UFOption {
  uf_id: number
  uf: string
  uf_nome: string
  cod_ibge: number | null
}

export interface CidadeOption {
  cidade_id: number
  uf_id: number
  cidade: string
  uf: string | null
  uf_nome: string | null
}

export interface BairroOption {
  bairro_id: number
  cidade_id: number
  bairro_nome: string
  cidade: string | null
  uf: string | null
}

export interface FeriadoOption {
  feriado_id: number
  data: string
  cidade_id: number | null
  cidade: string | null
  uf: string | null
  descricao: string
  nivel: number
}

export interface UFInput {
  uf: string
  uf_nome: string
  cod_ibge: number | null
}

export interface CidadeInput {
  uf_id: number
  cidade: string
}

export interface BairroInput {
  cidade_id: number
  bairro_nome: string
}

export interface FeriadoInput {
  data: string
  cidade_id: number | null
  uf: string | null
  descricao: string
  nivel: number
}

export interface AddressLookupResponse {
  found: boolean
  source: string | null
  cep: string | null
  endereco: string | null
  complemento: string | null
  bairro: string | null
  bairro_id: number | null
  cidade: string | null
  cidade_id: number | null
  uf: string | null
}