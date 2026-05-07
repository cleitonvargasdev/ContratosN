from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Marca(Base):
    __tablename__ = "marcas"

    marca_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    descricao: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)

    produtos: Mapped[list["Produto"]] = relationship("Produto", back_populates="marca", lazy="selectin")


class Produto(Base):
    __tablename__ = "produtos"

    produto_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    descricao: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    valor_compra: Mapped[float | None] = mapped_column(Numeric(19, 2, asdecimal=False), nullable=True)
    valor_venda: Mapped[float | None] = mapped_column(Numeric(19, 2, asdecimal=False), nullable=True)
    marca_id: Mapped[int | None] = mapped_column(ForeignKey("marcas.marca_id", ondelete="SET NULL"), nullable=True, index=True)
    garantia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    estoque: Mapped[int | None] = mapped_column(Integer, nullable=True)
    modelo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cor: Mapped[str | None] = mapped_column(String(15), nullable=True)

    marca: Mapped[Marca | None] = relationship("Marca", back_populates="produtos", lazy="selectin")

    @property
    def marca_descricao(self) -> str | None:
        return self.marca.descricao if self.marca else None