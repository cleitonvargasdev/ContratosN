export interface WhatsAppConnectionStatus {
  session_key: string
  expected_phone: string | null
  connected: boolean
  connected_phone: string | null
  provider_status: string | null
  verified: boolean
  message: string | null
}

export interface WhatsAppQrCodeResponse {
  session_key: string
  expected_phone: string | null
  qr_code_data_url: string
  expires_in_seconds: number
  provider_status: string | null
  message: string | null
}

export interface WhatsAppDispatchBatch {
  id: number
  parametros_id: number | null
  scheduled_for: string | null
  executed_at: string
  status: string
  source_phone: string | null
  total_items: number
  total_sent: number
  total_errors: number
  error_message: string | null
}

export interface WhatsAppDispatchItem {
  id: number
  batch_id: number
  conta_receber_id: number | null
  contratos_id: number | null
  cliente_id: number | null
  parcela_nro: number | null
  client_name: string | null
  destination_phone: string | null
  source_phone: string | null
  status: string
  amount: number | null
  due_at: string | null
  sent_at: string | null
  message_payload: {
    text?: string
    [key: string]: unknown
  }
  provider_payload: Record<string, unknown> | null
  error_message: string | null
}

export interface WhatsAppDispatchBatchFilters {
  page: number
  page_size: number
  data_inicial?: string
  data_final?: string
}

export interface WhatsAppDispatchBatchListResponse {
  items: readonly WhatsAppDispatchBatch[]
  total: number
  page: number
  page_size: number
}

export interface WhatsAppDispatchItemListResponse {
  items: readonly WhatsAppDispatchItem[]
  total: number
  page: number
  page_size: number
}