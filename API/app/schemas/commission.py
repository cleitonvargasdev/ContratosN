from datetime import date
from pydantic import BaseModel

class CommissionRead(BaseModel):
    comissao_id: int; tipo: str; situacao: str; funcionario_id: int; funcionario_nome: str
    contrato_id: int | None; recebimento_id: int | None; parcela_nro: int | None = None; competencia: date
    base_calculo: float; percentual: float; valor_comissao: float; conta_pagar_id: int | None; motivo: str | None

class CommissionReprocessRequest(BaseModel):
    contrato_id: int | None = None
    data_final: date | None = None
    funcionario_id: int | None = None
    comissao_ids: list[int] = []
    todos_carteira: bool = False

class CommissionCloseRequest(BaseModel):
    comissao_ids: list[int]
    vencimento: date
