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
  pagar_comissao_venda: boolean
  pagar_comissao_cobranca: boolean
  aluguel: boolean | null
  recorrencia: boolean | null
  conta_pagar_id: number | null
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
  pagar_comissao_venda: boolean
  pagar_comissao_cobranca: boolean
  aluguel: boolean | null
  recorrencia: boolean | null
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

export interface AccountsReceivableListFilters {
  page: number
  page_size: number
  recebida: boolean
  cliente_ativo?: boolean
  cliente_query?: string
  data_vencimento_inicial?: string
  data_vencimento_final?: string
}

export interface AccountsReceivableListItem {
  id: number
  contratos_id: number | null
  cliente_id: number | null
  cliente_nome: string | null
  cliente_cpf_cnpj: string | null
  cliente_valor_em_aberto: number | null
  parcela_nro: number | null
  vencimento: string | null
  valor_juros: number | null
  valor_total: number | null
  valor_recebido: number | null
  valor_em_aberto: number
  data_recebimento: string | null
  quitado: boolean | null
  dia_semana: string | null
  contrato_valor_parcela: number | null
  contrato_valor_total: number | null
  contrato_valor_recebido: number | null
  contrato_valor_em_aberto: number | null
  contrato_valor_em_atraso: number | null
  contrato_quitado: boolean | null
  contrato_ultimo_recebimento: string | null
}

export interface AccountsReceivableContractGroup {
  contract_key: string
  contratos_id: number | null
  valor_parcela: number | null
  valor_total: number | null
  valor_recebido: number | null
  valor_em_aberto: number | null
  valor_em_atraso: number | null
  quitado: boolean | null
  ultimo_recebimento: string | null
  items: readonly AccountsReceivableListItem[]
}

export interface AccountsReceivableClientGroup {
  client_key: string
  cliente_id: number | null
  cliente_nome: string | null
  cliente_cpf_cnpj: string | null
  cliente_valor_em_aberto: number | null
  installment_count: number
  contracts: readonly AccountsReceivableContractGroup[]
}

export interface AccountsReceivableListResponse {
  items: readonly AccountsReceivableClientGroup[]
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
  msg_whatsapp: boolean
  dt_hora_envio: string | null
  tipo_envio: number | null
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

export interface BatchInstallmentReceivePayload {
  valor_recebido: number
  data_recebimento: string | null
}

export interface BatchInstallmentReceivePreviewItem {
  installment: ContractInstallment
  saldo_restante: number
  valor_recebimento: number
}

export interface BatchInstallmentReceivePreview {
  contrato_id: number
  valor_informado: number
  valor_distribuido: number
  parcelas: BatchInstallmentReceivePreviewItem[]
}

export interface BatchInstallmentReceiveConfirmResult {
  contrato_id: number
  valor_informado: number
  valor_processado: number
  parcelas_processadas: ContractInstallment[]
}

export interface BatchReceiptContractSearchFilters {
  page: number
  page_size: number
  query?: string
}

export interface BatchReceiptContractSearchContractGroup {
  contract_key: string
  contratos_id: number
  comodato: boolean
  valor_parcela: number | null
}

export interface BatchReceiptContractSearchClientGroup {
  client_key: string
  cliente_id: number | null
  cliente_nome: string | null
  cliente_cpf_cnpj: string | null
  contract_count: number
  contracts: readonly BatchReceiptContractSearchContractGroup[]
}

export interface BatchReceiptContractSearchResponse {
  items: readonly BatchReceiptContractSearchClientGroup[]
  total: number
  page: number
  page_size: number
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

export interface InstallmentCreatePayload {
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

export interface ContractComodatoItemRead {
  item_id: number
  produto_id: number
  produto_descricao: string
  quantidade: number
  valor_unitario: number | null
  observacao: string | null
}

export interface ContractComodato {
  contrato_id: number
  avalista_id: number | null
  avalista_nome: string | null
  items: readonly ContractComodatoItemRead[]
  total_itens: number
  total_quantidade: number
  pode_imprimir: boolean
}

export interface ContractComodatoItemInput {
  item_id: number | null
  produto_id: number
  quantidade: number
  valor_unitario: number | null
  observacao: string | null
}

export interface ContractComodatoInput {
  avalista_id: number | null
  items: ContractComodatoItemInput[]
}
