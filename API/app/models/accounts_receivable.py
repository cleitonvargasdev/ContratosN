from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContaReceber(Base):
    __tablename__ = "contas_receber"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contratos_id: Mapped[int | None] = mapped_column(ForeignKey("contratos.contratos_id", ondelete="SET NULL"), nullable=True, index=True)
    vencimento_original: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    vencimentol: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    valor_base: Mapped[float | None] = mapped_column(Float, nullable=True)
    valor_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_recebimento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valor_recebido: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    percent_juros: Mapped[float | None] = mapped_column(Float, nullable=True)
    quitado: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    usuarios_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    parcela_nro: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valor_juros: Mapped[float | None] = mapped_column(Float, nullable=True)
    dias_atraso_quitacao: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dias_atrasado: Mapped[int | None] = mapped_column(Integer, nullable=True)
    desconto: Mapped[float | None] = mapped_column(Float, nullable=True)
    prorrogada: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    msg_whatsapp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dt_hora_envio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tipo_envio: Mapped[int | None] = mapped_column(Integer, nullable=True)