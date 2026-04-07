from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import PaginatedResponse, PaginationParams


class ContractBase(BaseModel):
    data_lancto: datetime | None = None
    data_contrato: datetime | None = None
    cliente_id: int | None = None
    plano_id: int | None = None
    qtde_dias: int | None = None
    percent_juros: float | None = None
    valor_empretismo: float | None = None
    data_final: datetime | None = None
    valor_final: float | None = None
    quitado: bool | None = None
    obs: str | None = None
    valor_parcela: float | None = None
    user_add: int | None = None
    contrato_status: int
    negociacao_id: int | None = None
    usuario_id_vendedor: int | None = None
    comissao_percentual: float | None = None
    valor_comissao_previsto: float | None = None
    valor_comissao_apurada: float | None = None
    regra_comissao_id: int | None = None
    regra_juros_id: int | None = None
    recorrencia: bool | None = None


class ContractCreate(ContractBase):
    contratos_id: int


class ContractUpdate(ContractBase):
    pass


class ContractRead(ContractBase):
    contratos_id: int
    cliente_nome: str | None = None
    cliente_telefone: str | None = None
    valor_recebido: float = 0
    valor_em_aberto: float = 0
    valor_em_atraso: float = 0

    model_config = ConfigDict(from_attributes=True)


class ContractListParams(PaginationParams):
    contratos_id: int | None = None
    cliente_id: int | None = None
    contrato_status: int | None = None
    quitado: bool | None = None


class ContractListResponse(PaginatedResponse[ContractRead]):
    model_config = ConfigDict()