from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.whatsapp_chatbot import Solicitacao, WhatsAppChatbotSession


class WhatsAppChatbotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_session_by_chat_id(self, chat_id: str) -> WhatsAppChatbotSession | None:
        result = await self.session.execute(select(WhatsAppChatbotSession).where(WhatsAppChatbotSession.chat_id == chat_id))
        return result.scalar_one_or_none()

    async def create_session(self, chatbot_session: WhatsAppChatbotSession) -> WhatsAppChatbotSession:
        self.session.add(chatbot_session)
        await self.session.commit()
        await self.session.refresh(chatbot_session)
        return chatbot_session

    async def save_session(self, chatbot_session: WhatsAppChatbotSession) -> WhatsAppChatbotSession:
        await self.session.commit()
        await self.session.refresh(chatbot_session)
        return chatbot_session

    async def get_client_by_id(self, client_id: int | None) -> Cliente | None:
        if client_id is None:
            return None
        result = await self.session.execute(select(Cliente).where(Cliente.clientes_id == client_id))
        return result.scalar_one_or_none()

    async def find_client_candidates(self, name: str | None, document_digits: str | None, phone_digits: str | None) -> Sequence[Cliente]:
        filters = []

        if document_digits:
            normalized_cpf = func.regexp_replace(func.coalesce(Cliente.cpf_cnpj, ""), r"\D", "", "g")
            normalized_cnpj = func.regexp_replace(func.coalesce(Cliente.cnpj, ""), r"\D", "", "g")
            filters.append(or_(normalized_cpf == document_digits, normalized_cnpj == document_digits))

        name_tokens = [token for token in (name or "").split() if len(token) >= 3]
        if name:
            name_filters = [Cliente.nome.ilike(f"%{name}%")]
            name_filters.extend(Cliente.nome.ilike(f"%{token}%") for token in name_tokens[:5])
            filters.append(or_(*name_filters))

        if phone_digits:
            phone_suffixes = []
            for length in (11, 10, 9, 8):
                if len(phone_digits) >= length:
                    phone_suffixes.append(phone_digits[-length:])

            phone_columns = (
                Cliente.telefone,
                Cliente.celular01,
                Cliente.celular02,
                Cliente.fone_responsavel,
                Cliente.cel_responsavel,
            )
            phone_filters = []
            for column in phone_columns:
                normalized_phone = func.regexp_replace(func.coalesce(column, ""), r"\D", "", "g")
                for suffix in phone_suffixes:
                    phone_filters.append(func.right(normalized_phone, len(suffix)) == suffix)
            if phone_filters:
                filters.append(or_(*phone_filters))

        if not filters:
            return []

        stmt = select(Cliente).where(or_(*filters)).limit(60)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_contracts_for_client(self, client_id: int) -> Sequence[Contrato]:
        result = await self.session.execute(
            select(Contrato)
            .where(Contrato.cliente_id == client_id)
            .order_by(Contrato.data_contrato.desc(), Contrato.contratos_id.desc())
        )
        return result.scalars().all()

    async def get_contract_by_id(self, contract_id: int) -> Contrato | None:
        result = await self.session.execute(select(Contrato).where(Contrato.contratos_id == contract_id))
        return result.scalar_one_or_none()

    async def list_installments_for_contract(self, contract_id: int) -> Sequence[ContaReceber]:
        result = await self.session.execute(
            select(ContaReceber)
            .where(ContaReceber.contratos_id == contract_id)
            .order_by(ContaReceber.parcela_nro.asc(), ContaReceber.vencimentol.asc(), ContaReceber.id.asc())
        )
        return result.scalars().all()

    async def mark_client_opt_out(self, client_id: int) -> None:
        client = await self.get_client_by_id(client_id)
        if client is None:
            return
        client.nao_enviar_whatsapp = True
        await self.session.commit()

    async def create_solicitacao(self, solicitacao: Solicitacao) -> Solicitacao:
        self.session.add(solicitacao)
        await self.session.commit()
        await self.session.refresh(solicitacao)
        return solicitacao