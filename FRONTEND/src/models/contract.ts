export interface Contract {
  contratos_id: number
  data_lancto: string | null
  data_contrato: string | null
  cliente_id: number | null
  cliente_nome: string | null
  cliente_telefone: string | null
  cobrador_nome: string | null
  plano_id: number | null
  qtde_dias: number | null
  percent_juros: number | null
  valor_empretismo: number | null
  data_final: string | null
  valor_final: number | null
  valor_recebido: number
  valor_em_aberto: number
  valor_em_atraso: number
  quitado: boolean | null
  obs: string | null
  valor_parcela: number | null
  user_add: number | null
  contrato_status: number
  negociacao_id: number | null
  usuario_id_vendedor: number | null
  comissao_percentual: number | null
  valor_comissao_previsto: number | null
  valor_comissao_apurada: number | null
  regra_comissao_id: number | null
  regra_juros_id: number | null
  recorrencia: boolean | null
}

export interface ContractBaseInput {
  data_lancto: string | null
  data_contrato: string | null
  cliente_id: number | null
  plano_id: number | null
  qtde_dias: number | null
  percent_juros: number | null
  valor_empretismo: number | null
  data_final: string | null
  valor_final: number | null
  quitado: boolean | null
  obs: string | null
  valor_parcela: number | null
  user_add: number | null
  contrato_status: number
  negociacao_id: number | null
  usuario_id_vendedor: number | null
  comissao_percentual: number | null
  valor_comissao_previsto: number | null
  valor_comissao_apurada: number | null
  regra_comissao_id: number | null
  regra_juros_id: number | null
  recorrencia: boolean | null
}

export interface ContractCreateInput extends ContractBaseInput {
  contratos_id: number
}

export type ContractUpdateInput = ContractBaseInput

export interface ContractListFilters {
  page: number
  page_size: number
  contratos_id?: number
  cliente_nome?: string
  cobrador_nome?: string
  quitado?: boolean
}

export interface ContractListResponse {
  items: readonly Contract[]
  total: number
  page: number
  page_size: number
}

export interface ContractInstallment {
  id: number
  contratos_id: number | null
  parcela_nro: number | null
  vencimento_original: string | null
  vencimentol: string | null
  valor_base: number | null
  valor_total: number | null
  valor_recebido: number | null
  data_recebimento: string | null
  quitado: boolean | null
  desconto: number | null
  valor_juros: number | null
  dia_semana: string | null
  possui_pagamento: boolean
}

export interface ContractInstallmentGenerateItem {
  parcela_nro: number
  vencimento: string
  valor_total: number
}

export interface ContractInstallmentGeneratePayload {
  parcelas: ContractInstallmentGenerateItem[]
}

export interface InstallmentPaymentPayload {
  valor_recebido: number
  data_recebimento: string | null
  desconto: number | null
  juros: number | null
}

export interface InstallmentSettlePayload {
  data_recebimento: string | null
}

export interface InstallmentUpdatePayload {
  parcela_nro: number
  vencimento: string
  valor_base: number
  valor_juros: number
  valor_total: number
}

export interface ContractReceipt {
  recebimento_id: number
  contrato_id: number | null
  parcela_nro: number | null
  valor_recebido: number | null
  desconto: number | null
  juros: number | null
  data_recebimento: string | null
  usuario_id: number | null
  usuario_nome: string | null
}