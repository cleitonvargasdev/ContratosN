from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ComissaoLancamento(Base):
    __tablename__ = "comissoes_lancamentos"

    comissao_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(String(12), nullable=False, index=True)  # venda | cobranca | ajuste
    situacao: Mapped[str] = mapped_column(String(16), nullable=False, default="pendente", index=True)
    funcionario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    contrato_id: Mapped[int | None] = mapped_column(ForeignKey("contratos.contratos_id", ondelete="SET NULL"), nullable=True, index=True)
    recebimento_id: Mapped[int | None] = mapped_column(ForeignKey("recebimentos.recebimento_id", ondelete="SET NULL"), nullable=True, index=True)
    competencia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    base_calculo: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False)
    percentual: Mapped[float] = mapped_column(Numeric(8, 2, asdecimal=False), nullable=False)
    valor_comissao: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False)
    conta_pagar_id: Mapped[int | None] = mapped_column(ForeignKey("contas_pagar.conta_pagar_id", ondelete="SET NULL"), nullable=True, index=True)
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("comissoes_lotes.lote_id", ondelete="SET NULL"), nullable=True, index=True)
    origem_comissao_id: Mapped[int | None] = mapped_column(ForeignKey("comissoes_lancamentos.comissao_id", ondelete="SET NULL"), nullable=True)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ComissaoLote(Base):
    __tablename__ = "comissoes_lotes"
    lote_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    funcionario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    data_inicial: Mapped[date] = mapped_column(Date, nullable=False)
    data_final: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    situacao: Mapped[int] = mapped_column(nullable=False, default=1, index=True)
    conta_pagar_id: Mapped[int | None] = mapped_column(ForeignKey("contas_pagar.conta_pagar_id", ondelete="SET NULL"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
