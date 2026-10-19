from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

MOTIVOS = {
    "entrada": ("Estoque inicial", "Compra", "Outros"),
    "baixa": ("Quebra", "Extravio", "Furto ou roubo", "Desgaste", "Descarte", "Outros"),
    "ajuste": ("Inventário", "Correção de lançamento", "Outros"),
    "devolucao": ("Devolução de cliente",),
}


class StockWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    operacao_id: UUID
    tipo: Literal["entrada", "baixa", "ajuste", "devolucao"]
    condicao: Literal["novo", "usado"]
    quantidade: int = Field(ge=0, le=1000000000, strict=True)
    motivo: str
    observacao: str = Field(min_length=3, max_length=1000)
    versao_esperada: int | None = None
    item_id: int | None = None

    @model_validator(mode="after")
    def validate_operation(self):
        if self.motivo not in MOTIVOS[self.tipo]:
            raise ValueError("Motivo inválido para esta operação")
        if self.tipo != "ajuste" and self.quantidade == 0:
            raise ValueError("Informe uma quantidade maior que zero")
        if self.tipo == "ajuste" and self.versao_esperada is None:
            raise ValueError("Informe a versão do estoque conferido")
        if (self.tipo == "devolucao") != (self.item_id is not None):
            raise ValueError("A devolução deve identificar o item vendido")
        return self


class StockMovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    movimento_id: int
    produto_id: int
    item_id: int | None
    usuario_nome: str
    criado_em: datetime
    tipo: str
    condicao: str
    quantidade: int
    saldo_antes: int
    saldo_depois: int
    motivo: str
    observacao: str | None


class StockHistory(BaseModel):
    items: list[StockMovementRead]
    total: int
    page: int
    page_size: int


class SaleConfirm(BaseModel):
    versao_esperada: int
