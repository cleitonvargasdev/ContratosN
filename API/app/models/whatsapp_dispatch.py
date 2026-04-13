from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WhatsAppDispatchBatch(Base):
    __tablename__ = "whatsapp_dispatch_batches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    parametros_id: Mapped[int | None] = mapped_column(ForeignKey("parametros.parametros_id", ondelete="SET NULL"), nullable=True, index=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    source_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    schedule_snapshot: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    summary_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_errors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class WhatsAppDispatchItem(Base):
    __tablename__ = "whatsapp_dispatch_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_dispatch_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    conta_receber_id: Mapped[int | None] = mapped_column(ForeignKey("contas_receber.id", ondelete="SET NULL"), nullable=True, index=True)
    contratos_id: Mapped[int | None] = mapped_column(ForeignKey("contratos.contratos_id", ondelete="SET NULL"), nullable=True, index=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.clientes_id", ondelete="SET NULL"), nullable=True, index=True)
    parcela_nro: Mapped[int | None] = mapped_column(Integer, nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    destination_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    amount: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    message_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    provider_payload: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)