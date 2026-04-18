from calendar import monthrange
from datetime import date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone import get_local_timezone
from app.models.accounts_receivable import ContaReceber
from app.models.contract import Contrato
from app.models.negotiation import Negociacao, NegociacaoContrato
from app.models.receipt import Recebimento
from app.repositories.accounts_receivable_repository import AccountsReceivableRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.contract_repository import ContractRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.negotiation_repository import NegotiationRepository
from app.services.client_metrics_service import ClientMetricsService
from app.schemas.negotiation import (
    NegotiationCreateRequest,
    NegotiationListParams,
    NegotiationListResponse,
    NegotiationRead,
    NegotiationContractRead,
    OpenContractForNegotiation,
)


class NegotiationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = NegotiationRepository(session)
        self.contract_repository = ContractRepository(session)
        self.accounts_repository = AccountsReceivableRepository(session)
        self.client_repository = ClientRepository(session)
        self.location_repository = LocationRepository(session)
        self.client_metrics_service = ClientMetricsService(session)
        self.local_timezone = get_local_timezone()

    async def list_negotiations(self, params: NegotiationListParams) -> NegotiationListResponse:
        negotiations, total = await self.repository.list_all(params)
        items: list[NegotiationRead] = []
        for neg in negotiations:
            contracts = await self.repository.get_negotiation_contracts(neg.negociacao_id)
            items.append(self._build_read(neg, contracts))
        return NegotiationListResponse(items=items, total=total, page=params.page, page_size=params.page_size)

    async def get_negotiation(self, negotiation_id: int) -> NegotiationRead | None:
        neg = await self.repository.get_by_id(negotiation_id)
        if neg is None:
            return None
        contracts = await self.repository.get_negotiation_contracts(neg.negociacao_id)
        return self._build_read(neg, contracts)

    async def list_open_contracts(self, cliente_id: int) -> list[OpenContractForNegotiation]:
        result = await self.session.execute(
            select(Contrato)
            .where(
                Contrato.cliente_id == cliente_id,
                or_(Contrato.quitado == False, Contrato.quitado.is_(None)),  # noqa: E712
            )
            .order_by(Contrato.contratos_id.asc())
        )
        contracts = result.scalars().all()
        items: list[OpenContractForNegotiation] = []
        has_changes = False

        for contract in contracts:
            installments = await self.accounts_repository.list_by_contract(contract.contratos_id)
            totals = self.accounts_repository.build_contract_totals(installments)

            for field in ("valor_final", "valor_recebido", "valor_em_aberto", "valor_em_atraso", "quitado"):
                new_value = totals[field]
                if getattr(contract, field) != new_value:
                    setattr(contract, field, new_value)
                    has_changes = True

            if float(contract.valor_em_aberto or 0) <= 0:
                continue

            items.append(
                OpenContractForNegotiation(
                    contratos_id=contract.contratos_id,
                    data_contrato=contract.data_contrato,
                    valor_empretismo=contract.valor_empretismo,
                    valor_em_aberto=contract.valor_em_aberto,
                    valor_parcela=contract.valor_parcela,
                    qtde_dias=contract.qtde_dias,
                    quitado=contract.quitado,
                )
            )

        if has_changes:
            await self.accounts_repository.commit()

        return items

    async def create_negotiation(self, payload: NegotiationCreateRequest, current_user_id: int, current_user_name: str) -> NegotiationRead:
        now = datetime.now(self.local_timezone)

        if payload.qtde_parcelas < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantidade de parcelas deve ser maior que zero")

        if payload.valor_parcela <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valor da parcela deve ser maior que zero")

        if payload.cobranca_mensal and payload.cobranca_quinzenal:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selecione apenas uma frequencia: mensal ou quinzenal")

        # Validate contracts exist and belong to the client
        selected_contracts: list[Contrato] = []
        total_open = 0.0
        for cid in dict.fromkeys(payload.contratos_ids):
            contract = await self.contract_repository.get_by_id(cid)
            if contract is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Contrato {cid} nao encontrado")
            if contract.cliente_id != payload.cliente_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Contrato {cid} nao pertence ao cliente selecionado")
            if contract.quitado:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Contrato {cid} ja esta quitado")
            selected_contracts.append(contract)
            total_open += float(contract.valor_em_aberto or 0)

        if not selected_contracts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selecione ao menos um contrato para negociar")
        # Get next contract ID
        max_id = await self.session.scalar(select(func.max(Contrato.contratos_id)))
        new_contract_id = (max_id or 0) + 1

        # Create negotiation record
        negotiation = Negociacao(
            cliente_id=payload.cliente_id,
            data_negociacao=now,
            valor_total_aberto=total_open,
            qtde_parcelas=payload.qtde_parcelas,
            valor_parcela=payload.valor_parcela,
            contrato_gerado_id=new_contract_id,
            usuario_id=current_user_id,
            obs=payload.obs,
            cobranca_segunda=payload.cobranca_segunda,
            cobranca_terca=payload.cobranca_terca,
            cobranca_quarta=payload.cobranca_quarta,
            cobranca_quinta=payload.cobranca_quinta,
            cobranca_sexta=payload.cobranca_sexta,
            cobranca_sabado=payload.cobranca_sabado,
            cobranca_domingo=payload.cobranca_domingo,
            cobranca_feriado=payload.cobranca_feriado,
            cobranca_mensal=payload.cobranca_mensal,
            cobranca_quinzenal=payload.cobranca_quinzenal,
        )
        await self.repository.create(negotiation)

        # Link original contracts
        for contract in selected_contracts:
            link = NegociacaoContrato(
                negociacao_id=negotiation.negociacao_id,
                contrato_id=contract.contratos_id,
                valor_aberto=float(contract.valor_em_aberto or 0),
            )
            await self.repository.create_negotiation_contract(link)

        # Create new contract from negotiation
        date_str = now.strftime("%d/%m/%Y")
        contract_ids_str = ", ".join(str(c.contratos_id) for c in selected_contracts)
        obs_text = (
            f"Negociado em {date_str}, por Usuario {current_user_name}, "
            f"gerado contrato {new_contract_id}. "
            f"Contratos originais: {contract_ids_str}"
        )
        if payload.obs:
            obs_text += f"\n{payload.obs}"

        new_contract = Contrato(
            contratos_id=new_contract_id,
            data_lancto=now,
            data_contrato=now,
            cliente_id=payload.cliente_id,
            valor_empretismo=total_open,
            qtde_dias=payload.qtde_parcelas,
            valor_parcela=payload.valor_parcela,
            valor_final=round(payload.valor_parcela * payload.qtde_parcelas, 4),
            valor_em_aberto=round(payload.valor_parcela * payload.qtde_parcelas, 4),
            obs=obs_text,
            user_add=current_user_id,
            contrato_status=1,
            negociacao_id=negotiation.negociacao_id,
            cobranca_segunda=payload.cobranca_segunda,
            cobranca_terca=payload.cobranca_terca,
            cobranca_quarta=payload.cobranca_quarta,
            cobranca_quinta=payload.cobranca_quinta,
            cobranca_sexta=payload.cobranca_sexta,
            cobranca_sabado=payload.cobranca_sabado,
            cobranca_domingo=payload.cobranca_domingo,
            cobranca_feriado=payload.cobranca_feriado,
            cobranca_mensal=payload.cobranca_mensal,
            cobranca_quinzenal=payload.cobranca_quinzenal,
        )
        self.session.add(new_contract)
        await self.session.flush()

        generated_installments = await self._build_installments(
            contract=new_contract,
            qtde_parcelas=payload.qtde_parcelas,
            valor_parcela=payload.valor_parcela,
            current_user_id=current_user_id,
            reference_datetime=now,
        )
        await self.accounts_repository.add_installments(generated_installments)
        if generated_installments:
            new_contract.data_final = generated_installments[-1].vencimentol or generated_installments[-1].vencimento_original

        # Settle all open installments of original contracts and mark them as negotiated
        for contract in selected_contracts:
            installments = await self.accounts_repository.list_by_contract(contract.contratos_id)
            for installment in installments:
                if not installment.quitado:
                    remaining_value = max(float(installment.valor_total or 0) - float(installment.valor_recebido or 0), 0)
                    self.session.add(
                        Recebimento(
                            contrato_id=contract.contratos_id,
                            valor_recebido=0,
                            usuario_id=current_user_id,
                            data_recebimento=now,
                            parcela_nro=installment.parcela_nro,
                            desconto=remaining_value,
                            juros=0,
                        )
                    )
                    installment.quitado = True
                    installment.data_recebimento = now
                    installment.desconto = float(installment.desconto or 0) + remaining_value

            # Mark the original contract
            contract.negociacao_id = negotiation.negociacao_id
            contract.quitado = True
            contract.valor_em_aberto = 0
            contract.valor_em_atraso = 0
            old_obs = (contract.obs or "").strip()
            neg_note = f"Negociado em {date_str}, por Usuario {current_user_name}, gerado contrato {new_contract_id}"
            contract.obs = f"{old_obs}\n{neg_note}".strip() if old_obs else neg_note

        await self.client_metrics_service.refresh_client_metrics(payload.cliente_id)
        await self.repository.commit()

        # Reload and return
        neg = await self.repository.get_by_id(negotiation.negociacao_id)
        contracts_links = await self.repository.get_negotiation_contracts(negotiation.negociacao_id)
        return self._build_read(neg, contracts_links)  # type: ignore[arg-type]

    async def _build_installments(
        self,
        *,
        contract: Contrato,
        qtde_parcelas: int,
        valor_parcela: float,
        current_user_id: int,
        reference_datetime: datetime,
    ) -> list[ContaReceber]:
        holidays = await self._load_contract_holidays(contract)
        installments: list[ContaReceber] = []
        previous_due = reference_datetime

        for parcela_nro in range(1, qtde_parcelas + 1):
            due_date = self._calculate_due_date(contract, previous_due, holidays, parcela_nro == 1)
            installments.append(
                ContaReceber(
                    contratos_id=contract.contratos_id,
                    vencimento_original=due_date,
                    vencimentol=due_date,
                    valor_base=valor_parcela,
                    valor_total=valor_parcela,
                    valor_recebido=0,
                    quitado=False,
                    usuarios_id=current_user_id,
                    parcela_nro=parcela_nro,
                    desconto=0,
                    valor_juros=0,
                )
            )
            previous_due = due_date

        return installments

    async def _load_contract_holidays(self, contract: Contrato) -> set[date]:
        holidays = await self.location_repository.list_feriados(nivel=1)
        holiday_dates = {item.data for item in holidays}

        if contract.cliente_id is None:
            return holiday_dates

        client = await self.client_repository.get_by_id(contract.cliente_id)
        if client is None:
            return holiday_dates

        if client.uf:
            state_holidays = await self.location_repository.list_feriados(nivel=2, uf=client.uf)
            holiday_dates.update(item.data for item in state_holidays)

        if client.cidade_id is not None:
            city_holidays = await self.location_repository.list_feriados(nivel=3, cidade_id=client.cidade_id)
            holiday_dates.update(item.data for item in city_holidays)

        return holiday_dates

    def _calculate_due_date(
        self,
        contract: Contrato,
        previous_due: datetime,
        holidays: set[date],
        first_installment: bool,
    ) -> datetime:
        if first_installment:
            return self._move_to_next_allowed_due_date(previous_due, contract, holidays)

        if bool(contract.cobranca_mensal):
            candidate = self._add_months(previous_due, 1)
            return self._move_to_next_allowed_due_date(candidate, contract, holidays)

        if bool(contract.cobranca_quinzenal):
            candidate = previous_due + timedelta(days=15)
            return self._move_to_next_allowed_due_date(candidate, contract, holidays)

        allowed_weekdays = self._get_allowed_weekdays(contract)
        candidate = previous_due + timedelta(days=1)
        safety = 0
        while not self._is_allowed_due_date(candidate, contract, holidays, allowed_weekdays):
            candidate += timedelta(days=1)
            safety += 1
            if safety > 370:
                break
        return candidate

    def _move_to_next_allowed_due_date(self, value: datetime, contract: Contrato, holidays: set[date]) -> datetime:
        candidate = value
        allowed_weekdays = self._get_allowed_weekdays(contract)
        safety = 0
        while not self._is_allowed_due_date(candidate, contract, holidays, allowed_weekdays):
            candidate += timedelta(days=1)
            safety += 1
            if safety > 370:
                break
        return candidate

    @staticmethod
    def _get_allowed_weekdays(contract: Contrato) -> set[int]:
        allowed_weekdays: set[int] = set()
        if bool(contract.cobranca_domingo):
            allowed_weekdays.add(6)
        if bool(contract.cobranca_segunda):
            allowed_weekdays.add(0)
        if bool(contract.cobranca_terca):
            allowed_weekdays.add(1)
        if bool(contract.cobranca_quarta):
            allowed_weekdays.add(2)
        if bool(contract.cobranca_quinta):
            allowed_weekdays.add(3)
        if bool(contract.cobranca_sexta):
            allowed_weekdays.add(4)
        if bool(contract.cobranca_sabado):
            allowed_weekdays.add(5)
        return allowed_weekdays or {0, 1, 2, 3, 4}

    @staticmethod
    def _is_allowed_due_date(value: datetime, contract: Contrato, holidays: set[date], allowed_weekdays: set[int]) -> bool:
        if value.weekday() not in allowed_weekdays:
            return False
        if not bool(contract.cobranca_feriado) and value.date() in holidays:
            return False
        return True

    @staticmethod
    def _add_months(value: datetime, months: int) -> datetime:
        month_index = value.month - 1 + months
        year = value.year + month_index // 12
        month = month_index % 12 + 1
        day = min(value.day, monthrange(year, month)[1])
        return value.replace(year=year, month=month, day=day)

    @staticmethod
    def _build_read(neg: Negociacao, contracts: list[NegociacaoContrato]) -> NegotiationRead:
        return NegotiationRead(
            negociacao_id=neg.negociacao_id,
            cliente_id=neg.cliente_id,
            cliente_nome=getattr(neg, "cliente_nome", None),
            data_negociacao=neg.data_negociacao,
            valor_total_aberto=neg.valor_total_aberto,
            qtde_parcelas=neg.qtde_parcelas,
            valor_parcela=neg.valor_parcela,
            contrato_gerado_id=neg.contrato_gerado_id,
            usuario_id=neg.usuario_id,
            usuario_nome=getattr(neg, "usuario_nome", None),
            obs=neg.obs,
            contrato_quitado=getattr(neg, "contrato_quitado", None),
            cobranca_segunda=neg.cobranca_segunda,
            cobranca_terca=neg.cobranca_terca,
            cobranca_quarta=neg.cobranca_quarta,
            cobranca_quinta=neg.cobranca_quinta,
            cobranca_sexta=neg.cobranca_sexta,
            cobranca_sabado=neg.cobranca_sabado,
            cobranca_domingo=neg.cobranca_domingo,
            cobranca_feriado=neg.cobranca_feriado,
            cobranca_mensal=neg.cobranca_mensal,
            cobranca_quinzenal=neg.cobranca_quinzenal,
            contratos_originais=[
                NegotiationContractRead(
                    id=c.id,
                    negociacao_id=c.negociacao_id,
                    contrato_id=c.contrato_id,
                    valor_aberto=c.valor_aberto,
                )
                for c in contracts
            ],
        )
