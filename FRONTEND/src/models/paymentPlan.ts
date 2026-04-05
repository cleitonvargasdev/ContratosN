export interface PaymentPlanOption {
  plano_id: number
  descricao: string | null
  qtde_dias: number | null
  percent_juros: number | null
  valor_parcela: number | null
  valor_base: number | null
  valor_final: number | null
}

export interface PaymentPlanInput {
  descricao: string | null
  qtde_dias: number | null
  percent_juros: number | null
  valor_parcela: number | null
  valor_base: number | null
  valor_final: number | null
}