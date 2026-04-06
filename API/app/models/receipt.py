from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Recebimento(Base):
    __tablename__ = "recebimentos"

    recebimento_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    contrato_id: Mapped[int | None] = mapped_column(ForeignKey("contratos.contratos_id", ondelete="SET NULL"), nullable=True, index=True)
    valor_recebido: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    data_recebimento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    parcela_nro: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latitude: Mapped[str | None] = mapped_column(String(50), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(50), nullable=True)
    desconto: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    juros: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    lote_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    item_lote_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)