from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UF(Base):
    __tablename__ = "uf"

    uf_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uf: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    uf_nome: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    cod_ibge: Mapped[int | None] = mapped_column(Integer, nullable=True)

    cidades: Mapped[list["Cidade"]] = relationship(back_populates="uf_ref")


class Cidade(Base):
    __tablename__ = "cidades"

    cidade_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uf_id: Mapped[int] = mapped_column(ForeignKey("uf.uf_id", ondelete="RESTRICT"), nullable=False, index=True)
    cidade: Mapped[str] = mapped_column(String(75), nullable=False, index=True)

    uf_ref: Mapped[UF] = relationship(back_populates="cidades")
    bairros: Mapped[list["Bairro"]] = relationship(back_populates="cidade_ref")
    feriados: Mapped[list["Feriado"]] = relationship(back_populates="cidade_ref")


class Bairro(Base):
    __tablename__ = "bairros"

    bairro_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bairro_nome: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    cidade_id: Mapped[int] = mapped_column(ForeignKey("cidades.cidade_id", ondelete="RESTRICT"), nullable=False, index=True)

    cidade_ref: Mapped[Cidade] = relationship(back_populates="bairros")


class Feriado(Base):
    __tablename__ = "feriados"

    feriado_id: Mapped[int] = mapped_column("feriados_id", Integer, primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column("data", Date, nullable=False, index=True)
    cidade_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cidades.cidade_id", ondelete="SET NULL"), nullable=True, index=True)
    uf: Mapped[str | None] = mapped_column(String(2), ForeignKey("uf.uf", ondelete="SET NULL"), nullable=True, index=True)
    descricao: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    nivel: Mapped[int] = mapped_column(Numeric(1, 0, asdecimal=False), nullable=False, index=True)

    cidade_ref: Mapped[Cidade | None] = relationship(back_populates="feriados")