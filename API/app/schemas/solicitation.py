from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import PaginatedResponse, PaginationParams


class SolicitationListParams(PaginationParams):
    status: str | None = None
    tipo: str | None = None
    cliente_id: int | None = None
    termo: str | None = None


class SolicitationClientBrief(BaseModel):
    clientes_id: int
    nome: str | None = None
    cpf_cnpj: str | None = None
    celular01: str | None = None
    telefone: str | None = None
    flag_whatsapp: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class SolicitationContractDraft(BaseModel):
    contrato_referencia_id: int | None = None
    cliente_id: int | None = None
    usuario_id_vendedor: int | None = None
    regra_juros_id: int | None = None
    plano_id: int | None = None
    qtde_dias: int | None = None
    percent_juros: float | None = None
    valor_empretismo: float | None = None
    valor_parcela: float | None = None
    recorrencia: bool | None = None
    aluguel: bool | None = None
    cobranca_segunda: bool | None = None
    cobranca_terca: bool | None = None
    cobranca_quarta: bool | None = None
    cobranca_quinta: bool | None = None
    cobranca_sexta: bool | None = None
    cobranca_sabado: bool | None = None
    cobranca_domingo: bool | None = None
    cobranca_feriado: bool | None = None
    cobranca_mensal: bool | None = None
    cobranca_quinzenal: bool | None = None
    frequencia_pagamento: str | None = None
    numero_parcelas: int | None = None


class SolicitationClientDraft(BaseModel):
    nome: str | None = None
    cpf_cnpj: str | None = None
    telefone: str | None = None
    celular01: str | None = None
    flag_whatsapp: bool = True


class SolicitationRead(BaseModel):
    id: int
    cliente_id: int | None = None
    cliente_nome: str | None = None
    session_id: int | None = None
    nome_informado: str | None = None
    telefone: str | None = None
    cpf_cnpj: str | None = None
    valor_pretendido: float | None = None
    frequencia_pagamento: str | None = None
    numero_parcelas: int | None = None
    tipo: str
    status: str
    vendedor_id: int | None = None
    vendedor_nome: str | None = None
    valor_parcela: float | None = None
    taxa_juros: float | None = None
    contrato_id: int | None = None
    usuario_id_aprovou: int | None = None
    usuario_nome_aprovou: str | None = None
    datahora_solicitacao: datetime
    datahora_aprovacao: datetime | None = None
    observacao: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SolicitationDetailRead(SolicitationRead):
    cliente_existente: SolicitationClientBrief | None = None
    cliente_sugerido: SolicitationClientDraft
    contrato_sugerido: SolicitationContractDraft


class SolicitationListResponse(PaginatedResponse[SolicitationRead]):
    model_config = ConfigDict()


class SolicitationPendingCountRead(BaseModel):
    pendentes: int


class SolicitationLinkClientRequest(BaseModel):
    cliente_id: int


class SolicitationCompleteContractRequest(BaseModel):
    contrato_id: int
    status: str = "APROVADO"
