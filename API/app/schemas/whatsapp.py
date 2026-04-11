from pydantic import BaseModel


class WhatsAppConnectionStatusRead(BaseModel):
    session_key: str
    expected_phone: str | None = None
    connected: bool
    connected_phone: str | None = None
    provider_status: str | None = None
    verified: bool = False
    message: str | None = None


class WhatsAppQrCodeRead(BaseModel):
    session_key: str
    expected_phone: str | None = None
    qr_code_data_url: str
    expires_in_seconds: int
    provider_status: str | None = None
    message: str | None = None