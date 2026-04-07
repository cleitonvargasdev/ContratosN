from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Contrato(Base):
    __tablename__ = "contratos"

    contratos_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False, index=True)
    data_lancto: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    data_contrato: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.clientes_id", ondelete="SET NULL"), nullable=True, index=True)
    plano_id: Mapped[int | None] = mapped_column(ForeignKey("planos_pagamentos.planos_id", ondelete="SET NULL"), nullable=True, index=True)
    qtde_dias: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percent_juros: Mapped[float | None] = mapped_column(Float, nullable=True)
    valor_empretismo: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    data_final: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valor_final: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    valor_recebido: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    valor_em_aberto: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    valor_em_atraso: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    quitado: Mapped[bool | None] = mapped_column(nullable=True)
    obs: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_parcela: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    user_add: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    contrato_status: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    negociacao_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    usuario_id_vendedor: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    comissao_percentual: Mapped[float | None] = mapped_column(Numeric(19, 0, asdecimal=False), nullable=True)
    valor_comissao_previsto: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    valor_comissao_apurada: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    regra_comissao_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    regra_juros_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    recorrencia: Mapped[bool | None] = mapped_column(Boolean, nullable=True)