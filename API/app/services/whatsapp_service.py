import base64
import json
from ast import literal_eval
from typing import Any

import httpx
from dotenv import dotenv_values
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.secrets import decrypt_secret
from app.repositories.api_config_repository import ApiConfigRepository
from app.core.config import ENV_FILE, settings
from app.services.parameter_service import ParameterService


class WhatsAppService:
	def __init__(self, session: AsyncSession) -> None:
		self.session = session
		self.parameter_service = ParameterService(session)
		self.api_config_repository = ApiConfigRepository(session)
		self.base_url = settings.quepasa_middleware_url.rstrip("/")
		self.timeout = settings.quepasa_timeout_seconds

	async def get_connection_status(self) -> dict[str, Any]:
		config = await self._get_whatsapp_config()
		api_health = await self._get_api_health_status(config)
		expected_phone = config["expected_phone"]
		payload = await self._get_info_payload(config) if api_health["available"] else {}
		provider_status = self._extract_provider_status(payload)
		connected_phone = self._extract_connected_phone(payload)
		verified = self._extract_verified(payload)
		connected = self._is_connected(
			payload,
			config["expected_phones"],
			config["country_code"],
			config["ninth_digit_rules"],
			connected_phone,
			verified,
		)

		return {
			"session_key": config["session_key"],
			"expected_phone": expected_phone,
			"connected": connected,
			"connected_phone": connected_phone,
			"api_available": api_health["available"],
			"api_status": api_health["status"],
			"api_message": api_health["message"],
			"provider_status": provider_status,
			"verified": verified,
			"message": self._build_status_message(
				config["expected_phones"],
				config["country_code"],
				config["ninth_digit_rules"],
				connected_phone,
				provider_status,
				verified,
				connected,
			),
		}

	async def create_session_qr_code(self) -> dict[str, Any]:
		config = await self._get_whatsapp_config(required_phone=True, required_user=True, required_token=True)
		expected_phone = config["expected_phone"]
		qr_code_data_url, provider_status = await self._fetch_qr_code_data_url()

		return {
			"session_key": config["session_key"],
			"expected_phone": expected_phone,
			"qr_code_data_url": qr_code_data_url,
			"expires_in_seconds": 15,
			"provider_status": provider_status,
			"message": "Escaneie o QR Code com o WhatsApp do Telefone 1 ou Telefone 2.",
		}

	async def send_text_message(self, phone_number: str, text: str) -> dict[str, Any]:
		config = await self._get_whatsapp_config(required_user=True, required_token=True)
		chatid = self._build_chatid(
			phone_number,
			country_code=config["country_code"],
			suffix=config["suffix"],
			ninth_digit_rules=config["ninth_digit_rules"],
		)
		request_config = await self._build_api_request_config(
			"mensagem",
			config,
			extra_placeholders={"chatid": chatid, "text": text},
		)
		async with httpx.AsyncClient(timeout=self.timeout) as client:
			response = await client.post(request_config["url"], headers=request_config["headers"], json=request_config["json"])
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

	async def send_text_to_chatid(self, chatid: str, text: str) -> dict[str, Any]:
		config = await self._get_whatsapp_config(required_user=True, required_token=True)
		clean_chatid = self._clean_text(chatid)
		if not clean_chatid:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ChatId invalido para envio.")
		request_config = await self._build_api_request_config(
			"mensagem",
			config,
			extra_placeholders={"chatid": clean_chatid, "text": text},
		)
		async with httpx.AsyncClient(timeout=self.timeout) as client:
			response = await client.post(request_config["url"], headers=request_config["headers"], json=request_config["json"])
		response = self._validate_provider_response(response)
		data = self._parse_json_response(response)
		if data.get("success") is False:
			message = self._extract_error_message(data) or "Falha ao enviar mensagem pelo WhatsApp."
			raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=message)
		return {
			"success": True,
			"message": self._extract_error_message(data) or "Mensagem enviada com sucesso.",
			"chatid": clean_chatid,
		}

	async def send_document_message(self, phone_number: str, document_url: str, text: str) -> dict[str, Any]:
		config = await self._get_whatsapp_config(required_user=True, required_token=True)
		chatid = self._build_chatid(
			phone_number,
			country_code=config["country_code"],
			suffix=config["suffix"],
			ninth_digit_rules=config["ninth_digit_rules"],
		)
		request_config = await self._build_api_request_config(
			"documento",
			config,
			extra_placeholders={"chatid": chatid, "chatId": chatid, "url": document_url, "text": text},
		)
		async with httpx.AsyncClient(timeout=self.timeout) as client:
			response = await client.post(request_config["url"], headers=request_config["headers"], json=request_config["json"])
		response = self._validate_provider_response(response)
		data = self._parse_json_response(response)
		if data.get("success") is False:
			message = self._extract_error_message(data) or "Falha ao enviar documento pelo WhatsApp."
			raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=message)
		return {
			"success": True,
			"message": self._extract_error_message(data) or "Documento enviado com sucesso.",
			"chatid": chatid,
		}

	async def _get_whatsapp_config(
		self,
		*,
		required_phone: bool = False,
		required_user: bool = False,
		required_token: bool = False,
	) -> dict[str, Any]:
		parameter = await self.parameter_service.get_parameters()
		country_code = self._normalize_country_code(parameter.pais_whatsapp)
		ninth_digit_rules = self._parse_ninth_digit_rules(parameter.regra_nono_dig_whats)
		expected_phones = self._build_expected_phones(parameter, country_code, ninth_digit_rules)
		expected_phone = expected_phones[0] if expected_phones else None
		if required_phone and not expected_phones:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Configure o Telefone 1 ou Telefone 2 em Parametros antes de conectar o WhatsApp.",
			)

		session_key = self._clean_text(parameter.token_api_whatsapp) or settings.quepasa_token.strip() or "CONTRATOS"
		if required_token and not session_key:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Configure o token da API do WhatsApp em Parametros antes de conectar.",
			)

		quepasa_user = self._clean_text(parameter.usuario_api_whatsapp) or (settings.quepasa_user.strip() if settings.quepasa_user else None)
		if required_user and not quepasa_user:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Configure o usuario da API do WhatsApp em Parametros antes de gerar o QR Code.",
			)

		suffix = self._normalize_suffix(parameter.sufixo_whatsapp)

		return {
			"api_name": self._clean_text(parameter.api_whatsapp) or "quepasa",
			"session_key": session_key,
			"quepasa_user": quepasa_user,
			"country_code": country_code,
			"suffix": suffix,
			"ninth_digit_rules": ninth_digit_rules,
			"expected_phone": expected_phone,
			"expected_phones": expected_phones,
		}

	async def _get_quepasa_user(self, required: bool = False) -> str | None:
		config = await self._get_whatsapp_config(required_user=required)
		quepasa_user = config["quepasa_user"]
		if quepasa_user:
			return quepasa_user

		env_user = dotenv_values(ENV_FILE).get("QUEPASA_USER")
		if isinstance(env_user, str) and env_user.strip():
			return env_user.strip()

		if required:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Configure o usuário do QuePasa em QUEPASA_USER para gerar o QR Code.",
			)

		return None

	async def _get_info_payload(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
		config = config or await self._get_whatsapp_config(required_token=True)
		request_config = await self._build_api_request_config("verificar", config)
		async with httpx.AsyncClient(timeout=self.timeout) as client:
			response = await client.get(request_config["url"], headers=request_config["headers"])
		if response.status_code == status.HTTP_404_NOT_FOUND:
			return {}
		return self._parse_json_response(response)

	async def _get_api_health_status(self, config: dict[str, Any]) -> dict[str, Any]:
		request_config = await self._build_api_request_config("health", config)
		async with httpx.AsyncClient(timeout=self.timeout) as client:
			response = await client.get(request_config["url"], headers=request_config["headers"])

		if not response.is_success:
			message = self._extract_error_message_from_response(response)
			return {
				"available": False,
				"status": str(response.status_code),
				"message": message,
			}

		try:
			payload = self._parse_json_response(response)
		except HTTPException:
			return {
				"available": True,
				"status": "online",
				"message": "API do WhatsApp disponivel.",
			}

		available = self._is_api_health_available(payload)
		status_text = self._extract_api_health_status(payload, available)
		message = self._extract_error_message(payload) or (
			"API do WhatsApp disponivel." if available else "API do WhatsApp indisponivel."
		)
		return {
			"available": available,
			"status": status_text,
			"message": message,
		}

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
		config = await self._get_whatsapp_config(required_user=True, required_token=True)
		request_config = await self._build_api_request_config("conectar", config)
		async with httpx.AsyncClient(timeout=self.timeout) as client:
			response = await client.get(request_config["url"], headers=request_config["headers"])
		return self._validate_provider_response(response)

	async def _build_api_request_config(
		self,
		funcionalidade: str,
		config: dict[str, Any],
		*,
		extra_placeholders: dict[str, Any] | None = None,
	) -> dict[str, Any]:
		record = await self._get_api_config_record(config, funcionalidade)
		placeholders = self._build_api_placeholders(config, extra_placeholders)
		url = self._format_api_value(record.url, placeholders)
		if url is None:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"URL da API WhatsApp nao configurada para {funcionalidade}.")

		headers: dict[str, str] = {}
		for index in range(1, 6):
			key = getattr(record, f"key{index}")
			value = getattr(record, f"value{index}")
			formatted_key = self._clean_text(key)
			formatted_value = self._format_api_value(value, placeholders)
			if formatted_key and formatted_value:
				headers[formatted_key] = formatted_value

		body = self._format_api_value(record.body, placeholders)
		json_body: dict[str, Any] | None = None
		if body:
			try:
				parsed_body = json.loads(body)
			except ValueError as exc:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Body da API WhatsApp invalido para {funcionalidade}.") from exc
			if isinstance(parsed_body, dict):
				json_body = parsed_body

		return {"url": url, "headers": headers, "json": json_body}

	async def _get_api_config_record(self, config: dict[str, Any], funcionalidade: str):
		api_name = self._clean_text(config.get("api_name")) or "quepasa"
		record = await self.api_config_repository.get_by_name_and_functionality(api_name, funcionalidade)
		if record is None:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"API WhatsApp '{api_name}' nao configurada para {funcionalidade}.",
			)
		return record

	@classmethod
	def _build_api_placeholders(cls, config: dict[str, Any], extra_placeholders: dict[str, Any] | None = None) -> dict[str, str]:
		placeholders = {
			"api_whatsapp": str(config.get("api_name") or "quepasa"),
			"token_api_whatsapp": str(config.get("session_key") or ""),
			"usuario_api_whatsapp": str(config.get("quepasa_user") or ""),
			"pais_whatsapp": str(config.get("country_code") or "55"),
			"sufixo_whatsapp": str(config.get("suffix") or "@s.whatsapp.net"),
		}
		if extra_placeholders:
			for key, value in extra_placeholders.items():
				placeholders[key] = "" if value is None else str(value)
		return placeholders

	@classmethod
	def _format_api_value(cls, value: Any, placeholders: dict[str, str]) -> str | None:
		formatted = cls._clean_text(value)
		if formatted is None:
			return None
		for key, replacement in placeholders.items():
			formatted = formatted.replace(f"{{{key}}}", replacement)
		return decrypt_secret(formatted)

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
		config = await self._get_whatsapp_config(required_user=True, required_token=True)
		headers = {
			"Accept": "application/json",
			"X-QUEPASA-TOKEN": config["session_key"],
		}
		username = config["quepasa_user"]
		if username:
			headers["X-QUEPASA-USER"] = username
		if extra_headers and extra_headers.get("Accept") == "application/json":
			headers.pop("X-QUEPASA-USER", None)
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
			data = payload.get("data")
			if isinstance(data, dict):
				return WhatsAppService._extract_error_message(data)
		return None

	@staticmethod
	def _is_api_health_available(payload: dict[str, Any]) -> bool:
		for key in ("healthy", "ok", "available", "success", "connected", "online"):
			value = payload.get(key)
			if isinstance(value, bool):
				return value
			if isinstance(value, str):
				normalized = value.strip().lower()
				if normalized in {"true", "ok", "healthy", "online", "up", "available", "ready", "success"}:
					return True
				if normalized in {"false", "error", "down", "offline", "unavailable", "failed"}:
					return False

		status_text = WhatsAppService._extract_provider_status(payload)
		if status_text:
			normalized = status_text.strip().lower()
			if normalized in {"ok", "healthy", "online", "up", "available", "ready", "success"}:
				return True
			if normalized in {"error", "down", "offline", "unavailable", "failed"}:
				return False
		return True

	@staticmethod
	def _extract_api_health_status(payload: dict[str, Any], available: bool) -> str:
		status_text = WhatsAppService._extract_provider_status(payload)
		if status_text:
			return status_text
		for key in ("message", "detail"):
			value = payload.get(key)
			if isinstance(value, str) and value.strip():
				return value.strip()
		return "online" if available else "offline"

	@staticmethod
	def _extract_provider_status(payload: dict[str, Any]) -> str | None:
		for key in ("status", "stats", "state"):
			value = payload.get(key)
			if isinstance(value, str) and value.strip():
				return value.strip()
			if isinstance(value, int):
				return str(value)

		server = payload.get("server")
		if isinstance(server, dict):
			for key in ("status", "state"):
				value = server.get(key)
				if isinstance(value, str) and value.strip():
					return value.strip()

		data = payload.get("data")
		if isinstance(data, dict):
			for key in ("status", "state"):
				value = data.get(key)
				if isinstance(value, str) and value.strip():
					return value.strip()
			server = data.get("server")
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
		data = payload.get("data")
		if isinstance(data, dict):
			candidates.append(data.get("wid"))
			candidates.append(data.get("phone"))
			server = data.get("server")
			if isinstance(server, dict):
				candidates.append(server.get("wid"))
				candidates.append(server.get("phone"))

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
		data = payload.get("data")
		if isinstance(data, dict):
			if isinstance(data.get("verified"), bool):
				return bool(data.get("verified"))
			if isinstance(data.get("connected"), bool):
				return bool(data.get("connected"))
			server = data.get("server")
			if isinstance(server, dict) and isinstance(server.get("verified"), bool):
				return bool(server.get("verified"))
		return bool(payload.get("verified"))

	def _is_connected(
		self,
		payload: dict[str, Any],
		expected_phones: list[str],
		country_code: str,
		ninth_digit_rules: list[dict[str, Any]],
		connected_phone: str | None,
		verified: bool,
	) -> bool:
		provider_status = (self._extract_provider_status(payload) or "").strip().lower()
		data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
		ready_by_status = provider_status in {"1", "ready", "connected", "online"}
		data_success = data.get("success") is True if isinstance(data, dict) else False
		ready_by_flags = (payload.get("success") is True or data_success) and (verified or data.get("connected") is True)
		if not (ready_by_status or ready_by_flags):
			return False
		if not connected_phone:
			return verified and not expected_phones
		if not expected_phones:
			return True
		return any(
			self._phone_matches(expected_phone, connected_phone, country_code, ninth_digit_rules)
			for expected_phone in expected_phones
		)

	@staticmethod
	def _build_status_message(
		expected_phones: list[str],
		country_code: str,
		ninth_digit_rules: list[dict[str, Any]],
		connected_phone: str | None,
		provider_status: str | None,
		verified: bool,
		connected: bool,
	) -> str:
		if verified and connected_phone and expected_phones and not any(
			WhatsAppService._phone_matches(expected_phone, connected_phone, country_code, ninth_digit_rules)
			for expected_phone in expected_phones
		):
			return f"Existe uma conta conectada, mas o numero {connected_phone} nao corresponde ao Telefone 1 ou Telefone 2."
		if connected and connected_phone:
			return f"Conta conectada no numero {connected_phone}."
		if expected_phones:
			if len(expected_phones) == 1:
				return f"Sessao aguardando conexao para o numero {expected_phones[0]}."
			return f"Sessao aguardando conexao para os numeros {expected_phones[0]} ou {expected_phones[1]}."
		if provider_status:
			return f"Status atual do provedor: {provider_status}."
		return "Sessao desconectada."

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

	@staticmethod
	def _clean_text(value: Any) -> str | None:
		if value is None:
			return None
		cleaned = str(value).strip()
		return cleaned or None

	@classmethod
	def _normalize_country_code(cls, value: Any) -> str:
		return cls._digits_only(value) or "55"

	@classmethod
	def _normalize_suffix(cls, value: Any) -> str:
		suffix = cls._clean_text(value)
		return suffix or "@s.whatsapp.net"

	@classmethod
	def _build_chatid(
		cls,
		phone_number: str,
		*,
		country_code: str,
		suffix: str,
		ninth_digit_rules: list[dict[str, Any]],
	) -> str:
		digits = cls._digits_only(phone_number)
		if not digits:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Numero de WhatsApp invalido para envio.")
		normalized = cls._normalize_chat_phone_digits(digits, country_code, ninth_digit_rules)
		return f"{country_code}{normalized}{suffix}"

	@staticmethod
	def _normalize_chat_phone_digits(phone_digits: str, country_code: str, ninth_digit_rules: list[dict[str, Any]]) -> str:
		normalized = phone_digits[len(country_code):] if phone_digits.startswith(country_code) else phone_digits
		if len(normalized) == 11 and normalized[2] == "9":
			ddd = int(normalized[:2])
			if not WhatsAppService._should_keep_ninth_digit(ddd, ninth_digit_rules):
				return f"{normalized[:2]}{normalized[3:]}"
		return normalized

	@classmethod
	def _phone_matches(
		cls,
		expected_phone: str,
		connected_phone: str,
		country_code: str,
		ninth_digit_rules: list[dict[str, Any]],
	) -> bool:
		return cls._normalize_chat_phone_digits(expected_phone, country_code, ninth_digit_rules) == cls._normalize_chat_phone_digits(
			connected_phone,
			country_code,
			ninth_digit_rules,
		)

	@classmethod
	def _build_expected_phones(
		cls,
		parameter: Any,
		country_code: str,
		ninth_digit_rules: list[dict[str, Any]],
	) -> list[str]:
		phone_entries = [
			(getattr(parameter, "telefone1", None), bool(getattr(parameter, "flag_whatsapp_telefone1", False))),
			(getattr(parameter, "telefone2", None), bool(getattr(parameter, "flag_whatsapp_telefone2", False))),
		]
		candidate_phones = [phone for phone, enabled in phone_entries if enabled] or [phone for phone, _ in phone_entries]
		phones: list[str] = []
		for raw_phone in candidate_phones:
			digits = cls._digits_only(raw_phone)
			if not digits:
				continue
			normalized = cls._normalize_chat_phone_digits(digits, country_code, ninth_digit_rules)
			formatted = f"{country_code}{normalized}"
			if formatted not in phones:
				phones.append(formatted)
		return phones

	@staticmethod
	def _parse_ninth_digit_rules(value: Any) -> list[dict[str, Any]]:
		if isinstance(value, dict):
			value = [value]
		elif isinstance(value, str):
			parsed = WhatsAppService._parse_rule_string(value)
			value = [parsed] if isinstance(parsed, dict) else []
		if not isinstance(value, list):
			return []

		rules: list[dict[str, Any]] = []
		for item in value:
			candidate = item
			if isinstance(item, str):
				candidate = WhatsAppService._parse_rule_string(item)
			if isinstance(candidate, dict):
				field_name = WhatsAppService._clean_text(candidate.get("campo"))
				operator = WhatsAppService._clean_text(candidate.get("operador"))
				if field_name and operator:
					rules.append(
						{
							"campo": field_name.upper(),
							"operador": operator.lower(),
							"valor": candidate.get("valor"),
						}
					)
		return rules

	@staticmethod
	def _parse_rule_string(value: str) -> dict[str, Any] | None:
		cleaned = value.strip()
		if not cleaned:
			return None
		for parser in (json.loads, literal_eval):
			try:
				parsed = parser(cleaned)
			except (ValueError, SyntaxError):
				continue
			if isinstance(parsed, dict):
				return parsed
		return None

	@staticmethod
	def _should_keep_ninth_digit(ddd: int, rules: list[dict[str, Any]]) -> bool:
		if not rules:
			return 11 <= ddd <= 29
		for rule in rules:
			if rule.get("campo") != "DDD":
				continue
			if WhatsAppService._matches_rule(ddd, rule.get("operador"), rule.get("valor")):
				return True
		return False

	@staticmethod
	def _matches_rule(number: int, operator: Any, value: Any) -> bool:
		normalized_operator = str(operator or "").strip().lower()
		if normalized_operator == "between":
			if not isinstance(value, list) or len(value) != 2:
				return False
			lower = WhatsAppService._to_int(value[0])
			upper = WhatsAppService._to_int(value[1])
			if lower is None or upper is None:
				return False
			return lower <= number <= upper
		if normalized_operator in {"=", "==", "eq"}:
			compare = WhatsAppService._to_int(value)
			return compare is not None and number == compare
		if normalized_operator in {"!=", "<>", "ne"}:
			compare = WhatsAppService._to_int(value)
			return compare is not None and number != compare
		if normalized_operator == "in":
			if not isinstance(value, list):
				return False
			return any(number == candidate for candidate in (WhatsAppService._to_int(item) for item in value) if candidate is not None)
		if normalized_operator in {"not in", "nin"}:
			if not isinstance(value, list):
				return False
			candidates = [candidate for candidate in (WhatsAppService._to_int(item) for item in value) if candidate is not None]
			return bool(candidates) and number not in candidates
		if normalized_operator in {">", "gt"}:
			compare = WhatsAppService._to_int(value)
			return compare is not None and number > compare
		if normalized_operator in {">=", "gte"}:
			compare = WhatsAppService._to_int(value)
			return compare is not None and number >= compare
		if normalized_operator in {"<", "lt"}:
			compare = WhatsAppService._to_int(value)
			return compare is not None and number < compare
		if normalized_operator in {"<=", "lte"}:
			compare = WhatsAppService._to_int(value)
			return compare is not None and number <= compare
		return False

	@staticmethod
	def _to_int(value: Any) -> int | None:
		try:
			return int(value)
		except (TypeError, ValueError):
			return None

