from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.solicitation import (
    SolicitationClientBrief,
    SolicitationClientDraft,
    SolicitationCompleteContractRequest,
    SolicitationDetailRead,
    SolicitationLinkClientRequest,
    SolicitationListParams,
    SolicitationListResponse,
    SolicitationPendingCountRead,
    SolicitationRead,
    SolicitationContractDraft,
)
from app.repositories.solicitation_repository import SolicitationRepository


class SolicitationService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = SolicitationRepository(session)

    async def list_solicitations(self, params: SolicitationListParams) -> SolicitationListResponse:
        solicitations, total = await self.repository.list_all(params)
        items = [SolicitationRead.model_validate(item) for item in solicitations]
        return SolicitationListResponse(items=items, total=total, page=params.page, page_size=params.page_size)

    async def get_pending_count(self) -> SolicitationPendingCountRead:
        return SolicitationPendingCountRead(pendentes=await self.repository.count_pending())

    async def get_solicitation_detail(self, solicitation_id: int) -> SolicitationDetailRead | None:
        solicitation = await self.repository.get_by_id(solicitation_id)
        if solicitation is None:
            return None

        existing_client = await self.repository.get_client_by_id(solicitation.cliente_id)
        reference_contract = await self.repository.get_contract_by_id(solicitation.contrato_id)
        if reference_contract is None:
            reference_contract = await self.repository.get_latest_contract_for_client(solicitation.cliente_id)

        return SolicitationDetailRead(
            **SolicitationRead.model_validate(solicitation).model_dump(),
            cliente_existente=None if existing_client is None else SolicitationClientBrief.model_validate(existing_client),
            cliente_sugerido=self._build_client_draft(solicitation, existing_client),
            contrato_sugerido=self._build_contract_draft(solicitation, reference_contract),
        )

    async def link_client(self, solicitation_id: int, payload: SolicitationLinkClientRequest) -> SolicitationRead | None:
        solicitation = await self.repository.get_by_id(solicitation_id)
        if solicitation is None:
            return None

        client = await self.repository.get_client_by_id(payload.cliente_id)
        if client is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")

        solicitation.cliente_id = client.clientes_id
        if not solicitation.nome_informado and client.nome:
            solicitation.nome_informado = client.nome
        if not solicitation.cpf_cnpj and client.cpf_cnpj:
            solicitation.cpf_cnpj = client.cpf_cnpj
        if not solicitation.telefone:
            solicitation.telefone = (client.celular01 or client.telefone or None)
        await self.repository.save(solicitation)
        refreshed = await self.repository.get_by_id(solicitation_id)
        return None if refreshed is None else SolicitationRead.model_validate(refreshed)

    async def complete_with_contract(
        self,
        solicitation_id: int,
        payload: SolicitationCompleteContractRequest,
        *,
        current_user_id: int,
    ) -> SolicitationRead | None:
        solicitation = await self.repository.get_by_id(solicitation_id)
        if solicitation is None:
            return None

        contract = await self.repository.get_contract_by_id(payload.contrato_id)
        if contract is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")

        solicitation.contrato_id = contract.contratos_id
        solicitation.status = (payload.status or "APROVADO").strip().upper()
        solicitation.usuario_id_aprovou = current_user_id
        solicitation.datahora_aprovacao = datetime.now(UTC)
        if solicitation.cliente_id is None and contract.cliente_id is not None:
            solicitation.cliente_id = contract.cliente_id
        await self.repository.save(solicitation)
        refreshed = await self.repository.get_by_id(solicitation_id)
        return None if refreshed is None else SolicitationRead.model_validate(refreshed)

    async def reject(self, solicitation_id: int, *, current_user_id: int) -> SolicitationRead | None:
        solicitation = await self.repository.get_by_id(solicitation_id)
        if solicitation is None:
            return None

        solicitation.status = "REJEITADO"
        solicitation.usuario_id_aprovou = current_user_id
        solicitation.datahora_aprovacao = datetime.now(UTC)
        await self.repository.save(solicitation)
        refreshed = await self.repository.get_by_id(solicitation_id)
        return None if refreshed is None else SolicitationRead.model_validate(refreshed)

    @staticmethod
    def _build_client_draft(solicitation: object, existing_client: object | None) -> SolicitationClientDraft:
        if existing_client is not None:
            return SolicitationClientDraft(
                nome=getattr(existing_client, "nome", None),
                cpf_cnpj=getattr(existing_client, "cpf_cnpj", None),
                telefone=getattr(existing_client, "telefone", None),
                celular01=getattr(existing_client, "celular01", None),
                flag_whatsapp=bool(getattr(existing_client, "flag_whatsapp", False)),
            )
        phone_number = getattr(solicitation, "telefone", None)
        return SolicitationClientDraft(
            nome=getattr(solicitation, "nome_informado", None),
            cpf_cnpj=getattr(solicitation, "cpf_cnpj", None),
            telefone=phone_number,
            celular01=phone_number,
            flag_whatsapp=True,
        )

    @staticmethod
    def _build_contract_draft(solicitation: object, reference_contract: object | None) -> SolicitationContractDraft:
        return SolicitationContractDraft(
            contrato_referencia_id=getattr(reference_contract, "contratos_id", None),
            cliente_id=getattr(solicitation, "cliente_id", None),
            usuario_id_vendedor=(
                getattr(reference_contract, "usuario_id_vendedor", None)
                if reference_contract is not None
                else getattr(solicitation, "vendedor_id", None)
            ),
            regra_juros_id=getattr(reference_contract, "regra_juros_id", None),
            plano_id=getattr(reference_contract, "plano_id", None),
            qtde_dias=getattr(reference_contract, "qtde_dias", None),
            percent_juros=(
                getattr(reference_contract, "percent_juros", None)
                if reference_contract is not None
                else getattr(solicitation, "taxa_juros", None)
            ),
            valor_empretismo=getattr(solicitation, "valor_pretendido", None),
            valor_parcela=(
                getattr(reference_contract, "valor_parcela", None)
                if reference_contract is not None
                else getattr(solicitation, "valor_parcela", None)
            ),
            recorrencia=getattr(reference_contract, "recorrencia", None),
            aluguel=getattr(reference_contract, "aluguel", None),
            cobranca_segunda=getattr(reference_contract, "cobranca_segunda", None),
            cobranca_terca=getattr(reference_contract, "cobranca_terca", None),
            cobranca_quarta=getattr(reference_contract, "cobranca_quarta", None),
            cobranca_quinta=getattr(reference_contract, "cobranca_quinta", None),
            cobranca_sexta=getattr(reference_contract, "cobranca_sexta", None),
            cobranca_sabado=getattr(reference_contract, "cobranca_sabado", None),
            cobranca_domingo=getattr(reference_contract, "cobranca_domingo", None),
            cobranca_feriado=getattr(reference_contract, "cobranca_feriado", None),
            cobranca_mensal=getattr(reference_contract, "cobranca_mensal", None),
            cobranca_quinzenal=getattr(reference_contract, "cobranca_quinzenal", None),
            frequencia_pagamento=getattr(solicitation, "frequencia_pagamento", None),
            numero_parcelas=getattr(solicitation, "numero_parcelas", None),
        )
