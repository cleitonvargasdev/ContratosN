from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.client import Cliente
    from app.models.supplier import Fornecedor
    from app.models.user import User


class ContaPagar(Base):
    __tablename__ = "contas_pagar"

    conta_pagar_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    descricao: Mapped[str] = mapped_column(String(160), nullable=False)
    tipo_pessoa: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.clientes_id", ondelete="RESTRICT"), nullable=True, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True, index=True)
    fornecedor_id: Mapped[int | None] = mapped_column(ForeignKey("fornecedores.fornecedor_id", ondelete="RESTRICT"), nullable=True, index=True)
    data_referencia_inicial: Mapped[date | None] = mapped_column(Date(), nullable=True, index=True)
    data_referencia_final: Mapped[date | None] = mapped_column(Date(), nullable=True, index=True)
    observacao: Mapped[str | None] = mapped_column(Text(), nullable=True)
    valor_total: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    valor_pago: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    saldo_pagar: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    quitado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    usuario_lancamento_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    cliente: Mapped["Cliente | None"] = relationship("Cliente", foreign_keys=[cliente_id], lazy="selectin")
    usuario: Mapped["User | None"] = relationship("User", foreign_keys=[usuario_id], lazy="selectin")
    fornecedor: Mapped["Fornecedor | None"] = relationship("Fornecedor", foreign_keys=[fornecedor_id], lazy="selectin")
    parcelas: Mapped[list["ContaPagarParcela"]] = relationship(
        "ContaPagarParcela",
        back_populates="conta",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ContaPagarParcela.numero_parcela",
    )


class ContaPagarParcela(Base):
    __tablename__ = "contas_pagar_parcelas"

    parcela_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conta_pagar_id: Mapped[int] = mapped_column(ForeignKey("contas_pagar.conta_pagar_id", ondelete="CASCADE"), nullable=False, index=True)
    numero_parcela: Mapped[int] = mapped_column(Integer, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(160), nullable=True)
    data_referencia_inicial: Mapped[date | None] = mapped_column(Date(), nullable=True, index=True)
    data_referencia_final: Mapped[date | None] = mapped_column(Date(), nullable=True, index=True)
    vencimento: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    valor_original: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    acrescimos: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    desconto: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    valor_total: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    valor_pago: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    saldo_pagar: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    quitado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    observacao: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    conta: Mapped[ContaPagar] = relationship("ContaPagar", back_populates="parcelas", lazy="selectin")
    pagamentos: Mapped[list["PagamentoContaPagar"]] = relationship(
        "PagamentoContaPagar",
        back_populates="parcela",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PagamentoContaPagar.data_pagamento",
    )


class PagamentoContaPagar(Base):
    __tablename__ = "contas_pagar_pagamentos"

    pagamento_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    parcela_id: Mapped[int] = mapped_column(ForeignKey("contas_pagar_parcelas.parcela_id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    data_pagamento: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    valor_pago: Mapped[float] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=False, default=0)
    juros: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    acrescimos: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    desconto: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    observacao: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parcela: Mapped[ContaPagarParcela] = relationship("ContaPagarParcela", back_populates="pagamentos", lazy="selectin")
    usuario: Mapped["User | None"] = relationship("User", foreign_keys=[usuario_id], lazy="selectin")