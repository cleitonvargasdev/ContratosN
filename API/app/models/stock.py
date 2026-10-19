from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MovimentoEstoque(Base):
    __tablename__ = "estoque_movimentos"
    __table_args__ = (
        UniqueConstraint("produto_id", "operacao_id", name="uq_estoque_operacao_produto"),
        CheckConstraint("condicao IN ('novo', 'usado')", name="ck_estoque_condicao"),
        CheckConstraint("saldo_depois = saldo_antes + quantidade", name="ck_estoque_saldo"),
    )

    movimento_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.produto_id", ondelete="RESTRICT"), index=True)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("contratos_comodato_itens.item_id", ondelete="RESTRICT"), index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    usuario_nome: Mapped[str] = mapped_column(String(120))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    tipo: Mapped[str] = mapped_column(String(20))
    condicao: Mapped[str] = mapped_column(String(10))
    quantidade: Mapped[int] = mapped_column(Integer)
    saldo_antes: Mapped[int] = mapped_column(Integer)
    saldo_depois: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str] = mapped_column(String(60))
    observacao: Mapped[str | None] = mapped_column(Text)
    operacao_id: Mapped[str] = mapped_column(String(100))
    assinatura: Mapped[str] = mapped_column(String(64))
