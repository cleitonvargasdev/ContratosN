from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_payable import ContaPagar, ContaPagarParcela, PagamentoContaPagar
from app.models.commission import ComissaoLancamento, ComissaoLote
from app.models.client import Cliente
from app.models.supplier import Fornecedor
from app.models.user import User
from app.repositories.accounts_payable_repository import AccountsPayableRepository
from app.schemas.accounts_payable import (
    AccountsPayableAddInstallmentsRequest,
    AccountsPayableCreate,
    AccountsPayableInstallmentCreate,
    AccountsPayableInstallmentRead,
    AccountsPayableListItem,
    AccountsPayableListParams,
    AccountsPayableListResponse,
    AccountsPayablePaymentCreate,
    AccountsPayablePaymentRead,
    AccountsPayablePersonSearchItem,
    AccountsPayableRead,
    AccountsPayableUpdate,
    PaymentMovementItem,
    PaymentMovementListParams,
    PaymentMovementListResponse,
)


class AccountsPayableService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = AccountsPayableRepository(session)

    async def list_accounts_payable(self, params: AccountsPayableListParams) -> AccountsPayableListResponse:
        if (
            params.data_vencimento_inicial is not None
            and params.data_vencimento_final is not None
            and params.data_vencimento_final < params.data_vencimento_inicial
        ):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Periodo de vencimento invalido.")

        items, total = await self.repository.list_accounts_payable(params)
        return AccountsPayableListResponse(
            items=[self._build_list_item(item) for item in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_account(self, conta_pagar_id: int) -> AccountsPayableRead | None:
        record = await self.repository.get_by_id(conta_pagar_id)
        return None if record is None else self._build_read(record)

    async def list_payment_movements(self, params: PaymentMovementListParams) -> PaymentMovementListResponse:
        if params.data_vencimento_final < params.data_vencimento_inicial:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Periodo de vencimento invalido.")

        person_name = func.coalesce(Cliente.nome, User.nome, Fornecedor.nome, "Sem pessoa")
        document = func.coalesce(Cliente.cpf_cnpj, User.cpf, Fornecedor.cpf_cnpj)
        phone = func.coalesce(Cliente.celular01, Cliente.telefone, User.celular, User.telefone, Fornecedor.telefone)
        person_type = ContaPagar.tipo_pessoa
        base = (
            select(ContaPagarParcela, ContaPagar, person_name, document, phone, person_type)
            .join(ContaPagar, ContaPagar.conta_pagar_id == ContaPagarParcela.conta_pagar_id)
            .outerjoin(Cliente, Cliente.clientes_id == ContaPagar.cliente_id)
            .outerjoin(User, User.id == ContaPagar.usuario_id)
            .outerjoin(Fornecedor, Fornecedor.fornecedor_id == ContaPagar.fornecedor_id)
        )
        filters = []
        # Os status funcionam como dois filtros independentes: selecionando
        # somente um, mostra aquele status; ambos selecionados ou ambos
        # desmarcados incluem todas as parcelas.
        if params.aberto != params.quitado:
            filters.append(ContaPagarParcela.quitado.is_(params.quitado))
        if params.query:
            term = f"%{params.query.strip()}%"
            filters.append(or_(person_name.ilike(term), ContaPagar.descricao.ilike(term), ContaPagarParcela.descricao.ilike(term)))
        if params.data_vencimento_inicial:
            filters.append(ContaPagarParcela.vencimento >= params.data_vencimento_inicial)
        if params.data_vencimento_final:
            filters.append(ContaPagarParcela.vencimento <= params.data_vencimento_final)
        if filters:
            base = base.where(*filters)
        filtered = base.subquery()
        total = int((await self.repository.session.scalar(select(func.count()).select_from(filtered))) or 0)
        sums = (await self.repository.session.execute(
            select(
                func.coalesce(func.sum(filtered.c.valor_total), 0),
                func.coalesce(func.sum(filtered.c.valor_pago), 0),
                func.coalesce(func.sum(filtered.c.saldo_pagar), 0),
            ).select_from(filtered)
        )).one()
        rows = (await self.repository.session.execute(
            base.order_by(ContaPagarParcela.vencimento.asc(), ContaPagarParcela.parcela_id.desc())
            .offset((params.page - 1) * params.page_size).limit(params.page_size)
        )).all()
        payment_dates = {}
        if rows:
            ids = [item.parcela_id for item, *_ in rows]
            payment_dates = dict((await self.repository.session.execute(
                select(PagamentoContaPagar.parcela_id, func.max(PagamentoContaPagar.data_pagamento)).where(PagamentoContaPagar.parcela_id.in_(ids)).group_by(PagamentoContaPagar.parcela_id)
            )).all())
        return PaymentMovementListResponse(
            items=[PaymentMovementItem(parcela_id=installment.parcela_id, conta_pagar_id=account.conta_pagar_id, vencimento=installment.vencimento, quitado=installment.quitado, data_pagamento=payment_dates.get(installment.parcela_id), descricao=installment.descricao or account.descricao, pessoa_nome=name, pessoa_tipo=kind, documento=doc, telefone=telephone, valor_total=float(installment.valor_total or 0), valor_pago=float(installment.valor_pago or 0), saldo_pagar=float(installment.saldo_pagar or 0)) for installment, account, name, doc, telephone, kind in rows],
            total=total, page=params.page, page_size=params.page_size,
            total_valor=float(sums[0] or 0), total_pago=float(sums[1] or 0), total_aberto=float(sums[2] or 0),
        )

    async def search_people(self, query: str) -> list[AccountsPayablePersonSearchItem]:
        normalized = query.strip()
        if len(normalized) < 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe ao menos 3 caracteres para pesquisar.")
        clients, users, suppliers = await self.repository.search_people(normalized)
        items: list[AccountsPayablePersonSearchItem] = []
        items.extend(
            AccountsPayablePersonSearchItem(
                entity_id=item.clientes_id,
                tipo_pessoa="cliente",
                nome=str(item.nome or "Cliente sem nome"),
                cpf_cnpj=item.cpf_cnpj,
            )
            for item in clients
        )
        items.extend(
            AccountsPayablePersonSearchItem(
                entity_id=item.id,
                tipo_pessoa="funcionario",
                nome=item.nome,
                cpf_cnpj=item.cpf,
            )
            for item in users
        )
        items.extend(
            AccountsPayablePersonSearchItem(
                entity_id=item.fornecedor_id,
                tipo_pessoa="fornecedor",
                nome=item.nome,
                cpf_cnpj=item.cpf_cnpj,
            )
            for item in suppliers
        )
        items.sort(key=lambda item: (item.nome.lower(), item.tipo_pessoa, item.entity_id))
        return items

    async def create_account(self, payload: AccountsPayableCreate, current_user_id: int | None) -> AccountsPayableRead:
        if not payload.parcelas:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe ao menos uma parcela.")

        await self._validate_person_binding(payload.tipo_pessoa, payload.cliente_id, payload.usuario_id, payload.fornecedor_id)

        account = ContaPagar(
            descricao=payload.descricao,
            tipo_pessoa=payload.tipo_pessoa,
            cliente_id=payload.cliente_id,
            usuario_id=payload.usuario_id,
            fornecedor_id=payload.fornecedor_id,
            data_referencia_inicial=payload.data_referencia_inicial,
            data_referencia_final=payload.data_referencia_final,
            observacao=payload.observacao,
            usuario_lancamento_id=current_user_id,
            parcelas=[self._build_installment_model(item, index + 1) for index, item in enumerate(payload.parcelas)],
        )
        self._recalculate_account(account)
        await self.repository.add_account(account)
        hydrated = await self.repository.get_by_id(account.conta_pagar_id)
        if hydrated is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao carregar conta criada.")
        return self._build_read(hydrated)

    async def update_account(self, conta_pagar_id: int, payload: AccountsPayableUpdate) -> AccountsPayableRead | None:
        account = await self.repository.get_by_id(conta_pagar_id)
        if account is None:
            return None
        await self._validate_person_binding(payload.tipo_pessoa, payload.cliente_id, payload.usuario_id, payload.fornecedor_id)
        account.descricao = payload.descricao
        account.tipo_pessoa = payload.tipo_pessoa
        account.cliente_id = payload.cliente_id
        account.usuario_id = payload.usuario_id
        account.fornecedor_id = payload.fornecedor_id
        account.data_referencia_inicial = payload.data_referencia_inicial
        account.data_referencia_final = payload.data_referencia_final
        account.observacao = payload.observacao
        self._recalculate_account(account)
        await self.repository.commit()
        hydrated = await self.repository.get_by_id(conta_pagar_id)
        if hydrated is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao recarregar conta.")
        return self._build_read(hydrated)

    async def add_installments(self, conta_pagar_id: int, payload: AccountsPayableAddInstallmentsRequest) -> AccountsPayableRead:
        account = await self.repository.get_by_id(conta_pagar_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta a pagar nao encontrada")
        if not payload.parcelas:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhuma parcela informada")

        next_number = max((item.numero_parcela or 0 for item in account.parcelas), default=0)
        for item in payload.parcelas:
            next_number += 1
            account.parcelas.append(self._build_installment_model(item, next_number))
        self._recalculate_account(account)
        await self.repository.commit()
        hydrated = await self.repository.get_by_id(conta_pagar_id)
        if hydrated is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao recarregar conta.")
        return self._build_read(hydrated)

    async def register_payment(
        self,
        parcela_id: int,
        payload: AccountsPayablePaymentCreate,
        current_user_id: int | None,
    ) -> AccountsPayableInstallmentRead:
        installment = await self.repository.get_installment_by_id(parcela_id)
        if installment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela nao encontrada")

        juros = float(payload.juros or 0)
        acrescimos = float(payload.acrescimos or 0)
        desconto = float(payload.desconto or 0)
        installment.acrescimos = round(float(installment.acrescimos or 0) + juros + acrescimos, 4)
        installment.desconto = round(float(installment.desconto or 0) + desconto, 4)
        self._recalculate_installment(installment)

        remaining = max(float(installment.saldo_pagar or 0), 0)
        payment_value = remaining if payload.valor_pago is None else float(payload.valor_pago)
        if payment_value <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valor do pagamento deve ser maior que zero.")

        payment = PagamentoContaPagar(
            parcela_id=installment.parcela_id,
            usuario_id=current_user_id,
            data_pagamento=payload.data_pagamento or date.today(),
            valor_pago=payment_value,
            juros=juros,
            acrescimos=acrescimos,
            desconto=desconto,
            observacao=payload.observacao,
        )
        await self.repository.add_payment(payment)
        installment.valor_pago = round(float(installment.valor_pago or 0) + payment_value, 4)
        self._recalculate_installment(installment)
        if installment.conta is not None:
            self._recalculate_account(installment.conta)
            await self._sync_commission_batch(installment.conta)
        await self.repository.commit()
        refreshed = await self.repository.get_by_id(installment.conta_pagar_id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao recarregar conta.")
        selected = next((item for item in refreshed.parcelas if item.parcela_id == parcela_id), None)
        if selected is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao recarregar parcela.")
        return self._build_installment_read(selected)

    async def _sync_commission_batch(self, account: ContaPagar) -> None:
        batch = await self.repository.session.scalar(
            select(ComissaoLote).where(ComissaoLote.conta_pagar_id == account.conta_pagar_id)
        )
        if batch is None:
            return

        paid = bool(account.quitado)
        batch.situacao = 3 if paid else 2
        rows = (await self.repository.session.execute(
            select(ComissaoLancamento).where(ComissaoLancamento.lote_id == batch.lote_id)
        )).scalars().all()
        for row in rows:
            row.situacao = 'pago' if paid else 'em_lote'

    async def delete_account(self, conta_pagar_id: int) -> bool:
        account = await self.repository.get_by_id(conta_pagar_id)
        if account is None:
            return False
        if any(parcela.pagamentos for parcela in account.parcelas):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nao e possivel excluir uma conta com pagamentos registrados.",
            )
        await self.repository.delete_account(account)
        return True

    async def remove_installment_payments(self, parcela_id: int) -> AccountsPayableInstallmentRead:
        installment = await self.repository.get_installment_by_id(parcela_id)
        if installment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela nao encontrada")

        installment.acrescimos = round(float(installment.acrescimos or 0) - sum(float(item.juros or 0) + float(item.acrescimos or 0) for item in installment.pagamentos), 4)
        installment.desconto = round(float(installment.desconto or 0) - sum(float(item.desconto or 0) for item in installment.pagamentos), 4)
        installment.valor_pago = 0
        installment.pagamentos.clear()
        self._recalculate_installment(installment)
        if installment.conta is not None:
            self._recalculate_account(installment.conta)
            await self._sync_commission_batch(installment.conta)
        await self.repository.commit()
        refreshed = await self.repository.get_installment_by_id(parcela_id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao recarregar parcela.")
        return self._build_installment_read(refreshed)

    async def delete_installment(self, parcela_id: int) -> bool:
        installment = await self.repository.get_installment_by_id(parcela_id)
        if installment is None:
            return False
        account = installment.conta
        if account is not None:
            account.parcelas.remove(installment)
            self._recalculate_account(account)
        await self.repository.delete_installment(installment)
        return True

    def _build_installment_model(self, payload: AccountsPayableInstallmentCreate, fallback_number: int) -> ContaPagarParcela:
        installment = ContaPagarParcela(
            numero_parcela=payload.numero_parcela or fallback_number,
            descricao=payload.descricao,
            data_referencia_inicial=payload.data_referencia_inicial,
            data_referencia_final=payload.data_referencia_final,
            vencimento=payload.vencimento,
            valor_original=round(float(payload.valor_original or 0), 4),
            acrescimos=round(float(payload.acrescimos or 0), 4),
            desconto=round(float(payload.desconto or 0), 4),
            observacao=payload.observacao,
            valor_pago=0,
        )
        self._recalculate_installment(installment)
        return installment

    def _recalculate_installment(self, installment: ContaPagarParcela) -> None:
        valor_original = float(installment.valor_original or 0)
        acrescimos = float(installment.acrescimos or 0)
        desconto = float(installment.desconto or 0)
        valor_total = round(max(valor_original + acrescimos - desconto, 0), 4)
        valor_pago = round(float(installment.valor_pago or 0), 4)
        saldo = round(max(valor_total - valor_pago, 0), 4)
        installment.valor_total = valor_total
        installment.saldo_pagar = saldo
        installment.quitado = saldo <= 0

    def _recalculate_account(self, account: ContaPagar) -> None:
        total = 0.0
        paid = 0.0
        for installment in account.parcelas:
            self._recalculate_installment(installment)
            total += float(installment.valor_total or 0)
            paid += float(installment.valor_pago or 0)
        account.valor_total = round(total, 4)
        account.valor_pago = round(paid, 4)
        account.saldo_pagar = round(max(total - paid, 0), 4)
        account.quitado = account.saldo_pagar <= 0 and len(account.parcelas) > 0

    def _build_person_payload(self, account: ContaPagar) -> tuple[int, str, str | None]:
        if account.tipo_pessoa == "cliente" and account.cliente is not None:
            return account.cliente.clientes_id, str(account.cliente.nome or "Cliente sem nome"), account.cliente.cpf_cnpj
        if account.tipo_pessoa == "funcionario" and account.usuario is not None:
            return account.usuario.id, account.usuario.nome, account.usuario.cpf
        if account.tipo_pessoa == "fornecedor" and account.fornecedor is not None:
            return account.fornecedor.fornecedor_id, account.fornecedor.nome, account.fornecedor.cpf_cnpj
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta a pagar sem pessoa vinculada corretamente.")

    def _build_list_item(self, account: ContaPagar) -> AccountsPayableListItem:
        pessoa_id, pessoa_nome, pessoa_cpf_cnpj = self._build_person_payload(account)
        parcelas_ordenadas = sorted(account.parcelas, key=lambda item: (item.vencimento, item.numero_parcela))
        abertas = [item for item in parcelas_ordenadas if not item.quitado]
        return AccountsPayableListItem(
            conta_pagar_id=account.conta_pagar_id,
            descricao=account.descricao,
            tipo_pessoa=account.tipo_pessoa,
            pessoa_id=pessoa_id,
            pessoa_nome=pessoa_nome,
            pessoa_cpf_cnpj=pessoa_cpf_cnpj,
            data_referencia_inicial=account.data_referencia_inicial,
            data_referencia_final=account.data_referencia_final,
            proximo_vencimento=None if not abertas else abertas[0].vencimento,
            ultima_data_vencimento=None if not parcelas_ordenadas else parcelas_ordenadas[-1].vencimento,
            quantidade_parcelas=len(parcelas_ordenadas),
            quantidade_parcelas_abertas=len(abertas),
            valor_total=round(float(account.valor_total or 0), 4),
            valor_pago=round(float(account.valor_pago or 0), 4),
            saldo_pagar=round(float(account.saldo_pagar or 0), 4),
            quitado=bool(account.quitado),
        )

    def _build_installment_read(self, installment: ContaPagarParcela) -> AccountsPayableInstallmentRead:
        return AccountsPayableInstallmentRead(
            parcela_id=installment.parcela_id,
            numero_parcela=installment.numero_parcela,
            descricao=installment.descricao,
            data_referencia_inicial=installment.data_referencia_inicial,
            data_referencia_final=installment.data_referencia_final,
            vencimento=installment.vencimento,
            valor_original=round(float(installment.valor_original or 0), 4),
            acrescimos=round(float(installment.acrescimos or 0), 4),
            desconto=round(float(installment.desconto or 0), 4),
            valor_total=round(float(installment.valor_total or 0), 4),
            valor_pago=round(float(installment.valor_pago or 0), 4),
            saldo_pagar=round(float(installment.saldo_pagar or 0), 4),
            quitado=bool(installment.quitado),
            observacao=installment.observacao,
            pagamentos=[
                AccountsPayablePaymentRead(
                    pagamento_id=item.pagamento_id,
                    usuario_id=item.usuario_id,
                    created_at=item.created_at,
                    data_pagamento=item.data_pagamento,
                    valor_pago=round(float(item.valor_pago or 0), 4),
                    juros=round(float(item.juros or 0), 4),
                    acrescimos=round(float(item.acrescimos or 0), 4),
                    desconto=round(float(item.desconto or 0), 4),
                    observacao=item.observacao,
                )
                for item in installment.pagamentos
            ],
        )

    async def _validate_person_binding(
        self,
        tipo_pessoa: str,
        cliente_id: int | None,
        usuario_id: int | None,
        fornecedor_id: int | None,
    ) -> None:
        if tipo_pessoa == "cliente":
            if cliente_id is None or usuario_id is not None or fornecedor_id is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cliente deve informar apenas cliente_id.")
            if await self.repository.get_client_by_id(cliente_id) is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")
            return

        if tipo_pessoa == "funcionario":
            if usuario_id is None or cliente_id is not None or fornecedor_id is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Funcionario deve informar apenas usuario_id.")
            if await self.repository.get_user_by_id(usuario_id) is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionario nao encontrado")
            return

        if tipo_pessoa == "fornecedor":
            if fornecedor_id is None or cliente_id is not None or usuario_id is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fornecedor deve informar apenas fornecedor_id.")
            if await self.repository.get_supplier_by_id(fornecedor_id) is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor nao encontrado")
            return

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de pessoa invalido")

    def _build_read(self, account: ContaPagar) -> AccountsPayableRead:
        pessoa_id, pessoa_nome, pessoa_cpf_cnpj = self._build_person_payload(account)
        return AccountsPayableRead(
            conta_pagar_id=account.conta_pagar_id,
            descricao=account.descricao,
            tipo_pessoa=account.tipo_pessoa,
            cliente_id=account.cliente_id,
            usuario_id=account.usuario_id,
            fornecedor_id=account.fornecedor_id,
            data_referencia_inicial=account.data_referencia_inicial,
            data_referencia_final=account.data_referencia_final,
            observacao=account.observacao,
            pessoa_id=pessoa_id,
            pessoa_nome=pessoa_nome,
            pessoa_cpf_cnpj=pessoa_cpf_cnpj,
            valor_total=round(float(account.valor_total or 0), 4),
            valor_pago=round(float(account.valor_pago or 0), 4),
            saldo_pagar=round(float(account.saldo_pagar or 0), 4),
            quitado=bool(account.quitado),
            created_at=account.created_at,
            updated_at=account.updated_at,
            parcelas=[self._build_installment_read(item) for item in sorted(account.parcelas, key=lambda row: (row.numero_parcela, row.vencimento))],
        )
