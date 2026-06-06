export type AccountsPayablePersonType = 'cliente' | 'fornecedor' | 'funcionario'

export interface AccountsPayablePersonOption {
  entity_id: number
  tipo_pessoa: AccountsPayablePersonType
  nome: string
  cpf_cnpj: string | null
}

export interface AccountsPayablePayment {
  pagamento_id: number
  usuario_id: number | null
  created_at: string
  data_pagamento: string | null
  valor_pago: number | null
  juros: number | null
  acrescimos: number | null
  desconto: number | null
  observacao: string | null
}

export interface AccountsPayablePaymentInput {
  data_pagamento?: string | null
  valor_pago?: number | null
  juros?: number | null
  acrescimos?: number | null
  desconto?: number | null
  observacao?: string | null
}

export interface AccountsPayableInstallment {
  parcela_id: number
  numero_parcela: number | null
  descricao: string | null
  data_referencia_inicial: string | null
  data_referencia_final: string | null
  vencimento: string
  valor_original: number
  acrescimos: number | null
  desconto: number | null
  valor_total: number
  valor_pago: number
  saldo_pagar: number
  quitado: boolean
  observacao: string | null
  pagamentos: readonly AccountsPayablePayment[]
}

export interface AccountsPayableInstallmentInput {
  numero_parcela?: number | null
  descricao?: string | null
  data_referencia_inicial?: string | null
  data_referencia_final?: string | null
  vencimento: string
  valor_original: number
  acrescimos?: number | null
  desconto?: number | null
  observacao?: string | null
}

export interface AccountsPayable {
  conta_pagar_id: number
  descricao: string
  tipo_pessoa: AccountsPayablePersonType
  cliente_id: number | null
  usuario_id: number | null
  fornecedor_id: number | null
  pessoa_id: number
  pessoa_nome: string
  pessoa_cpf_cnpj: string | null
  data_referencia_inicial: string | null
  data_referencia_final: string | null
  observacao: string | null
  valor_total: number
  valor_pago: number
  saldo_pagar: number
  quitado: boolean
  created_at: string
  updated_at: string
  parcelas: readonly AccountsPayableInstallment[]
}

export interface AccountsPayableInput {
  descricao: string
  tipo_pessoa: AccountsPayablePersonType
  cliente_id?: number | null
  usuario_id?: number | null
  fornecedor_id?: number | null
  data_referencia_inicial?: string | null
  data_referencia_final?: string | null
  observacao?: string | null
  parcelas: AccountsPayableInstallmentInput[]
}

export interface AccountsPayableBaseUpdateInput {
  descricao: string
  tipo_pessoa: AccountsPayablePersonType
  cliente_id?: number | null
  usuario_id?: number | null
  fornecedor_id?: number | null
  data_referencia_inicial?: string | null
  data_referencia_final?: string | null
  observacao?: string | null
}

export interface AccountsPayableListItem {
  conta_pagar_id: number
  descricao: string
  tipo_pessoa: AccountsPayablePersonType
  pessoa_id: number
  pessoa_nome: string
  pessoa_cpf_cnpj: string | null
  data_referencia_inicial: string | null
  data_referencia_final: string | null
  proximo_vencimento: string | null
  ultima_data_vencimento: string | null
  quantidade_parcelas: number
  quantidade_parcelas_abertas: number
  valor_total: number
  valor_pago: number
  saldo_pagar: number
  quitado: boolean
}

export interface AccountsPayableListFilters {
  page: number
  page_size: number
  quitado?: boolean
  pessoa_query?: string
  tipo_pessoa?: AccountsPayablePersonType
  data_vencimento_inicial?: string
  data_vencimento_final?: string
  data_referencia_inicial?: string
  data_referencia_final?: string
}

export interface AccountsPayableListResponse {
  items: readonly AccountsPayableListItem[]
  total: number
  page: number
  page_size: number
}