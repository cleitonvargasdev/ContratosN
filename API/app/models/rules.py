from sqlalchemy import BigInteger, Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RegraJuros(Base):
    __tablename__ = "regras_juros"

    regra_juros_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    descricao: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    juros_dia: Mapped[float | None] = mapped_column(Numeric(8, 2, asdecimal=False), nullable=True)
    mora_dia: Mapped[float | None] = mapped_column(Numeric(8, 2, asdecimal=False), nullable=True)
    ativo: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class RegraComissao(Base):
    __tablename__ = "regras_comissao"

    regra_comissao_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    descricao: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    percentual_comissao: Mapped[float | None] = mapped_column(Numeric(8, 2, asdecimal=False), nullable=True)
    com_quitacao: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    a_partir_perc_total: Mapped[float | None] = mapped_column(Numeric(8, 2, asdecimal=False), nullable=True)
    ativo: Mapped[bool | None] = mapped_column(Boolean, nullable=True)