export interface SolicitationClientBrief {
  clientes_id: number
  nome: string | null
  cpf_cnpj: string | null
  celular01: string | null
  telefone: string | null
  flag_whatsapp: boolean | null
}

export interface SolicitationClientDraft {
  nome: string | null
  cpf_cnpj: string | null
  telefone: string | null
  celular01: string | null
  flag_whatsapp: boolean
}

export interface SolicitationContractDraft {
  contrato_referencia_id: number | null
  cliente_id: number | null
  usuario_id_vendedor: number | null
  regra_juros_id: number | null
  plano_id: number | null
  qtde_dias: number | null
  percent_juros: number | null
  valor_empretismo: number | null
  valor_parcela: number | null
  recorrencia: boolean | null
  aluguel: boolean | null
  cobranca_segunda: boolean | null
  cobranca_terca: boolean | null
  cobranca_quarta: boolean | null
  cobranca_quinta: boolean | null
  cobranca_sexta: boolean | null
  cobranca_sabado: boolean | null
  cobranca_domingo: boolean | null
  cobranca_feriado: boolean | null
  cobranca_mensal: boolean | null
  cobranca_quinzenal: boolean | null
  frequencia_pagamento: string | null
  numero_parcelas: number | null
}

export interface Solicitation {
  id: number
  cliente_id: number | null
  cliente_nome: string | null
  session_id: number | null
  nome_informado: string | null
  telefone: string | null
  cpf_cnpj: string | null
  valor_pretendido: number | null
  frequencia_pagamento: string | null
  numero_parcelas: number | null
  tipo: string
  status: string
  vendedor_id: number | null
  vendedor_nome: string | null
  valor_parcela: number | null
  taxa_juros: number | null
  contrato_id: number | null
  usuario_id_aprovou: number | null
  usuario_nome_aprovou: string | null
  datahora_solicitacao: string
  datahora_aprovacao: string | null
  observacao: string | null
}

export interface SolicitationDetail extends Solicitation {
  cliente_existente: SolicitationClientBrief | null
  cliente_sugerido: SolicitationClientDraft
  contrato_sugerido: SolicitationContractDraft
}

export interface SolicitationListFilters {
  page: number
  page_size: number
  status?: string
  tipo?: string
  cliente_id?: number
  termo?: string
}

export interface SolicitationListResponse {
  items: readonly Solicitation[]
  total: number
  page: number
  page_size: number
}

export interface SolicitationPendingCount {
  pendentes: number
}
