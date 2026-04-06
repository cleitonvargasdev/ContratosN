from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Parametro(Base):
    __tablename__ = "parametros"

    parametros_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    nome_fantasia: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    razao_social: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    endereco: Mapped[str | None] = mapped_column(String(70), nullable=True)
    bairrosid: Mapped[int | None] = mapped_column(ForeignKey("bairros.bairro_id", ondelete="SET NULL"), nullable=True, index=True)
    cep: Mapped[str | None] = mapped_column(String(9), nullable=True)
    nro: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cnpj: Mapped[str | None] = mapped_column(String(18), nullable=True, index=True)
    uf: Mapped[str | None] = mapped_column(String(2), ForeignKey("uf.uf", ondelete="SET NULL"), nullable=True, index=True)
    cidade_id: Mapped[int | None] = mapped_column(ForeignKey("cidades.cidade_id", ondelete="SET NULL"), nullable=True, index=True)
    telefone1: Mapped[str | None] = mapped_column(String(17), nullable=True)
    telefone2: Mapped[str | None] = mapped_column(String(17), nullable=True)
    e_mail: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    responsavel: Mapped[str | None] = mapped_column(String(120), nullable=True)
    complemento: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
    rg: Mapped[str | None] = mapped_column(String(25), nullable=True)
    cidade_id_responsavel: Mapped[int | None] = mapped_column(ForeignKey("cidades.cidade_id", ondelete="SET NULL"), nullable=True)
    bairro_id_responsavel: Mapped[int | None] = mapped_column(ForeignKey("bairros.bairro_id", ondelete="SET NULL"), nullable=True)
    uf_responsavel: Mapped[str | None] = mapped_column(String(2), ForeignKey("uf.uf", ondelete="SET NULL"), nullable=True)
    estado_civil: Mapped[str | None] = mapped_column(String(30), nullable=True)
    nacionalidade: Mapped[str | None] = mapped_column(String(40), nullable=True)
    endereco_responsavel: Mapped[str | None] = mapped_column(String(80), nullable=True)