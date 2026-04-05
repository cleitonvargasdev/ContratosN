from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.access_control import Profile, ProfilePermission, UserApiKey


class User(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    login: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    funcao: Mapped[str] = mapped_column(String(40), default="Operador", nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    celular: Mapped[str | None] = mapped_column(String(20), nullable=True)
    flag_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cep: Mapped[str | None] = mapped_column(String(8), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    numero: Mapped[str | None] = mapped_column(String(20), nullable=True)
    complemento: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bairro_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("bairros.bairro_id", ondelete="SET NULL"), nullable=True)
    cidade_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cidades.cidade_id", ondelete="SET NULL"), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), ForeignKey("uf.uf", ondelete="SET NULL"), nullable=True)
    perfil_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("perfis.id", ondelete="SET NULL"), nullable=True, index=True)
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
    rg: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_nascimento: Mapped[date | None] = mapped_column(Date(), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    profile: Mapped["Profile | None"] = relationship("Profile", back_populates="users", lazy="selectin")
    api_key: Mapped["UserApiKey | None"] = relationship(
        "UserApiKey",
        back_populates="user",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def perfil_nome(self) -> str | None:
        return self.profile.nome if self.profile is not None else None

    @property
    def permissions(self) -> list["ProfilePermission"]:
        if self.profile is None:
            return []
        return list(self.profile.permissions)

    @property
    def api_key_info(self) -> "UserApiKey | None":
        return self.api_key
