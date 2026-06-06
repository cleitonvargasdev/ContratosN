from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    fornecedor_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    cpf_cnpj: Mapped[str | None] = mapped_column(String(18), nullable=True, index=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    cep: Mapped[str | None] = mapped_column(String(8), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(180), nullable=True)
    numero: Mapped[str | None] = mapped_column(String(20), nullable=True)
    complemento: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bairro: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cidade: Mapped[str | None] = mapped_column(String(120), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )