from pydantic import BaseModel, ConfigDict


class RegraJurosOptionRead(BaseModel):
    regra_juros_id: int
    descricao: str | None = None
    juros_dia: float | None = None
    mora_dia: float | None = None
    ativo: bool | None = None

    model_config = ConfigDict(from_attributes=True)