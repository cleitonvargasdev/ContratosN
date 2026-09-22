from datetime import date

from pydantic import BaseModel, Field


class DashboardChartPoint(BaseModel):
    label: str
    previsto: float = 0
    recebido: float = 0


class DashboardEndingContract(BaseModel):
    contratos_id: int
    cliente_nome: str | None = None
    data_final: date | None = None
    valor_em_aberto: float = 0
    dias_para_finalizar: int


class DashboardSummaryRead(BaseModel):
    pontos: list[DashboardChartPoint] = Field(default_factory=list)
    contratos_finalizando: list[DashboardEndingContract] = Field(default_factory=list)
    total_contratos_finalizando: int = 0
