from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WhatsAppChatbotSession(Base):
    __tablename__ = "whatsapp_chatbot_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.clientes_id", ondelete="SET NULL"), nullable=True, index=True)
    current_state: Mapped[str] = mapped_column(String(40), nullable=False, default="AWAITING_NAME")
    identified_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    identified_document: Mapped[str | None] = mapped_column(String(18), nullable=True)
    context_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_interaction_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opted_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Solicitacao(Base):
    __tablename__ = "solicitacoes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.clientes_id", ondelete="SET NULL"), nullable=True, index=True)
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("whatsapp_chatbot_sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    nome_informado: Mapped[str | None] = mapped_column(String(120), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    cpf_cnpj: Mapped[str | None] = mapped_column(String(18), nullable=True, index=True)
    valor_pretendido: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    frequencia_pagamento: Mapped[str | None] = mapped_column(String(20), nullable=True)
    numero_parcelas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="WhatsApp")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDENTE")
    vendedor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    valor_parcela: Mapped[float | None] = mapped_column(Numeric(19, 4, asdecimal=False), nullable=True)
    taxa_juros: Mapped[float | None] = mapped_column(Numeric(19, 6, asdecimal=False), nullable=True)
    contrato_id: Mapped[int | None] = mapped_column(ForeignKey("contratos.contratos_id", ondelete="SET NULL"), nullable=True, index=True)
    usuario_id_aprovou: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    datahora_solicitacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    datahora_aprovacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)