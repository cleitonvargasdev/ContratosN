import logging
import json
import re
import unicodedata
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.security import create_access_token
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.whatsapp_chatbot import Solicitacao, WhatsAppChatbotSession
from app.repositories.accounts_receivable_repository import AccountsReceivableRepository
from app.repositories.whatsapp_chatbot_repository import WhatsAppChatbotRepository
from app.services.whatsapp_service import WhatsAppService


EXIT_WORDS = {"sair", "ok", "encerrar", "encerre", "fim", "finalizar"}
GREETING_WORDS = {"oi", "ola", "olá", "bom dia", "boa tarde", "boa noite", "iniciar", "inicio", "início"}
BACK_WORDS = {"0", "voltar"}
NAME_STOPWORDS = {"da", "das", "de", "do", "dos", "e"}
SESSION_TIMEOUT = timedelta(minutes=30)
logger = logging.getLogger(__name__)


class WhatsAppChatbotService:
    def __init__(self, session) -> None:
        self.repository = WhatsAppChatbotRepository(session)
        self.accounts_repository = AccountsReceivableRepository(session)
        self.whatsapp_service = WhatsAppService(session)

    async def handle_webhook_event(self, request: Request, payload: dict[str, Any]) -> dict[str, Any]:
        event = self._extract_event(payload)
        if event is None:
            logger.info("Webhook WhatsApp ignorado. payload_type=%s payload_summary=%s", type(payload).__name__, self._summarize_payload(payload))
            return {"success": True, "ignored": True}

        phone = event["phone"]
        chat_id = event["chat_id"]
        text = event["text"]
        logger.info("Webhook WhatsApp recebido. chat_id=%s phone=%s text=%s", chat_id, phone, text[:80])

        chatbot_session = await self.repository.get_session_by_chat_id(chat_id)
        if chatbot_session is None:
            chatbot_session = await self.repository.create_session(
                WhatsAppChatbotSession(
                    chat_id=chat_id,
                    phone=phone,
                    current_state="AWAITING_NAME",
                    last_interaction_at=datetime.now(UTC),
                )
            )

        chatbot_session.phone = phone

        if self._is_session_expired(chatbot_session):
            self._reset_session(chatbot_session)

        normalized_text = self._normalize_text(text)
        if normalized_text in EXIT_WORDS:
            response_text = self._close_session(chatbot_session)
        elif chatbot_session.current_state == "CLOSED":
            self._reset_session(chatbot_session)
            response_text = self._build_greeting_message() + "\n\nInforme seu nome completo."
        elif chatbot_session.current_state == "AWAITING_NAME":
            response_text = await self._handle_awaiting_name(chatbot_session, text)
        elif chatbot_session.current_state == "AWAITING_DOCUMENT":
            response_text = await self._handle_awaiting_document(chatbot_session, text)
        elif chatbot_session.current_state == "MENU":
            response_text = await self._handle_menu(chatbot_session, normalized_text)
        elif chatbot_session.current_state == "CONTRACT_STATUS_MENU":
            response_text = await self._handle_contract_status_menu(chatbot_session, normalized_text)
        elif chatbot_session.current_state == "CONTRACT_SELECTION":
            response_text = await self._handle_contract_selection(chatbot_session, normalized_text)
        elif chatbot_session.current_state == "PDF_CHOICE":
            response_text = await self._handle_pdf_choice(request, chatbot_session, normalized_text)
        elif chatbot_session.current_state == "LOAN_AMOUNT":
            response_text = await self._handle_loan_amount(chatbot_session, text)
        elif chatbot_session.current_state == "LOAN_FREQUENCY":
            response_text = await self._handle_loan_frequency(chatbot_session, normalized_text)
        elif chatbot_session.current_state == "LOAN_INSTALLMENTS":
            response_text = await self._handle_loan_installments(chatbot_session, text)
        elif chatbot_session.current_state == "LOAN_CONTACT_PHONE":
            response_text = await self._handle_loan_contact_phone(chatbot_session, text)
        elif chatbot_session.current_state == "LOAN_CONTACT_DOCUMENT":
            response_text = await self._handle_loan_contact_document(chatbot_session, text)
        else:
            self._reset_session(chatbot_session)
            response_text = self._build_greeting_message() + "\n\nInforme seu nome completo."

        chatbot_session.last_interaction_at = datetime.now(UTC)
        await self.repository.save_session(chatbot_session)
        await self.whatsapp_service.send_text_message(phone, response_text)
        return {"success": True, "ignored": False, "chat_id": chat_id, "state": chatbot_session.current_state}

    async def _handle_awaiting_name(self, chatbot_session: WhatsAppChatbotSession, text: str) -> str:
        normalized_text = self._normalize_text(text)
        if normalized_text in GREETING_WORDS:
            return self._build_greeting_message() + "\n\nInforme seu nome completo."

        cleaned_name = re.sub(r"\s+", " ", text).strip()
        if len(cleaned_name) < 3:
            return "Informe seu nome completo para localizar seu cadastro."

        chatbot_session.identified_name = cleaned_name
        chatbot_session.current_state = "AWAITING_DOCUMENT"
        return "Agora informe seu CPF ou CNPJ."

    async def _handle_awaiting_document(self, chatbot_session: WhatsAppChatbotSession, text: str) -> str:
        document_digits = self._extract_digits(text)
        if len(document_digits) not in {11, 14}:
            return "CPF ou CNPJ invalido. Informe apenas os numeros do documento."

        chatbot_session.identified_document = document_digits
        client = await self._find_best_client(chatbot_session.identified_name, document_digits, chatbot_session.phone)
        chatbot_session.client_id = client.clientes_id if client else None
        chatbot_session.current_state = "MENU"

        if client is not None:
            display_name = str(client.nome or chatbot_session.identified_name or "cliente").strip()
            return (
                f"Cadastro encontrado: {display_name}.\n\n"
                f"{self._build_main_menu()}"
            )

        return (
            "Cadastro nao localizado. Voce ainda pode solicitar um emprestimo pelo WhatsApp.\n\n"
            f"{self._build_main_menu()}"
        )

    async def _handle_menu(self, chatbot_session: WhatsAppChatbotSession, normalized_text: str) -> str:
        if normalized_text == "1":
            if chatbot_session.client_id is None:
                return "Cadastro nao localizado. Para solicitar um emprestimo escolha a opcao 2.\n\n" + self._build_main_menu()
            chatbot_session.current_state = "CONTRACT_STATUS_MENU"
            return self._build_contract_status_menu()

        if normalized_text == "2":
            chatbot_session.current_state = "LOAN_AMOUNT"
            return "Qual o valor pretendido?"

        if normalized_text == "3":
            if chatbot_session.client_id is not None:
                await self.repository.mark_client_opt_out(chatbot_session.client_id)
                chatbot_session.opted_out_at = datetime.now(UTC)
            return self._close_session(chatbot_session, "Voce nao recebera mais WhatsApp. Quando quiser retomar, mande uma saudacao.")

        if normalized_text in {"4", "sair", "encerrar", "fim"}:
            return self._close_session(chatbot_session)

        return self._build_main_menu()

    async def _handle_contract_status_menu(self, chatbot_session: WhatsAppChatbotSession, normalized_text: str) -> str:
        if normalized_text in BACK_WORDS:
            chatbot_session.current_state = "MENU"
            return self._build_main_menu()

        if normalized_text in {"3", "sair", "encerrar", "fim"}:
            return self._close_session(chatbot_session)

        if normalized_text not in {"1", "2"}:
            return self._build_contract_status_menu()

        quitado = normalized_text == "1"
        contracts = await self._list_contract_options(chatbot_session.client_id, quitado=quitado)
        if not contracts:
            status_text = "quitados" if quitado else "abertos"
            return f"Nenhum contrato {status_text} encontrado.\n\n{self._build_contract_status_menu()}"

        context = self._load_context(chatbot_session)
        context["available_contract_ids"] = [item["contract_id"] for item in contracts]
        context["selected_status"] = "quitado" if quitado else "aberto"
        context["contract_list_message"] = self._format_contract_list_message(contracts, quitado=quitado)
        self._save_context(chatbot_session, context)
        chatbot_session.current_state = "CONTRACT_SELECTION"
        return str(context["contract_list_message"])

    async def _handle_contract_selection(self, chatbot_session: WhatsAppChatbotSession, normalized_text: str) -> str:
        if normalized_text in BACK_WORDS:
            chatbot_session.current_state = "CONTRACT_STATUS_MENU"
            return self._build_contract_status_menu()

        if normalized_text in {"3", "sair", "encerrar", "fim"}:
            return self._close_session(chatbot_session)

        context = self._load_context(chatbot_session)
        available_contract_ids = {str(contract_id) for contract_id in context.get("available_contract_ids", [])}
        if normalized_text not in available_contract_ids:
            return "Informe um numero de contrato que esteja na lista enviada."

        contract_id = int(normalized_text)
        selected_status = str(context.get("selected_status") or "aberto")
        detail_message = await self._build_contract_detail_message(contract_id, selected_status)
        context["selected_contract_id"] = contract_id
        self._save_context(chatbot_session, context)
        chatbot_session.current_state = "PDF_CHOICE"
        return detail_message + "\n\n" + self._build_pdf_menu()

    async def _handle_pdf_choice(self, request: Request, chatbot_session: WhatsAppChatbotSession, normalized_text: str) -> str:
        context = self._load_context(chatbot_session)

        if normalized_text in BACK_WORDS:
            chatbot_session.current_state = "CONTRACT_SELECTION"
            return str(context.get("contract_list_message") or "")

        if normalized_text in {"3", "sair", "encerrar", "fim"}:
            return self._close_session(chatbot_session)

        if normalized_text == "2":
            chatbot_session.current_state = "MENU"
            return self._build_main_menu()

        if normalized_text != "1":
            return self._build_pdf_menu()

        contract_id = context.get("selected_contract_id")
        if not isinstance(contract_id, int):
            chatbot_session.current_state = "MENU"
            return self._build_main_menu()

        pdf_url = self._build_public_contract_pdf_url(request, contract_id)
        await self.whatsapp_service.send_document_message(
            chatbot_session.phone or "",
            pdf_url,
            f"Segue o PDF do contrato {contract_id}.",
        )
        chatbot_session.current_state = "MENU"
        return f"PDF do contrato {contract_id} enviado com sucesso.\n\n{self._build_main_menu()}"

    async def _handle_loan_amount(self, chatbot_session: WhatsAppChatbotSession, text: str) -> str:
        amount = self._parse_decimal(text)
        if amount is None or amount <= 0:
            return "Informe um valor pretendido valido. Exemplo: 1500 ou 1500,00"

        context = self._load_context(chatbot_session)
        context["loan_amount"] = amount
        self._save_context(chatbot_session, context)
        chatbot_session.current_state = "LOAN_FREQUENCY"
        return "Qual a frequencia?\n1-Diario\n2-Semanal\n3-Mensal\n4-Sair\n0-Voltar"

    async def _handle_loan_frequency(self, chatbot_session: WhatsAppChatbotSession, normalized_text: str) -> str:
        if normalized_text in BACK_WORDS:
            chatbot_session.current_state = "LOAN_AMOUNT"
            return "Qual o valor pretendido?"

        if normalized_text in {"4", "sair", "encerrar", "fim"}:
            return self._close_session(chatbot_session)

        frequency_map = {"1": "DIARIO", "2": "SEMANAL", "3": "MENSAL"}
        frequency = frequency_map.get(normalized_text)
        if frequency is None:
            return "Escolha 1-Diario, 2-Semanal, 3-Mensal, 4-Sair ou 0-Voltar."

        context = self._load_context(chatbot_session)
        context["loan_frequency"] = frequency
        self._save_context(chatbot_session, context)
        chatbot_session.current_state = "LOAN_INSTALLMENTS"
        return "Em quantas parcelas?"

    async def _handle_loan_installments(self, chatbot_session: WhatsAppChatbotSession, text: str) -> str:
        installments = self._parse_integer(text)
        if installments is None or installments <= 0:
            return "Informe um numero de parcelas valido."

        context = self._load_context(chatbot_session)
        context["loan_installments"] = installments
        self._save_context(chatbot_session, context)

        if chatbot_session.client_id is not None:
            solicitation = await self._create_solicitacao(chatbot_session)
            chatbot_session.current_state = "MENU"
            return (
                f"Solicitacao registrada com numero {solicitation.id}. Retornaremos em breve.\n\n"
                f"{self._build_main_menu()}"
            )

        chatbot_session.current_state = "LOAN_CONTACT_PHONE"
        return "Informe um telefone para contato."

    async def _handle_loan_contact_phone(self, chatbot_session: WhatsAppChatbotSession, text: str) -> str:
        phone_digits = self._extract_digits(text)
        if len(phone_digits) < 10:
            return "Telefone invalido. Informe DDD e numero."

        context = self._load_context(chatbot_session)
        context["loan_contact_phone"] = phone_digits
        self._save_context(chatbot_session, context)
        chatbot_session.current_state = "LOAN_CONTACT_DOCUMENT"
        return "Agora informe o CPF ou CNPJ para contato."

    async def _handle_loan_contact_document(self, chatbot_session: WhatsAppChatbotSession, text: str) -> str:
        document_digits = self._extract_digits(text)
        if len(document_digits) not in {11, 14}:
            return "CPF ou CNPJ invalido. Informe apenas os numeros do documento."

        context = self._load_context(chatbot_session)
        context["loan_contact_document"] = document_digits
        self._save_context(chatbot_session, context)

        client = await self._find_best_client(chatbot_session.identified_name, document_digits, context.get("loan_contact_phone"))
        if client is not None:
            chatbot_session.client_id = client.clientes_id

        solicitation = await self._create_solicitacao(chatbot_session)
        chatbot_session.current_state = "MENU"
        return (
            f"Solicitacao registrada com numero {solicitation.id}. Retornaremos em breve.\n\n"
            f"{self._build_main_menu()}"
        )

    async def _find_best_client(self, name: str | None, document_digits: str | None, phone: str | None) -> Cliente | None:
        phone_digits = self._normalize_phone_digits(phone)
        candidates = await self.repository.find_client_candidates(name, document_digits, phone_digits)
        if not candidates:
            return None

        normalized_name = self._normalize_name(name)
        best_client: Cliente | None = None
        best_score = -1
        for candidate in candidates:
            score = 0
            candidate_document = self._extract_digits(str(candidate.cpf_cnpj or candidate.cnpj or ""))
            if document_digits and candidate_document == document_digits:
                score += 100

            candidate_name = self._normalize_name(candidate.nome)
            score += self._score_name(normalized_name, candidate_name)

            phones = [candidate.telefone, candidate.celular01, candidate.celular02, candidate.fone_responsavel, candidate.cel_responsavel]
            if phone_digits and any(self._phones_match(phone_digits, phone_value) for phone_value in phones):
                score += 40

            if score > best_score:
                best_client = candidate
                best_score = score

        return best_client if best_score >= 100 else None

    async def _list_contract_options(self, client_id: int | None, *, quitado: bool) -> list[dict[str, Any]]:
        if client_id is None:
            return []

        options: list[dict[str, Any]] = []
        for contract in await self.repository.list_contracts_for_client(client_id):
            installments = await self.repository.list_installments_for_contract(contract.contratos_id)
            totals = self.accounts_repository.build_contract_totals(installments)
            is_quitado = bool(totals["quitado"])
            if is_quitado != quitado:
                continue

            options.append(
                {
                    "contract_id": contract.contratos_id,
                    "data_contrato": contract.data_contrato,
                    "valor_parcela": float(contract.valor_parcela or 0),
                    "valor_em_aberto": float(totals["valor_em_aberto"] or 0),
                    "valor_pago": float(totals["valor_recebido"] or 0),
                }
            )
        return options

    async def _build_contract_detail_message(self, contract_id: int, selected_status: str) -> str:
        contract = await self.repository.get_contract_by_id(contract_id)
        if contract is None:
            return "Contrato nao encontrado."

        installments = await self.repository.list_installments_for_contract(contract_id)
        totals = self.accounts_repository.build_contract_totals(installments)
        last_receipt_date = max((item.data_recebimento for item in installments if item.data_recebimento is not None), default=None)

        if selected_status == "quitado":
            return (
                f"Contrato {contract_id}\n"
                f"Valor inicial: {self._format_currency(contract.valor_empretismo)}\n"
                f"Valor pago: {self._format_currency(totals['valor_recebido'])}\n"
                f"Quantidade parcelas: {len(installments)}\n"
                f"Valor parcela: {self._format_currency(contract.valor_parcela)}\n"
                f"Data quitacao: {self._format_date(last_receipt_date)}"
            )

        next_open_installment = next(
            (
                item
                for item in installments
                if not item.quitado and max(float(item.valor_total or 0) - float(item.valor_recebido or 0), 0) > 0
            ),
            None,
        )
        next_open_date = None if next_open_installment is None else (next_open_installment.vencimentol or next_open_installment.vencimento_original)
        return (
            f"Contrato {contract_id}\n"
            f"Data contrato: {self._format_date(contract.data_contrato)}\n"
            f"Valor pago: {self._format_currency(totals['valor_recebido'])}\n"
            f"Valor parcela: {self._format_currency(contract.valor_parcela)}\n"
            f"Valor em aberto: {self._format_currency(totals['valor_em_aberto'])}\n"
            f"Proxima parcela em aberto: {self._format_date(next_open_date)}"
        )

    async def _create_solicitacao(self, chatbot_session: WhatsAppChatbotSession) -> Solicitacao:
        context = self._load_context(chatbot_session)
        linked_client = await self.repository.get_client_by_id(chatbot_session.client_id)
        latest_contract = await self._get_latest_contract(chatbot_session.client_id)
        contact_phone = context.get("loan_contact_phone") or self._extract_digits(chatbot_session.phone or "")
        document_digits = context.get("loan_contact_document") or chatbot_session.identified_document

        solicitation = Solicitacao(
            cliente_id=chatbot_session.client_id,
            session_id=chatbot_session.id,
            nome_informado=chatbot_session.identified_name,
            telefone=str(contact_phone or "")[:20] or None,
            cpf_cnpj=str(document_digits or "")[:18] or None,
            valor_pretendido=float(context.get("loan_amount") or 0) or None,
            frequencia_pagamento=context.get("loan_frequency"),
            numero_parcelas=self._parse_integer(context.get("loan_installments")),
            tipo="WhatsApp",
            status="PENDENTE",
            vendedor_id=None if latest_contract is None else latest_contract.usuario_id_vendedor,
            valor_parcela=None if latest_contract is None else float(latest_contract.valor_parcela or 0),
            taxa_juros=None if latest_contract is None else float(latest_contract.percent_juros or 0),
            contrato_id=None if latest_contract is None else latest_contract.contratos_id,
            usuario_id_aprovou=None,
            observacao=(
                None
                if linked_client is not None
                else "Solicitacao criada sem cliente previamente identificado pelo chatbot do WhatsApp."
            ),
        )
        return await self.repository.create_solicitacao(solicitation)

    async def _get_latest_contract(self, client_id: int | None) -> Contrato | None:
        if client_id is None:
            return None
        contracts = await self.repository.list_contracts_for_client(client_id)
        return contracts[0] if contracts else None

    def _extract_event(self, payload: Any) -> dict[str, str] | None:
        candidate = self._find_message_candidate(payload)
        if not isinstance(candidate, dict):
            return None
        if candidate.get("fromme") or candidate.get("frominternal"):
            return None
        if str(candidate.get("type") or "").lower() != "text":
            return None

        text = str(candidate.get("text") or "").strip()
        chat = candidate.get("chat") or {}
        chat_id = str(chat.get("id") or candidate.get("chatid") or candidate.get("chatId") or "").strip()
        phone = str(chat.get("phone") or candidate.get("phone") or "").strip()
        if not phone and chat_id.endswith("@s.whatsapp.net"):
            phone = self._extract_digits(chat_id)
            if phone.startswith("55") and len(phone) > 11:
                phone = phone[2:]

        if not text or not chat_id or not phone:
            return None
        return {"text": text, "chat_id": chat_id, "phone": phone}

    def _find_message_candidate(self, payload: Any) -> dict[str, Any] | None:
        if isinstance(payload, dict):
            if self._looks_like_message_payload(payload):
                return payload

            for key in ("data", "message", "messages", "event", "events", "result", "payload"):
                nested = payload.get(key)
                candidate = self._find_message_candidate(nested)
                if candidate is not None:
                    return candidate

        if isinstance(payload, list):
            for item in payload:
                candidate = self._find_message_candidate(item)
                if candidate is not None:
                    return candidate

        return None

    @staticmethod
    def _looks_like_message_payload(payload: dict[str, Any]) -> bool:
        return any(key in payload for key in ("text", "chat", "chatid", "chatId", "fromme", "frominternal", "type"))

    def _summarize_payload(self, payload: Any) -> str:
        if isinstance(payload, dict):
            top_keys = sorted(str(key) for key in payload.keys())
            summary = {"keys": top_keys[:10]}
            for key in ("type", "event", "chatid", "chatId", "phone", "fromme", "frominternal"):
                if key in payload:
                    summary[key] = payload.get(key)
            chat = payload.get("chat")
            if isinstance(chat, dict):
                summary["chat_keys"] = sorted(str(key) for key in chat.keys())[:10]
            return json.dumps(summary, ensure_ascii=True)

        if isinstance(payload, list):
            return json.dumps({"list_length": len(payload)}, ensure_ascii=True)

        return json.dumps({"value": str(payload)[:120]}, ensure_ascii=True)

    def _build_public_contract_pdf_url(self, request: Request, contract_id: int) -> str:
        token = create_access_token(
            {"sub": str(contract_id), "type": "contract_pdf"},
            settings.jwt_secret_key,
            settings.jwt_algorithm,
            expires_minutes=15,
        )
        route_path = request.app.url_path_for("print_contract_public", contract_id=str(contract_id))
        base_url = (settings.public_api_base_url or str(request.base_url)).rstrip("/")
        if any(loopback in base_url.lower() for loopback in ("127.0.0.1", "localhost", "0.0.0.0")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configure PUBLIC_API_BASE_URL com uma URL publica acessivel para enviar o PDF do contrato.",
            )
        return f"{base_url}{route_path}?token={token}"

    def _build_greeting_message(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            period = "bom dia"
        elif 12 <= hour < 18:
            period = "boa tarde"
        else:
            period = "boa noite"
        return f"Ola, {period}!"

    @staticmethod
    def _build_main_menu() -> str:
        return "O que voce deseja?\n1-Consultar um contrato\n2-Solicitar um emprestimo\n3-Nao receber mais whatsapp\n4-Sair"

    @staticmethod
    def _build_contract_status_menu() -> str:
        return "Escolha uma opcao:\n1-Quitado\n2-Aberto\n3-Sair\n0-Voltar"

    @staticmethod
    def _build_pdf_menu() -> str:
        return "Deseja o PDF do contrato?\n1-Sim\n2-Nao\n3-Sair\n0-Voltar"

    def _format_contract_list_message(self, contracts: list[dict[str, Any]], *, quitado: bool) -> str:
        title = "Contratos quitados" if quitado else "Contratos abertos"
        lines = [title + ":"]
        for item in contracts:
            lines.append(
                f"{item['contract_id']} - {self._format_date(item['data_contrato'])} - "
                f"Parcela {self._format_currency(item['valor_parcela'])} - "
                f"Pago {self._format_currency(item['valor_pago'])} - "
                f"Aberto {self._format_currency(item['valor_em_aberto'])}"
            )
        lines.append("Qual numero do contrato voce quer consultar?")
        return "\n".join(lines)

    def _close_session(self, chatbot_session: WhatsAppChatbotSession, message: str | None = None) -> str:
        chatbot_session.current_state = "CLOSED"
        chatbot_session.closed_at = datetime.now(UTC)
        return message or "Sessao encerrada. Quando quiser, mande uma saudacao para iniciar uma nova consulta."

    def _reset_session(self, chatbot_session: WhatsAppChatbotSession) -> None:
        chatbot_session.current_state = "AWAITING_NAME"
        chatbot_session.client_id = None
        chatbot_session.identified_name = None
        chatbot_session.identified_document = None
        chatbot_session.context_data = None
        chatbot_session.closed_at = None

    def _is_session_expired(self, chatbot_session: WhatsAppChatbotSession) -> bool:
        last_interaction_at = chatbot_session.last_interaction_at
        if last_interaction_at is None:
            return False
        return datetime.now(UTC) - last_interaction_at >= SESSION_TIMEOUT

    @staticmethod
    def _extract_digits(value: str) -> str:
        return re.sub(r"\D", "", value or "")

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").strip().lower())

    @classmethod
    def _normalize_name(cls, value: str | None) -> str:
        if not value:
            return ""
        normalized = unicodedata.normalize("NFKD", value)
        ascii_text = "".join(character for character in normalized if not unicodedata.combining(character))
        collapsed = re.sub(r"[^a-zA-Z0-9\s]", " ", ascii_text.lower())
        return re.sub(r"\s+", " ", collapsed).strip()

    @classmethod
    def _score_name(cls, expected_name: str, candidate_name: str) -> int:
        if not expected_name or not candidate_name:
            return 0
        if expected_name == candidate_name:
            return 60
        expected_tokens = [token for token in expected_name.split() if token not in NAME_STOPWORDS and len(token) >= 3]
        candidate_tokens = set(candidate_name.split())
        matches = sum(1 for token in expected_tokens if token in candidate_tokens)
        return matches * 12

    @classmethod
    def _normalize_phone_digits(cls, value: str | None) -> str | None:
        digits = cls._extract_digits(value or "")
        if digits.startswith("55") and len(digits) > 11:
            digits = digits[2:]
        return digits or None

    @classmethod
    def _phones_match(cls, incoming_phone: str, stored_phone: str | None) -> bool:
        normalized_incoming = cls._normalize_phone_digits(incoming_phone)
        normalized_stored = cls._normalize_phone_digits(stored_phone)
        if not normalized_incoming or not normalized_stored:
            return False
        comparable = {
            normalized_incoming,
            normalized_incoming[-10:],
            normalized_incoming[-11:],
        }
        if len(normalized_incoming) == 11 and normalized_incoming[2] == "9":
            comparable.add(normalized_incoming[:2] + normalized_incoming[3:])
        if len(normalized_incoming) == 10:
            comparable.add(normalized_incoming[:2] + "9" + normalized_incoming[2:])

        stored_comparable = {normalized_stored, normalized_stored[-10:], normalized_stored[-11:]}
        return bool(comparable.intersection(stored_comparable))

    @staticmethod
    def _format_currency(value: Any) -> str:
        numeric_value = float(value or 0)
        formatted = f"{numeric_value:,.2f}"
        return "R$ " + formatted.replace(",", "_").replace(".", ",").replace("_", ".")

    @staticmethod
    def _format_date(value: datetime | None) -> str:
        if value is None:
            return "Nao informado"
        return value.astimezone().strftime("%d/%m/%Y") if value.tzinfo else value.strftime("%d/%m/%Y")

    @staticmethod
    def _parse_decimal(value: str) -> float | None:
        if value is None:
            return None
        normalized = value.strip().replace("R$", "").replace(" ", "")
        if not normalized:
            return None
        if "," in normalized and "." in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        else:
            normalized = normalized.replace(",", ".")
        try:
            return round(float(normalized), 4)
        except ValueError:
            return None

    @staticmethod
    def _parse_integer(value: Any) -> int | None:
        digits = re.sub(r"\D", "", str(value or ""))
        return int(digits) if digits else None

    @staticmethod
    def _load_context(chatbot_session: WhatsAppChatbotSession) -> dict[str, Any]:
        raw_context = chatbot_session.context_data
        if not raw_context:
            return {}
        try:
            loaded = json.loads(raw_context)
        except ValueError:
            return {}
        return loaded if isinstance(loaded, dict) else {}

    @staticmethod
    def _save_context(chatbot_session: WhatsAppChatbotSession, context: dict[str, Any]) -> None:
        chatbot_session.context_data = json.dumps(context, ensure_ascii=True)