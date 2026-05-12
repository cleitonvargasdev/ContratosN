from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ContratoComodato(Base):
    __tablename__ = "contratos_comodatos"

    comodato_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    contrato_id: Mapped[int] = mapped_column(ForeignKey("contratos.contratos_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    avalista_cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.clientes_id", ondelete="SET NULL"), nullable=True, index=True)

    avalista: Mapped[object | None] = relationship("Cliente", lazy="selectin")

    items: Mapped[list["ContratoComodatoItem"]] = relationship(
        "ContratoComodatoItem",
        back_populates="comodato",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ContratoComodatoItem.item_id.asc()",
    )


class ContratoComodatoItem(Base):
    __tablename__ = "contratos_comodato_itens"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    comodato_id: Mapped[int] = mapped_column(ForeignKey("contratos_comodatos.comodato_id", ondelete="CASCADE"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.produto_id"), nullable=False, index=True)
    descricao_produto: Mapped[str] = mapped_column(String(120), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    valor_unitario: Mapped[float | None] = mapped_column(Numeric(19, 2, asdecimal=False), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    produto: Mapped[object | None] = relationship("Produto", lazy="selectin")

    comodato: Mapped[ContratoComodato] = relationship("ContratoComodato", back_populates="items", lazy="selectin")
