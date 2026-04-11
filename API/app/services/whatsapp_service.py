import base64
from typing import Any

import httpx
from dotenv import dotenv_values
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ENV_FILE, settings
from app.services.parameter_service import ParameterService


class WhatsAppService:
	def __init__(self, session: AsyncSession) -> None:
		self.session = session
		self.parameter_service = ParameterService(session)
		self.base_url = settings.quepasa_apiwpp_url.rstrip("/")
		self.session_key = settings.quepasa_token.strip() or "CONTRATOS"
		self.quepasa_user = settings.quepasa_user.strip() if settings.quepasa_user else None
		self.timeout = settings.quepasa_timeout_seconds

	async def get_connection_status(self) -> dict[str, Any]:
		expected_phone = await self._get_expected_phone()
		payload = await self._get_info_payload()
		provider_status = self._extract_provider_status(payload)
		connected_phone = self._extract_connected_phone(payload)
		verified = self._extract_verified(payload)
		connected = self._is_connected(payload, expected_phone, connected_phone, verified)

		return {
			"session_key": self.session_key,
			"expected_phone": expected_phone,
			"connected": connected,
			"connected_phone": connected_phone,
			"provider_status": provider_status,
			"verified": verified,
			"message": self._build_status_message(expected_phone, connected_phone, provider_status, verified, connected),
		}

	async def create_session_qr_code(self) -> dict[str, Any]:
		expected_phone = await self._get_expected_phone(required=True)
		await self._get_quepasa_user(required=True)
		qr_code_data_url, provider_status = await self._fetch_qr_code_data_url()

		return {
			"session_key": self.session_key,
			"expected_phone": expected_phone,
			"qr_code_data_url": qr_code_data_url,
			"expires_in_seconds": 15,
			"provider_status": provider_status,
			"message": "Escaneie o QR Code com o WhatsApp do Telefone 1.",
		}

	async def send_text_message(self, phone_number: str, text: str) -> dict[str, Any]:
		chatid = self._build_chatid(phone_number)
		async with httpx.AsyncClient(timeout=self.timeout) as client:
			response = await client.post(
				f"{self.base_url}/v3/bot/{self.session_key}/send",
				headers={"Accept": "application/json", "Content-Type": "application/json"},
				json={"chatid": chatid, "text": text},
			)
		response = self._validate_provider_response(response)
		data = self._parse_json_response(response)
		if data.get("success") is False:
			message = self._extract_error_message(data) or "Falha ao enviar mensagem pelo WhatsApp."
			raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=message)
		return {
			"success": True,
			"message": self._extract_error_message(data) or "Mensagem enviada com sucesso.",
			"chatid": chatid,
		}

	async def _get_expected_phone(self, required: bool = False) -> str | None:
		parameter = await self.parameter_service.get_parameters()
		phone = self._digits_only(parameter.telefone1)
		if required and not phone:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Configure o Telefone 1 em Parâmetros antes de conectar o WhatsApp.",
			)
		return phone

	async def _get_quepasa_user(self, required: bool = False) -> str | None:
		if self.quepasa_user:
			return self.quepasa_user

		env_user = dotenv_values(ENV_FILE).get("QUEPASA_USER")
		if isinstance(env_user, str) and env_user.strip():
			self.quepasa_user = env_user.strip()
			return self.quepasa_user

		if required:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Configure o usuário do QuePasa em QUEPASA_USER para gerar o QR Code.",
			)

		return None

	async def _get_info_payload(self) -> dict[str, Any]:
		response = await self._request_provider_endpoint("GET", "/info", allow_not_found=True)
		if response.status_code == status.HTTP_404_NOT_FOUND:
			return {}
		return self._parse_json_response(response)

	async def _fetch_qr_code_data_url(self) -> tuple[str, str | None]:
		response = await self._request_qr_code_endpoint()
		content_type = response.headers.get("content-type", "")

		if "image/png" in content_type:
			encoded = base64.b64encode(response.content).decode("ascii")
			return f"data:image/png;base64,{encoded}", "scan"

		data = self._parse_json_response(response)
		qr_code = self._find_qr_code_value(data)
		if not qr_code:
			message = self._extract_error_message(data) or "A API do WhatsApp nao retornou um QR Code valido."
			raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=message)

		if qr_code.startswith("data:image"):
			return qr_code, self._extract_provider_status(data)

		return f"data:image/png;base64,{qr_code}", self._extract_provider_status(data)

	async def _request_qr_code_endpoint(self) -> httpx.Response:
		return await self._request_provider_endpoint(
			"GET",
			"/scan",
			headers={"Accept": "application/json, image/png"},
		)

	async def _request_provider_endpoint(
		self,
		method: str,
		path: str,
		*,
		headers: dict[str, str] | None = None,
		json: dict[str, Any] | None = None,
		allow_not_found: bool = False,
	) -> httpx.Response:
		request_headers = await self._build_provider_headers(headers)
		async with httpx.AsyncClient(timeout=self.timeout) as client:
			response = await client.request(method, f"{self.base_url}{path}", headers=request_headers, json=json)
		return self._validate_provider_response(response, allow_not_found=allow_not_found)

	async def _build_provider_headers(self, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
		headers = {
			"Accept": "application/json",
			"X-QUEPASA-TOKEN": self.session_key,
		}
		username = await self._get_quepasa_user(required=True)
		if username:
			headers["X-QUEPASA-USER"] = username
		if extra_headers:
			headers.update(extra_headers)
		return headers

	def _validate_provider_response(self, response: httpx.Response, *, allow_not_found: bool = False) -> httpx.Response:
		if response.status_code == status.HTTP_404_NOT_FOUND and allow_not_found:
			return response
		if response.is_success:
			return response

		message = self._extract_error_message_from_response(response)
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=message)

	@staticmethod
	def _parse_json_response(response: httpx.Response) -> dict[str, Any]:
		try:
			payload = response.json()
		except ValueError as exc:
			raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Resposta invalida da API do WhatsApp.") from exc

		if isinstance(payload, dict):
			return payload
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Resposta inesperada da API do WhatsApp.")

	def _extract_error_message_from_response(self, response: httpx.Response) -> str:
		try:
			payload = response.json()
		except ValueError:
			return f"Falha ao consultar a API do WhatsApp ({response.status_code})."
		return self._extract_error_message(payload) or f"Falha ao consultar a API do WhatsApp ({response.status_code})."

	@staticmethod
	def _extract_error_message(payload: Any) -> str | None:
		if isinstance(payload, dict):
			for key in ("message", "status", "detail", "error"):
				value = payload.get(key)
				if isinstance(value, str) and value.strip():
					return value.strip()
		return None

	@staticmethod
	def _extract_provider_status(payload: dict[str, Any]) -> str | None:
		for key in ("status", "stats", "state"):
			value = payload.get(key)
			if isinstance(value, str) and value.strip():
				return value.strip()

		server = payload.get("server")
		if isinstance(server, dict):
			for key in ("status", "state"):
				value = server.get(key)
				if isinstance(value, str) and value.strip():
					return value.strip()
		return None

	@staticmethod
	def _extract_connected_phone(payload: dict[str, Any]) -> str | None:
		candidates: list[Any] = [payload.get("wid")]
		server = payload.get("server")
		if isinstance(server, dict):
			candidates.append(server.get("wid"))

		for candidate in candidates:
			normalized_candidate = candidate
			if isinstance(candidate, str):
				normalized_candidate = candidate.split("@", 1)[0].split(":", 1)[0]
			digits = WhatsAppService._digits_only(normalized_candidate)
			if digits:
				return digits
		return None

	@staticmethod
	def _extract_verified(payload: dict[str, Any]) -> bool:
		server = payload.get("server")
		if isinstance(server, dict) and isinstance(server.get("verified"), bool):
			return bool(server.get("verified"))
		return bool(payload.get("verified"))

	def _is_connected(
		self,
		payload: dict[str, Any],
		expected_phone: str | None,
		connected_phone: str | None,
		verified: bool,
	) -> bool:
		provider_status = (self._extract_provider_status(payload) or "").strip().lower()
		ready_by_status = provider_status in {"ready", "connected", "online"}
		ready_by_flags = payload.get("success") is True and verified
		if not (ready_by_status or ready_by_flags):
			return False
		return bool(connected_phone or verified)

	@staticmethod
	def _build_status_message(
		expected_phone: str | None,
		connected_phone: str | None,
		provider_status: str | None,
		verified: bool,
		connected: bool,
	) -> str:
		if verified and expected_phone and connected_phone and not WhatsAppService._phone_matches(expected_phone, connected_phone):
			return f"Existe uma conta conectada, mas o numero {connected_phone} nao corresponde ao Telefone 1."
		if connected and connected_phone:
			return f"Conta conectada no numero {connected_phone}."
		if expected_phone:
			return f"Sessao CONTRATOS aguardando conexao para o numero {expected_phone}."
		if provider_status:
			return f"Status atual do provedor: {provider_status}."
		return "Sessao CONTRATOS desconectada."

	@staticmethod
	def _find_qr_code_value(payload: Any) -> str | None:
		if isinstance(payload, dict):
			for key in ("qrcode", "qrCode", "qr", "code", "base64", "image", "content"):
				value = payload.get(key)
				if isinstance(value, str) and value.strip():
					return value.strip()
			for value in payload.values():
				found = WhatsAppService._find_qr_code_value(value)
				if found:
					return found
		elif isinstance(payload, list):
			for item in payload:
				found = WhatsAppService._find_qr_code_value(item)
				if found:
					return found
		return None

	@staticmethod
	def _digits_only(value: Any) -> str | None:
		if value is None:
			return None
		digits = "".join(char for char in str(value) if char.isdigit())
		return digits or None

	@classmethod
	def _build_chatid(cls, phone_number: str) -> str:
		digits = cls._digits_only(phone_number)
		if not digits:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Numero de WhatsApp invalido para envio.")
		normalized = cls._normalize_chat_phone_digits(digits)
		return f"55{normalized}@s.whatsapp.net"

	@staticmethod
	def _normalize_chat_phone_digits(phone_digits: str) -> str:
		normalized = phone_digits[2:] if phone_digits.startswith("55") else phone_digits
		if len(normalized) == 11 and normalized[2] == "9":
			ddd = int(normalized[:2])
			if not 11 <= ddd <= 29:
				return f"{normalized[:2]}{normalized[3:]}"
		return normalized

	@staticmethod
	def _phone_matches(expected_phone: str, connected_phone: str) -> bool:
		def normalize(phone: str) -> str:
			return phone[2:] if phone.startswith("55") else phone

		return normalize(expected_phone) == normalize(connected_phone)

