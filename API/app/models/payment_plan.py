from sqlalchemy import BigInteger, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaymentPlan(Base):
    __tablename__ = "planos_pagamentos"

    plano_id: Mapped[int] = mapped_column("planos_id", BigInteger, primary_key=True, autoincrement=True)
    descricao: Mapped[str | None] = mapped_column("descricao", String(50), nullable=True, index=True)
    qtde_dias: Mapped[int | None] = mapped_column("qtde_dias", Integer, nullable=True)
    percent_juros: Mapped[float | None] = mapped_column("percent_juros", Float, nullable=True)
    valor_parcela: Mapped[float | None] = mapped_column("valor_parcela", Float, nullable=True)
    valor_base: Mapped[float | None] = mapped_column("valor_base", Float, nullable=True)
    valor_final: Mapped[float | None] = mapped_column("valor_final", Float, nullable=True)