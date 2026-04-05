from math import isclose

from fastapi import HTTPException, status

from app.repositories.payment_plan_repository import PaymentPlanRepository
from app.schemas.payment_plan import PaymentPlanCreate, PaymentPlanRead, PaymentPlanUpdate


class PaymentPlanService:
    def __init__(self, session) -> None:
        self.repository = PaymentPlanRepository(session)

    async def list_payment_plans(self, descricao: str | None = None) -> list[PaymentPlanRead]:
        return [PaymentPlanRead.model_validate(item) for item in await self.repository.list_payment_plans(descricao)]

    async def get_payment_plan(self, plano_id: int) -> PaymentPlanRead | None:
        record = await self.repository.get_by_id(plano_id)
        return PaymentPlanRead.model_validate(record) if record else None

    async def create_payment_plan(self, payload: PaymentPlanCreate) -> PaymentPlanRead:
        data = self._normalize_payload(payload.model_dump())
        saved = await self.repository.create(data)
        return PaymentPlanRead.model_validate(saved)

    async def update_payment_plan(self, plano_id: int, payload: PaymentPlanUpdate) -> PaymentPlanRead | None:
        record = await self.repository.get_by_id(plano_id)
        if record is None:
            return None
        data = {
            "descricao": record.descricao,
            "qtde_dias": record.qtde_dias,
            "percent_juros": record.percent_juros,
            "valor_parcela": record.valor_parcela,
            "valor_base": record.valor_base,
            "valor_final": record.valor_final,
        }
        data.update(payload.model_dump(exclude_unset=True))
        data = self._normalize_payload(data, partial=True)
        saved = await self.repository.update(record, data)
        return PaymentPlanRead.model_validate(saved)

    async def delete_payment_plan(self, plano_id: int) -> bool:
        record = await self.repository.get_by_id(plano_id)
        if record is None:
            return False
        await self.repository.delete(record)
        return True

    def _normalize_payload(self, values: dict[str, object], partial: bool = False) -> dict[str, object]:
        descricao = values.get("descricao")
        if not partial and descricao is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Descricao obrigatoria")
        if descricao is not None and not str(descricao).strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Descricao obrigatoria")

        for field in ("qtde_dias",):
            if field in values and values[field] is not None and int(values[field]) <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantidade de dias invalida")

        for field in ("percent_juros", "valor_parcela", "valor_base", "valor_final"):
            if field in values and values[field] is not None and float(values[field]) < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valores nao podem ser negativos")

        qtde_dias = int(values["qtde_dias"]) if values.get("qtde_dias") is not None else None
        percent_juros = float(values["percent_juros"]) if values.get("percent_juros") is not None else None
        valor_parcela = float(values["valor_parcela"]) if values.get("valor_parcela") is not None else None
        valor_base = float(values["valor_base"]) if values.get("valor_base") is not None else None

        if qtde_dias and valor_parcela is not None:
            values["valor_final"] = self._round_currency(valor_parcela * qtde_dias)

        if qtde_dias and valor_base is not None and percent_juros is not None and valor_parcela is None:
            valor_final = self._calculate_final_from_monthly_interest(valor_base, percent_juros, qtde_dias)
            values["valor_final"] = self._round_currency(valor_final)
            values["valor_parcela"] = self._round_currency(valor_final / qtde_dias)
        elif qtde_dias and valor_base is not None and valor_parcela is not None:
            valor_final = valor_parcela * qtde_dias
            juros = self._calculate_monthly_interest_from_final(valor_base, valor_final, qtde_dias)
            values["percent_juros"] = round(juros, 2)
            values["valor_final"] = self._round_currency(valor_final)

        for field in ("valor_parcela", "valor_base", "valor_final"):
            if values.get(field) is not None:
                values[field] = self._round_currency(float(values[field]))

        return values

    @staticmethod
    def _round_currency(value: float) -> float:
        return round(value + 1e-9, 2)

    def _calculate_final_from_monthly_interest(self, valor_base: float, percent_juros: float, qtde_dias: int) -> float:
        if qtde_dias <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantidade de dias invalida")

        if isclose(percent_juros, 0.0, abs_tol=1e-12):
            return valor_base

        rate = percent_juros / 100
        period_in_months = qtde_dias / 30
        return valor_base * ((1 + rate) ** period_in_months)

    def _calculate_monthly_interest_from_final(self, valor_base: float, valor_final: float, qtde_dias: int) -> float:
        if qtde_dias <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantidade de dias invalida")
        if valor_final <= 0 or valor_base <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valores invalidos para calculo")

        if valor_final < valor_base:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valor final invalido para calculo")
        if isclose(valor_final, valor_base, abs_tol=1e-9):
            return 0.0

        period_in_months = qtde_dias / 30
        if period_in_months <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantidade de dias invalida")

        return (((valor_final / valor_base) ** (1 / period_in_months)) - 1) * 100