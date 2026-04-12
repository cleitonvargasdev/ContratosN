export interface ParameterScheduleEntry {
  dias_semana: number[]
  horario: string
}

export interface ParameterNinthDigitRule {
  campo: string
  operador: string
  valor: unknown
}

export interface Parameter {
  parametros_id: number
  nome_fantasia: string | null
  razao_social: string | null
  endereco: string | null
  bairrosid: number | null
  cep: string | null
  nro: number | null
  cnpj: string | null
  uf: string | null
  cidade_id: number | null
  telefone1: string | null
  flag_whatsapp_telefone1: boolean
  telefone2: string | null
  flag_whatsapp_telefone2: boolean
  e_mail: string | null
  responsavel: string | null
  complemento: string | null
  emitir_sons: boolean
  score_valor_inicial: number
  score_pontos_atraso_parcela: number
  score_pontos_atraso_quitacao_contrato: number
  score_pontos_pagamento_em_dia: number
  score_pontos_quitacao_em_dia: number
  score_atualizacao_automatica: boolean
  score_agendamentos: ParameterScheduleEntry[]
  score_atualizacao_ultima_execucao: string | null
  score_atualizacao_proxima_execucao: string | null
  score_ultima_execucao_sucesso: boolean | null
  score_ultimo_erro: string | null
  whatsapp_cobranca_automatica: boolean
  whatsapp_agendamentos: ParameterScheduleEntry[]
  whatsapp_cobranca_ultima_execucao: string | null
  whatsapp_cobranca_proxima_execucao: string | null
  whatsapp_ultima_execucao_sucesso: boolean | null
  whatsapp_ultimo_erro: string | null
  whatsapp_cobranca_dias_antes: number
  whatsapp_cobranca_dias_depois: number
  whatsapp_cobranca_modelo: string | null
  api_whatsapp: string | null
  usuario_api_whatsapp: string | null
  token_api_whatsapp: string | null
  regra_nono_dig_whats: ParameterNinthDigitRule[]
  sufixo_whatsapp: string | null
  msg_renovacao: string | null
  msg_negociacao: string | null
  pais_whatsapp: number
  msg_campanha: string | null
  ligar_websocket: boolean
  silenciar_mensagem: boolean
}

export interface ParameterInput {
  nome_fantasia: string | null
  razao_social: string | null
  endereco: string | null
  bairrosid: number | null
  cep: string | null
  nro: number | null
  cnpj: string | null
  uf: string | null
  cidade_id: number | null
  telefone1: string | null
  flag_whatsapp_telefone1: boolean
  telefone2: string | null
  flag_whatsapp_telefone2: boolean
  e_mail: string | null
  responsavel: string | null
  complemento: string | null
  emitir_sons: boolean
  score_valor_inicial: number
  score_pontos_atraso_parcela: number
  score_pontos_atraso_quitacao_contrato: number
  score_pontos_pagamento_em_dia: number
  score_pontos_quitacao_em_dia: number
  score_atualizacao_automatica: boolean
  score_agendamentos: ParameterScheduleEntry[]
  whatsapp_cobranca_automatica: boolean
  whatsapp_agendamentos: ParameterScheduleEntry[]
  whatsapp_cobranca_dias_antes: number
  whatsapp_cobranca_dias_depois: number
  whatsapp_cobranca_modelo: string | null
  api_whatsapp: string | null
  usuario_api_whatsapp: string | null
  token_api_whatsapp: string | null
  regra_nono_dig_whats: ParameterNinthDigitRule[]
  sufixo_whatsapp: string | null
  msg_renovacao: string | null
  msg_negociacao: string | null
  pais_whatsapp: number
  msg_campanha: string | null
  ligar_websocket: boolean
  silenciar_mensagem: boolean
}

export interface ParameterAutomationRunResult {
  executado_em: string
  clientes_recalculados: number
  cobrancas_whatsapp_preparadas: number
  parametros: Parameter
}