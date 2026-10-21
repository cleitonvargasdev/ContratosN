from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MobileBatch(Base):
    __tablename__ = "mobile_batches"
    __table_args__ = (UniqueConstraint("user_id", "source_id", name="uq_mobile_batches_user_source"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created", index=True)
    blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    execution_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unlocked_by_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    unlock_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class MobileBatchItem(Base):
    __tablename__ = "mobile_batch_items"
    __table_args__ = (
        UniqueConstraint("batch_id", "source_item_id", name="uq_mobile_batch_items_source"),
        # A device operation may only belong to one batch for the collector.
        # This is the second idempotency barrier, in addition to the batch key.
        UniqueConstraint("user_id", "source_item_id", name="uq_mobile_batch_items_user_source"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("mobile_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_item_id: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.clientes_id", ondelete="SET NULL"), nullable=True, index=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contratos.contratos_id", ondelete="SET NULL"), nullable=True, index=True)
    installment_id: Mapped[int | None] = mapped_column(ForeignKey("contas_receber.id", ondelete="SET NULL"), nullable=True, index=True)
    amount: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    latitude: Mapped[str | None] = mapped_column(String(50), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gps_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    device_recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    server_date: Mapped[date] = mapped_column(Date, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_id: Mapped[int | None] = mapped_column(ForeignKey("recebimentos.recebimento_id", ondelete="SET NULL"), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MobileOccurrence(Base):
    __tablename__ = "mobile_occurrences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("mobile_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("mobile_batch_items.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.clientes_id", ondelete="SET NULL"), nullable=True, index=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contratos.contratos_id", ondelete="SET NULL"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    latitude: Mapped[str | None] = mapped_column(String(50), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gps_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    device_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    server_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
