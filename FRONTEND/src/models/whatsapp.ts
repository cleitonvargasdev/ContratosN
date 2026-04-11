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