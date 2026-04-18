from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Negociacao(Base):
    __tablename__ = "negociacoes"

    negociacao_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.clientes_id", ondelete="SET NULL"), nullable=True, index=True)
    data_negociacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    valor_total_aberto: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    qtde_parcelas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valor_parcela: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    contrato_gerado_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    obs: Mapped[str | None] = mapped_column(Text, nullable=True)
    cobranca_segunda: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cobranca_terca: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cobranca_quarta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cobranca_quinta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cobranca_sexta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cobranca_sabado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cobranca_domingo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cobranca_feriado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cobranca_mensal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cobranca_quinzenal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class NegociacaoContrato(Base):
    __tablename__ = "negociacao_contratos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    negociacao_id: Mapped[int] = mapped_column(ForeignKey("negociacoes.negociacao_id", ondelete="CASCADE"), nullable=False, index=True)
    contrato_id: Mapped[int] = mapped_column(ForeignKey("contratos.contratos_id", ondelete="CASCADE"), nullable=False, index=True)
    valor_aberto: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
