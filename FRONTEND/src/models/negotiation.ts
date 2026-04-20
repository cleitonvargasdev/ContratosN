export interface NegotiationContractItem {
  id: number
  negociacao_id: number
  contrato_id: number
  valor_aberto: number
}

export interface Negotiation {
  negociacao_id: number
  cliente_id: number | null
  cliente_nome: string | null
  data_negociacao: string | null
  valor_total_aberto: number
  qtde_parcelas: number
  valor_parcela: number
  contrato_gerado_id: number | null
  usuario_id: number | null
  usuario_nome: string | null
  obs: string | null
  contrato_quitado: boolean | null
  cobranca_segunda: boolean
  cobranca_terca: boolean
  cobranca_quarta: boolean
  cobranca_quinta: boolean
  cobranca_sexta: boolean
  cobranca_sabado: boolean
  cobranca_domingo: boolean
  cobranca_feriado: boolean
  cobranca_mensal: boolean
  cobranca_quinzenal: boolean
  contratos_originais: readonly NegotiationContractItem[]
}

export interface NegotiationListFilters {
  page: number
  page_size: number
  cliente_nome?: string
  contrato_gerado_id?: number
}

export interface NegotiationListResponse {
  items: readonly Negotiation[]
  total: number
  page: number
  page_size: number
}

export interface OpenContractForNegotiation {
  contratos_id: number
  data_contrato: string | null
  valor_empretismo: number | null
  valor_em_aberto: number
  valor_parcela: number | null
  qtde_dias: number | null
  quitado: boolean | null
}

export interface NegotiationCreatePayload {
  cliente_id: number
  contratos_ids: number[]
  qtde_parcelas: number
  valor_parcela: number
  obs: string | null
  cobranca_segunda: boolean
  cobranca_terca: boolean
  cobranca_quarta: boolean
  cobranca_quinta: boolean
  cobranca_sexta: boolean
  cobranca_sabado: boolean
  cobranca_domingo: boolean
  cobranca_feriado: boolean
  cobranca_mensal: boolean
  cobranca_quinzenal: boolean
}
