from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import PaginatedResponse, PaginationParams


class NegotiationContractItem(BaseModel):
    contrato_id: int
    valor_aberto: float = 0


class NegotiationCreateRequest(BaseModel):
    cliente_id: int
    contratos_ids: list[int]
    qtde_parcelas: int
    valor_parcela: float
    obs: str | None = None
    cobranca_segunda: bool = True
    cobranca_terca: bool = True
    cobranca_quarta: bool = True
    cobranca_quinta: bool = True
    cobranca_sexta: bool = True
    cobranca_sabado: bool = False
    cobranca_domingo: bool = False
    cobranca_feriado: bool = False
    cobranca_mensal: bool = False
    cobranca_quinzenal: bool = False


class NegotiationContractRead(BaseModel):
    id: int
    negociacao_id: int
    contrato_id: int
    valor_aberto: float = 0

    model_config = ConfigDict(from_attributes=True)


class NegotiationRead(BaseModel):
    negociacao_id: int
    cliente_id: int | None = None
    cliente_nome: str | None = None
    data_negociacao: datetime | None = None
    valor_total_aberto: float = 0
    qtde_parcelas: int = 0
    valor_parcela: float = 0
    contrato_gerado_id: int | None = None
    usuario_id: int | None = None
    usuario_nome: str | None = None
    obs: str | None = None
    contrato_quitado: bool | None = None
    cobranca_segunda: bool = True
    cobranca_terca: bool = True
    cobranca_quarta: bool = True
    cobranca_quinta: bool = True
    cobranca_sexta: bool = True
    cobranca_sabado: bool = False
    cobranca_domingo: bool = False
    cobranca_feriado: bool = False
    cobranca_mensal: bool = False
    cobranca_quinzenal: bool = False
    contratos_originais: list[NegotiationContractRead] = []

    model_config = ConfigDict(from_attributes=True)


class NegotiationListParams(PaginationParams):
    cliente_nome: str | None = None
    contrato_gerado_id: int | None = None


class NegotiationListResponse(PaginatedResponse[NegotiationRead]):
    model_config = ConfigDict()


class OpenContractForNegotiation(BaseModel):
    contratos_id: int
    data_contrato: datetime | None = None
    valor_empretismo: float | None = None
    valor_em_aberto: float = 0
    valor_parcela: float | None = None
    qtde_dias: int | None = None
    quitado: bool | None = None

    model_config = ConfigDict(from_attributes=True)
