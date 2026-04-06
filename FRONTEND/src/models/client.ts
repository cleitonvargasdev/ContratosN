export interface Client {
  clientes_id: number
  nome: string | null
  rg: number | null
  cpf_cnpj: string | null
  endereco: string | null
  bairro_id: number | null
  cidade_id: number | null
  uf: string | null
  usuario_id: number | null
  cnpj: string | null
  telefone: string | null
  celular01: string | null
  celular02: string | null
  flag_whatsapp: boolean
  email: string | null
  limite_credito: number | null
  debito_atual: number | null
  prox_vencto: string | null
  data_ultcompra: string | null
  rg_ie: string | null
  latitude: string | null
  longitude: string | null
  cep: string | null
  nro: string | null
  complemento: string | null
  ativo: boolean
  bloqueado: boolean
  comissao_diferente: boolean
  percent_comissao: number | null
  naopagarcomissao: boolean
  parc_atrasadas: number | null
  valor_atrasado: number | null
  valor_em_aberto: number | null
  parc_aberto: number | null
  desativado: boolean
  data_desat: string | null
  contato_responsavel: string | null
  endereco_responsavel: string | null
  fone_responsavel: string | null
  cel_responsavel: string | null
  flag_whatsapp_responsavel: boolean
  cep_responsavel: string | null
  complemento_responsavel: string | null
  uf_responsavel: string | null
  cidade_responsavel_id: number | null
  bairro_id_responsavel: number | null
  nro_responsavel: string | null
  nacionalidade: string | null
  estado_civil: string | null
  profissao: string | null
  turno_cobranca: string | null
  score: number | null
  regra_juros_id: number | null
  media_atraso_parcelas: number | null
  media_atraso_contratos: number | null
}

export interface ClientInput {
  nome: string | null
  rg: number | null
  cpf_cnpj: string | null
  endereco: string | null
  bairro_id: number | null
  cidade_id: number | null
  uf: string | null
  usuario_id: number | null
  cnpj: string | null
  telefone: string | null
  celular01: string | null
  celular02: string | null
  flag_whatsapp: boolean
  email: string | null
  limite_credito: number | null
  debito_atual: number | null
  latitude: string | null
  longitude: string | null
  rg_ie: string | null
  cep: string | null
  nro: string | null
  complemento: string | null
  ativo: boolean
  bloqueado: boolean
  comissao_diferente: boolean
  percent_comissao: number | null
  naopagarcomissao: boolean
  parc_atrasadas: number | null
  valor_atrasado: number | null
  valor_em_aberto: number | null
  parc_aberto: number | null
  contato_responsavel: string | null
  endereco_responsavel: string | null
  fone_responsavel: string | null
  cel_responsavel: string | null
  flag_whatsapp_responsavel: boolean
  cep_responsavel: string | null
  complemento_responsavel: string | null
  uf_responsavel: string | null
  cidade_responsavel_id: number | null
  bairro_id_responsavel: number | null
  nro_responsavel: string | null
  nacionalidade: string | null
  estado_civil: string | null
  profissao: string | null
  turno_cobranca: string | null
  score: number | null
  media_atraso_parcelas: number | null
  media_atraso_contratos: number | null
  regra_juros_id: number | null
}

export interface RegraJurosOption {
  regra_juros_id: number
  descricao: string | null
  juros_dia: number | null
  mora_dia: number | null
  ativo: boolean | null
}

export interface CobradorOption {
  id: number
  nome: string
}

export interface ClientListFilters {
  page: number
  page_size: number
  nome?: string
  cpf_cnpj?: string
  ativo?: boolean
}

export interface ClientListResponse {
  items: readonly Client[]
  total: number
  page: number
  page_size: number
}