from pydantic import BaseModel, ConfigDict


class RegraJurosOptionRead(BaseModel):
    regra_juros_id: int
    descricao: str | None = None
    juros_dia: float | None = None
    mora_dia: float | None = None
    ativo: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class RegraComissaoOptionRead(BaseModel):
    regra_comissao_id: int
    descricao: str | None = None
    percentual_comissao: float | None = None
    com_quitacao: bool | None = None
    a_partir_perc_total: float | None = None
    ativo: bool | None = None

    model_config = ConfigDict(from_attributes=True)